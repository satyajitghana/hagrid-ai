# Fyers Broker SDK

A comprehensive Python SDK for interacting with the Fyers trading API, including OAuth authentication, rate limiting, WebSocket support, and comprehensive logging.

## Features

- **Smart Token Management**: Auto-loads and validates saved tokens - no explicit auth call needed if token exists
- **OAuth Authentication**: Complete OAuth 2.0 flow with automatic browser-based login
- **Token Validation**: Uses Profile API to verify tokens actually work (not just local expiry check)
- **Rate Limiting**: Built-in rate limiting to comply with API limits
- **WebSocket Support**: Real-time updates for orders, trades, positions, and market data
- **Symbol Master**: Easy symbol lookup and management
- **Environment Variables**: Support for loading credentials from env vars
- **Comprehensive Logging**: Detailed logging for debugging

## Installation

```bash
# Install from source (development)
pip install -e .
```

## Quick Start (Recommended)

The simplest way to get started - just works if you have a valid token saved!

```python
from broker.fyers import create_client

# Create client with token file
client = create_client(
    client_id="TX4LY7JMLL-100",
    secret_key="YOUR_SECRET",
    token_file="fyers_token.json",  # Saves/loads token here
)

# Check if ready (token was loaded and validated with Profile API)
if client.is_authenticated:
    print(f"Welcome back, {client.user_name}!")
    # Client is ready to use - no authenticate() call needed!
else:
    # No valid token, need to authenticate (opens browser automatically)
    client.authenticate_sync()

# Make API calls
import asyncio
quotes = asyncio.run(client.get_quotes(["NSE:SBIN-EQ"]))
print(quotes)
```

### Using Environment Variables

```bash
# Set environment variables
export FYERS_CLIENT_ID="TX4LY7JMLL-100"
export FYERS_SECRET_KEY="YOUR_SECRET"
export FYERS_TOKEN_FILE="fyers_token.json"  # Optional
```

```python
from broker.fyers import create_client_from_env

# Creates client from env vars - super clean!
client = create_client_from_env()

if client.is_authenticated:
    print(f"Hello, {client.user_name}!")
else:
    client.authenticate_sync()
```

### Auto-Authenticate Option

```python
from broker.fyers import create_client

# This will always result in an authenticated client
client = create_client(
    client_id="TX4LY7JMLL-100",
    secret_key="YOUR_SECRET",
    token_file="fyers_token.json",
    auto_authenticate=True,  # Opens browser if no valid token
)

# Client is GUARANTEED to be authenticated here
quotes = asyncio.run(client.get_quotes(["NSE:SBIN-EQ"]))
```

### Async Context Manager

```python
from broker.fyers import FyersClient, FyersConfig

config = FyersConfig(
    client_id="YOUR_CLIENT_ID",
    secret_key="YOUR_SECRET_KEY",
    token_file_path="fyers_token.json",
)

async with FyersClient(config) as client:
    # Token auto-loaded and validated if available!
    if client.is_authenticated:
        print(f"Welcome, {client.user_name}!")
        quotes = await client.get_quotes(["NSE:INFY-EQ"])
    else:
        await client.authenticate()  # Opens browser
        quotes = await client.get_quotes(["NSE:INFY-EQ"])
```

### User Info Properties

Once authenticated, you have easy access to user info:

```python
# After authentication
print(f"Name: {client.user_name}")
print(f"Fyers ID: {client.user_id}")
print(f"Email: {client.user_email}")

# Or get full profile
if client.user_profile:
    print(f"TOTP enabled: {client.user_profile.totp}")
    print(f"MTF enabled: {client.user_profile.mtf_enabled}")
```

## Authentication

### Automatic Authentication (Recommended)

The easiest way to authenticate - no manual copy-paste required!

```python
# Step 1: Register redirect URI in Fyers dashboard
# Go to: https://myapi.fyers.in/dashboard
# Add redirect URI: http://127.0.0.1:9000/

# Step 2: Configure client with the same redirect URI
config = FyersConfig(
    client_id="YOUR_CLIENT_ID",
    secret_key="YOUR_SECRET_KEY",
    redirect_uri="http://127.0.0.1:9000/",  # Must match dashboard
)

client = FyersClient(config)

# Step 3: Authenticate automatically
# Browser opens, you login, callback is captured automatically
await client.authenticate_with_callback_server()

# That's it! No copy-paste needed.
```

