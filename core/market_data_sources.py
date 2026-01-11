"""
Additional Data Source Toolkits
Mock implementations for FII/DII flows, news, fundamentals data
"""
from agno.tools import Toolkit
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random

# Import real clients
from tools.cogencis import CogencisClient
from tools.screener import ScreenerClient
from tools.tradingview import TradingViewClient
from tools.yahoo_finance import YFinanceClient

class FIIDIIToolkit(Toolkit):
    """Toolkit for FII/DII institutional flow data"""
    
    def __init__(self, cogencis_token: str = "demo_token", **kwargs):
        self.cogencis = CogencisClient(bearer_token=cogencis_token)
        tools = [
            self.get_fii_dii_data,
            self.get_bulk_deals,
            self.get_block_deals,
            self.get_shareholding_pattern
        ]
        super().__init__(name="fii_dii_toolkit", tools=tools, **kwargs)
    
    def get_fii_dii_data(self, symbol: str, days: int = 5) -> str:
        """
        Get FII/DII buy/sell data for last N days (Mock data as this is usually market-wide).
        
        Args:
            symbol (str): Stock symbol
            days (int): Number of days of data
            
        Returns:
            str: CSV formatted FII/DII flow data
        """
        # Mock data generation for now
        lines = ["DATE,FII_BUY_CR,FII_SELL_CR,FII_NET_CR,DII_BUY_CR,DII_SELL_CR,DII_NET_CR"]
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=days-i-1)).strftime("%Y-%m-%d")
            fii_buy = round(random.uniform(10, 100), 2)
            fii_sell = round(random.uniform(10, 100), 2)
            fii_net = round(fii_buy - fii_sell, 2)
            dii_buy = round(random.uniform(20, 80), 2)
            dii_sell = round(random.uniform(20, 80), 2)
            dii_net = round(dii_buy - dii_sell, 2)
            
            lines.append(f"{date},{fii_buy},{fii_sell},{fii_net},{dii_buy},{dii_sell},{dii_net}")
        
        return "\n".join(lines)
    
    def get_bulk_deals(self, symbol: str, days: int = 30) -> str:
        """
        Get bulk deal data using Cogencis API.
        
        Args:
            symbol (str): Stock symbol
            days (int): Number of days
            
        Returns:
            str: CSV formatted bulk deals
        """
        try:
            # Clean symbol (remove exchange prefix)
            clean_symbol = symbol.split(":")[-1].replace("-EQ", "")
            
            # Lookup symbol to get path
            matches = self.cogencis.symbol_lookup(clean_symbol)
            if not matches:
                return "SYMBOL_NOT_FOUND"
                
            path = matches[0].path
            
            # Get bulk deals
            deals = self.cogencis.get_bulk_deals(path, page_size=20)
            
            if not deals:
                return "NO_BULK_DEALS"
                
            lines = ["DATE,CLIENT_NAME,DEAL_TYPE,QUANTITY,PRICE"]
            for deal in deals:
                lines.append(f"{deal.date_parsed},{deal.client_name},{deal.transaction_type},{deal.quantity},{deal.weighted_avg_price}")
                
            return "\n".join(lines)
            
        except Exception as e:
            return f"Error fetching bulk deals: {str(e)}"
    
    def get_block_deals(self, symbol: str, days: int = 30) -> str:
        """
        Get block deal data using Cogencis API.
        
        Args:
            symbol (str): Stock symbol
            days (int): Number of days
            
        Returns:
            str: CSV formatted block deals
        """
        try:
            # Clean symbol (remove exchange prefix)
            clean_symbol = symbol.split(":")[-1].replace("-EQ", "")
            
            # Lookup symbol to get path
            matches = self.cogencis.symbol_lookup(clean_symbol)
            if not matches:
                return "SYMBOL_NOT_FOUND"
                
            path = matches[0].path
            
            # Get block deals
            deals = self.cogencis.get_block_deals(path, page_size=20)
            
            if not deals:
                return "NO_BLOCK_DEALS"
                
            lines = ["DATE,CLIENT_NAME,DEAL_TYPE,QUANTITY,PRICE"]
            for deal in deals:
                lines.append(f"{deal.date_parsed},{deal.client_name},{deal.transaction_type},{deal.quantity},{deal.weighted_avg_price}")
                
            return "\n".join(lines)
            
        except Exception as e:
            return f"Error fetching block deals: {str(e)}"
    
    def get_shareholding_pattern(self, symbol: str) -> str:
        """
        Get latest shareholding pattern using Cogencis API.
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            str: Formatted shareholding data
        """
        try:
            # Clean symbol (remove exchange prefix)
            clean_symbol = symbol.split(":")[-1].replace("-EQ", "")
            
            # Use Cogencis for shareholding
            info = self.cogencis.get_company_info(clean_symbol)
            if not info:
                return "DATA_NOT_AVAILABLE"
                
            # Parse shareholding data
            shareholders = info.get("shareholders", [])
            promoters = [s for s in shareholders if s.is_promoter and not s.is_group]
            
            promoter_holding = 0.0
            for p in promoters:
                holding = p.get_latest_holding()
                if holding:
                    promoter_holding += holding.percentage
                    
            # This is simplified - real implementation would aggregate categories
            return f"""SHAREHOLDING_PATTERN:
Promoter: {promoter_holding:.2f}%
Public: {100 - promoter_holding:.2f}%
(Detailed breakdown available via get_key_shareholders)"""
            
        except Exception as e:
            return f"Error fetching shareholding pattern: {str(e)}"


