"""
Postback (Webhooks) handler for Fyers order notifications.

Fyers sends POST requests with JSON payloads to your registered
webhook URL when order status changes.

Setup:
1. Register webhook URL in Fyers API Dashboard
2. Set webhook secret and preferences (Cancel, Rejected, Pending, Traded)
3. After successful login via your app, webhooks become active

Note: URL can be blacklisted for 30 minutes if:
- Response status is not 200
- POST request fails after 3 retries
"""

from datetime import datetime
from enum import IntEnum
from typing import Optional, Callable, Awaitable, Any, Dict, List
from pydantic import BaseModel, Field

from broker.fyers.core.logger import get_logger

logger = get_logger("fyers.webhooks")


class OrderStatus(IntEnum):
    """Order status codes."""
    CANCELLED = 1
    TRADED = 2
    # 3 is not used
    TRANSIT = 4
    REJECTED = 5
    PENDING = 6
    EXPIRED = 7


class Segment(IntEnum):
    """Segment codes."""
    EQUITY = 10
    DERIVATIVE = 11
    CURRENCY = 12
    COMMODITY = 20


class PostbackPayload(BaseModel):
    """
    Model for Fyers postback/webhook payload.
    
    This is sent to your webhook URL when an order status changes.
    """
    
    id: str = Field(..., description="Unique order ID")
    exchOrdId: Optional[str] = Field(None, description="Exchange order ID")
    symbol: str = Field(..., description="Symbol (e.g., NSE:SBIN-EQ)")
    qty: int = Field(..., description="Original order quantity")
    remainingQuantity: int = Field(..., description="Remaining quantity")
    filledQty: int = Field(..., description="Filled quantity")
    status: int = Field(..., description="Order status (1-7)")
    message: Optional[str] = Field(None, description="Status message")
    segment: int = Field(..., description="Segment (10, 11, 12, 20)")
    limitPrice: float = Field(0, description="Limit price")
    stopPrice: float = Field(0, description="Stop price")
    productType: str = Field(..., description="Product type")
    type: int = Field(..., description="Order type (1-4)")
    side: int = Field(..., description="Order side (1=Buy, -1=Sell)")
    disclosedQty: int = Field(0, alias="discloseQty", description="Disclosed quantity")
    dqQtyRem: int = Field(0, description="Remaining disclosed quantity")
    orderValidity: str = Field(..., description="Order validity (DAY, IOC)")
    orderDateTime: str = Field(..., description="Order datetime (epoch or formatted)")
    tradedPrice: float = Field(0, description="Average traded price")
    source: Optional[str] = Field(None, description="Order source")
    fytoken: Optional[str] = Field(None, alias="fyToken", description="Fytoken")
    offlineOrder: bool = Field(False, description="Is AMO order")
    pan: Optional[str] = Field(None, description="Client PAN")
    clientId: Optional[str] = Field(None, description="Client ID")
    exchange: int = Field(..., description="Exchange code")
    instrument: Optional[str] = Field(None, description="Instrument type")
    orderNumStatus: Optional[str] = Field(None, description="Order number with status")
    
    class Config:
        populate_by_name = True
        extra = "ignore"
    
    def is_filled(self) -> bool:
        """Check if order is fully filled."""
        return self.status == OrderStatus.TRADED
    
    def is_pending(self) -> bool:
        """Check if order is pending."""
        return self.status == OrderStatus.PENDING
    
    def is_cancelled(self) -> bool:
        """Check if order is cancelled."""
        return self.status == OrderStatus.CANCELLED
    
    def is_rejected(self) -> bool:
        """Check if order is rejected."""
        return self.status == OrderStatus.REJECTED
    
    def is_expired(self) -> bool:
        """Check if order is expired."""
        return self.status == OrderStatus.EXPIRED
    
    def get_status_name(self) -> str:
        """Get human-readable status name."""
        status_map = {
            OrderStatus.CANCELLED: "Cancelled",
            OrderStatus.TRADED: "Traded",
            OrderStatus.TRANSIT: "Transit",
            OrderStatus.REJECTED: "Rejected",
            OrderStatus.PENDING: "Pending",
            OrderStatus.EXPIRED: "Expired",
        }
        return status_map.get(self.status, f"Unknown({self.status})")


# Type for callback functions
PostbackCallback = Callable[[PostbackPayload], Awaitable[None]]


