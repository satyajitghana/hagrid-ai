"""
Paper Trading Module for Fyers Broker.

Provides simulated trading functionality for testing strategies without real money.
All trading operations (orders, positions, funds) are simulated locally while
market data (quotes, history, option chains) still uses the real Fyers API.

Usage:
    ```python
    from broker.fyers.paper_trade import PaperTradeFyersClient
    from broker.fyers.models.config import FyersConfig

    config = FyersConfig.from_env()
    client = PaperTradeFyersClient(
        config=config,
        state_file=".hagrid/paper_trade_state.json",
        initial_balance=100000.0
    )

    # Authenticate for market data access
    await client.authenticate()

    # Place simulated orders
    response = await client.place_order({
        'symbol': 'NSE:SBIN-EQ',
        'qty': 10,
        'side': 1,
        'type': 2,  # Market
        'productType': 'INTRADAY'
    })

    # Get positions with live LTP
    positions = await client.get_positions()

    # Periodic LTP updates
    await client.update_positions_ltp()
    # Or start background updates
    task = await client.start_ltp_updates(interval_seconds=600)
    ```
"""

from .models import (
    PaperTradeState,
    PaperOrder,
    PaperTrade,
    PaperPosition,
    PaperHolding,
    PaperFunds,
    PaperOrderStatus,
)
from .state_manager import PaperTradeStateManager
from .execution import PaperTradeExecutionEngine
from .client import PaperTradeFyersClient

__all__ = [
    # Client
    "PaperTradeFyersClient",
    # Models
    "PaperTradeState",
    "PaperOrder",
    "PaperTrade",
    "PaperPosition",
    "PaperHolding",
    "PaperFunds",
    "PaperOrderStatus",
    # State Management
    "PaperTradeStateManager",
    "PaperTradeExecutionEngine",
]
