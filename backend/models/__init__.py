"""Models package"""
from .phone import Phone, PhoneFilter, PhoneComparison, CameraSpec
from .chat import (
    ChatMessage, ChatRequest, ChatResponse, 
    ProductCard, ComparisonData, SessionContext,
    MessageRole, QueryIntent
)

__all__ = [
    "Phone", "PhoneFilter", "PhoneComparison", "CameraSpec",
    "ChatMessage", "ChatRequest", "ChatResponse",
    "ProductCard", "ComparisonData", "SessionContext",
    "MessageRole", "QueryIntent"
]
