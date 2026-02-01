"""Routes package"""
from .chat import router as chat_router
from .products import router as products_router

__all__ = ["chat_router", "products_router"]
