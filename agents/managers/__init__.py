"""
Department Managers and Chief Investment Officer

Hierarchical structure for Hagrid Trading LLC:
- CIO (Chief Investment Officer) - Top level manager
- Department Managers - Each manages a specialized team
  - Technical Analysis Manager
  - Fundamentals Manager
  - Market Intelligence Manager
  - Derivatives Manager
"""

from agents.managers.technical_manager import technical_manager
from agents.managers.fundamentals_manager import fundamentals_manager
from agents.managers.market_intel_manager import market_intel_manager
from agents.managers.derivatives_manager import derivatives_manager
from agents.managers.cio import chief_investment_officer

__all__ = [
    "technical_manager",
    "fundamentals_manager",
    "market_intel_manager",
    "derivatives_manager",
    "chief_investment_officer",
]
