"""
API Routes Package

Provides REST API endpoints for:
- /api/trades - Trade history and management
- /api/workflows - Workflow sessions and runs
"""

from api.routes.trades import router as trades_router
from api.routes.workflows import router as workflows_router

__all__ = ["trades_router", "workflows_router"]
