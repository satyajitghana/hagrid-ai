"""
Additional Data Source Toolkits
Mock implementations for FII/DII flows, news, fundamentals data
"""
from agno.tools import Toolkit
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random


class FIIDIIToolkit(Toolkit):
    """Toolkit for FII/DII institutional flow data"""
    
    def __init__(self, **kwargs):
        tools = [
            self.get_fii_dii_data,
            self.get_bulk_deals,
            self.get_block_deals,
            self.get_shareholding_pattern
        ]
        super().__init__(name="fii_dii_toolkit", tools=tools, **kwargs)
    
    def get_fii_dii_data(self, symbol: str, days: int = 5) -> str:
        """
        Get FII/DII buy/sell data for last N days (Mock data).
        
        Args:
            symbol (str): Stock symbol
            days (int): Number of days of data
            
        Returns:
            str: CSV formatted FII/DII flow data
        """
        # Mock data generation
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
    
    def get_bulk_deals(self, symbol: str, days: int = 10) -> str:
        """
        Get bulk deal data for last N days (Mock data).
        
        Args:
            symbol (str): Stock symbol
            days (int): Number of days
            
        Returns:
            str: CSV formatted bulk deals
        """
        lines = ["DATE,CLIENT_NAME,DEAL_TYPE,QUANTITY,PRICE"]
        
        # Mock: 0-3 bulk deals
        num_deals = random.randint(0, 3)
        for i in range(num_deals):
            date = (datetime.now() - timedelta(days=random.randint(0, days))).strftime("%Y-%m-%d")
            clients = ["HDFC Mutual Fund", "SBI Mutual Fund", "LIC", "Goldman Sachs", "Morgan Stanley"]
            client = random.choice(clients)
            deal_type = random.choice(["BUY", "SELL"])
            quantity = random.randint(50000, 500000)
            price = round(random.uniform(1000, 3000), 2)
            
            lines.append(f"{date},{client},{deal_type},{quantity},{price}")
        
        if num_deals == 0:
            return "NO_BULK_DEALS"
        
        return "\n".join(lines)
    
    def get_block_deals(self, symbol: str, days: int = 10) -> str:
        """
        Get block deal data for last N days (Mock data).
        
        Args:
            symbol (str): Stock symbol
            days (int): Number of days
            
        Returns:
            str: CSV formatted block deals
        """
        lines = ["DATE,BUYER,SELLER,QUANTITY,PRICE"]
        
        # Mock: 0-2 block deals
        num_deals = random.randint(0, 2)
        for i in range(num_deals):
            date = (datetime.now() - timedelta(days=random.randint(0, days))).strftime("%Y-%m-%d")
            buyer = random.choice(["FII-ABC", "DII-XYZ", "Promoter Group"])
            seller = random.choice(["FII-DEF", "DII-UVW", "Retail"])
            quantity = random.randint(100000, 1000000)
            price = round(random.uniform(1000, 3000), 2)
            
            lines.append(f"{date},{buyer},{seller},{quantity},{price}")
        
        if num_deals == 0:
            return "NO_BLOCK_DEALS"
        
        return "\n".join(lines)
    
    def get_shareholding_pattern(self, symbol: str) -> str:
        """
        Get latest shareholding pattern (Mock data).
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            str: Formatted shareholding data
        """
        # Mock shareholding pattern
        promoter = round(random.uniform(40, 75), 2)
        fii = round(random.uniform(10, 30), 2)
        dii = round(random.uniform(10, 25), 2)
        public = round(100 - promoter - fii - dii, 2)
        
        promoter_change = round(random.uniform(-2, 2), 2)
        fii_change = round(random.uniform(-3, 3), 2)
        dii_change = round(random.uniform(-2, 2), 2)
        
        return f"""SHAREHOLDING_PATTERN:
Promoter: {promoter}% (QoQ Change: {promoter_change:+.2f}%)
FII: {fii}% (QoQ Change: {fii_change:+.2f}%)
DII: {dii}% (QoQ Change: {dii_change:+.2f}%)
Public: {public}%
Pledged Promoter Shares: {round(random.uniform(0, 20), 2)}%"""


