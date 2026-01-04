from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

class BrokerService(ABC):
    """Abstract base class for broker integrations following Fyers-like API structure"""
    
    # Market Data APIs
    @abstractmethod
    async def get_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """Get market quotes for multiple symbols"""
        pass
    
    @abstractmethod
    async def get_market_depth(self, symbol: str, ohlcv_flag: int = 1) -> Dict[str, Any]:
        """Get market depth for a symbol"""
        pass
    
    @abstractmethod
    async def get_history(
        self, 
        symbol: str, 
        resolution: str, 
        date_format: int,
        range_from: str,
        range_to: str,
        cont_flag: int = 0
    ) -> Dict[str, Any]:
        """Get historical candle data"""
        pass
    
    @abstractmethod
    async def get_option_chain(self, symbol: str, strike_count: int = 10) -> Dict[str, Any]:
        """Get option chain data"""
        pass
    
    # Order Management APIs
    @abstractmethod
    async def place_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Place a single order"""
        pass
    
    @abstractmethod
    async def place_multi_order(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Place multiple orders"""
        pass
    
    @abstractmethod
    async def modify_order(self, order_id: str, modifications: Dict[str, Any]) -> Dict[str, Any]:
        """Modify an existing order"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order"""
        pass
    
    @abstractmethod
    async def cancel_multi_order(self, order_ids: List[str]) -> Dict[str, Any]:
        """Cancel multiple orders"""
        pass
    
    # Position Management APIs
    @abstractmethod
    async def get_positions(self) -> Dict[str, Any]:
        """Get all positions"""
        pass
    
    @abstractmethod
    async def exit_position(self, position_id: Optional[str] = None) -> Dict[str, Any]:
        """Exit position(s)"""
        pass
    
    @abstractmethod
    async def convert_position(self, conversion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert position from one product type to another"""
        pass
    
    # GTT Orders
    @abstractmethod
    async def place_gtt_order(self, gtt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Place GTT order"""
        pass
    
    @abstractmethod
    async def modify_gtt_order(self, gtt_id: str, modifications: Dict[str, Any]) -> Dict[str, Any]:
        """Modify GTT order"""
        pass
    
    @abstractmethod
    async def cancel_gtt_order(self, gtt_id: str) -> Dict[str, Any]:
        """Cancel GTT order"""
        pass
    
    @abstractmethod
    async def get_gtt_orders(self) -> Dict[str, Any]:
        """Get all GTT orders"""
        pass
    
    # Margin Calculator
    @abstractmethod
    async def calculate_span_margin(self, positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate span margin"""
        pass
    
    @abstractmethod
    async def calculate_multi_order_margin(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate margin for multiple orders"""
        pass