**How it works:**
1. Starts a local HTTP server on the configured port
2. Opens your browser to the Fyers login page
3. After you login, Fyers redirects to your local server
4. The server captures the auth code automatically
5. Exchanges it for an access token

**Requirements:**
- The redirect URI must be registered in Fyers dashboard beforehand
- The configured port must be available (not used by another app)
- Supports localhost URLs only (127.0.0.1 or localhost)

### Manual OAuth Flow

For cases where automatic callback isn't possible:

```python
# 1. Generate auth URL
auth_url = client.generate_auth_url(state="random_state_string")

# 2. User visits URL and authenticates
# 3. Capture redirect URL with auth_code

# 4. Exchange auth code for access token
await client.authenticate(redirect_url)

# Or use auth code directly
await client.authenticate_with_auth_code(auth_code)
```

### Token Management

```python
# Load previously saved token
loaded = await client.load_saved_token()
if not loaded:
    # Need to re-authenticate
    pass

# Refresh token (requires PIN)
await client.refresh_token(pin="1234")

# Check authentication status
if client.is_authenticated:
    print("Ready to trade!")

# Logout
await client.logout()
```

## Market Data APIs

### Quotes

```python
# Get quotes for multiple symbols (max 50)
quotes = await client.get_quotes(["NSE:SBIN-EQ", "NSE:INFY-EQ"])
```

### Market Depth

```python
# Get 5-level order book
depth = await client.get_market_depth("NSE:SBIN-EQ")
```

### Historical Data

```python
# Get historical candles
history = await client.get_history(
    symbol="NSE:SBIN-EQ",
    resolution="D",  # Daily candles
    date_format=1,   # YYYY-MM-DD format
    range_from="2024-01-01",
    range_to="2024-01-31",
)
```

### Option Chain

```python
# Get option chain
chain = await client.get_option_chain(
    symbol="NSE:NIFTY-INDEX",
    strike_count=10,  # 10 ITM + ATM + 10 OTM
)
```

## Order APIs

### Place Orders

```python
from broker.fyers import create_market_order, create_limit_order

# Market order
order = create_market_order(
    symbol="NSE:SBIN-EQ",
    qty=1,
    side=1,  # 1=Buy, -1=Sell
    product_type="INTRADAY",
)
response = await client.place_order(order)

# Limit order
order = create_limit_order(
    symbol="NSE:SBIN-EQ",
    qty=1,
    side=1,
    limit_price=500.0,
    product_type="INTRADAY",
)
response = await client.place_order(order)
```

### Modify & Cancel Orders

```python
# Modify order
await client.modify_order(
    order_id="order_123",
    modifications={"qty": 2, "limitPrice": 510.0}
)

# Cancel order
await client.cancel_order(order_id="order_123")

# Cancel multiple orders
await client.cancel_multi_order(["order_123", "order_456"])
```

### Get Orders

```python
# Get all orders
orders = await client.get_orders()

# Get specific order
order = await client.get_order_by_id("order_123")
```

## Position APIs

```python
# Get positions
positions = await client.get_positions()

# Exit position
await client.exit_position(position_id="pos_123")

# Exit all positions
await client.exit_position()

# Convert position
await client.convert_position({
    "symbol": "NSE:SBIN-EQ",
    "positionSide": 1,
    "convertQty": 1,
    "convertFrom": "INTRADAY",
    "convertTo": "CNC",
})
```

## Portfolio APIs

```python
# Get holdings
holdings = await client.get_holdings()

# Get funds
funds = await client.get_funds()

# Get profile
profile = await client.get_profile()

# Get tradebook
trades = await client.get_tradebook()
```

---

# WebSocket Support

The SDK provides comprehensive WebSocket support for real-time updates.

## Order WebSocket

For real-time order, trade, and position updates.

### Async Usage

```python
import asyncio
from broker.fyers import FyersClient, FyersOrderWebSocket, OrderUpdate, TradeUpdate

async def main():
    # Setup client and authenticate first
    client = FyersClient(config)
    await client.authenticate(redirect_url)
    
    # Define callbacks
    async def on_order(order: OrderUpdate):
        print(f"Order {order.id}: {order.status_name}")
        print(f"  Symbol: {order.symbol}")
        print(f"  Side: {'Buy' if order.is_buy else 'Sell'}")
        print(f"  Qty: {order.qty}, Filled: {order.filled_qty}")
    
    async def on_trade(trade: TradeUpdate):
        print(f"Trade: {trade.trade_number}")
        print(f"  Price: {trade.trade_price}")
        print(f"  Qty: {trade.traded_qty}")
    
    async def on_position(position: PositionUpdate):
        print(f"Position: {position.symbol}")
        print(f"  Net Qty: {position.net_qty}")
        print(f"  P&L: {position.realized_profit}")
    
    # Create WebSocket
    ws = client.create_order_websocket(
        on_order=on_order,
        on_trade=on_trade,
        on_position=on_position,
    )
    
    # Connect and subscribe
    await ws.connect()
    await ws.subscribe_all()  # Or specific: subscribe_orders(), subscribe_trades()
    
    # Keep running
    try:
        await ws.keep_running()
    finally:
        await ws.close()

asyncio.run(main())
```