class NewsToolkit(Toolkit):
    """Toolkit for news and sentiment data"""
    
    def __init__(self, cogencis_token: str = "demo_token", **kwargs):
        self.cogencis = CogencisClient(bearer_token=cogencis_token)
        self.tradingview = TradingViewClient()
        self.yf = YFinanceClient()
        
        tools = [
            self.get_latest_news,
            self.get_broker_ratings,
            self.get_social_sentiment
        ]
        super().__init__(name="news_toolkit", tools=tools, **kwargs)
    
    def get_latest_news(self, symbol: str, hours: int = 24) -> str:
        """
        Get latest news for stock in last N hours using multiple sources.
        
        Args:
            symbol (str): Stock symbol
            hours (int): Hours of news to fetch
            
        Returns:
            str: Formatted news items
        """
        try:
            # Clean symbol for different APIs
            clean_symbol = symbol.split(":")[-1].replace("-EQ", "")
            tv_symbol = symbol.replace("-EQ", "") # NSE:RELIANCE
            
            lines = ["LATEST_NEWS:"]
            
            # 1. TradingView News
            try:
                tv_news = self.tradingview.get_latest_news(tv_symbol, count=5)
                for item in tv_news:
                    lines.append(f"[TradingView] {item.title} ({item.provider_name}) - {item.published_datetime}")
            except Exception as e:
                lines.append(f"Error fetching TV news: {str(e)}")
                
            # 2. Cogencis News
            try:
                cog_news = self.cogencis.get_news_for_symbol(clean_symbol, page_size=5)
                for item in cog_news:
                    lines.append(f"[Cogencis] {item.headline} - {item.source_datetime_parsed}")
            except Exception as e:
                lines.append(f"Error fetching Cogencis news: {str(e)}")
                
            # 3. Yahoo Finance News (as backup)
            try:
                yf_news = self.yf.get_news(f"{clean_symbol}.NS")
                for item in yf_news[:3]:
                    title = item.get('title', 'No Title')
                    pub = item.get('publisher', 'Unknown')
                    lines.append(f"[Yahoo] {title} ({pub})")
            except Exception:
                pass
            
            return "\n".join(lines)
            
        except Exception as e:
            return f"Error fetching news: {str(e)}"
    
    def get_broker_ratings(self, symbol: str, days: int = 30) -> str:
        """
        Get broker ratings/recommendations using Yahoo Finance.
        
        Args:
            symbol (str): Stock symbol
            days (int): Days of rating data
            
        Returns:
            str: Formatted broker ratings
        """
        try:
            clean_symbol = symbol.split(":")[-1].replace("-EQ", "") + ".NS"
            analysis = self.yf.get_analysis(clean_symbol)
            
            summary = analysis.recommendations_summary
            if not summary:
                return "NO_BROKER_RATINGS_AVAILABLE"
                
            # Format the latest summary
            latest = summary[0] if summary else {}
            
            return f"""BROKER_RATINGS:
Strong Buy: {latest.get('strongBuy', 0)}
Buy: {latest.get('buy', 0)}
Hold: {latest.get('hold', 0)}
Sell: {latest.get('sell', 0)}
Strong Sell: {latest.get('strongSell', 0)}
Period: {latest.get('period', 'Unknown')}"""
            
        except Exception as e:
            return f"Error fetching broker ratings: {str(e)}"
    
    def get_social_sentiment(self, symbol: str) -> str:
        """
        Get social media sentiment (Mock data for now).
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            str: Sentiment score and summary
        """
        sentiment_score = round(random.uniform(-1, 1), 2)
        sentiment_label = "POSITIVE" if sentiment_score > 0.3 else "NEGATIVE" if sentiment_score < -0.3 else "NEUTRAL"
        mentions = random.randint(100, 5000)
        
        return f"""SOCIAL_SENTIMENT:
Score: {sentiment_score} ({sentiment_label})
Mentions (24h): {mentions}
Trending: {'Yes' if mentions > 2000 else 'No'}"""


