from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class GlobalIndex(BaseModel):
    """
    Model for Global Index data.
    """
    symbol: str
    name: str
    country: Optional[str] = None
    last_price: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    market_state: Optional[str] = None