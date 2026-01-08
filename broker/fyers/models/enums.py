"""
Enums and constants for the Fyers API.
Based on official Fyers API documentation.
"""

from enum import IntEnum


# ==================== Exchange Codes ====================

class Exchange(IntEnum):
    """Exchange codes."""
    NSE = 10  # National Stock Exchange
    MCX = 11  # Multi Commodity Exchange
    BSE = 12  # Bombay Stock Exchange


# ==================== Segment Codes ====================

class Segment(IntEnum):
    """Market segment codes."""
    CAPITAL_MARKET = 10  # Capital Market (Equity)
    EQUITY_DERIVATIVES = 11  # Equity Derivatives (F&O)
    CURRENCY_DERIVATIVES = 12  # Currency Derivatives
    COMMODITY_DERIVATIVES = 20  # Commodity Derivatives


# ==================== Instrument Types ====================

class InstrumentType(IntEnum):
    """Instrument type codes."""
    # CM segment
    EQ = 0  # Equity
    PREFSHARES = 1  # Preference Shares
    DEBENTURES = 2  # Debentures
    WARRANTS = 3  # Warrants
    MISC_NSE_BSE = 4  # Miscellaneous (NSE, BSE)
    SGB = 5  # Sovereign Gold Bonds
    G_SECS = 6  # Government Securities
    T_BILLS = 7  # Treasury Bills
    MF = 8  # Mutual Funds
    ETF = 9  # Exchange Traded Funds
    INDEX = 10  # Index
    MISC_BSE = 50  # Miscellaneous (BSE)
    
    # FO segment
    FUTIDX = 11  # Index Futures
    FUTIVX = 12  # Index Futures (Volatility)
    FUTSTK = 13  # Stock Futures
    OPTIDX = 14  # Index Options
    OPTSTK = 15  # Stock Options
    
    # CD segment
    FUTCUR = 16  # Currency Futures
    FUTIRT = 17  # Interest Rate Futures
    FUTIRC = 18  # Interest Rate Currency Futures
    OPTCUR = 19  # Currency Options
    UNDCUR = 20  # Underlying Currency
    UNDIRC = 21  # Underlying Interest Rate Currency
    UNDIRT = 22  # Underlying Interest Rate
    UNDIRD = 23  # Underlying Interest Rate Derivatives
    INDEX_CD = 24  # Currency Index
    FUTIRD = 25  # Interest Rate Derivatives Futures
    
    # COM segment
    FUTCOM = 30  # Commodity Futures
    OPTFUT = 31  # Commodity Options on Futures
    OPTCOM = 32  # Commodity Options
    FUTBAS = 33  # Commodity Futures (Basis)
    FUTBLN = 34  # Commodity Futures (Blend)
    FUTENR = 35  # Commodity Futures (Energy)
    OPTBLN = 36  # Commodity Options (Blend)
    OPTFUT_NCOM = 37  # Commodity Options on Futures (NCOM)


# ==================== Order Types ====================

class OrderType(IntEnum):
    """Order types."""
    LIMIT = 1  # Limit order
    MARKET = 2  # Market order
    STOP = 3  # Stop order (SL-M)
    STOP_LIMIT = 4  # Stop-limit order (SL-L)


# ==================== Order Sides ====================

class OrderSide(IntEnum):
    """Order side."""
    BUY = 1  # Buy order
    SELL = -1  # Sell order


# ==================== Order Status ====================

class OrderStatus(IntEnum):
    """Order status codes."""
    CANCELLED = 1  # Order cancelled
    TRADED = 2  # Order traded/filled
    TRANSIT = 4  # Order in transit
    REJECTED = 5  # Order rejected
    PENDING = 6  # Order pending
    EXPIRED = 7  # Order expired (for GTD orders)


# ==================== Position Sides ====================

class PositionSide(IntEnum):
    """Position side."""
    LONG = 1  # Long position
    SHORT = -1  # Short position
    CLOSED = 0  # Closed position


# ==================== Product Types ====================

class ProductType:
    """Product types as strings (not enum since used in requests)."""
    CNC = "CNC"  # Cash and Carry (for equity only)
    INTRADAY = "INTRADAY"  # Intraday (applicable for all segments)
    MARGIN = "MARGIN"  # Margin (applicable only for derivatives)
    CO = "CO"  # Cover Order
    BO = "BO"  # Bracket Order
    MTF = "MTF"  # Margin Trading Facility


# ==================== Order Validity ====================

class OrderValidity:
    """Order validity types."""
    DAY = "DAY"  # Day order
    IOC = "IOC"  # Immediate or Cancel


# ==================== Holding Types ====================

class HoldingType:
    """Holding types."""
    T1 = "T1"  # T+1 holdings (purchased but not yet delivered)
    HLD = "HLD"  # Holdings (delivered to demat account)


# ==================== Order Sources ====================

class OrderSource:
    """Order source codes."""
    MOBILE = "M"  # Mobile app
    WEB = "W"  # Web platform
    FYERS_ONE = "R"  # Fyers One desktop app
    ADMIN = "A"  # Admin
    API = "ITS"  # API/Third-party system