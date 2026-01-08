"""
Symbol Master module for the Fyers SDK.

Provides functionality to download and query symbol master files.
"""

import csv
import io
from datetime import datetime, date
from enum import IntEnum
from pathlib import Path
from typing import Optional, Dict, List, Any, Iterator
from pydantic import BaseModel, Field

import httpx

from broker.fyers.core.logger import get_logger

logger = get_logger("fyers.symbol_master")


class Exchange(IntEnum):
    """Exchange codes."""
    NSE = 10
    MCX = 11
    BSE = 12


class Segment(IntEnum):
    """Segment codes."""
    CAPITAL_MARKET = 10
    EQUITY_DERIVATIVES = 11
    CURRENCY_DERIVATIVES = 12
    COMMODITY = 20


class ExchangeSegment:
    """Exchange and segment combinations with URLs."""
    
    # CSV URLs
    NSE_CM = "NSE_CM"  # NSE Capital Market
    NSE_FO = "NSE_FO"  # NSE Equity Derivatives
    NSE_CD = "NSE_CD"  # NSE Currency Derivatives
    NSE_COM = "NSE_COM"  # NSE Commodity
    BSE_CM = "BSE_CM"  # BSE Capital Market
    BSE_FO = "BSE_FO"  # BSE Equity Derivatives
    MCX_COM = "MCX_COM"  # MCX Commodity
    
    CSV_URLS = {
        NSE_CM: "https://public.fyers.in/sym_details/NSE_CM.csv",
        NSE_FO: "https://public.fyers.in/sym_details/NSE_FO.csv",
        NSE_CD: "https://public.fyers.in/sym_details/NSE_CD.csv",
        NSE_COM: "https://public.fyers.in/sym_details/NSE_COM.csv",
        BSE_CM: "https://public.fyers.in/sym_details/BSE_CM.csv",
        BSE_FO: "https://public.fyers.in/sym_details/BSE_FO.csv",
        MCX_COM: "https://public.fyers.in/sym_details/MCX_COM.csv",
    }
    
    JSON_URLS = {
        NSE_CM: "https://public.fyers.in/sym_details/NSE_CM_sym_master.json",
        NSE_FO: "https://public.fyers.in/sym_details/NSE_FO_sym_master.json",
        NSE_CD: "https://public.fyers.in/sym_details/NSE_CD_sym_master.json",
        NSE_COM: "https://public.fyers.in/sym_details/NSE_COM_sym_master.json",
        BSE_CM: "https://public.fyers.in/sym_details/BSE_CM_sym_master.json",
        BSE_FO: "https://public.fyers.in/sym_details/BSE_FO_sym_master.json",
        MCX_COM: "https://public.fyers.in/sym_details/MCX_COM_sym_master.json",
    }
    
    ALL = [NSE_CM, NSE_FO, NSE_CD, NSE_COM, BSE_CM, BSE_FO, MCX_COM]


