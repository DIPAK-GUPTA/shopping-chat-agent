"""
Pydantic models for Phone data
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class Brand(str, Enum):
    """Supported phone brands"""
    SAMSUNG = "Samsung"
    ONEPLUS = "OnePlus"
    GOOGLE = "Google"
    XIAOMI = "Xiaomi"
    APPLE = "Apple"
    REALME = "Realme"
    VIVO = "Vivo"
    OPPO = "Oppo"
    MOTOROLA = "Motorola"
    NOTHING = "Nothing"


class CameraSpec(BaseModel):
    """Camera specifications"""
    main_mp: int = Field(description="Main camera megapixels")
    ultra_wide_mp: Optional[int] = Field(default=None, description="Ultra-wide camera MP")
    telephoto_mp: Optional[int] = Field(default=None, description="Telephoto camera MP")
    front_mp: int = Field(description="Front camera megapixels")
    features: List[str] = Field(default_factory=list, description="Camera features like OIS, EIS")


class Phone(BaseModel):
    """Complete phone model"""
    id: str = Field(description="Unique identifier")
    brand: str = Field(description="Phone brand")
    model: str = Field(description="Phone model name")
    price_inr: int = Field(description="Price in Indian Rupees")
    
    # Display
    display_size: float = Field(description="Display size in inches")
    display_type: str = Field(description="Display type (AMOLED, LCD, etc.)")
    refresh_rate: int = Field(default=60, description="Refresh rate in Hz")
    resolution: str = Field(description="Screen resolution")
    
    # Performance
    processor: str = Field(description="Processor/SoC name")
    ram_gb: int = Field(description="RAM in GB")
    storage_gb: int = Field(description="Storage in GB")
    expandable_storage: bool = Field(default=False, description="Has SD card slot")
    
    # Battery
    battery_mah: int = Field(description="Battery capacity in mAh")
    fast_charging_watts: int = Field(description="Fast charging power in watts")
    wireless_charging: bool = Field(default=False, description="Supports wireless charging")
    
    # Camera
    camera: CameraSpec = Field(description="Camera specifications")
    
    # Software
    os_version: str = Field(description="Operating system version")
    
    # Physical
    weight_grams: int = Field(description="Weight in grams")
    dimensions: str = Field(description="Dimensions in mm")
    
    # Special features
    special_features: List[str] = Field(default_factory=list, description="Special features")
    
    # Ratings
    rating: float = Field(default=4.0, ge=1.0, le=5.0, description="User rating")
    reviews_count: int = Field(default=0, description="Number of reviews")
    
    # Media
    image_url: str = Field(default="", description="Product image URL")
    
    @property
    def full_name(self) -> str:
        """Get full phone name"""
        return f"{self.brand} {self.model}"
    
    @property
    def is_compact(self) -> bool:
        """Check if phone is compact (under 6.3 inches)"""
        return self.display_size < 6.3
    
    @property
    def has_telephoto(self) -> bool:
        """Check if phone has telephoto lens"""
        return self.camera.telephoto_mp is not None


class PhoneFilter(BaseModel):
    """Filter criteria for phone search"""
    brand: Optional[str] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    min_ram: Optional[int] = None
    min_storage: Optional[int] = None
    min_battery: Optional[int] = None
    has_fast_charging: Optional[bool] = None
    features: Optional[List[str]] = None
    compact_only: Optional[bool] = None


class PhoneComparison(BaseModel):
    """Comparison result between phones"""
    phones: List[Phone]
    highlights: dict = Field(default_factory=dict, description="Key differences highlighted")
    recommendation: Optional[str] = None