### Using Context Manager

```python
async with client.create_order_websocket(on_order=on_order) as ws:
    await ws.subscribe_orders()
    await ws.keep_running()
```

### Synchronous Usage

```python
from broker.fyers import FyersClient

def on_order(message):
    print(f"Order: {message}")

# Create sync WebSocket
ws = client.create_order_websocket_sync(on_order=on_order)

ws.connect()
ws.subscribe_orders()
ws.keep_running()  # Blocks
```

### Subscription Types

```python
from broker.fyers import SubscriptionType

# Subscribe to specific types
await ws.subscribe(
    SubscriptionType.ORDERS,
    SubscriptionType.TRADES,
    SubscriptionType.POSITIONS,
    SubscriptionType.GENERAL,
)

# Or use convenience methods
await ws.subscribe_orders()
await ws.subscribe_trades()
await ws.subscribe_positions()
await ws.subscribe_all()

# Unsubscribe
await ws.unsubscribe(SubscriptionType.POSITIONS)
```

## Data WebSocket

For real-time market data (up to 5000 symbols).

### Async Usage

```python
import asyncio
from broker.fyers import FyersClient, SymbolUpdate, DepthUpdate

async def main():
    client = FyersClient(config)
    await client.authenticate(redirect_url)
    
    # Define callback
    async def on_tick(data: SymbolUpdate):
        print(f"{data.symbol}: ₹{data.ltp} ({data.chp:+.2f}%)")
        print(f"  Bid: {data.bid_price} x {data.bid_size}")
        print(f"  Ask: {data.ask_price} x {data.ask_size}")
        print(f"  Volume: {data.vol_traded_today}")
    
    # Create WebSocket
    ws = client.create_data_websocket(on_message=on_tick)
    
    # Connect and subscribe
    await ws.connect()
    await ws.subscribe([
        "NSE:SBIN-EQ",
        "NSE:INFY-EQ",
        "NSE:RELIANCE-EQ",
        "NSE:NIFTY50-INDEX",
    ])
    
    # Keep running
    try:
        await ws.keep_running()
    finally:
        await ws.close()

asyncio.run(main())
```

### Market Depth Subscription

```python
from broker.fyers import DataType, DepthUpdate

async def on_depth(data: DepthUpdate):
    print(f"Depth for {data.symbol}")
    for bid in data.bids:
        print(f"  Bid: {bid['price']} x {bid['size']}")
    for ask in data.asks:
        print(f"  Ask: {ask['price']} x {ask['size']}")

ws = client.create_data_websocket(on_message=on_depth)
await ws.connect()
await ws.subscribe_depth_updates(["NSE:SBIN-EQ"])
```

### Lite Mode (LTP Only)

For lower bandwidth usage when you only need LTP:

```python
from broker.fyers import WebSocketConfig

config = WebSocketConfig(lite_mode=True)
ws = client.create_data_websocket(
    on_message=on_tick,
    config=config,
)
```

### Synchronous Usage

```python
def on_tick(message):
    print(f"Tick: {message['symbol']} @ {message['ltp']}")

ws = client.create_data_websocket_sync(on_message=on_tick)
ws.connect()
ws.subscribe(["NSE:SBIN-EQ", "NSE:INFY-EQ"])
ws.keep_running()  # Blocks
```

### Managing Subscriptions

```python
# Subscribe
await ws.subscribe(["NSE:SBIN-EQ", "NSE:INFY-EQ"])

# Add more symbols
await ws.subscribe(["NSE:RELIANCE-EQ", "NSE:TCS-EQ"])

# Unsubscribe
await ws.unsubscribe(["NSE:SBIN-EQ"])

# Check subscribed symbols
print(ws.subscribed_symbols)
print(f"Total subscriptions: {ws.subscription_count}")
```

## WebSocket Configuration