class Symbol(BaseModel):
    """Model for a trading symbol from the symbol master."""
    
    fytoken: str = Field(..., alias="fyToken", description="Unique token for the symbol")
    symbol_ticker: str = Field(..., alias="symTicker", description="Unique symbol ticker")
    symbol_details: Optional[str] = Field(None, alias="symDetails", description="Full name of the symbol")
    exchange: int = Field(..., description="Exchange code")
    segment: int = Field(..., description="Segment code")
    exchange_symbol: Optional[str] = Field(None, alias="exSymbol", description="Exchange symbol")
    exchange_token: Optional[int] = Field(None, alias="exToken", description="Exchange token")
    isin: Optional[str] = Field(None, description="ISIN code")
    min_lot_size: int = Field(1, alias="minLotSize", description="Minimum lot size")
    tick_size: float = Field(0.05, alias="tickSize", description="Tick size")
    trading_session: Optional[str] = Field(None, alias="tradingSession", description="Trading session")
    last_update: Optional[str] = Field(None, alias="lastUpdate", description="Last update date")
    expiry_date: Optional[str] = Field(None, alias="expiryDate", description="Expiry date timestamp")
    strike_price: Optional[float] = Field(None, alias="strikePrice", description="Strike price")
    option_type: Optional[str] = Field(None, alias="optType", description="Option type (CE/PE/XX)")
    underlying_symbol: Optional[str] = Field(None, alias="underSym", description="Underlying symbol")
    underlying_fytoken: Optional[str] = Field(None, alias="underFyTok", description="Underlying fytoken")
    exchange_instrument_type: Optional[int] = Field(None, alias="exInstType", description="Exchange instrument type")
    qty_freeze: Optional[str] = Field(None, alias="qtyFreeze", description="Freeze quantity")
    trade_status: int = Field(1, alias="tradeStatus", description="Trade status (0/1)")
    currency_code: Optional[str] = Field(None, alias="currencyCode", description="Currency code")
    upper_price: Optional[float] = Field(None, alias="upperPrice", description="Upper circuit price")
    lower_price: Optional[float] = Field(None, alias="lowerPrice", description="Lower circuit price")
    face_value: Optional[float] = Field(None, alias="faceValue", description="Face value")
    qty_multiplier: float = Field(1.0, alias="qtyMultiplier", description="Quantity multiplier")
    previous_close: Optional[float] = Field(None, alias="previousClose", description="Previous close price")
    previous_oi: Optional[float] = Field(None, alias="previousOi", description="Previous OI")
    exchange_name: Optional[str] = Field(None, alias="exchangeName", description="Exchange name")
    symbol_desc: Optional[str] = Field(None, alias="symbolDesc", description="Symbol description")
    is_mtf_tradable: int = Field(0, alias="is_mtf_tradable", description="MTF tradable (0/1)")
    mtf_margin: float = Field(0.0, alias="mtf_margin", description="MTF margin multiplier")
    stream: Optional[str] = Field(None, description="Stream group")
    ex_series: Optional[str] = Field(None, alias="exSeries", description="Series")
    
    class Config:
        populate_by_name = True
        extra = "ignore"
    
    def is_active(self) -> bool:
        """Check if the symbol is actively tradable."""
        return self.trade_status == 1
    
    def is_option(self) -> bool:
        """Check if this is an option."""
        return self.option_type in ["CE", "PE"]
    
    def is_future(self) -> bool:
        """Check if this is a future."""
        return self.expiry_date is not None and not self.is_option()
    
    def is_equity(self) -> bool:
        """Check if this is an equity stock."""
        return self.segment == Segment.CAPITAL_MARKET and not self.is_option() and not self.is_future()
    
    def get_expiry_date(self) -> Optional[date]:
        """Get expiry date as datetime.date object."""
        if not self.expiry_date:
            return None
        try:
            # Expiry date is typically in timestamp format
            timestamp = int(self.expiry_date)
            return datetime.fromtimestamp(timestamp).date()
        except (ValueError, TypeError):
            return None


