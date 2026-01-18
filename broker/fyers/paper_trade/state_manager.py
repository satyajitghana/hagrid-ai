"""
Paper trading state manager with JSON file persistence.

Handles loading, saving, and managing the paper trading state including
orders, trades, positions, holdings, and funds.
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional

from .models import (
    PaperTradeState,
    PaperFunds,
    PaperOrderStatus,
)


class PaperTradeStateManager:
    """Manages paper trading state with file persistence."""

    def __init__(self, state_file: str, initial_balance: float = 100000.0):
        """
        Initialize the state manager.

        Args:
            state_file: Path to the JSON state file.
            initial_balance: Starting capital for paper trading.
        """
        self.state_file = Path(state_file)
        self.initial_balance = initial_balance
        self._state: Optional[PaperTradeState] = None
        self._lock = asyncio.Lock()

    async def load_or_create(self) -> PaperTradeState:
        """
        Load existing state from file or create a new one.

        Returns:
            The loaded or newly created PaperTradeState.
        """
        async with self._lock:
            if self.state_file.exists():
                try:
                    with open(self.state_file, "r") as f:
                        data = json.load(f)
                    self._state = PaperTradeState(**data)
                except Exception:
                    # If loading fails, create fresh state
                    self._state = self._create_fresh_state()
            else:
                self._state = self._create_fresh_state()
            return self._state

    def _create_fresh_state(self) -> PaperTradeState:
        """Create a new paper trading state with initial balance."""
        now = datetime.now().isoformat()
        return PaperTradeState(
            created_at=now,
            updated_at=now,
            funds=PaperFunds(
                total_balance=self.initial_balance,
                available_balance=self.initial_balance,
            ),
        )

    async def save(self) -> None:
        """Persist current state to JSON file."""
        async with self._lock:
            if self._state:
                self._state.updated_at = datetime.now().isoformat()
                # Ensure parent directory exists
                self.state_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.state_file, "w") as f:
                    json.dump(self._state.model_dump(), f, indent=2)

    @property
    def state(self) -> PaperTradeState:
        """
        Get the current state.

        Raises:
            RuntimeError: If state has not been loaded yet.
        """
        if self._state is None:
            raise RuntimeError("State not loaded. Call load_or_create() first")
        return self._state

    def generate_order_id(self) -> str:
        """
        Generate a unique order ID.

        Format: PT-{YYYYMMDDHHMMSS}-{counter:06d}
        """
        self.state.order_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"PT-{timestamp}-{self.state.order_counter:06d}"

    def generate_trade_id(self) -> str:
        """
        Generate a unique trade ID.

        Format: PTT-{YYYYMMDDHHMMSS}-{counter:06d}
        """
        self.state.trade_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"PTT-{timestamp}-{self.state.trade_counter:06d}"

    def generate_holding_id(self) -> int:
        """Generate a unique holding ID."""
        self.state.holding_counter += 1
        return self.state.holding_counter

    async def reset_daily_positions(self, current_date: str) -> None:
        """
        Reset intraday positions at day change.

        Squares off all INTRADAY positions and updates realized P&L.

        Args:
            current_date: Current trading date in YYYY-MM-DD format.
        """
        if self.state.last_trading_date != current_date:
            # Square off intraday positions
            positions_to_remove = []
            for pos_id, position in self.state.positions.items():
                if position.productType == "INTRADAY" and position.netQty != 0:
                    # Mark realized P&L from position
                    self.state.funds.realized_pnl += position.pl
                    self.state.funds.available_balance += position.utilized_margin if hasattr(position, 'utilized_margin') else 0
                    positions_to_remove.append(pos_id)

            # Remove squared-off positions
            for pos_id in positions_to_remove:
                del self.state.positions[pos_id]

            # Reset day quantities for remaining positions
            for position in self.state.positions.values():
                position.dayBuyQty = 0
                position.daySellQty = 0

            self.state.last_trading_date = current_date
            await self.save()

    async def reset_state(self) -> None:
        """
        Reset the paper trading state to initial values.

        This clears all orders, trades, positions, holdings and resets funds.
        """
        self._state = self._create_fresh_state()
        await self.save()

    def get_open_orders(self) -> list:
        """Get all orders with PENDING status."""
        return [
            order
            for order in self.state.orders.values()
            if order.status == PaperOrderStatus.PENDING
        ]

    def get_open_positions(self) -> list:
        """Get all positions with non-zero net quantity."""
        return [pos for pos in self.state.positions.values() if pos.netQty != 0]

    def get_today_orders(self) -> list:
        """Get orders placed today."""
        today = datetime.now().strftime("%Y-%m-%d")
        return [
            order
            for order in self.state.orders.values()
            if order.created_at.startswith(today)
        ]

    def get_today_trades(self) -> list:
        """Get trades executed today."""
        today = datetime.now().strftime("%Y-%m-%d")
        return [
            trade
            for trade in self.state.trades
            if trade.orderDateTime.startswith(today)
        ]
