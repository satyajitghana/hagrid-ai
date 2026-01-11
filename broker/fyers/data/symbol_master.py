"""
Symbol Master module for the Fyers SDK.

Provides functionality to download and query symbol master files.
"""

import csv
import io
import json
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Dict, List, Any, Iterator, Union
from pydantic import BaseModel, Field

import httpx

from broker.fyers.core.logger import get_logger
from broker.fyers.models.enums import Exchange, Segment

logger = get_logger("fyers.symbol_master")

# Default cache directory for all Fyers SDK data
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "fyers"


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
        """Check if this is a future contract."""
        # Futures are derivatives (segment 11, 12, 20) with expiry but not options
        return (
            self.segment in [Segment.EQUITY_DERIVATIVES, Segment.CURRENCY_DERIVATIVES, Segment.COMMODITY]
            and self.expiry_date is not None
            and not self.is_option()
        )
    
    def is_equity(self) -> bool:
        """Check if this is an equity stock (not derivative)."""
        # Equities are in Capital Market segment and are not options
        # Note: Some equities might have expiry_date (bonds, warrants) but they're still equities
        return self.segment == Segment.CAPITAL_MARKET and not self.is_option()
    
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
    
    def __init__(self, cache_dir: Optional[str] = None, enable_cache: bool = True):
        """
        Initialize Symbol Master with automatic daily caching.
        
        Args:
            cache_dir: Directory to cache downloaded files (default: ~/.cache/fyers)
            enable_cache: Enable daily caching to avoid re-downloads (default: True)
        """
        self.cache_dir = Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR
        self.enable_cache = enable_cache
        self._symbols: Dict[str, Symbol] = {}
        self._by_fytoken: Dict[str, Symbol] = {}
        self._by_isin: Dict[str, List[Symbol]] = {}
        self._by_underlying: Dict[str, List[Symbol]] = {}
        self._loaded_segments: set = set()
        
        # Create cache directory if it doesn't exist
        if self.enable_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Symbol Master initialized with cache: {self.cache_dir}")
        else:
            logger.info("Symbol Master initialized (caching disabled)")
    
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
    
    def _get_cache_path(self, exchange_segment: str) -> Path:
        """Get cache file path for a segment."""
        today = date.today().isoformat()
        return self.cache_dir / f"{exchange_segment}_{today}.json"
    
    def _is_cache_valid(self, exchange_segment: str) -> bool:
        """Check if cached data exists and is from today."""
        if not self.enable_cache:
            return False
        
        cache_path = self._get_cache_path(exchange_segment)
        if not cache_path.exists():
            return False
        
        # Check if it's from today
        today = date.today().isoformat()
        return today in cache_path.name
    
    def _save_to_cache(self, exchange_segment: str, data: Dict[str, Any]) -> None:
        """Save symbol data to cache."""
        if not self.enable_cache:
            return
        
        try:
            cache_path = self._get_cache_path(exchange_segment)
            with open(cache_path, 'w') as f:
                json.dump(data, f)
            logger.debug(f"Cached {exchange_segment} data to {cache_path}")
        except Exception as e:
            logger.warning(f"Failed to cache {exchange_segment}: {e}")
    
    def _load_from_cache(self, exchange_segment: str) -> Optional[Dict[str, Any]]:
        """Load symbol data from cache."""
        if not self.enable_cache:
            return None
        
        try:
            cache_path = self._get_cache_path(exchange_segment)
            if cache_path.exists():
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                logger.info(f"Loaded {exchange_segment} from cache")
                return data
        except Exception as e:
            logger.warning(f"Failed to load cache for {exchange_segment}: {e}")
        
        return None
    
    async def load_segment(
        self,
        exchange_segment: str,
        use_json: bool = True,
        force_download: bool = False,
    ) -> int:
        """
        Load symbols for a specific exchange segment with daily caching.
        
        Symbol master is cached daily. If cache exists from today, it's loaded
        instantly without downloading. Cache automatically expires next day.
        
        Args:
            exchange_segment: One of ExchangeSegment values
            use_json: Use JSON format (True) or CSV (False)
            force_download: Force download even if cache exists
            
        Returns:
            Number of symbols loaded
        """
        if exchange_segment in self._loaded_segments:
            logger.debug(f"Segment {exchange_segment} already loaded in memory")
            return 0
        
        count = 0
        
        # Try cache first (unless force_download)
        if not force_download and self._is_cache_valid(exchange_segment):
            cached_data = self._load_from_cache(exchange_segment)
            if cached_data:
                for ticker, symbol_data in cached_data.items():
                    try:
                        symbol = Symbol(**symbol_data)
                        self._add_symbol(symbol)
                        count += 1
                    except Exception as e:
                        logger.warning(f"Failed to parse cached symbol {ticker}: {e}")
                
                self._loaded_segments.add(exchange_segment)
                logger.info(f"Loaded {count} symbols from cache ({exchange_segment})")
                return count
        
        # Download if no cache or force_download
        if use_json:
            data = await self.download_json(exchange_segment)
            
            # Save to cache
            if self.enable_cache:
                self._save_to_cache(exchange_segment, data)
            
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
        logger.info(f"Downloaded and loaded {count} symbols from {exchange_segment}")
        
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
    
    def _ensure_data_loaded(self) -> None:
        """Ensure symbol data is loaded before querying."""
        if not self._symbols:
            raise ValueError(
                "No symbol data loaded. "
                "Call 'await symbol_master.load_segment()' or 'await symbol_master.download_all()' first."
            )
    
    def get_symbol(self, ticker: str) -> Optional[Symbol]:
        """
        Get symbol by ticker.
        
        Args:
            ticker: Symbol ticker (e.g., "NSE:RELIANCE-EQ")
            
        Returns:
            Symbol if found, None otherwise
            
        Raises:
            ValueError: If no symbol data is loaded
        """
        self._ensure_data_loaded()
        return self._symbols.get(ticker)
    
    def get_by_fytoken(self, fytoken: str) -> Optional[Symbol]:
        """
        Get symbol by fytoken.
        
        Args:
            fytoken: Fyers token
            
        Returns:
            Symbol if found, None otherwise
            
        Raises:
            ValueError: If no symbol data is loaded
        """
        self._ensure_data_loaded()
        return self._by_fytoken.get(fytoken)
    
    def get_by_isin(
        self,
        isin: str,
        as_dataframe: bool = False,
    ) -> Union[List[Symbol], "pd.DataFrame"]:
        """
        Get all symbols with the given ISIN.
        
        Args:
            isin: ISIN code
            as_dataframe: Return as pandas DataFrame (default: False)
            
        Returns:
            List of Symbol objects or DataFrame if as_dataframe=True
            
        Raises:
            ValueError: If no symbol data is loaded
            ImportError: If as_dataframe=True but pandas not installed
            
        Example:
            ```python
            # Get as list
            symbols = sm.get_by_isin("INE002A01018")
            
            # Get as DataFrame
            df = sm.get_by_isin("INE002A01018", as_dataframe=True)
            ```
        """
        self._ensure_data_loaded()
        
        symbols = self._by_isin.get(isin, [])
        
        if as_dataframe:
            try:
                import pandas as pd
            except ImportError:
                raise ImportError("pandas required for as_dataframe=True. Install: pip install pandas")
            
            if not symbols:
                return pd.DataFrame()
            
            return pd.DataFrame([s.model_dump() for s in symbols])
        
        return symbols
    
    def search(
        self,
        query: str,
        exchange: Optional[Union[int, Exchange]] = None,
        segment: Optional[Union[int, Segment]] = None,
        limit: int = 50,
        as_dataframe: bool = False,
    ) -> Union[List[Symbol], "pd.DataFrame"]:
        """
        Search for symbols matching a query.
        
        Args:
            query: Search query (matches ticker, symbol name, etc.)
            exchange: Filter by exchange (use Exchange enum)
            segment: Filter by segment (use Segment enum)
            limit: Maximum results to return
            as_dataframe: Return as pandas DataFrame (default: False)
            
        Returns:
            List of Symbol objects or DataFrame if as_dataframe=True
            
        Raises:
            ValueError: If no symbol data is loaded
            ImportError: If as_dataframe=True but pandas not installed
            
        Example:
            ```python
            from broker.fyers.models.enums import Exchange, Segment
            
            # Search as list
            results = sm.search("RELIANCE", exchange=Exchange.NSE)
            
            # Search as DataFrame
            df = sm.search("RELIANCE", exchange=Exchange.NSE, as_dataframe=True)
            print(df[['symbol_ticker', 'symbol_details']])
            ```
        """
        self._ensure_data_loaded()
        
        # Convert enums to int
        exchange_val = int(exchange) if exchange is not None else None
        segment_val = int(segment) if segment is not None else None
        
        query_lower = query.lower()
        results = []
        
        for symbol in self._symbols.values():
            # Check filters
            if exchange_val is not None and symbol.exchange != exchange_val:
                continue
            if segment_val is not None and symbol.segment != segment_val:
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
        
        if as_dataframe:
            try:
                import pandas as pd
            except ImportError:
                raise ImportError("pandas required for as_dataframe=True. Install: pip install pandas")
            
            if not results:
                return pd.DataFrame()
            
            return pd.DataFrame([s.model_dump() for s in results])
        
        return results
    
    def get_options_chain(
        self,
        underlying: str,
        expiry_date: Optional[date] = None,
        as_dataframe: bool = False,
    ) -> Union[List[Symbol], "pd.DataFrame"]:
        """
        Get options chain for an underlying symbol.
        
        Args:
            underlying: Underlying symbol name
            expiry_date: Filter by specific expiry date
            as_dataframe: Return as pandas DataFrame (default: False)
            
        Returns:
            List of Symbol objects or DataFrame if as_dataframe=True
            
        Raises:
            ValueError: If no symbol data is loaded
            ImportError: If as_dataframe=True but pandas not installed
            
        Example:
            ```python
            # Get as list
            options = sm.get_options_chain("NIFTY")
            
            # Get as DataFrame
            df = sm.get_options_chain("NIFTY", as_dataframe=True)
            print(df.groupby('strike_price')['option_type'].value_counts())
            ```
        """
        self._ensure_data_loaded()
        
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
        
        if as_dataframe:
            try:
                import pandas as pd
            except ImportError:
                raise ImportError("pandas required for as_dataframe=True. Install: pip install pandas")
            
            if not options:
                return pd.DataFrame()
            
            df = pd.DataFrame([o.model_dump() for o in options])
            # Add parsed expiry date
            df['expiry_date_parsed'] = df['expiry_date'].apply(
                lambda x: datetime.fromtimestamp(int(x)).date() if x else None
            )
            return df
        
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
            
        Raises:
            ValueError: If no symbol data is loaded
        """
        self._ensure_data_loaded()
        
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
    
    def get_all_equities(
        self,
        exchange: Optional[Union[int, Exchange]] = None,
        as_dataframe: bool = False,
    ) -> Union[List[Symbol], "pd.DataFrame"]:
        """
        Get all equity symbols.
        
        Args:
            exchange: Filter by exchange (use Exchange.NSE, Exchange.BSE, or Exchange.MCX)
            as_dataframe: Return as pandas DataFrame (default: False)
            
        Returns:
            List of Symbol objects or DataFrame if as_dataframe=True
            
        Raises:
            ValueError: If no symbol data is loaded
            ImportError: If as_dataframe=True but pandas not installed
            
        Example:
            ```python
            from broker.fyers.models.enums import Exchange
            
            sm = SymbolMaster()
            await sm.load_segment("NSE_CM")
            
            # Get as list
            nse_equities = sm.get_all_equities(exchange=Exchange.NSE)
            print(f"Found {len(nse_equities)} NSE equities")
            
            # Get as DataFrame
            df = sm.get_all_equities(exchange=Exchange.NSE, as_dataframe=True)
            print(df[['symbol_ticker', 'symbol_details', 'previous_close']])
            ```
        """
        self._ensure_data_loaded()
        
        equities = list(self.get_equity_symbols(exchange))
        
        if as_dataframe:
            try:
                import pandas as pd
            except ImportError:
                raise ImportError("pandas required for as_dataframe=True. Install: pip install pandas")
            
            if not equities:
                return pd.DataFrame()
            
            return pd.DataFrame([e.model_dump() for e in equities])
        
        return equities
    
    def get_equity_symbols(
        self,
        exchange: Optional[Union[int, Exchange]] = None,
    ) -> Iterator[Symbol]:
        """
        Iterate over equity symbols (memory efficient for large datasets).
        
        Args:
            exchange: Filter by exchange (use Exchange enum)
            
        Yields:
            Equity symbols
        """
        # Convert enum to int if needed
        exchange_val = int(exchange) if exchange is not None else None
        
        for symbol in self._symbols.values():
            if not symbol.is_equity():
                continue
            if exchange_val is not None and symbol.exchange != exchange_val:
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
    
    # ==================== DataFrame Methods ====================
    
    def to_dataframe(
        self,
        exchange: Optional[Union[int, Exchange]] = None,
        segment: Optional[Union[int, Segment]] = None,
    ) -> "pd.DataFrame":
        """
        Convert loaded symbols to pandas DataFrame.
        
        Args:
            exchange: Filter by exchange (use Exchange enum)
            segment: Filter by segment (use Segment enum)
            
        Returns:
            DataFrame with all symbol data
            
        Example:
            ```python
            sm = SymbolMaster()
            await sm.load_segment("NSE_CM")
            
            # Get all symbols as DataFrame
            df = sm.to_dataframe()
            
            # Filter using enums (recommended!)
            from broker.fyers.models.enums import Exchange, Segment
            df_nse = sm.to_dataframe(exchange=Exchange.NSE)
            df_nse_eq = sm.to_dataframe(exchange=Exchange.NSE, segment=Segment.CAPITAL_MARKET)
            
            # Explore data
            print(df.head())
            print(df[df['is_mtf_tradable'] == 1])
            ```
        """
        self._ensure_data_loaded()
        
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for DataFrame operations. Install with: pip install pandas")
        
        # Convert enums to int
        exchange_val = int(exchange) if exchange is not None else None
        segment_val = int(segment) if segment is not None else None
        
        # Filter symbols
        symbols = []
        for symbol in self._symbols.values():
            if exchange_val is not None and symbol.exchange != exchange_val:
                continue
            if segment_val is not None and symbol.segment != segment_val:
                continue
            symbols.append(symbol)
        
        if not symbols:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame([s.model_dump() for s in symbols])
        
        # Add helper columns with corrected logic
        df['is_option'] = df['option_type'].isin(['CE', 'PE'])
        df['is_future'] = (
            df['segment'].isin([11, 12, 20]) &  # Derivatives segments
            df['expiry_date'].notna() &
            ~df['is_option']
        )
        df['is_equity'] = (df['segment'] == 10) & ~df['is_option']  # Capital Market, not options
        
        return df
    
    def search_dataframe(
        self,
        query: str,
        exchange: Optional[int] = None,
        segment: Optional[int] = None,
        limit: int = 50,
    ) -> "pd.DataFrame":
        """
        Search symbols and return results as DataFrame.
        
        Args:
            query: Search query
            exchange: Filter by exchange
            segment: Filter by segment
            limit: Maximum results
            
        Returns:
            DataFrame with matching symbols
            
        Example:
            ```python
            # Search for RELIANCE
            results = sm.search_dataframe("RELIANCE")
            print(results[['symbol_ticker', 'symbol_details', 'ltp']])
            ```
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required. Install with: pip install pandas")
        
        symbols = self.search(query, exchange, segment, limit)
        
        if not symbols:
            return pd.DataFrame()
        
        return pd.DataFrame([s.model_dump() for s in symbols])
    
    def get_options_chain_dataframe(
        self,
        underlying: str,
        expiry_date: Optional[date] = None,
    ) -> "pd.DataFrame":
        """
        Get options chain as DataFrame.
        
        Args:
            underlying: Underlying symbol
            expiry_date: Filter by expiry
            
        Returns:
            DataFrame with option chain data
            
        Example:
            ```python
            # Get NIFTY options
            options_df = sm.get_options_chain_dataframe("NIFTY")
            
            # Analyze strikes
            print(options_df.groupby('strike_price')['option_type'].value_counts())
            
            # Filter by expiry
            from datetime import date
            options_df = sm.get_options_chain_dataframe("NIFTY", date(2025, 1, 30))
            ```
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required. Install with: pip install pandas")
        
        options = self.get_options_chain(underlying, expiry_date)
        
        if not options:
            return pd.DataFrame()
        
        df = pd.DataFrame([o.model_dump() for o in options])
        
        # Add expiry as proper date column
        df['expiry_date_parsed'] = df['expiry_date'].apply(
            lambda x: datetime.fromtimestamp(int(x)).date() if x else None
        )
        
        return df
    
    def get_equity_symbols_dataframe(
        self,
        exchange: Optional[Union[int, Exchange]] = None,
    ) -> "pd.DataFrame":
        """
        Get equity symbols as DataFrame.
        
        Args:
            exchange: Filter by exchange (use Exchange enum)
            
        Returns:
            DataFrame with equity symbols
            
        Example:
            ```python
            from broker.fyers.models.enums import Exchange
            
            # Get all NSE equities using enum (recommended!)
            equities = sm.get_equity_symbols_dataframe(exchange=Exchange.NSE)
            
            # Find high-value stocks
            high_value = equities[equities['previous_close'] > 1000]
            
            # MTF eligible stocks
            mtf_stocks = equities[equities['is_mtf_tradable'] == 1]
            ```
        """
        self._ensure_data_loaded()
        
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required. Install with: pip install pandas")
        
        equities = list(self.get_equity_symbols(exchange))
        
        if not equities:
            return pd.DataFrame()
        
        return pd.DataFrame([e.model_dump() for e in equities])