class FundamentalsToolkit(Toolkit):
    """Toolkit for fundamental data"""
    
    def __init__(self, **kwargs):
        self.screener = ScreenerClient()
        self.yf = YFinanceClient()
        
        tools = [
            self.get_financial_ratios,
            self.get_quarterly_results,
            self.get_peer_comparison
        ]
        super().__init__(name="fundamentals_toolkit", tools=tools, **kwargs)
    
    def get_financial_ratios(self, symbol: str) -> str:
        """
        Get key financial ratios using Screener and Yahoo Finance.
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            str: Formatted financial ratios
        """
        try:
            clean_symbol = symbol.split(":")[-1].replace("-EQ", "")
            
            # Try Screener first (better for Indian stocks)
            company = self.screener.search_first(clean_symbol)
            if company and company.id:
                # Get valuation chart to extract current PE
                val_chart = self.screener.get_valuation_chart(company.id)
                margin_chart = self.screener.get_margin_chart(company.id)
                
                pe = val_chart.pe_ratio.latest_value or "N/A"
                opm = margin_chart.opm.latest_value or "N/A"
                npm = margin_chart.npm.latest_value or "N/A"
                
                return f"""FINANCIAL_RATIOS (Screener):
PE Ratio: {pe}
OPM: {opm}%
NPM: {npm}%
(More details available via get_quarterly_results)"""
            
            # Fallback to Yahoo Finance
            info = self.yf.get_ticker_info(f"{clean_symbol}.NS").info
            
            return f"""FINANCIAL_RATIOS (Yahoo):
PE Ratio: {info.get('trailingPE', 'N/A')}
PB Ratio: {info.get('priceToBook', 'N/A')}
ROE: {info.get('returnOnEquity', 'N/A')}
Debt-to-Equity: {info.get('debtToEquity', 'N/A')}
Current Ratio: {info.get('currentRatio', 'N/A')}"""
            
        except Exception as e:
            return f"Error fetching ratios: {str(e)}"
    
    def get_quarterly_results(self, symbol: str, quarters: int = 4) -> str:
        """
        Get quarterly results using Screener markdown.
        
        Args:
            symbol (str): Stock symbol
            quarters (int): Number of quarters (ignored, returns full table)
            
        Returns:
            str: Quarterly results table in markdown
        """
        try:
            clean_symbol = symbol.split(":")[-1].replace("-EQ", "")
            
            # Screener provides a nice markdown table
            markdown = self.screener.get_company_page(clean_symbol)
            
            # Extract just the Quarterly Results section
            if "## Quarterly Results" in markdown:
                # Simple extraction logic
                parts = markdown.split("## Quarterly Results")
                if len(parts) > 1:
                    section = parts[1].split("##")[0]
                    return "QUARTERLY_RESULTS:" + section
            
            return markdown[:2000] # Return truncated page if parsing fails
            
        except Exception as e:
            return f"Error fetching quarterly results: {str(e)}"
    
    def get_peer_comparison(self, symbol: str, sector: str) -> str:
        """
        Get peer comparison data (Mock data for now).
        
        Args:
            symbol (str): Stock symbol
            sector (str): Sector name
            
        Returns:
            str: Peer comparison table
        """
        lines = ["PEER_COMPARISON:"]
        lines.append("METRIC,THIS_STOCK,SECTOR_MEDIAN")
        lines.append(f"PE Ratio,{round(random.uniform(20, 35), 2)},{round(random.uniform(22, 30), 2)}")
        lines.append(f"ROE %,{round(random.uniform(15, 25), 2)},{round(random.uniform(16, 20), 2)}")
        lines.append(f"Debt/Equity,{round(random.uniform(0.3, 1.2), 2)},{round(random.uniform(0.5, 0.9), 2)}")
        lines.append(f"Market Cap Rank,{random.randint(1, 10)},N/A")
        
        return "\n".join(lines)


