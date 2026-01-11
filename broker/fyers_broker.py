from typing import List, Optional, Dict, Any
from broker.interface import BrokerService
from broker.fyers.client import FyersClient
from broker.fyers.models.config import FyersConfig

class FyersBroker(BrokerService):
    """Fyers implementation of BrokerService using the Fyers SDK"""
    
    def __init__(self, client_id: str, secret_key: str, token_file: Optional[str] = None):
        self.config = FyersConfig(
            client_id=client_id,
            secret_key=secret_key,
            token_file_path=token_file
        )
        self.client = FyersClient(self.config)
        
    async def authenticate(self, auto_browser: bool = False):
        """Ensure client is authenticated"""
        if not self.client.is_authenticated:
            await self.client.authenticate(auto_browser=auto_browser)

    # Market Data APIs
    async def get_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """Get market quotes for multiple symbols"""
        response = await self.client.get_quotes(symbols)
        return response.model_dump()
    
    async def get_market_depth(self, symbol: str, ohlcv_flag: int = 1) -> Dict[str, Any]:
        """Get market depth for a symbol"""
        response = await self.client.get_market_depth(symbol, ohlcv_flag=ohlcv_flag)
        return response.model_dump()
    
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
        response = await self.client.get_history(
            symbol=symbol,
            resolution=resolution,
            date_format=date_format,
            range_from=range_from,
            range_to=range_to,
            cont_flag=cont_flag
        )
        return response.model_dump()
    
    async def get_option_chain(self, symbol: str, strike_count: int = 10) -> Dict[str, Any]:
        """Get option chain data"""
        response = await self.client.get_option_chain(symbol, strike_count=strike_count)
        return response.model_dump()
    
    # Order Management APIs
    async def place_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Place a single order"""
        response = await self.client.place_order(order_data)
        return response.model_dump()
    
    async def place_multi_order(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Place multiple orders"""
        response = await self.client.place_multi_order(orders)
        return response.model_dump()
    
    async def modify_order(self, order_id: str, modifications: Dict[str, Any]) -> Dict[str, Any]:
        """Modify an existing order"""
        response = await self.client.modify_order(order_id, modifications)
        return response.model_dump()
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order"""
        response = await self.client.cancel_order(order_id)
        return response.model_dump()
    
    async def cancel_multi_order(self, order_ids: List[str]) -> Dict[str, Any]:
        """Cancel multiple orders"""
        response = await self.client.cancel_multi_order(order_ids)
        return response.model_dump()
    
    # Position Management APIs
    async def get_positions(self) -> Dict[str, Any]:
        """Get all positions"""
        response = await self.client.get_positions()
        return response.model_dump()
    
    async def exit_position(self, position_id: Optional[str] = None) -> Dict[str, Any]:
        """Exit position(s)"""
        response = await self.client.exit_position(position_id)
        return response.model_dump()
    
    async def convert_position(self, conversion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert position from one product type to another"""
        response = await self.client.convert_position(conversion_data)
        return response.model_dump()
    
    # GTT Orders
    async def place_gtt_order(self, gtt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Place GTT order"""
        # Note: FyersClient.place_gtt_order takes individual args, but interface expects dict
        # We need to unpack gtt_data to match client signature or use the internal method if available
        # The client implementation takes specific args, let's map them
        return (await self.client.place_gtt_order(
            symbol=gtt_data["symbol"],
            side=gtt_data["side"],
            product_type=gtt_data["productType"],
            leg1_price=gtt_data["orderInfo"]["leg1"]["price"],
            leg1_trigger_price=gtt_data["orderInfo"]["leg1"]["triggerPrice"],
            leg1_qty=gtt_data["orderInfo"]["leg1"]["qty"],
            leg2_price=gtt_data.get("orderInfo", {}).get("leg2", {}).get("price"),
            leg2_trigger_price=gtt_data.get("orderInfo", {}).get("leg2", {}).get("triggerPrice"),
            leg2_qty=gtt_data.get("orderInfo", {}).get("leg2", {}).get("qty")
        )).model_dump()
    
    async def modify_gtt_order(self, gtt_id: str, modifications: Dict[str, Any]) -> Dict[str, Any]:
        """Modify GTT order"""
        # Similar mapping for modify
        leg1 = modifications.get("orderInfo", {}).get("leg1", {})
        leg2 = modifications.get("orderInfo", {}).get("leg2", {})
        
        return (await self.client.modify_gtt_order(
            order_id=gtt_id,
            leg1_price=leg1.get("price"),
            leg1_trigger_price=leg1.get("triggerPrice"),
            leg1_qty=leg1.get("qty"),
            leg2_price=leg2.get("price"),
            leg2_trigger_price=leg2.get("triggerPrice"),
            leg2_qty=leg2.get("qty")
        )).model_dump()
    
    async def cancel_gtt_order(self, gtt_id: str) -> Dict[str, Any]:
        """Cancel GTT order"""
        response = await self.client.cancel_gtt_order(gtt_id)
        return response.model_dump()
    
    async def get_gtt_orders(self) -> Dict[str, Any]:
        """Get all GTT orders"""
        response = await self.client.get_gtt_orders()
        return response.model_dump()
    
    # Margin Calculator
    async def calculate_span_margin(self, positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate span margin"""
        response = await self.client.calculate_span_margin(positions)
        return response.model_dump()
    
    async def calculate_multi_order_margin(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate margin for multiple orders"""
        response = await self.client.calculate_order_margin(orders)
        return response.model_dump()