class SymbolMaster:
    """
    Symbol Master manager for downloading and querying symbol data.
    
    Example:
        ```python
        sm = SymbolMaster()
        
        # Download all symbols
        await sm.download_all()
        
        # Search for symbols
        symbols = sm.search("RELIANCE")
        
        # Get specific symbol
        symbol = sm.get_symbol("NSE:RELIANCE-EQ")
        
        # Get all options for a stock
        options = sm.get_options_chain("RELIANCE")
        ```
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize Symbol Master.
        
        Args:
            cache_dir: Directory to cache downloaded files
        """
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self._symbols: Dict[str, Symbol] = {}
        self._by_fytoken: Dict[str, Symbol] = {}
        self._by_isin: Dict[str, List[Symbol]] = {}
        self._by_underlying: Dict[str, List[Symbol]] = {}
        self._loaded_segments: set = set()
        
        logger.info("Symbol Master initialized")
    
    async def download_csv(
        self,
        exchange_segment: str,
        timeout: float = 30.0,
    ) -> str:
        """
        Download symbol master CSV file.
        
        Args:
            exchange_segment: One of ExchangeSegment values
            timeout: Request timeout
            
        Returns:
            CSV content as string
        """
        url = ExchangeSegment.CSV_URLS.get(exchange_segment)
        if not url:
            raise ValueError(f"Invalid exchange segment: {exchange_segment}")
        
        logger.info(f"Downloading symbol master CSV: {exchange_segment}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
    
    async def download_json(
        self,
        exchange_segment: str,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        """
        Download symbol master JSON file.
        
        Args:
            exchange_segment: One of ExchangeSegment values
            timeout: Request timeout
            
        Returns:
            JSON data as dictionary
        """
        url = ExchangeSegment.JSON_URLS.get(exchange_segment)
        if not url:
            raise ValueError(f"Invalid exchange segment: {exchange_segment}")
        
        logger.info(f"Downloading symbol master JSON: {exchange_segment}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json()
    
    async def load_segment(
        self,
        exchange_segment: str,
        use_json: bool = True,
    ) -> int:
        """
        Load symbols for a specific exchange segment.
        
        Args:
            exchange_segment: One of ExchangeSegment values
            use_json: Use JSON format (True) or CSV (False)
            
        Returns:
            Number of symbols loaded
        """
        if exchange_segment in self._loaded_segments:
            logger.debug(f"Segment {exchange_segment} already loaded")
            return 0
        
        count = 0
        
        if use_json:
            data = await self.download_json(exchange_segment)
            for ticker, symbol_data in data.items():
                try:
                    symbol = Symbol(**symbol_data)
                    self._add_symbol(symbol)
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to parse symbol {ticker}: {e}")
        else:
            csv_content = await self.download_csv(exchange_segment)
            count = self._parse_csv(csv_content)
        
        self._loaded_segments.add(exchange_segment)
        logger.info(f"Loaded {count} symbols from {exchange_segment}")
        
        return count
    
    def _parse_csv(self, csv_content: str) -> int:
        """Parse CSV content and add symbols."""
        count = 0
        reader = csv.DictReader(io.StringIO(csv_content))
        
        # CSV column mapping
        column_map = {
            "Fytoken": "fyToken",
            "Symbol Details": "symDetails",
            "Exchange Instrument type": "exInstType",
            "Minimum lot size": "minLotSize",
            "Tick size": "tickSize",
            "ISIN": "isin",
            "Trading Session": "tradingSession",
            "Last update date": "lastUpdate",
            "Expiry date": "expiryDate",
            "Symbol ticker": "symTicker",
            "Exchange": "exchange",
            "Segment": "segment",
            "Scrip code": "exToken",
            "Underlying symbol": "underSym",
            "Underlying scrip code": "underExToken",
            "Strike price": "strikePrice",
            "Option type": "optType",
            "Underlying FyToken": "underFyTok",
        }
        
        for row in reader:
            try:
                # Map columns
                symbol_data = {}
                for csv_col, model_field in column_map.items():
                    if csv_col in row:
                        value = row[csv_col]
                        # Type conversions
                        if model_field in ["exchange", "segment", "exInstType", "exToken", "minLotSize"]:
                            symbol_data[model_field] = int(value) if value else 0
                        elif model_field in ["tickSize", "strikePrice"]:
                            symbol_data[model_field] = float(value) if value else 0.0
                        else:
                            symbol_data[model_field] = value
                
                symbol = Symbol(**symbol_data)
                self._add_symbol(symbol)
                count += 1
            except Exception as e:
                logger.debug(f"Failed to parse CSV row: {e}")
        
        return count
    
    def _add_symbol(self, symbol: Symbol) -> None:
        """Add a symbol to the internal indexes."""
        self._symbols[symbol.symbol_ticker] = symbol
        self._by_fytoken[symbol.fytoken] = symbol
        
        if symbol.isin:
            if symbol.isin not in self._by_isin:
                self._by_isin[symbol.isin] = []
            self._by_isin[symbol.isin].append(symbol)
        
        if symbol.underlying_symbol:
            if symbol.underlying_symbol not in self._by_underlying:
                self._by_underlying[symbol.underlying_symbol] = []
            self._by_underlying[symbol.underlying_symbol].append(symbol)
    
    async def download_all(self, use_json: bool = True) -> int:
        """
        Download all symbol master files.
        
        Args:
            use_json: Use JSON format (True) or CSV (False)
            
        Returns:
            Total number of symbols loaded
        """
        total = 0
        for segment in ExchangeSegment.ALL:
            try:
                count = await self.load_segment(segment, use_json)
                total += count
            except Exception as e:
                logger.error(f"Failed to load {segment}: {e}")
        
        logger.info(f"Total symbols loaded: {total}")
        return total
    
    def get_symbol(self, ticker: str) -> Optional[Symbol]:
        """
        Get symbol by ticker.
        
        Args:
            ticker: Symbol ticker (e.g., "NSE:RELIANCE-EQ")
            
        Returns:
            Symbol if found, None otherwise
        """
        return self._symbols.get(ticker)
    
    def get_by_fytoken(self, fytoken: str) -> Optional[Symbol]:
        """
        Get symbol by fytoken.
        
        Args:
            fytoken: Fyers token
            
        Returns:
            Symbol if found, None otherwise
        """
        return self._by_fytoken.get(fytoken)
    
    def get_by_isin(self, isin: str) -> List[Symbol]:
        """
        Get all symbols with the given ISIN.
        
        Args:
            isin: ISIN code
            
        Returns:
            List of matching symbols
        """
        return self._by_isin.get(isin, [])
    
    def search(
        self,
        query: str,
        exchange: Optional[int] = None,
        segment: Optional[int] = None,
        limit: int = 50,
    ) -> List[Symbol]:
        """
        Search for symbols matching a query.
        
        Args:
            query: Search query (matches ticker, symbol name, etc.)
            exchange: Filter by exchange
            segment: Filter by segment
            limit: Maximum results to return
            
        Returns:
            List of matching symbols
        """
        query_lower = query.lower()
        results = []
        
        for symbol in self._symbols.values():
            # Check filters
            if exchange is not None and symbol.exchange != exchange:
                continue
            if segment is not None and symbol.segment != segment:
                continue
            
            # Match against various fields
            if (
                query_lower in symbol.symbol_ticker.lower()
                or (symbol.symbol_details and query_lower in symbol.symbol_details.lower())
                or (symbol.exchange_symbol and query_lower in symbol.exchange_symbol.lower())
                or (symbol.symbol_desc and query_lower in symbol.symbol_desc.lower())
            ):
                results.append(symbol)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_options_chain(
        self,
        underlying: str,
        expiry_date: Optional[date] = None,
    ) -> List[Symbol]:
        """
        Get options chain for an underlying symbol.
        
        Args:
            underlying: Underlying symbol name
            expiry_date: Filter by specific expiry date
            
        Returns:
            List of option symbols
        """
        options = []
        
        for symbol in self._by_underlying.get(underlying, []):
            if not symbol.is_option():
                continue
            
            if expiry_date:
                sym_expiry = symbol.get_expiry_date()
                if sym_expiry != expiry_date:
                    continue
            
            options.append(symbol)
        
        # Sort by expiry, then strike, then option type
        options.sort(key=lambda s: (
            s.expiry_date or "",
            s.strike_price or 0,
            s.option_type or "",
        ))
        
        return options
    
    def get_futures(
        self,
        underlying: str,
        expiry_date: Optional[date] = None,
    ) -> List[Symbol]:
        """
        Get futures for an underlying symbol.
        
        Args:
            underlying: Underlying symbol name
            expiry_date: Filter by specific expiry date
            
        Returns:
            List of future symbols
        """
        futures = []
        
        for symbol in self._by_underlying.get(underlying, []):
            if not symbol.is_future():
                continue
            
            if expiry_date:
                sym_expiry = symbol.get_expiry_date()
                if sym_expiry != expiry_date:
                    continue
            
            futures.append(symbol)
        
        # Sort by expiry
        futures.sort(key=lambda s: s.expiry_date or "")
        
        return futures
    
    def get_expiry_dates(self, underlying: str) -> List[date]:
        """
        Get all available expiry dates for an underlying.
        
        Args:
            underlying: Underlying symbol name
            
        Returns:
            Sorted list of expiry dates
        """
        dates = set()
        
        for symbol in self._by_underlying.get(underlying, []):
            expiry = symbol.get_expiry_date()
            if expiry:
                dates.add(expiry)
        
        return sorted(dates)
    
    def get_all_tickers(self) -> List[str]:
        """Get all loaded symbol tickers."""
        return list(self._symbols.keys())
    
    def get_equity_symbols(
        self,
        exchange: Optional[int] = None,
    ) -> Iterator[Symbol]:
        """
        Iterate over equity symbols.
        
        Args:
            exchange: Filter by exchange
            
        Yields:
            Equity symbols
        """
        for symbol in self._symbols.values():
            if not symbol.is_equity():
                continue
            if exchange is not None and symbol.exchange != exchange:
                continue
            yield symbol
    
    @property
    def symbol_count(self) -> int:
        """Get total number of loaded symbols."""
        return len(self._symbols)
    
    @property
    def loaded_segments(self) -> List[str]:
        """Get list of loaded segments."""
        return list(self._loaded_segments)