class EventsToolkit(Toolkit):
    """Toolkit for corporate events calendar"""
    
    def __init__(self, cogencis_token: str = "demo_token", **kwargs):
        self.cogencis = CogencisClient(bearer_token=cogencis_token)
        self.yf = YFinanceClient()
        
        tools = [
            self.get_earnings_calendar,
            self.get_dividend_calendar,
            self.get_corporate_actions
        ]
        super().__init__(name="events_toolkit", tools=tools, **kwargs)
    
    def get_earnings_calendar(self, symbol: str, days_ahead: int = 30) -> str:
        """
        Get upcoming earnings announcements using Yahoo Finance.
        
        Args:
            symbol (str): Stock symbol
            days_ahead (int): Days to look ahead
            
        Returns:
            str: Formatted earnings calendar
        """
        try:
            clean_symbol = symbol.split(":")[-1].replace("-EQ", "") + ".NS"
            calendar = self.yf.get_calendar(clean_symbol)
            
            if not calendar.earnings_dates:
                return "NO_EARNINGS_ANNOUNCEMENT_SCHEDULED"
                
            # Filter for future dates
            future_earnings = []
            for item in calendar.earnings_dates:
                # Yahoo often returns dates as keys in the dict list
                # Implementation depends on exact YF response structure
                # This is a simplified view
                future_earnings.append(str(item))
                
            return f"EARNINGS_CALENDAR: {future_earnings[:2]}"
            
        except Exception as e:
            return f"Error fetching earnings: {str(e)}"
    
    def get_dividend_calendar(self, symbol: str) -> str:
        """
        Get dividend information using Cogencis.
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            str: Formatted dividend info
        """
        try:
            clean_symbol = symbol.split(":")[-1].replace("-EQ", "")
            
            matches = self.cogencis.symbol_lookup(clean_symbol)
            if not matches:
                return "SYMBOL_NOT_FOUND"
                
            actions = self.cogencis.get_corporate_actions(matches[0].path)
            dividends = [a for a in actions if a.is_dividend]
            
            if not dividends:
                return "NO_UPCOMING_DIVIDEND"
                
            lines = ["DIVIDEND_INFO:"]
            for div in dividends[:3]:
                lines.append(f"Dividend: ₹{div.dividend_amount} (Ex-Date: {div.ex_date_parsed})")
                
            return "\n".join(lines)
            
        except Exception as e:
            return f"Error fetching dividends: {str(e)}"
    
    def get_corporate_actions(self, symbol: str, days_ahead: int = 30) -> str:
        """
        Get corporate actions (splits, bonus, buyback) using Cogencis.
        
        Args:
            symbol (str): Stock symbol
            days_ahead (int): Days to look ahead
            
        Returns:
            str: Formatted corporate actions
        """
        try:
            clean_symbol = symbol.split(":")[-1].replace("-EQ", "")
            
            matches = self.cogencis.symbol_lookup(clean_symbol)
            if not matches:
                return "SYMBOL_NOT_FOUND"
                
            actions = self.cogencis.get_corporate_actions(matches[0].path)
            
            # Filter non-dividends
            corp_actions = [a for a in actions if not a.is_dividend]
            
            if not corp_actions:
                return "NO_CORPORATE_ACTIONS_SCHEDULED"
                
            lines = ["CORPORATE_ACTIONS:"]
            for act in corp_actions[:3]:
                lines.append(f"{act.purpose} (Ex-Date: {act.ex_date_parsed})")
                
            return "\n".join(lines)
            
        except Exception as e:
            return f"Error fetching corporate actions: {str(e)}"


class MacroToolkit(Toolkit):
    """Toolkit for global macro data"""
    
    def __init__(self, **kwargs):
        self.yf = YFinanceClient()
        tools = [
            self.get_global_market_status
        ]
        super().__init__(name="macro_toolkit", tools=tools, **kwargs)
        
    def get_global_market_status(self) -> str:
        """
        Get status of global indices (US, Europe, Asia).
        
        Returns:
            str: Global market summary
        """
        try:
            indexes = self.yf.get_global_indexes()
            
            lines = ["GLOBAL_MARKETS:"]
            for idx in indexes:
                change_str = f"{idx.change_percent:+.2f}%" if idx.change_percent is not None else "N/A"
                price_str = f"{idx.last_price:.2f}" if idx.last_price is not None else "N/A"
                lines.append(f"{idx.name} ({idx.country}): {price_str} ({change_str})")
                
            return "\n".join(lines)
            
        except Exception as e:
            return f"Error fetching global markets: {str(e)}"