```python
from broker.fyers import WebSocketConfig

config = WebSocketConfig(
    reconnect=True,              # Enable auto-reconnect
    max_reconnect_attempts=50,   # Max retry attempts
    reconnect_delay=5,           # Delay between retries (seconds)
    write_to_file=False,         # Write to log file
    log_path="/path/to/logs",    # Log directory
    lite_mode=False,             # Lite mode for data socket
)

ws = client.create_data_websocket(config=config)
```

## WebSocket Models

### OrderUpdate

```python
class OrderUpdate:
    id: str                    # Order ID
    symbol: str                # Symbol
    qty: int                   # Quantity
    filled_qty: int            # Filled quantity
    remaining_quantity: int    # Remaining quantity
    limit_price: float         # Limit price
    stop_price: float          # Stop price
    status: int                # Status code
    status_name: str           # Human-readable status
    side: int                  # 1=Buy, -1=Sell
    is_buy: bool               # Is buy order
    is_complete: bool          # Is order complete
    product_type: str          # Product type
    order_type: int            # Order type
    order_datetime: str        # Order time
    ...
```

### TradeUpdate

```python
class TradeUpdate:
    trade_number: str          # Trade number
    order_number: str          # Associated order ID
    symbol: str                # Symbol
    trade_price: float         # Execution price
    trade_value: float         # Trade value
    traded_qty: int            # Traded quantity
    side: int                  # 1=Buy, -1=Sell
    ...
```

### PositionUpdate

```python
class PositionUpdate:
    symbol: str                # Symbol
    net_qty: int               # Net quantity
    net_avg: float             # Net average price
    buy_qty: int               # Buy quantity
    buy_avg: float             # Buy average
    sell_qty: int              # Sell quantity
    sell_avg: float            # Sell average
    realized_profit: float     # Realized P&L
    is_long: bool              # Long position
    is_short: bool             # Short position
    is_closed: bool            # Position closed
    ...
```

### SymbolUpdate

```python
class SymbolUpdate:
    symbol: str                # Symbol
    ltp: float                 # Last traded price
    ch: float                  # Price change
    chp: float                 # Change percentage
    open_price: float          # Day open
    high_price: float          # Day high
    low_price: float           # Day low
    prev_close_price: float    # Previous close
    vol_traded_today: int      # Volume
    bid_price: float           # Best bid
    ask_price: float           # Best ask
    bid_size: int              # Bid size
    ask_size: int              # Ask size
    ...
```

### DepthUpdate

```python
class DepthUpdate:
    symbol: str                # Symbol
    bids: List[Dict]           # 5 bid levels
    asks: List[Dict]           # 5 ask levels
    # Each level has: price, size, orders
```

---

## TBT (Tick-by-Tick) WebSocket

For 50-level market depth data on NFO and NSE instruments.

### Key Features

- **50 levels of market depth** (vs 5 levels in standard depth)
- **Available for NFO and NSE instruments only**
- **Incremental updates** (diff packets after initial snapshot)
- **Channel-based subscription management**

### Rate Limits

- Max 3 active connections per app per user
- Max 5 symbols per connection
- Max 50 channels per connection (1-50)

### Async Usage

```python
import asyncio
from broker.fyers import FyersClient, TBTDepth, TBTConfig

async def main():
    client = FyersClient(config)
    await client.authenticate(redirect_url)
    
    # Define callback
    async def on_depth(depth: TBTDepth):
        print(f"{depth.symbol}:")
        print(f"  Total Buy Qty: {depth.total_buy_qty}")
        print(f"  Total Sell Qty: {depth.total_sell_qty}")
        
        if depth.best_bid:
            print(f"  Best Bid: {depth.best_bid.price} x {depth.best_bid.qty}")
        if depth.best_ask:
            print(f"  Best Ask: {depth.best_ask.price} x {depth.best_ask.qty}")
        
        print(f"  Spread: {depth.spread}")
        print(f"  Snapshot: {depth.is_snapshot}")
        
        # Access all 50 levels
        for i, bid in enumerate(depth.bids[:5]):  # First 5 bids
            print(f"  Bid {i+1}: {bid.price} x {bid.qty} ({bid.num_orders} orders)")
    
    # Create TBT WebSocket
    ws = client.create_tbt_websocket(on_depth_update=on_depth)
    
    # Connect
    await ws.connect()
    
    # Subscribe to symbols on a channel
    await ws.subscribe(
        symbols=["NSE:NIFTY25MARFUT", "NSE:BANKNIFTY25MARFUT"],
        channel="1",
    )
    
    # IMPORTANT: Must resume channel to start receiving data
    await ws.switch_channel(resume=["1"])
    
    # Keep running
    try:
        await ws.keep_running()
    finally:
        await ws.close()

asyncio.run(main())
```