class NewsToolkit(Toolkit):
    """Toolkit for news and sentiment data"""
    
    def __init__(self, **kwargs):
        tools = [
            self.get_latest_news,
            self.get_broker_ratings,
            self.get_social_sentiment
        ]
        super().__init__(name="news_toolkit", tools=tools, **kwargs)
    
    def get_latest_news(self, symbol: str, hours: int = 24) -> str:
        """
        Get latest news for stock in last N hours (Mock data).
        
        Args:
            symbol (str): Stock symbol
            hours (int): Hours of news to fetch
            
        Returns:
            str: Formatted news items
        """
        # Mock news items
        news_templates = [
            ("Positive", "Company announces Q{q} results beating estimates by {pct}%"),
            ("Positive", "Brokerage upgrades stock to BUY with target of ₹{target}"),
            ("Negative", "Company misses Q{q} revenue estimates by {pct}%"),
            ("Neutral", "Management holds analyst meeting to discuss strategy"),
            ("Positive", "Company wins major ₹{amt} crore contract"),
            ("Negative", "Regulatory authority issues notice to company"),
        ]
        
        num_news = random.randint(0, 3)
        lines = ["LATEST_NEWS:"]
        
        for i in range(num_news):
            sentiment, template = random.choice(news_templates)
            time_ago = random.randint(1, hours)
            
            news_text = template.format(
                q=random.choice(["Q1", "Q2", "Q3", "Q4"]),
                pct=random.randint(5, 25),
                target=random.randint(1500, 3000),
                amt=random.randint(100, 5000)
            )
            
            lines.append(f"{i+1}. [{sentiment}] {news_text} - {time_ago}h ago")
        
        if num_news == 0:
            lines.append("No significant news in last 24 hours")
        
        return "\n".join(lines)
    
    def get_broker_ratings(self, symbol: str, days: int = 30) -> str:
        """
        Get broker ratings/recommendations (Mock data).
        
        Args:
            symbol (str): Stock symbol
            days (int): Days of rating data
            
        Returns:
            str: Formatted broker ratings
        """
        upgrades = random.randint(0, 3)
        downgrades = random.randint(0, 2)
        maintains = random.randint(1, 5)
        
        avg_target = round(random.uniform(1500, 3000), 2)
        consensus = random.choice(["BUY", "HOLD", "SELL"])
        
        return f"""BROKER_RATINGS (Last {days} days):
Upgrades: {upgrades}
Downgrades: {downgrades}
Maintains: {maintains}
Consensus: {consensus}
Average Target: ₹{avg_target}"""
    
    def get_social_sentiment(self, symbol: str) -> str:
        """
        Get social media sentiment (Mock data).
        
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
        tools = [
            self.get_financial_ratios,
            self.get_quarterly_results,
            self.get_peer_comparison
        ]
        super().__init__(name="fundamentals_toolkit", tools=tools, **kwargs)
    
    def get_financial_ratios(self, symbol: str) -> str:
        """
        Get key financial ratios (Mock data).
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            str: Formatted financial ratios
        """
        pe = round(random.uniform(15, 40), 2)
        pb = round(random.uniform(2, 8), 2)
        roe = round(random.uniform(10, 25), 2)
        roce = round(random.uniform(12, 28), 2)
        debt_equity = round(random.uniform(0.1, 1.5), 2)
        current_ratio = round(random.uniform(1.0, 2.5), 2)
        
        return f"""FINANCIAL_RATIOS:
