import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from broker.interface import BrokerService

class MockBroker(BrokerService):
    """
    Mock implementation of BrokerService that emulates Fyers API responses.
    Uses similar data structures for testing without actual broker connection.
    """
    
    def __init__(self):
        self.orders: Dict[str, Dict] = {}
        self.positions: Dict[str, Dict] = {}
        self.gtt_orders: Dict[str, Dict] = {}
        
        # Mock symbol base prices
        self.symbol_prices = {
            "NSE:INFY-EQ": 1500.0,
            "NSE:TCS-EQ": 3500.0,
            "NSE:RELIANCE-EQ": 2500.0,
            "NSE:SBIN-EQ": 600.0,
            "NSE:HDFCBANK-EQ": 1600.0,
        }
    
    async def get_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """Get market quotes for multiple symbols - Fyers-like response"""
        quotes_data = []
        
        for symbol in symbols:
            base_price = self.symbol_prices.get(symbol, 1000.0)
            variation = random.uniform(-0.02, 0.02)
            ltp = round(base_price * (1 + variation), 2)
            prev_close = base_price
            
            quotes_data.append({
                "n": symbol,
                "s": "ok",
                "v": {
                    "ch": round(ltp - prev_close, 2),
                    "chp": round((ltp - prev_close) / prev_close * 100, 2),
                    "lp": ltp,
                    "spread": 0.05,
                    "ask": round(ltp + 0.05, 2),
                    "bid": round(ltp - 0.05, 2),
                    "open_price": round(base_price * (1 + random.uniform(-0.01, 0.01)), 2),
                    "high_price": round(ltp * 1.02, 2),
                    "low_price": round(ltp * 0.98, 2),
                    "prev_close_price": prev_close,
                    "atp": round(ltp, 2),
                    "volume": random.randint(100000, 5000000),
                    "short_name": symbol.split(":")[-1],
                    "exchange": symbol.split(":")[0],
                    "description": symbol,
                    "original_name": symbol,
                    "symbol": symbol,
                    "fyToken": f"101{random.randint(10000, 99999)}",
                    "tt": str(int(datetime.now().timestamp()))
                }
            })
        
        return {
            "s": "ok",
            "code": 200,
            "d": quotes_data
        }
    
    async def get_market_depth(self, symbol: str, ohlcv_flag: int = 1) -> Dict[str, Any]:
        """Get market depth - Fyers-like response"""
        base_price = self.symbol_prices.get(symbol, 1000.0)
        ltp = round(base_price * (1 + random.uniform(-0.01, 0.01)), 2)
        
        # Generate mock bid/ask data
        bids = []
        asks = []
        for i in range(5):
            bids.append({
                "price": round(ltp - (i + 1) * 0.05, 2),
                "volume": random.randint(100, 5000),
                "ord": random.randint(1, 20)
            })
            asks.append({
                "price": round(ltp + (i + 1) * 0.05, 2),
                "volume": random.randint(100, 5000),
                "ord": random.randint(1, 20)
            })
        
        return {
            "s": "ok",
            "d": {
                symbol: {
                    "totalbuyqty": sum(b["volume"] for b in bids),
                    "totalsellqty": sum(a["volume"] for a in asks),
                    "bids": bids,
                    "ask": asks,
                    "o": round(base_price * 1.001, 2),
                    "h": round(ltp * 1.02, 2),
                    "l": round(ltp * 0.98, 2),
                    "c": base_price,
                    "chp": round((ltp - base_price) / base_price * 100, 2),
                    "tick_Size": 0.05,
                    "ch": round(ltp - base_price, 2),
                    "ltq": random.randint(1, 100),
                    "ltt": int(datetime.now().timestamp()),
                    "ltp": ltp,
                    "v": random.randint(100000, 5000000),
                    "atp": ltp,
                    "lower_ckt": round(base_price * 0.90, 2),
                    "upper_ckt": round(base_price * 1.10, 2),
                }
            },
            "message": ""
        }
    
    async def get_history(
        self, 
        symbol: str, 
        resolution: str, 
        date_format: int,
        range_from: str,
        range_to: str,
        cont_flag: int = 0
    ) -> Dict[str, Any]:
        """Get historical data - Fyers-like response"""
        base_price = self.symbol_prices.get(symbol, 1000.0)
        
        # Generate mock candles (5 candles for simplicity)
        candles = []
        for i in range(5):
            timestamp = int((datetime.now() - timedelta(days=5-i)).timestamp())
            open_price = round(base_price * (1 + random.uniform(-0.02, 0.02)), 2)
            high_price = round(open_price * (1 + random.uniform(0, 0.03)), 2)
            low_price = round(open_price * (1 - random.uniform(0, 0.03)), 2)
            close_price = round((high_price + low_price) / 2, 2)
            volume = random.randint(1000000, 10000000)
            
            candles.append([timestamp, open_price, high_price, low_price, close_price, volume])
        
        return {
            "s": "ok",
            "candles": candles
        }
    
    async def get_option_chain(self, symbol: str, strike_count: int = 10) -> Dict[str, Any]:
        """Get option chain data - Fyers-like response"""
        base_price = self.symbol_prices.get(symbol, 1000.0)
        atm_strike = round(base_price / 100) * 100  # Round to nearest 100
        
        options_chain = []
        for i in range(-strike_count, strike_count + 1):
            strike = atm_strike + (i * 100)
            
            # Call option
            call_symbol = f"{symbol.replace('-EQ', '')}24DEC{strike}CE"
            options_chain.append({
                "symbol": call_symbol,
                "strike_price": strike,
                "option_type": "CE",
                "ltp": round(max(base_price - strike, 5), 2),
                "bid": round(max(base_price - strike - 0.5, 4.5), 2),
                "ask": round(max(base_price - strike + 0.5, 5.5), 2),
                "oi": random.randint(10000, 500000),
                "volume": random.randint(1000, 100000)
            })
            
            # Put option
            put_symbol = f"{symbol.replace('-EQ', '')}24DEC{strike}PE"
            options_chain.append({
                "symbol": put_symbol,
                "strike_price": strike,
                "option_type": "PE",
                "ltp": round(max(strike - base_price, 5), 2),
                "bid": round(max(strike - base_price - 0.5, 4.5), 2),
                "ask": round(max(strike - base_price + 0.5, 5.5), 2),
                "oi": random.randint(10000, 500000),
                "volume": random.randint(1000, 100000)
            })
        
        return {
            "s": "ok",
            "code": 200,
            "data": {
                "optionsChain": options_chain,
                "callOi": sum(o["oi"] for o in options_chain if o["option_type"] == "CE"),
                "putOi": sum(o["oi"] for o in options_chain if o["option_type"] == "PE"),
            }
        }
    
    async def place_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Place order - Fyers-like response"""
        order_id = f"25{datetime.now().strftime('%m%d')}00{random.randint(100000, 999999)}"
        
        self.orders[order_id] = {
            **order_data,
            "id": order_id,
            "status": 2,  # Filled
            "filledQty": order_data.get("qty", 0),
            "exchOrdId": f"11{random.randint(100000000, 999999999)}",
            "orderDateTime": datetime.now().strftime("%d-%b-%Y %H:%M:%S")
        }
        
        return {
            "s": "ok",
            "code": 1101,
            "message": f"Order submitted successfully. Your Order Ref. No.{order_id}",
            "id": order_id
        }
    
    async def place_multi_order(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Place multiple orders - Fyers-like response"""
        responses = []
        for order in orders:
            result = await self.place_order(order)
            responses.append({
                "statusCode": 200,
                "body": result,
                "statusDescription": "HTTP OK"
            })
        
        return {
            "s": "ok",
            "code": 200,
            "message": "",
            "data": responses
        }
    
    async def modify_order(self, order_id: str, modifications: Dict[str, Any]) -> Dict[str, Any]:
        """Modify order - Fyers-like response"""
        if order_id in self.orders:
            self.orders[order_id].update(modifications)
            return {
                "s": "ok",
                "code": 1102,
                "message": "Successfully modified order",
                "id": order_id
            }
        return {
            "s": "error",
            "code": -1,
            "message": "Order not found"
        }
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel order - Fyers-like response"""
        if order_id in self.orders:
            self.orders[order_id]["status"] = 1  # Cancelled
            return {
                "s": "ok",
                "code": 1103,
                "message": "Successfully cancelled order",
                "id": order_id
            }
        return {
            "s": "error",
            "code": -1,
            "message": "Order not found"
        }
    
    async def cancel_multi_order(self, order_ids: List[str]) -> Dict[str, Any]:
        """Cancel multiple orders - Fyers-like response"""
        responses = []
        for order_id in order_ids:
            result = await self.cancel_order(order_id)
            responses.append({
                "statusCode": 200,
                "body": result,
                "statusDescription": "HTTP OK"
            })
        
        return {
            "s": "ok",
            "code": 200,
            "message": "",
            "data": responses
        }
    
    async def get_positions(self) -> Dict[str, Any]:
        """Get positions - Fyers-like response"""
        positions_list = []
        for pos_id, pos in self.positions.items():
            positions_list.append(pos)
        
        return {
            "s": "ok",
            "code": 200,
            "netPositions": positions_list
        }
    
    async def exit_position(self, position_id: Optional[str] = None) -> Dict[str, Any]:
        """Exit position - Fyers-like response"""
        if position_id and position_id in self.positions:
            del self.positions[position_id]
            return {
                "s": "ok",
                "code": 200,
                "message": "The position is closed."
            }
        elif position_id is None:
            self.positions.clear()
            return {
                "s": "ok",
                "code": 200,
                "message": "All positions are closed"
            }
        return {
            "s": "error",
            "code": -1,
            "message": "Position not found"
        }
    
    async def convert_position(self, conversion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert position - Fyers-like response"""
        return {
            "s": "ok",
            "code": 200,
            "message": "Position Converted Successfully!!",
            "positionDetails": 1101
        }
    
    async def place_gtt_order(self, gtt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Place GTT order - Fyers-like response"""
        gtt_id = f"25{datetime.now().strftime('%m%d')}00{random.randint(100000, 999999)}"
        self.gtt_orders[gtt_id] = {**gtt_data, "id": gtt_id}
        
        return {
            "s": "ok",
            "code": 1101,
            "message": "Successfully placed order",
            "id": gtt_id
        }
    
    async def modify_gtt_order(self, gtt_id: str, modifications: Dict[str, Any]) -> Dict[str, Any]:
        """Modify GTT order - Fyers-like response"""
        if gtt_id in self.gtt_orders:
            self.gtt_orders[gtt_id].update(modifications)
            return {
                "s": "ok",
                "code": 1102,
                "message": "Successfully modified order",
                "id": gtt_id
            }
        return {"s": "error", "code": -1, "message": "GTT order not found"}
    
    async def cancel_gtt_order(self, gtt_id: str) -> Dict[str, Any]:
        """Cancel GTT order - Fyers-like response"""
        if gtt_id in self.gtt_orders:
            del self.gtt_orders[gtt_id]
            return {
                "s": "ok",
                "code": 1103,
                "message": "Successfully cancelled order",
                "id": gtt_id
            }
        return {"s": "error", "code": -1, "message": "GTT order not found"}
    
    async def get_gtt_orders(self) -> Dict[str, Any]:
        """Get all GTT orders - Fyers-like response"""
        return {
            "s": "ok",
            "code": 200,
            "message": "",
            "orderBook": list(self.gtt_orders.values())
        }
    
    async def calculate_span_margin(self, positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate span margin - Fyers-like response"""
        # Mock margin calculation
        total_margin = sum(
            pos.get("qty", 0) * pos.get("limitPrice", 100) * 0.20  # 20% margin
            for pos in positions
        )
        
        return {
            "s": "ok",
            "code": 200,
            "margin_total": round(total_margin, 2)
        }
    
    async def calculate_multi_order_margin(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate margin for multiple orders - Fyers-like response"""
        total_margin = sum(
            order.get("qty", 0) * order.get("limitPrice", 100) * 0.20  # 20% margin
            for order in orders
        )
        
        return {
            "s": "ok",
            "code": 200,
            "data": {
                "margin_avail": 100000.0,  # Mock available margin
                "margin_total": round(total_margin, 2),
                "margin_new_order": round(total_margin, 2)
            }
        }