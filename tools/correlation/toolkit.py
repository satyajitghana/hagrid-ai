"""
Correlation Toolkit with precomputed NIFTY100 correlation matrix.

Provides efficient correlation analysis for Indian stocks by:
- Precomputing and caching NIFTY100 correlation matrix (refreshed daily)
- Fast lookups for pair correlations
- Finding most/least correlated stocks for portfolio construction

Usage:
    ```python
    from tools.correlation import CorrelationToolkit
    from broker.fyers import FyersClient
    from tools.nse_india import NSEIndiaClient

    # Initialize with Fyers client for price data
    fyers_client = FyersClient(config)
    await fyers_client.authenticate()

    toolkit = CorrelationToolkit(fyers_client)

    # Get full correlation matrix (cached)
    matrix = await toolkit.get_nifty100_correlation_matrix()

    # Quick pair lookup
    corr = await toolkit.get_pair_correlation("NSE:RELIANCE-EQ", "NSE:TCS-EQ")

    # Find highly correlated stocks
    top = await toolkit.get_top_correlated_pairs("NSE:HDFC-EQ", limit=5)
    ```
"""

from agno.tools import Toolkit
from tools.nse_india import NSEIndiaClient
from core.indicators import CorrelationIndicators
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import time
import pandas as pd


class CorrelationToolkit(Toolkit):
    """
    Toolkit for correlation analysis with precomputed NIFTY100 correlation matrix.

    Features:
    - Precomputed correlation matrix for all NIFTY100 stocks
    - Automatic daily refresh of correlation data (24h TTL)
    - Cached correlation retrieval (no repeated API calls)
    - Pairwise correlation lookup
    - Top/least correlated pairs finder
    - Pairs trading metrics (Z-score, half-life, beta)

    The correlation matrix is computed on returns (not prices) over 100 trading days.
    """

    CACHE_DIR = Path(".cache/correlation")
    CORRELATION_FILE = "nifty100_correlation.json"

    def __init__(
        self,
        fyers_client,
        nse_client: Optional[NSEIndiaClient] = None,
        cache_ttl_hours: int = 24,
        **kwargs
    ):
        """
        Initialize CorrelationToolkit.

        Args:
            fyers_client: Authenticated FyersClient instance for price data
            nse_client: Optional NSEIndiaClient (created if not provided)
            cache_ttl_hours: Cache TTL in hours (default: 24)
            **kwargs: Additional arguments for Toolkit base class
        """
        self.fyers = fyers_client
        self.nse = nse_client or NSEIndiaClient()
        self.cache_ttl_hours = cache_ttl_hours

        tools = [
            self.get_nifty100_correlation_matrix,
            self.get_pair_correlation,
            self.get_top_correlated_pairs,
            self.get_least_correlated_pairs,
            self.get_pairs_trading_metrics,
            self.refresh_correlation_matrix,
        ]

        instructions = """Use these tools for correlation analysis:
- get_nifty100_correlation_matrix: Get precomputed correlation matrix (cached daily)
- get_pair_correlation: Get correlation between two specific symbols
- get_top_correlated_pairs: Find stocks most correlated with a symbol
- get_least_correlated_pairs: Find stocks least correlated (hedge candidates)
- get_pairs_trading_metrics: Get Z-score, beta, half-life for a pair
- refresh_correlation_matrix: Force refresh of correlation data

Correlation values range from -1 (inverse) to +1 (perfect correlation).
Values > 0.7 indicate strong positive correlation.
Values < -0.3 can be used for hedging."""

        super().__init__(name="correlation_toolkit", tools=tools, instructions=instructions, **kwargs)

        # Ensure cache directory exists
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self) -> Path:
        """Get path to correlation cache file."""
        return self.CACHE_DIR / self.CORRELATION_FILE

    def _is_cache_valid(self) -> bool:
        """Check if cache exists and is not expired."""
        cache_path = self._get_cache_path()
        if not cache_path.exists():
            return False

        # Check file modification time
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        return datetime.now() - mtime < timedelta(hours=self.cache_ttl_hours)

    def _load_cache(self) -> Optional[dict]:
        """Load cached correlation data."""
        cache_path = self._get_cache_path()
        if not cache_path.exists():
            return None
        try:
            with open(cache_path, "r") as f:
                return json.load(f)
        except Exception:
            return None

    def _save_cache(self, data: dict) -> None:
        """Save correlation data to cache."""
        cache_path = self._get_cache_path()
        try:
            with open(cache_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    async def _fetch_historical_prices(self, symbol: str, days: int = 100) -> Optional[pd.Series]:
        """Fetch historical close prices for a symbol."""
        try:
            from datetime import datetime, timedelta

            range_to = datetime.now().strftime("%Y-%m-%d")
            range_from = (datetime.now() - timedelta(days=days + 30)).strftime("%Y-%m-%d")  # Extra buffer for holidays

            response = await self.fyers.get_history(
                symbol=symbol,
                resolution="D",
                date_format=1,
                range_from=range_from,
                range_to=range_to
            )

            if not response.candles:
                return None

            # Extract close prices with timestamps
            timestamps = []
            prices = []
            for candle in response.candles[-days:]:  # Take last 100 days
                timestamps.append(candle[0])
                prices.append(candle[4])  # Close price

            if not prices:
                return None

            return pd.Series(prices, index=pd.to_datetime(timestamps, unit='s'), name=symbol)

        except Exception:
            return None

    async def _compute_correlation_matrix(self) -> dict:
        """Compute correlation matrix for all NIFTY100 stocks."""
        # Get NIFTY100 constituents from NSE
        try:
            response = self.nse.get_nifty100_constituents()
            symbols = [f"NSE:{stock.symbol}-EQ" for stock in response.data]
        except Exception as e:
            return {"error": f"Failed to get NIFTY100 constituents: {str(e)}"}

        if not symbols:
            return {"error": "No symbols found in NIFTY100"}

        # Fetch historical data for all symbols
        price_data = {}
        failed_symbols = []

        for symbol in symbols[:100]:  # Limit to 100 to avoid rate limits
            try:
                series = await self._fetch_historical_prices(symbol, days=100)
                if series is not None and len(series) > 50:  # Need at least 50 data points
                    price_data[symbol] = series
                else:
                    failed_symbols.append(symbol)
            except Exception:
                failed_symbols.append(symbol)

        if len(price_data) < 10:
            return {"error": f"Insufficient data. Only got {len(price_data)} symbols."}

        # Create DataFrame and align on dates
        df = pd.DataFrame(price_data)
        df = df.dropna(axis=0, how='any')  # Keep only rows where all symbols have data

        if len(df) < 30:
            return {"error": f"Insufficient overlapping data. Only {len(df)} common trading days."}

        # Compute correlation on returns (not prices)
        returns = df.pct_change().dropna()
        corr_matrix = returns.corr()

        # Convert to serializable format
        result = {
            "correlation_matrix": {
                sym: corr_matrix[sym].to_dict() for sym in corr_matrix.columns
            },
            "symbols": list(corr_matrix.columns),
            "data_points": len(returns),
            "computed_at": datetime.now().isoformat(),
            "failed_symbols": failed_symbols[:10],  # First 10 failed
            "total_symbols": len(price_data),
        }

        return result

    async def get_nifty100_correlation_matrix(self) -> str:
        """
        Get precomputed correlation matrix for NIFTY100 stocks.

        Returns cached data if available and not expired (24 hours).
        Otherwise computes fresh correlation matrix from 100 days of returns.

        This tool is optimized for quick lookups - the computation is done
        once and cached for 24 hours.

        Returns:
            JSON string with:
            - correlation_matrix: Dict of symbol -> correlation values
            - symbols: List of symbols included
            - data_points: Number of trading days used
            - computed_at: When the matrix was computed
            - source: "cache" or "computed"
        """
        if self._is_cache_valid():
            data = self._load_cache()
            if data:
                data["source"] = "cache"
                return json.dumps(data, indent=2)

        # Compute fresh correlation
        result = await self._compute_correlation_matrix()

        if "error" not in result:
            self._save_cache(result)
            result["source"] = "computed"

        return json.dumps(result, indent=2)

    async def get_pair_correlation(self, symbol1: str, symbol2: str) -> str:
        """
        Get correlation between two specific symbols.

        Uses cached NIFTY100 matrix if both symbols are in NIFTY100.
        Otherwise computes correlation directly from price data.

        Args:
            symbol1: First symbol (e.g., "NSE:RELIANCE-EQ")
            symbol2: Second symbol (e.g., "NSE:TCS-EQ")

        Returns:
            JSON with correlation coefficient and interpretation:
            - correlation: Value from -1 to +1
            - strength: "STRONG", "MODERATE", or "WEAK"
            - direction: "POSITIVE" or "NEGATIVE"
        """
        # Try to get from cached matrix first
        if self._is_cache_valid():
            data = self._load_cache()
            if data:
                matrix = data.get("correlation_matrix", {})
                if symbol1 in matrix and symbol2 in matrix.get(symbol1, {}):
                    corr = matrix[symbol1][symbol2]
                    return json.dumps({
                        "symbol1": symbol1,
                        "symbol2": symbol2,
                        "correlation": round(corr, 4),
                        "strength": "STRONG" if abs(corr) > 0.7 else "MODERATE" if abs(corr) > 0.4 else "WEAK",
                        "direction": "POSITIVE" if corr > 0 else "NEGATIVE",
                        "source": "cache"
                    }, indent=2)

        # Compute directly if not in cache
        try:
            series1 = await self._fetch_historical_prices(symbol1, days=100)
            series2 = await self._fetch_historical_prices(symbol2, days=100)

            if series1 is None or series2 is None:
                return json.dumps({"error": "Could not fetch price data for one or both symbols"})

            # Align series
            df = pd.DataFrame({symbol1: series1, symbol2: series2}).dropna()

            if len(df) < 30:
                return json.dumps({"error": "Insufficient overlapping data"})

            # Compute correlation on returns
            returns = df.pct_change().dropna()
            corr = returns[symbol1].corr(returns[symbol2])

            return json.dumps({
                "symbol1": symbol1,
                "symbol2": symbol2,
                "correlation": round(corr, 4),
                "strength": "STRONG" if abs(corr) > 0.7 else "MODERATE" if abs(corr) > 0.4 else "WEAK",
                "direction": "POSITIVE" if corr > 0 else "NEGATIVE",
                "source": "computed"
            }, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)})

    async def get_top_correlated_pairs(self, symbol: str, limit: int = 10) -> str:
        """
        Find stocks most positively correlated with a given symbol.

        Useful for:
        - Finding similar stocks for sector analysis
        - Identifying stocks that move together
        - Avoiding over-concentration in correlated assets

        Args:
            symbol: Reference symbol (e.g., "NSE:RELIANCE-EQ")
            limit: Number of top pairs to return (default: 10)

        Returns:
            JSON list of most correlated symbols with their correlation values
        """
        if not self._is_cache_valid():
            await self.get_nifty100_correlation_matrix()  # Refresh cache

        data = self._load_cache()
        if not data or "correlation_matrix" not in data:
            return json.dumps({"error": "Correlation matrix not available. Try refresh_correlation_matrix first."})

        matrix = data["correlation_matrix"]

        if symbol not in matrix:
            return json.dumps({
                "error": f"Symbol {symbol} not in correlation matrix",
                "available_symbols": data.get("symbols", [])[:10]
            })

        correlations = matrix[symbol]
        sorted_pairs = sorted(
            [(k, v) for k, v in correlations.items() if k != symbol],
            key=lambda x: x[1],
            reverse=True
        )[:limit]

        return json.dumps({
            "reference_symbol": symbol,
            "top_correlated": [
                {
                    "symbol": k,
                    "correlation": round(v, 4),
                    "strength": "STRONG" if v > 0.7 else "MODERATE" if v > 0.4 else "WEAK"
                }
                for k, v in sorted_pairs
            ]
        }, indent=2)

    async def get_least_correlated_pairs(self, symbol: str, limit: int = 10) -> str:
        """
        Find stocks least correlated with a given symbol (hedge candidates).

        Useful for:
        - Portfolio diversification
        - Finding hedge candidates
        - Reducing overall portfolio correlation

        Args:
            symbol: Reference symbol
            limit: Number of pairs to return (default: 10)

        Returns:
            JSON list of least correlated symbols (can include negative correlations)
        """
        if not self._is_cache_valid():
            await self.get_nifty100_correlation_matrix()

        data = self._load_cache()
        if not data or "correlation_matrix" not in data:
            return json.dumps({"error": "Correlation matrix not available"})

        matrix = data["correlation_matrix"]

        if symbol not in matrix:
            return json.dumps({"error": f"Symbol {symbol} not in correlation matrix"})

        correlations = matrix[symbol]
        sorted_pairs = sorted(
            [(k, v) for k, v in correlations.items() if k != symbol],
            key=lambda x: x[1]
        )[:limit]

        return json.dumps({
            "reference_symbol": symbol,
            "least_correlated": [
                {
                    "symbol": k,
                    "correlation": round(v, 4),
                    "hedge_quality": "GOOD" if v < 0.2 else "MODERATE" if v < 0.4 else "POOR"
                }
                for k, v in sorted_pairs
            ]
        }, indent=2)

    async def get_pairs_trading_metrics(self, symbol1: str, symbol2: str) -> str:
        """
        Get comprehensive pairs trading metrics for two symbols.

        Calculates:
        - Correlation (30d and 60d)
        - Beta (hedge ratio)
        - Spread statistics (mean, std)
        - Z-score (current deviation from mean)
        - Half-life (mean reversion speed)
        - Cointegration assessment

        Args:
            symbol1: First symbol
            symbol2: Second symbol

        Returns:
            JSON with all pairs trading metrics and trading signals
        """
        try:
            series1 = await self._fetch_historical_prices(symbol1, days=100)
            series2 = await self._fetch_historical_prices(symbol2, days=100)

            if series1 is None or series2 is None:
                return json.dumps({"error": "Could not fetch price data"})

            # Align series
            df = pd.DataFrame({symbol1: series1, symbol2: series2}).dropna()

            if len(df) < 60:
                return json.dumps({"error": "Insufficient data (need at least 60 days)"})

            prices1 = df[symbol1]
            prices2 = df[symbol2]

            # Calculate correlation
            corr_30 = CorrelationIndicators.correlation(prices1, prices2, 30)
            corr_60 = CorrelationIndicators.correlation(prices1, prices2, 60)

            # Calculate beta (hedge ratio)
            returns1 = prices1.pct_change().dropna()
            returns2 = prices2.pct_change().dropna()
            beta = CorrelationIndicators.beta(returns1, returns2)

            # Calculate spread and Z-score
            spread = prices1 - (beta * prices2)
            z_score = CorrelationIndicators.z_score(spread)

            # Calculate half-life
            half_life = CorrelationIndicators.half_life(spread)

            # Determine trading signal
            if z_score < -2:
                signal = "LONG_SPREAD"  # Long symbol1, Short symbol2
                signal_desc = f"Spread is oversold. Consider: Long {symbol1}, Short {symbol2}"
            elif z_score > 2:
                signal = "SHORT_SPREAD"  # Short symbol1, Long symbol2
                signal_desc = f"Spread is overbought. Consider: Short {symbol1}, Long {symbol2}"
            else:
                signal = "NEUTRAL"
                signal_desc = "Spread is within normal range. No action."

            # Cointegration assessment
            is_cointegrated = abs(z_score) < 3 and half_life < 30 and half_life > 0

            metrics = {
                "symbol1": symbol1,
                "symbol2": symbol2,
                "correlation_30d": round(corr_30, 4),
                "correlation_60d": round(corr_60, 4),
                "beta": round(beta, 4),
                "hedge_ratio": f"1:{round(beta, 2)}",
                "spread": {
                    "current": round(spread.iloc[-1], 2),
                    "mean": round(spread.mean(), 2),
                    "std": round(spread.std(), 2),
                },
                "z_score": round(z_score, 2),
                "half_life_days": round(half_life, 1) if half_life > 0 else None,
                "cointegrated": is_cointegrated,
                "signal": signal,
                "signal_description": signal_desc,
            }

            return json.dumps(metrics, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)})

    async def refresh_correlation_matrix(self) -> str:
        """
        Force refresh of the NIFTY100 correlation matrix.

        Use this when you need fresh data regardless of cache status.
        Note: This operation fetches data for ~100 symbols and may take time.

        Returns:
            JSON with fresh correlation matrix
        """
        result = await self._compute_correlation_matrix()

        if "error" not in result:
            self._save_cache(result)
            result["source"] = "refreshed"

        return json.dumps(result, indent=2)
