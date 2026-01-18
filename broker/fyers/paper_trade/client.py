"""
Paper trading Fyers client.

Intercepts all trading operations (orders, positions, funds, holdings)
and simulates them locally. Market data operations (quotes, history,
option chains) still use the real Fyers API.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from broker.fyers.client import FyersClient
from broker.fyers.models.config import FyersConfig
from broker.fyers.models.responses import (
    OrderPlacementResponse,
    OrderModifyResponse,
    OrderCancelResponse,
    MultiOrderResponse,
    MultiOrderItemResponse,
    OrdersResponse,
    OrderItem,
    PositionsResponse,
    PositionItem,
    PositionsOverall,
    FundsResponse,
    FundItem,
    HoldingsResponse,
    HoldingItem,
    HoldingsOverall,
    TradesResponse,
    TradeItem,
    GenericResponse,
)

from .models import PaperOrder, PaperOrderStatus
from .state_manager import PaperTradeStateManager
from .execution import PaperTradeExecutionEngine


class PaperTradeFyersClient(FyersClient):
    """
    Paper trading implementation of FyersClient.

    Intercepts all trading operations (orders, positions, funds, holdings)
    and simulates them locally. Market data operations (quotes, history,
    option chains) still use the real Fyers API.

    Usage:
        ```python
        from broker.fyers.paper_trade import PaperTradeFyersClient

        config = FyersConfig(...)
        client = PaperTradeFyersClient(
            config=config,
            state_file=".hagrid/paper_trade_state.json",
            initial_balance=100000.0
        )

        # Still authenticates with real API for market data
        await client.authenticate()

        # Orders are simulated
        response = await client.place_order({...})  # Paper trade!

        # Market data is real
        quotes = await client.get_quotes(["NSE:SBIN-EQ"])  # Real API
        ```
    """

    def __init__(
        self,
        config: FyersConfig,
        state_file: str,
        initial_balance: float = 100000.0,
        **kwargs,
    ):
        """
        Initialize the paper trading client.

        Args:
            config: FyersConfig for API authentication (market data).
            state_file: Path to the JSON state file.
            initial_balance: Starting capital for paper trading.
            **kwargs: Additional arguments passed to FyersClient.
        """
        super().__init__(config, **kwargs)
        self.state_manager = PaperTradeStateManager(state_file, initial_balance)
        self.execution_engine = PaperTradeExecutionEngine(self.state_manager)
        self._initialized = False
        self._ltp_update_task: Optional[asyncio.Task] = None

    async def _ensure_paper_trade_init(self) -> None:
        """Initialize paper trading state on first use."""
        if not self._initialized:
            await self.state_manager.load_or_create()
            self._initialized = True

    # ==================== Order Operations (Simulated) ====================

    async def place_order(self, order_data: Dict[str, Any]) -> OrderPlacementResponse:
        """
        Place a simulated order.

        For market orders, executes immediately at current LTP.
        For limit/stop orders, stays pending until price conditions are met.

        Args:
            order_data: Order parameters (symbol, qty, side, type, productType, etc.)

        Returns:
            OrderPlacementResponse with order ID or error.
        """
        await self._ensure_paper_trade_init()

        # Validate required fields
        required = ["symbol", "qty", "side", "type", "productType"]
        for field in required:
            if field not in order_data:
                return OrderPlacementResponse(
                    s="error",
                    code=500,
                    message=f"Missing required field: {field}",
                )

        # Create paper order
        now = datetime.now().isoformat()
        order_id = self.state_manager.generate_order_id()

        order = PaperOrder(
            id=order_id,
            symbol=order_data["symbol"],
            qty=order_data["qty"],
            remainingQuantity=order_data["qty"],
            type=order_data["type"],
            side=order_data["side"],
            productType=order_data["productType"],
            limitPrice=order_data.get("limitPrice", 0.0),
            stopPrice=order_data.get("stopPrice", 0.0),
            orderValidity=order_data.get("validity", "DAY"),
            orderDateTime=now,
            orderTag=order_data.get("orderTag"),
            created_at=now,
            updated_at=now,
        )

        # For market orders, execute immediately using real LTP
        if order_data["type"] == 2:  # Market order
            try:
                quotes = await super().get_quotes([order_data["symbol"]])
                ltp = 0.0
                if quotes.d:
                    for q in quotes.d:
                        if q.v and q.v.get("lp"):
                            ltp = q.v.get("lp")
                            break

                if ltp > 0:
                    order, trade = await self.execution_engine.execute_market_order(
                        order, ltp
                    )
                    if trade:
                        self.state_manager.state.trades.append(trade)
                else:
                    order.status = PaperOrderStatus.REJECTED
                    order.message = "Could not get LTP for market order"
            except Exception as e:
                order.status = PaperOrderStatus.REJECTED
                order.message = f"Market order execution failed: {str(e)}"

        # Store order
        self.state_manager.state.orders[order_id] = order
        await self.state_manager.save()

        if order.status == PaperOrderStatus.REJECTED:
            return OrderPlacementResponse(
                s="error", code=500, message=order.message, id=order_id
            )

        return OrderPlacementResponse(
            s="ok", code=1101, message="Order placed successfully", id=order_id
        )

    async def modify_order(
        self, order_id: str, modifications: Dict[str, Any]
    ) -> OrderModifyResponse:
        """
        Modify a pending paper order.

        Args:
            order_id: The order ID to modify.
            modifications: Fields to modify (qty, limitPrice, stopPrice, type).

        Returns:
            OrderModifyResponse indicating success or failure.
        """
        await self._ensure_paper_trade_init()

        if order_id not in self.state_manager.state.orders:
            return OrderModifyResponse(
                s="error", code=500, message="Order not found", id=order_id
            )

        order = self.state_manager.state.orders[order_id]

        if order.status != PaperOrderStatus.PENDING:
            return OrderModifyResponse(
                s="error",
                code=500,
                message="Cannot modify non-pending order",
                id=order_id,
            )

        # Apply modifications
        if "qty" in modifications:
            order.qty = modifications["qty"]
            order.remainingQuantity = modifications["qty"]
        if "limitPrice" in modifications:
            order.limitPrice = modifications["limitPrice"]
        if "stopPrice" in modifications:
            order.stopPrice = modifications["stopPrice"]
        if "type" in modifications:
            order.type = modifications["type"]

        order.updated_at = datetime.now().isoformat()
        await self.state_manager.save()

        return OrderModifyResponse(
            s="ok", code=1102, message="Order modified successfully", id=order_id
        )

    async def cancel_order(self, order_id: str) -> OrderCancelResponse:
        """
        Cancel a pending paper order.

        Args:
            order_id: The order ID to cancel.

        Returns:
            OrderCancelResponse indicating success or failure.
        """
        await self._ensure_paper_trade_init()

        if order_id not in self.state_manager.state.orders:
            return OrderCancelResponse(
                s="error", code=500, message="Order not found", id=order_id
            )

        order = self.state_manager.state.orders[order_id]

        if order.status != PaperOrderStatus.PENDING:
            return OrderCancelResponse(
                s="error",
                code=500,
                message="Cannot cancel non-pending order",
                id=order_id,
            )

        order.status = PaperOrderStatus.CANCELLED
        order.updated_at = datetime.now().isoformat()
        await self.state_manager.save()

        return OrderCancelResponse(
            s="ok", code=1103, message="Order cancelled successfully", id=order_id
        )

    async def get_orders(self) -> OrdersResponse:
        """
        Get all paper orders for the day.

        Returns:
            OrdersResponse with order book.
        """
        await self._ensure_paper_trade_init()

        today = datetime.now().strftime("%Y-%m-%d")
        orders = []

        for order in self.state_manager.state.orders.values():
            if order.created_at.startswith(today):
                orders.append(
                    OrderItem(
                        id=order.id,
                        exchOrdId=order.exchOrdId,
                        symbol=order.symbol,
                        qty=order.qty,
                        remainingQuantity=order.remainingQuantity,
                        filledQty=order.filledQty,
                        status=order.status,
                        segment=order.segment,
                        limitPrice=order.limitPrice,
                        stopPrice=order.stopPrice,
                        productType=order.productType,
                        type=order.type,
                        side=order.side,
                        orderValidity=order.orderValidity,
                        orderDateTime=order.orderDateTime,
                        tradedPrice=order.tradedPrice,
                        exchange=order.exchange,
                        message=order.message,
                    )
                )

        return OrdersResponse(s="ok", code=200, message="", orderBook=orders)

    # ==================== Position Operations (Simulated) ====================

    async def get_positions(self) -> PositionsResponse:
        """
        Get all paper positions with updated LTPs and P&L.

        Fetches current LTPs from real API to calculate unrealized P&L.

        Returns:
            PositionsResponse with positions and overall summary.
        """
        await self._ensure_paper_trade_init()

        # Update unrealized P&L with current LTPs
        positions = []
        total_pl = 0.0
        total_realized = 0.0
        total_unrealized = 0.0

        # Collect symbols for bulk quote fetch
        symbols = [
            pos.symbol
            for pos in self.state_manager.state.positions.values()
            if pos.netQty != 0
        ]

        # Fetch LTPs in bulk
        ltp_map = {}
        if symbols:
            try:
                quotes = await super().get_quotes(symbols[:50])  # Max 50
                if quotes.d:
                    for q in quotes.d:
                        if q.v and q.v.get("lp"):
                            ltp_map[q.n] = q.v.get("lp")
            except Exception:
                pass

        for pos in self.state_manager.state.positions.values():
            # Update LTP if available
            if pos.symbol in ltp_map:
                self.execution_engine.update_position_ltp(pos, ltp_map[pos.symbol])

            positions.append(
                PositionItem(
                    symbol=pos.symbol,
                    id=pos.id,
                    buyAvg=pos.buyAvg,
                    buyQty=pos.buyQty,
                    sellAvg=pos.sellAvg,
                    sellQty=pos.sellQty,
                    netAvg=pos.netAvg,
                    netQty=pos.netQty,
                    side=pos.side,
                    qty=pos.qty,
                    productType=pos.productType,
                    realized_profit=pos.realized_profit,
                    unrealized_profit=pos.unrealized_profit,
                    pl=pos.pl,
                    segment=pos.segment,
                    exchange=pos.exchange,
                    ltp=pos.ltp,
                    dayBuyQty=pos.dayBuyQty,
                    daySellQty=pos.daySellQty,
                    cfBuyQty=pos.cfBuyQty,
                    cfSellQty=pos.cfSellQty,
                )
            )

            total_pl += pos.pl
            total_realized += pos.realized_profit
            total_unrealized += pos.unrealized_profit

        overall = PositionsOverall(
            count_total=len(positions),
            count_open=sum(1 for p in positions if p.netQty != 0),
            pl_total=total_pl,
            pl_realized=total_realized,
            pl_unrealized=total_unrealized,
        )

        return PositionsResponse(
            s="ok", code=200, message="", netPositions=positions, overall=overall
        )

    async def exit_position(self, position_id: Optional[str] = None) -> GenericResponse:
        """
        Exit paper position(s) by placing opposite market orders.

        Args:
            position_id: Specific position ID to exit, or None for all.

        Returns:
            GenericResponse indicating success or failure.
        """
        await self._ensure_paper_trade_init()

        positions_to_exit = []
        if position_id:
            if position_id in self.state_manager.state.positions:
                positions_to_exit.append(
                    self.state_manager.state.positions[position_id]
                )
        else:
            positions_to_exit = list(self.state_manager.state.positions.values())

        for pos in positions_to_exit:
            if pos.netQty != 0:
                # Place opposite order to exit
                exit_order = {
                    "symbol": pos.symbol,
                    "qty": abs(pos.netQty),
                    "side": -1 if pos.netQty > 0 else 1,  # Opposite side
                    "type": 2,  # Market order
                    "productType": pos.productType,
                }
                await self.place_order(exit_order)

        return GenericResponse(s="ok", code=200, message="Position(s) exited")

    async def exit_positions_by_ids(
        self, position_ids: List[str]
    ) -> GenericResponse:
        """
        Exit multiple positions by their IDs.

        Args:
            position_ids: List of position IDs to exit.

        Returns:
            GenericResponse indicating success or failure.
        """
        for pos_id in position_ids:
            await self.exit_position(pos_id)
        return GenericResponse(s="ok", code=200, message="Positions exited")

    # ==================== Funds Operations (Simulated) ====================

    async def get_funds(self) -> FundsResponse:
        """
        Get simulated funds and margin.

        Returns:
            FundsResponse with fund limits.
        """
        await self._ensure_paper_trade_init()

        funds = self.state_manager.state.funds

        # Update unrealized P&L from positions
        total_unrealized = sum(
            pos.unrealized_profit
            for pos in self.state_manager.state.positions.values()
        )
        funds.unrealized_pnl = total_unrealized

        fund_items = [
            FundItem(
                id=1,
                title="Total Balance",
                equityAmount=funds.total_balance + funds.realized_pnl,
                commodityAmount=0,
            ),
            FundItem(
                id=10,
                title="Available Balance",
                equityAmount=funds.available_balance,
                commodityAmount=0,
            ),
            FundItem(
                id=2,
                title="Utilized Margin",
                equityAmount=funds.utilized_margin,
                commodityAmount=0,
            ),
            FundItem(
                id=5,
                title="Realized P&L",
                equityAmount=funds.realized_pnl,
                commodityAmount=0,
            ),
            FundItem(
                id=6,
                title="Unrealized P&L",
                equityAmount=funds.unrealized_pnl,
                commodityAmount=0,
            ),
        ]

        return FundsResponse(s="ok", code=200, message="", fund_limit=fund_items)

    # ==================== Holdings Operations (Simulated) ====================

    async def get_holdings(self) -> HoldingsResponse:
        """
        Get simulated holdings (CNC positions) with updated LTPs.

        Returns:
            HoldingsResponse with holdings and overall summary.
        """
        await self._ensure_paper_trade_init()

        holdings = []
        total_investment = 0.0
        total_current_value = 0.0
        total_pl = 0.0

        # Collect symbols for bulk quote fetch
        symbols = list(self.state_manager.state.holdings.keys())

        # Fetch LTPs in bulk
        ltp_map = {}
        if symbols:
            try:
                quotes = await super().get_quotes(symbols[:50])  # Max 50
                if quotes.d:
                    for q in quotes.d:
                        if q.v and q.v.get("lp"):
                            ltp_map[q.n] = q.v.get("lp")
            except Exception:
                pass

        for holding in self.state_manager.state.holdings.values():
            # Update LTP if available
            if holding.symbol in ltp_map:
                self.execution_engine.update_holding_ltp(holding, ltp_map[holding.symbol])

            holdings.append(
                HoldingItem(
                    symbol=holding.symbol,
                    holdingType=holding.holdingType,
                    quantity=holding.quantity,
                    remainingQuantity=holding.remainingQuantity,
                    pl=holding.pl,
                    costPrice=holding.costPrice,
                    marketVal=holding.marketVal,
                    ltp=holding.ltp,
                    id=holding.id,
                    exchange=holding.exchange,
                    segment=holding.segment,
                )
            )

            total_investment += holding.costPrice * holding.quantity
            total_current_value += holding.marketVal
            total_pl += holding.pl

        overall = HoldingsOverall(
            count_total=len(holdings),
            total_investment=total_investment,
            total_current_value=total_current_value,
            total_pl=total_pl,
            pnl_perc=(total_pl / total_investment * 100) if total_investment > 0 else 0,
        )

        return HoldingsResponse(
            s="ok", code=200, message="", holdings=holdings, overall=overall
        )

    # ==================== Trade Book (Simulated) ====================

    async def get_tradebook(self) -> TradesResponse:
        """
        Get paper trade book for the day.

        Returns:
            TradesResponse with trade history.
        """
        await self._ensure_paper_trade_init()

        today = datetime.now().strftime("%Y-%m-%d")
        trades = []

        for i, trade in enumerate(self.state_manager.state.trades):
            if trade.orderDateTime.startswith(today):
                trades.append(
                    TradeItem(
                        symbol=trade.symbol,
                        row=i,
                        orderDateTime=trade.orderDateTime,
                        orderNumber=trade.orderNumber,
                        tradeNumber=trade.tradeNumber,
                        tradePrice=trade.tradePrice,
                        tradeValue=trade.tradeValue,
                        tradedQty=trade.tradedQty,
                        side=trade.side,
                        productType=trade.productType,
                        exchangeOrderNo=trade.tradeNumber,
                        segment=trade.segment,
                        exchange=trade.exchange,
                    )
                )

        return TradesResponse(s="ok", code=200, message="", tradeBook=trades)

    # ==================== Multi-Order Operations (Simulated) ====================

    async def place_multi_order(
        self, orders: List[Dict[str, Any]]
    ) -> MultiOrderResponse:
        """
        Place multiple paper orders.

        Args:
            orders: List of order data dictionaries.

        Returns:
            MultiOrderResponse with results for each order.
        """
        results = []
        for order_data in orders:
            response = await self.place_order(order_data)
            results.append(
                MultiOrderItemResponse(
                    statusCode=200 if response.s == "ok" else 500,
                    body=response,
                    statusDescription="Success" if response.s == "ok" else "Failed",
                )
            )

        return MultiOrderResponse(s="ok", code=200, message="", data=results)

    async def cancel_multi_order(self, order_ids: List[str]) -> MultiOrderResponse:
        """
        Cancel multiple paper orders.

        Args:
            order_ids: List of order IDs to cancel.

        Returns:
            MultiOrderResponse with results for each cancellation.
        """
        results = []
        for order_id in order_ids:
            response = await self.cancel_order(order_id)
            results.append(
                MultiOrderItemResponse(
                    statusCode=200 if response.s == "ok" else 500,
                    body=OrderPlacementResponse(
                        s=response.s,
                        code=response.code,
                        message=response.message,
                        id=response.id,
                    ),
                    statusDescription="Success" if response.s == "ok" else "Failed",
                )
            )

        return MultiOrderResponse(s="ok", code=200, message="", data=results)

    # ==================== LTP Update Methods ====================

    async def update_positions_ltp(self) -> None:
        """
        Bulk fetch current LTPs for all positions and holdings.

        Uses get_quotes() which supports up to 50 symbols per request.
        Updates unrealized P&L and persists state.
        """
        await self._ensure_paper_trade_init()

        # Get unique symbols from positions and holdings
        symbols = set()
        for pos in self.state_manager.state.positions.values():
            if pos.netQty != 0:
                symbols.add(pos.symbol)
        for holding in self.state_manager.state.holdings.values():
            symbols.add(holding.symbol)

        if not symbols:
            return

        # Batch into chunks of 50 (Fyers limit)
        symbol_list = list(symbols)
        for i in range(0, len(symbol_list), 50):
            batch = symbol_list[i : i + 50]
            try:
                quotes = await super().get_quotes(batch)

                if quotes.d:
                    ltp_map = {}
                    for q in quotes.d:
                        if q.v and q.v.get("lp"):
                            ltp_map[q.n] = q.v.get("lp")

                    # Update positions
                    for pos in self.state_manager.state.positions.values():
                        if pos.symbol in ltp_map:
                            self.execution_engine.update_position_ltp(
                                pos, ltp_map[pos.symbol]
                            )

                    # Update holdings
                    for holding in self.state_manager.state.holdings.values():
                        if holding.symbol in ltp_map:
                            self.execution_engine.update_holding_ltp(
                                holding, ltp_map[holding.symbol]
                            )
            except Exception:
                # Log but don't crash
                pass

        # Update funds unrealized P&L
        total_unrealized = sum(
            p.unrealized_profit for p in self.state_manager.state.positions.values()
        )
        self.state_manager.state.funds.unrealized_pnl = total_unrealized

        await self.state_manager.save()

    async def start_ltp_updates(self, interval_seconds: int = 600) -> asyncio.Task:
        """
        Start background task to update position LTPs periodically.

        Args:
            interval_seconds: Update interval in seconds (default: 600 = 10 minutes).

        Returns:
            asyncio.Task that can be cancelled with task.cancel().
        """

        async def _update_loop():
            while True:
                try:
                    await self.update_positions_ltp()
                except Exception:
                    # Log but don't crash
                    pass
                await asyncio.sleep(interval_seconds)

        self._ltp_update_task = asyncio.create_task(_update_loop())
        return self._ltp_update_task

    def stop_ltp_updates(self) -> None:
        """Stop the background LTP update task if running."""
        if self._ltp_update_task:
            self._ltp_update_task.cancel()
            self._ltp_update_task = None

    # ==================== State Management ====================

    async def reset_paper_trade_state(self) -> None:
        """
        Reset the paper trading state to initial values.

        Clears all orders, trades, positions, holdings and resets funds.
        """
        await self.state_manager.reset_state()
