"""
Paper trade execution engine.

Handles order execution logic including market orders, limit orders,
position updates, and P&L calculations.
"""

from datetime import datetime
from typing import Optional, Tuple

from .models import (
    PaperOrder,
    PaperTrade,
    PaperPosition,
    PaperHolding,
    PaperOrderStatus,
)
from .state_manager import PaperTradeStateManager


class PaperTradeExecutionEngine:
    """Simulates order execution logic for paper trading."""

    def __init__(self, state_manager: PaperTradeStateManager):
        """
        Initialize the execution engine.

        Args:
            state_manager: The PaperTradeStateManager instance for state access.
        """
        self.state_manager = state_manager

    async def execute_market_order(
        self, order: PaperOrder, ltp: float
    ) -> Tuple[PaperOrder, Optional[PaperTrade]]:
        """
        Execute a market order immediately at the given LTP.

        Args:
            order: The order to execute.
            ltp: Last traded price to execute at.

        Returns:
            Tuple of (updated order, trade record or None if failed).
        """
        order.status = PaperOrderStatus.TRADED
        order.tradedPrice = ltp
        order.filledQty = order.qty
        order.remainingQuantity = 0
        order.updated_at = datetime.now().isoformat()

        # Create trade record
        trade = PaperTrade(
            tradeNumber=self.state_manager.generate_trade_id(),
            orderNumber=order.id,
            symbol=order.symbol,
            tradePrice=ltp,
            tradeValue=ltp * order.qty,
            tradedQty=order.qty,
            side=order.side,
            productType=order.productType,
            orderDateTime=datetime.now().isoformat(),
            segment=order.segment,
            exchange=order.exchange,
        )

        # Update position
        await self._update_position(order, ltp)

        # Update holdings for CNC orders
        if order.productType == "CNC":
            await self._update_holding(order, ltp)

        return order, trade

    async def check_limit_order(
        self,
        order: PaperOrder,
        ltp: float,
        high: float,
        low: float,
    ) -> Tuple[PaperOrder, Optional[PaperTrade]]:
        """
        Check if a limit/stop order should execute based on price range.

        Args:
            order: The order to check.
            ltp: Current last traded price.
            high: High price of the period.
            low: Low price of the period.

        Returns:
            Tuple of (updated order, trade record or None if not executed).
        """
        if order.status != PaperOrderStatus.PENDING:
            return order, None

        should_execute = False
        exec_price = order.limitPrice

        # Order type constants matching Fyers
        ORDER_TYPE_LIMIT = 1
        ORDER_TYPE_MARKET = 2
        ORDER_TYPE_STOP = 3
        ORDER_TYPE_STOP_LIMIT = 4

        if order.type == ORDER_TYPE_LIMIT:
            # Buy limit: executes if price <= limit
            # Sell limit: executes if price >= limit
            if order.side == 1:  # Buy
                should_execute = low <= order.limitPrice
                exec_price = min(order.limitPrice, ltp)
            else:  # Sell
                should_execute = high >= order.limitPrice
                exec_price = max(order.limitPrice, ltp)

        elif order.type == ORDER_TYPE_STOP:
            # Stop market: triggers when price crosses stop price
            if order.side == 1:  # Buy stop
                should_execute = high >= order.stopPrice
                exec_price = max(order.stopPrice, ltp)
            else:  # Sell stop
                should_execute = low <= order.stopPrice
                exec_price = min(order.stopPrice, ltp)

        elif order.type == ORDER_TYPE_STOP_LIMIT:
            # Stop limit: triggers at stop price, executes at limit
            if order.side == 1:  # Buy
                triggered = high >= order.stopPrice
                if triggered:
                    should_execute = low <= order.limitPrice
                    exec_price = min(order.limitPrice, ltp)
            else:  # Sell
                triggered = low <= order.stopPrice
                if triggered:
                    should_execute = high >= order.limitPrice
                    exec_price = max(order.limitPrice, ltp)

        if should_execute:
            return await self.execute_market_order(order, exec_price)

        return order, None

    async def _update_position(self, order: PaperOrder, exec_price: float) -> None:
        """
        Update or create a position based on an executed order.

        Args:
            order: The executed order.
            exec_price: The execution price.
        """
        state = self.state_manager.state
        pos_id = f"{order.symbol}-{order.productType}"

        if pos_id not in state.positions:
            state.positions[pos_id] = PaperPosition(
                id=pos_id,
                symbol=order.symbol,
                productType=order.productType,
                ltp=exec_price,
                segment=order.segment,
                exchange=order.exchange,
            )

        pos = state.positions[pos_id]
        trade_value = exec_price * order.qty

        if order.side == 1:  # Buy
            # Update buy average using weighted average
            total_buy_value = (pos.buyAvg * pos.buyQty) + trade_value
            pos.buyQty += order.qty
            pos.buyAvg = total_buy_value / pos.buyQty if pos.buyQty > 0 else 0
            pos.dayBuyQty += order.qty

            # Deduct from available balance
            state.funds.available_balance -= trade_value
            state.funds.utilized_margin += trade_value
        else:  # Sell
            # Update sell average using weighted average
            total_sell_value = (pos.sellAvg * pos.sellQty) + trade_value
            pos.sellQty += order.qty
            pos.sellAvg = total_sell_value / pos.sellQty if pos.sellQty > 0 else 0
            pos.daySellQty += order.qty

            # Add to available balance
            state.funds.available_balance += trade_value
            state.funds.utilized_margin -= trade_value

        # Calculate net position
        pos.netQty = pos.buyQty - pos.sellQty
        pos.qty = abs(pos.netQty)
        pos.side = 1 if pos.netQty > 0 else (-1 if pos.netQty < 0 else 0)

        # Calculate net average
        if pos.netQty > 0:
            pos.netAvg = pos.buyAvg
        elif pos.netQty < 0:
            pos.netAvg = pos.sellAvg
        else:
            pos.netAvg = 0

        # Calculate P&L
        min_qty = min(pos.buyQty, pos.sellQty)
        if min_qty > 0:
            pos.realized_profit = min_qty * (pos.sellAvg - pos.buyAvg)

        pos.ltp = exec_price
        if pos.netQty != 0:
            pos.unrealized_profit = pos.netQty * (exec_price - pos.netAvg)
        else:
            pos.unrealized_profit = 0

        pos.pl = pos.realized_profit + pos.unrealized_profit

        # Update funds realized P&L
        state.funds.realized_pnl = sum(p.realized_profit for p in state.positions.values())

    async def _update_holding(self, order: PaperOrder, exec_price: float) -> None:
        """
        Update holdings for CNC (delivery) orders.

        Args:
            order: The executed CNC order.
            exec_price: The execution price.
        """
        state = self.state_manager.state
        symbol = order.symbol

        if order.side == 1:  # Buy - add to holdings
            if symbol in state.holdings:
                holding = state.holdings[symbol]
                # Update weighted average cost
                total_value = (holding.costPrice * holding.quantity) + (exec_price * order.qty)
                holding.quantity += order.qty
                holding.remainingQuantity += order.qty
                holding.costPrice = total_value / holding.quantity if holding.quantity > 0 else 0
            else:
                # Create new holding
                state.holdings[symbol] = PaperHolding(
                    id=self.state_manager.generate_holding_id(),
                    symbol=symbol,
                    quantity=order.qty,
                    remainingQuantity=order.qty,
                    costPrice=exec_price,
                    marketVal=exec_price * order.qty,
                    ltp=exec_price,
                    exchange=order.exchange,
                    segment=order.segment,
                )
        else:  # Sell - reduce holdings
            if symbol in state.holdings:
                holding = state.holdings[symbol]
                holding.remainingQuantity -= order.qty
                if holding.remainingQuantity <= 0:
                    # Remove holding if fully sold
                    del state.holdings[symbol]

    def update_position_ltp(self, position: PaperPosition, ltp: float) -> None:
        """
        Update a position's LTP and recalculate unrealized P&L.

        Args:
            position: The position to update.
            ltp: New last traded price.
        """
        position.ltp = ltp
        if position.netQty != 0:
            position.unrealized_profit = position.netQty * (ltp - position.netAvg)
        else:
            position.unrealized_profit = 0
        position.pl = position.realized_profit + position.unrealized_profit

    def update_holding_ltp(self, holding: PaperHolding, ltp: float) -> None:
        """
        Update a holding's LTP and recalculate market value and P&L.

        Args:
            holding: The holding to update.
            ltp: New last traded price.
        """
        holding.ltp = ltp
        holding.marketVal = ltp * holding.quantity
        holding.pl = (ltp - holding.costPrice) * holding.quantity
