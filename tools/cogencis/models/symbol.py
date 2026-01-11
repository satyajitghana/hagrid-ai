"""Symbol lookup models for Cogencis API."""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, field_validator

from .common import PagingInfo


class SearchOn(str, Enum):
    """Search field options for symbol lookup."""

    NAME = "name"
    ISIN = "isin"
    SYMBOL = "symbol"
    NAME_ISIN = "name|isin"
    NAME_SYMBOL = "name|symbol"
    ISIN_SYMBOL = "isin|symbol"
    ALL = "name|isin|symbol"


class SymbolData(BaseModel):
    """Individual symbol data from lookup response.
    
    Field mappings from API:
    - f_5051: symbol (e.g., "RELINDUS.NS")
    - f_5104: isin (e.g., "INE002A01018")
    - f_400: company_name (e.g., "Reliance Industries Ltd.")
    - f_5121: symbol_type ("S" for stock)
    - f_2: last_price
    - f_11: price_change
    - f_56: percent_change
    - path: unique path identifier
    """

    symbol: str = Field(alias="f_5051")
    isin: str = Field(alias="f_5104")
    company_name: str = Field(alias="f_400")
    symbol_type: str = Field(alias="f_5121")
    last_price: float = Field(alias="f_2")
    price_change: float = Field(alias="f_11")
    percent_change: float = Field(alias="f_56")
    path: str

    @field_validator("last_price", "price_change", "percent_change", mode="before")
    @classmethod
    def parse_numeric(cls, v: Any) -> float:
        """Parse numeric values that may come as strings."""
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                return 0.0
        return float(v) if v is not None else 0.0

    @property
    def exchange(self) -> str | None:
        """Extract exchange from symbol (e.g., 'NS' from 'RELINDUS.NS')."""
        if "." in self.symbol:
            return self.symbol.split(".")[-1]
        return None

    @property
    def ticker(self) -> str:
        """Extract ticker without exchange suffix."""
        if "." in self.symbol:
            return self.symbol.split(".")[0]
        return self.symbol

    class Config:
        populate_by_name = True


class SymbolLookupData(BaseModel):
    """Paginated symbol lookup data."""

    paging_info: PagingInfo = Field(alias="pagingInfo")
    data: list[SymbolData]

    class Config:
        populate_by_name = True


class SymbolLookupResponse(BaseModel):
    """Response model for symbol lookup API."""

    status: bool
    message: str
    response: SymbolLookupData | None = None

    @property
    def is_success(self) -> bool:
        """Check if the response indicates success."""
        return self.status is True

    @property
    def symbols(self) -> list[SymbolData]:
        """Get the list of symbols from the response."""
        if self.response:
            return self.response.data
        return []

    @property
    def total_results(self) -> int:
        """Get total number of matching results."""
        if self.response:
            return self.response.paging_info.total_records
        return 0

    class Config:
        populate_by_name = True