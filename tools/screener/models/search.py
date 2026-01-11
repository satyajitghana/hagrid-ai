"""Search API response models."""

from pydantic import BaseModel, Field


class CompanySearchResult(BaseModel):
    """Individual company search result."""
    
    id: int | None = Field(
        default=None,
        description="Unique company ID in Screener database"
    )
    name: str = Field(
        description="Company name"
    )
    url: str = Field(
        description="URL path to company page"
    )
    
    @property
    def symbol(self) -> str | None:
        """Extract symbol from URL path."""
        # URL format: /company/SYMBOL/consolidated/ or /company/SYMBOL/
        if self.url:
            parts = self.url.strip("/").split("/")
            if len(parts) >= 2 and parts[0] == "company":
                return parts[1]
        return None
    
    @property
    def is_consolidated(self) -> bool:
        """Check if this is consolidated data."""
        return "consolidated" in self.url
    
    @property
    def is_search_everywhere(self) -> bool:
        """Check if this is a 'search everywhere' option."""
        return self.id is None and "full-text-search" in self.url


class CompanySearchResponse(BaseModel):
    """Response from company search API."""
    
    results: list[CompanySearchResult] = Field(
        default_factory=list,
        description="List of matching companies"
    )
    
    @classmethod
    def from_api_response(cls, data: list[dict]) -> "CompanySearchResponse":
        """Create response from raw API data."""
        results = [CompanySearchResult.model_validate(item) for item in data]
        return cls(results=results)
    
    @property
    def companies(self) -> list[CompanySearchResult]:
        """Get only actual company results (excluding search everywhere option)."""
        return [r for r in self.results if not r.is_search_everywhere]
    
    @property
    def first(self) -> CompanySearchResult | None:
        """Get the first company result."""
        companies = self.companies
        return companies[0] if companies else None