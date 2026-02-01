"""
Pydantic models for Chat functionality
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Chat message roles"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class QueryIntent(str, Enum):
    """Detected user query intents"""
    SEARCH = "search"              # Looking for phones
    COMPARE = "compare"            # Compare specific phones
    EXPLAIN = "explain"            # Explain a feature/term
    RECOMMEND = "recommend"        # Get recommendations
    DETAILS = "details"            # More details about a phone
    FILTER = "filter"              # Filter by brand/feature
    GREETING = "greeting"          # Hello/Hi
    OFF_TOPIC = "off_topic"        # Not related to phones
    ADVERSARIAL = "adversarial"    # Potentially malicious
    UNCLEAR = "unclear"            # Ambiguous query


class ChatMessage(BaseModel):
    """Single chat message"""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Optional metadata
    intent: Optional[QueryIntent] = None
    phone_ids: List[str] = Field(default_factory=list, description="Referenced phone IDs")


class ChatRequest(BaseModel):
    """Incoming chat request from frontend"""
    message: str = Field(min_length=1, max_length=1000, description="User message")
    session_id: Optional[str] = Field(default=None, description="Session ID for context")
    

class ProductCard(BaseModel):
    """Product card data for frontend display"""
    id: str
    brand: str
    model: str
    price_inr: int
    display_size: float
    ram_gb: int
    storage_gb: int
    battery_mah: int
    camera_main_mp: int
    rating: float
    image_url: str
    key_features: List[str] = Field(default_factory=list)


class ComparisonData(BaseModel):
    """Structured comparison data for frontend"""
    phones: List[ProductCard]
    comparison_table: dict = Field(default_factory=dict)
    winner_by_category: dict = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """Response from chat endpoint"""
    message: str = Field(description="AI response text")
    intent: QueryIntent = Field(description="Detected intent")
    session_id: str = Field(description="Session ID for continuity")
    
    # Optional structured data
    products: Optional[List[ProductCard]] = None
    comparison: Optional[ComparisonData] = None
    
    # Metadata
    sources: List[str] = Field(default_factory=list, description="Phone IDs used")
    is_refusal: bool = Field(default=False, description="Was this a refused query")


class SessionContext(BaseModel):
    """Session context for multi-turn conversations"""
    session_id: str
    messages: List[ChatMessage] = Field(default_factory=list)
    last_mentioned_phones: List[str] = Field(default_factory=list)
    current_filters: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