### Channel Management

Channels allow you to organize subscriptions and control data flow:

```python
# Subscribe to different symbols on different channels
await ws.subscribe(["NSE:NIFTY25MARFUT"], channel="1")  # Nifty channel
await ws.subscribe(["NSE:BANKNIFTY25MARFUT"], channel="2")  # BankNifty channel

# Start receiving data from channel 1 only
await ws.switch_channel(resume=["1"])

# Switch to channel 2 (pause 1, resume 2)
await ws.switch_channel(resume=["2"], pause=["1"])

# Receive from both channels
await ws.switch_channel(resume=["1", "2"])

# Pause all channels
await ws.switch_channel(pause=["1", "2"])
```

### Synchronous Usage

```python
from broker.fyers import FyersTBTWebSocketSync

def on_depth(ticker, depth):
    print(f"{ticker}: TBQ={depth.tbq}, TSQ={depth.tsq}")
    print(f"  Bids: {depth.bidprice[:5]}")
    print(f"  Asks: {depth.askprice[:5]}")

ws = client.create_tbt_websocket_sync(on_depth_update=on_depth)
ws.connect()
ws.subscribe(["NSE:NIFTY25MARFUT"], channel="1")
ws.switch_channel(resume=["1"])
ws.keep_running()  # Blocks
```

### TBT Configuration

```python
from broker.fyers import TBTConfig

config = TBTConfig(
    reconnect=True,              # Enable auto-reconnect
    max_reconnect_attempts=50,   # Max retry attempts
    write_to_file=False,         # Write to log file
    log_path="/path/to/logs",    # Log directory
    diff_only=False,             # If True, callbacks receive diff packets only
)

ws = client.create_tbt_websocket(config=config)
```

### TBTDepth Model

```python
@dataclass
class TBTDepth:
    symbol: str                    # Symbol ticker
    total_buy_qty: int             # Total buy quantity
    total_sell_qty: int            # Total sell quantity
    bid_prices: List[float]        # 50 bid prices
    ask_prices: List[float]        # 50 ask prices
    bid_quantities: List[int]      # 50 bid quantities
    ask_quantities: List[int]      # 50 ask quantities
    bid_orders: List[int]          # 50 bid order counts
    ask_orders: List[int]          # 50 ask order counts
    is_snapshot: bool              # True if snapshot, False if diff
    timestamp: int                 # Feed timestamp (epoch)
    send_time: int                 # Server send time (epoch)
    
    # Properties
    bids: List[TBTDepthLevel]      # All bid levels as objects
    asks: List[TBTDepthLevel]      # All ask levels as objects
    best_bid: TBTDepthLevel        # Best (highest) bid
    best_ask: TBTDepthLevel        # Best (lowest) ask
    spread: float                  # Bid-ask spread
```

### TBTDepthLevel Model

```python
@dataclass
class TBTDepthLevel:
    price: float                   # Price level
    qty: int                       # Quantity at this level
    num_orders: int                # Number of orders at this level
```

---

## Rate Limits

The SDK automatically handles Fyers rate limits:

- **Per second**: 10 requests
- **Per minute**: 200 requests
- **Per day**: 100,000 requests

```python
# Check rate limit status
status = client.get_rate_limit_status()
print(status)

# Check remaining daily calls
remaining = client.get_remaining_daily_calls()
print(f"Remaining: {remaining}")

# Check if limit reached
if client.is_daily_limit_reached():
    print("Daily limit reached!")
```

## Exceptions

```python
from broker.fyers import (
    FyersException,
    FyersAuthenticationError,
    FyersRateLimitError,
    FyersAPIError,
    FyersTokenExpiredError,
    FyersTokenNotFoundError,
    FyersNetworkError,
)

try:
    await client.get_quotes(["NSE:SBIN-EQ"])
except FyersRateLimitError as e:
    print(f"Rate limit: {e}")
except FyersAuthenticationError as e:
    print(f"Auth error: {e}")
except FyersAPIError as e:
    print(f"API error: {e}")
```

## Logging

```python
from broker.fyers import configure_logging, get_logger
import logging

# Configure logging
configure_logging(
    level=logging.DEBUG,
    log_file="fyers.log",
)

# Get logger for your module
logger = get_logger("my_app")
logger.info("Starting...")
```

## License

MIT License