class PostbackHandler:
    """
    Handler for processing Fyers postback notifications.
    
    Example:
        ```python
        handler = PostbackHandler()
        
        @handler.on_traded
        async def handle_traded(payload: PostbackPayload):
            print(f"Order {payload.id} traded at {payload.tradedPrice}")
        
        @handler.on_rejected
        async def handle_rejected(payload: PostbackPayload):
            print(f"Order {payload.id} rejected: {payload.message}")
        
        # In your webhook endpoint:
        await handler.process(json_data)
        ```
    """
    
    def __init__(self, webhook_secret: Optional[str] = None):
        """
        Initialize postback handler.
        
        Args:
            webhook_secret: Optional secret for verifying webhook requests
        """
        self.webhook_secret = webhook_secret
        
        self._on_any: List[PostbackCallback] = []
        self._on_traded: List[PostbackCallback] = []
        self._on_pending: List[PostbackCallback] = []
        self._on_cancelled: List[PostbackCallback] = []
        self._on_rejected: List[PostbackCallback] = []
        self._on_expired: List[PostbackCallback] = []
        self._on_transit: List[PostbackCallback] = []
        
        logger.info("PostbackHandler initialized")
    
    def on_any(self, callback: PostbackCallback) -> PostbackCallback:
        """Register callback for all order updates."""
        self._on_any.append(callback)
        return callback
    
    def on_traded(self, callback: PostbackCallback) -> PostbackCallback:
        """Register callback for traded/filled orders."""
        self._on_traded.append(callback)
        return callback
    
    def on_pending(self, callback: PostbackCallback) -> PostbackCallback:
        """Register callback for pending orders."""
        self._on_pending.append(callback)
        return callback
    
    def on_cancelled(self, callback: PostbackCallback) -> PostbackCallback:
        """Register callback for cancelled orders."""
        self._on_cancelled.append(callback)
        return callback
    
    def on_rejected(self, callback: PostbackCallback) -> PostbackCallback:
        """Register callback for rejected orders."""
        self._on_rejected.append(callback)
        return callback
    
    def on_expired(self, callback: PostbackCallback) -> PostbackCallback:
        """Register callback for expired orders."""
        self._on_expired.append(callback)
        return callback
    
    def on_transit(self, callback: PostbackCallback) -> PostbackCallback:
        """Register callback for orders in transit."""
        self._on_transit.append(callback)
        return callback
    
    async def process(self, data: Dict[str, Any]) -> PostbackPayload:
        """
        Process a postback payload.
        
        Args:
            data: Raw JSON payload from webhook
            
        Returns:
            Parsed PostbackPayload
        """
        payload = PostbackPayload(**data)
        
        logger.info(
            f"Received postback: order={payload.id}, "
            f"status={payload.get_status_name()}, "
            f"symbol={payload.symbol}"
        )
        
        # Call any handlers
        for callback in self._on_any:
            try:
                await callback(payload)
            except Exception as e:
                logger.error(f"Error in on_any callback: {e}")
        
        # Call status-specific handlers
        callbacks = []
        if payload.status == OrderStatus.TRADED:
            callbacks = self._on_traded
        elif payload.status == OrderStatus.PENDING:
            callbacks = self._on_pending
        elif payload.status == OrderStatus.CANCELLED:
            callbacks = self._on_cancelled
        elif payload.status == OrderStatus.REJECTED:
            callbacks = self._on_rejected
        elif payload.status == OrderStatus.EXPIRED:
            callbacks = self._on_expired
        elif payload.status == OrderStatus.TRANSIT:
            callbacks = self._on_transit
        
        for callback in callbacks:
            try:
                await callback(payload)
            except Exception as e:
                logger.error(f"Error in status callback: {e}")
        
        return payload
    
    def verify_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        """
        Verify webhook signature (if using webhook secret).
        
        Args:
            payload: Raw request body
            signature: Signature from request header
            
        Returns:
            True if signature is valid
        """
        if not self.webhook_secret:
            return True
        
        import hmac
        import hashlib
        
        expected = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        
        return hmac.compare_digest(expected, signature)


def create_webhook_server(
    handler: PostbackHandler,
    host: str = "0.0.0.0",
    port: int = 8080,
    path: str = "/webhook",
):
    """
    Create a simple webhook server using FastAPI.
    
    Requires FastAPI and uvicorn to be installed.
    
    Args:
        handler: PostbackHandler instance
        host: Server host
        port: Server port
        path: Webhook endpoint path
        
    Returns:
        FastAPI app instance
        
    Example:
        ```python
        handler = PostbackHandler()
        
        @handler.on_traded
        async def on_traded(payload):
            print(f"Order traded: {payload.id}")
        
        app = create_webhook_server(handler)
        
        # Run with: uvicorn module:app --host 0.0.0.0 --port 8080
        ```
    """
    try:
        from fastapi import FastAPI, Request, Response, HTTPException
    except ImportError:
        raise ImportError(
            "FastAPI is required for webhook server. "
            "Install with: pip install fastapi uvicorn"
        )
    
    app = FastAPI(
        title="Fyers Webhook Server",
        description="Handles Fyers order postback notifications",
    )
    
    @app.post(path)
    async def webhook_endpoint(request: Request):
        """Handle incoming webhook from Fyers."""
        try:
            body = await request.body()
            
            # Verify signature if configured
            signature = request.headers.get("X-Fyers-Signature", "")
            if handler.webhook_secret and signature:
                if not handler.verify_signature(body, signature):
                    raise HTTPException(status_code=401, detail="Invalid signature")
            
            # Parse and process payload
            import json
            data = json.loads(body)
            await handler.process(data)
            
            return Response(status_code=200, content="OK")
            
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            # Return 200 anyway to prevent blacklisting
            # Log the error for debugging
            return Response(status_code=200, content="Error logged")
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "ok"}
    
    return app