PE Ratio: {pe}
PB Ratio: {pb}
ROE: {roe}%
ROCE: {roce}%
Debt-to-Equity: {debt_equity}
Current Ratio: {current_ratio}
Interest Coverage: {round(random.uniform(3, 15), 2)}x"""
    
    def get_quarterly_results(self, symbol: str, quarters: int = 4) -> str:
        """
        Get quarterly results for last N quarters (Mock data).
        
        Args:
            symbol (str): Stock symbol
            quarters (int): Number of quarters
            
        Returns:
            str: CSV formatted quarterly data
        """
        lines = ["QUARTER,REVENUE_CR,NET_PROFIT_CR,EPS,YOY_GROWTH%"]
        
        base_revenue = random.uniform(5000, 20000)
        for i in range(quarters):
            quarter = f"Q{4-i}FY25" if i < 4 else f"Q{8-i}FY24"
            revenue = round(base_revenue * (1 + random.uniform(-0.1, 0.15)), 2)
            profit = round(revenue * random.uniform(0.10, 0.25), 2)
            eps = round(profit / 100, 2)  # Mock EPS
            yoy_growth = round(random.uniform(-5, 25), 2)
            
            lines.append(f"{quarter},{revenue},{profit},{eps},{yoy_growth}")
        
        return "\n".join(lines)
    
    def get_peer_comparison(self, symbol: str, sector: str) -> str:
        """
        Get peer comparison data (Mock data).
        
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
    
    def __init__(self, **kwargs):
        tools = [
            self.get_earnings_calendar,
            self.get_dividend_calendar,
            self.get_corporate_actions
        ]
        super().__init__(name="events_toolkit", tools=tools, **kwargs)
    
    def get_earnings_calendar(self, symbol: str, days_ahead: int = 5) -> str:
        """
        Get upcoming earnings announcements (Mock data).
        
        Args:
            symbol (str): Stock symbol
            days_ahead (int): Days to look ahead
            
        Returns:
            str: Formatted earnings calendar
        """
        # Mock: 30% chance of earnings in next 5 days
        if random.random() < 0.3:
            days_until = random.randint(1, days_ahead)
            date = (datetime.now() + timedelta(days=days_until)).strftime("%Y-%m-%d")
            quarter = random.choice(["Q1FY25", "Q2FY25", "Q3FY25", "Q4FY25"])
            consensus_eps = round(random.uniform(15, 50), 2)
            
            return f"""EARNINGS_ANNOUNCEMENT:
Date: {date} ({days_until} days)
Quarter: {quarter}
Consensus EPS: ₹{consensus_eps}
Market Expectation: {'BEAT' if random.random() > 0.5 else 'INLINE'}"""
        else:
            return "NO_EARNINGS_ANNOUNCEMENT_SCHEDULED"
    
    def get_dividend_calendar(self, symbol: str) -> str:
        """
        Get dividend information (Mock data).
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            str: Formatted dividend info
        """
        # Mock: 40% chance of dividend event
        if random.random() < 0.4:
            dividend_per_share = round(random.uniform(5, 20), 2)
            ex_date = (datetime.now() + timedelta(days=random.randint(1, 15))).strftime("%Y-%m-%d")
            record_date = (datetime.now() + timedelta(days=random.randint(2, 16))).strftime("%Y-%m-%d")
            
            return f"""DIVIDEND_INFO:
Dividend Per Share: ₹{dividend_per_share}
Ex-Dividend Date: {ex_date}
Record Date: {record_date}
Dividend Yield: {round(random.uniform(1, 4), 2)}%"""
        else:
            return "NO_UPCOMING_DIVIDEND"
    
    def get_corporate_actions(self, symbol: str, days_ahead: int = 30) -> str:
        """
        Get corporate actions (splits, bonus, buyback) (Mock data).
        
        Args:
            symbol (str): Stock symbol
            days_ahead (int): Days to look ahead
            
        Returns:
            str: Formatted corporate actions
        """
        actions = []
        
        # Mock: Random corporate actions
        if random.random() < 0.2:  # 20% chance of some action
            action_type = random.choice(["BONUS", "SPLIT", "BUYBACK", "RIGHTS"])
            date = (datetime.now() + timedelta(days=random.randint(1, days_ahead))).strftime("%Y-%m-%d")
            
            if action_type == "BONUS":
                actions.append(f"BONUS: 1:1 Bonus shares - Record Date: {date}")
            elif action_type == "SPLIT":
                actions.append(f"SPLIT: Stock split 1:2 - Effective Date: {date}")
            elif action_type == "BUYBACK":
                price = round(random.uniform(1500, 3000), 2)
                actions.append(f"BUYBACK: At ₹{price} per share - Open until: {date}")
            elif action_type == "RIGHTS":
                actions.append(f"RIGHTS: Rights issue 1:5 at ₹{round(random.uniform(100, 500), 2)} - Record Date: {date}")
        
        if not actions:
            return "NO_CORPORATE_ACTIONS_SCHEDULED"
        
        return "CORPORATE_ACTIONS:\n" + "\n".join(actions)