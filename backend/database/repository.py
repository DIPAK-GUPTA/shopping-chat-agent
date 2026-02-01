"""
Phone Database Repository
Handles all database operations for phone catalog
"""
import json
from pathlib import Path
from typing import List, Optional
from models.phone import Phone, PhoneFilter, PhoneComparison, CameraSpec


class PhoneRepository:
    """Repository for phone data access"""
    
    def __init__(self, data_path: str = None):
        """Initialize repository with data file path"""
        if data_path is None:
            data_path = Path(__file__).parent.parent / "data" / "phone_catalog.json"
        self.data_path = Path(data_path)
        self._phones: List[Phone] = []
        self._load_data()
    
    def _load_data(self) -> None:
        """Load phone data from JSON file"""
        try:
            with open(self.data_path, 'r') as f:
                data = json.load(f)
            
            self._phones = []
            for item in data:
                # Convert camera dict to CameraSpec
                camera_data = item.pop('camera', {})
                camera_spec = CameraSpec(**camera_data)
                item['camera'] = camera_spec
                self._phones.append(Phone(**item))
                
        except Exception as e:
            print(f"Error loading phone data: {e}")
            self._phones = []
    
    def get_all(self) -> List[Phone]:
        """Get all phones"""
        return self._phones
    
    def get_by_id(self, phone_id: str) -> Optional[Phone]:
        """Get phone by ID"""
        for phone in self._phones:
            if phone.id == phone_id:
                return phone
        return None
    
    def get_by_ids(self, phone_ids: List[str]) -> List[Phone]:
        """Get multiple phones by IDs"""
        return [p for p in self._phones if p.id in phone_ids]
    
    def search(self, query: str) -> List[Phone]:
        """Enhanced text search with fuzzy matching across brand and model"""
        query_lower = query.lower().strip()
        results = []
        
        # Common abbreviations and mappings
        abbreviations = {
            "op": "oneplus",
            "mi": "xiaomi",
            "rn": "redmi note",
            "poco": "poco",
            "nord": "nord",
            "pixel": "pixel",
            "iphone": "iphone",
            "galaxy": "galaxy",
            "s24": "galaxy s24",
            "a55": "galaxy a55",
            "m35": "galaxy m35",
        }
        
        # Expand abbreviations
        expanded_query = query_lower
        for abbr, full in abbreviations.items():
            if abbr in query_lower:
                expanded_query = query_lower.replace(abbr, full)
        
        for phone in self._phones:
            # Check various matching criteria
            model_lower = phone.model.lower()
            brand_lower = phone.brand.lower()
            full_name_lower = phone.full_name.lower()
            id_lower = phone.id.lower()
            
            # Direct matches
            if (query_lower in model_lower or 
                query_lower in brand_lower or
                query_lower in full_name_lower or
                query_lower in id_lower):
                results.append(phone)
                continue
            
            # Expanded query matches
            if (expanded_query in model_lower or 
                expanded_query in full_name_lower):
                results.append(phone)
                continue
            
            # Partial token matching (for queries like "pixel 8a" matching "Pixel 8a")
            query_tokens = query_lower.split()
            if len(query_tokens) >= 2:
                matches = sum(1 for token in query_tokens 
                             if token in model_lower or token in brand_lower or token in id_lower)
                if matches >= len(query_tokens) * 0.6:  # 60% token match
                    results.append(phone)
        
        return results
    
    def filter_phones(self, filters: PhoneFilter) -> List[Phone]:
        """Filter phones based on criteria"""
        results = self._phones.copy()
        
        if filters.brand:
            results = [p for p in results if p.brand.lower() == filters.brand.lower()]
        
        if filters.min_price is not None:
            results = [p for p in results if p.price_inr >= filters.min_price]
        
        if filters.max_price is not None:
            results = [p for p in results if p.price_inr <= filters.max_price]
        
        if filters.min_ram is not None:
            results = [p for p in results if p.ram_gb >= filters.min_ram]
        
        if filters.min_storage is not None:
            results = [p for p in results if p.storage_gb >= filters.min_storage]
        
        if filters.min_battery is not None:
            results = [p for p in results if p.battery_mah >= filters.min_battery]
        
        if filters.has_fast_charging:
            results = [p for p in results if p.fast_charging_watts >= 30]
        
        if filters.compact_only:
            results = [p for p in results if p.is_compact]
        
        if filters.features:
            for feature in filters.features:
                feature_lower = feature.lower()
                results = [p for p in results if any(
                    feature_lower in f.lower() for f in p.special_features
                ) or any(
                    feature_lower in f.lower() for f in p.camera.features
                )]
        
        return results
    
    def get_by_price_range(self, min_price: int, max_price: int) -> List[Phone]:
        """Get phones within price range"""
        return [p for p in self._phones if min_price <= p.price_inr <= max_price]
    
    def get_by_brand(self, brand: str) -> List[Phone]:
        """Get phones by brand"""
        return [p for p in self._phones if p.brand.lower() == brand.lower()]
    
    def get_camera_phones(self, max_price: Optional[int] = None) -> List[Phone]:
        """Get best camera phones, optionally within budget"""
        phones = self._phones.copy()
        if max_price:
            phones = [p for p in phones if p.price_inr <= max_price]
        
        # Sort by camera MP and features
        return sorted(phones, key=lambda p: (
            p.camera.main_mp,
            len(p.camera.features),
            1 if p.camera.telephoto_mp else 0
        ), reverse=True)
    
    def get_battery_champions(self, max_price: Optional[int] = None) -> List[Phone]:
        """Get phones with best battery"""
        phones = self._phones.copy()
        if max_price:
            phones = [p for p in phones if p.price_inr <= max_price]
        
        return sorted(phones, key=lambda p: (
            p.battery_mah,
            p.fast_charging_watts
        ), reverse=True)
    
    def get_compact_phones(self, max_price: Optional[int] = None) -> List[Phone]:
        """Get compact phones (under 6.3 inches)"""
        phones = [p for p in self._phones if p.is_compact]
        if max_price:
            phones = [p for p in phones if p.price_inr <= max_price]
        return sorted(phones, key=lambda p: p.rating, reverse=True)
    
    def get_fast_charging_phones(self, max_price: Optional[int] = None, min_watts: int = 60) -> List[Phone]:
        """Get phones with fast charging capability"""
        phones = self._phones.copy()
        if max_price:
            phones = [p for p in phones if p.price_inr <= max_price]
        
        # Filter for fast charging phones
        phones = [p for p in phones if p.fast_charging_watts >= min_watts]
        
        return sorted(phones, key=lambda p: (
            p.fast_charging_watts,
            p.battery_mah
        ), reverse=True)
    
    def get_value_phones(self, min_price: int = 0, max_price: int = 50000) -> List[Phone]:
        """Get best value phones in a price range (specs-to-price ratio)"""
        phones = [p for p in self._phones 
                  if min_price <= p.price_inr <= max_price]
        
        # Calculate value score: (RAM + storage/16 + battery/1000 + camera/10) / (price/10000)
        def value_score(p: Phone) -> float:
            spec_score = (p.ram_gb + p.storage_gb/16 + p.battery_mah/1000 + 
                         p.camera.main_mp/10 + p.refresh_rate/30)
            price_factor = p.price_inr / 10000
            return spec_score / price_factor if price_factor > 0 else 0
        
        return sorted(phones, key=value_score, reverse=True)
    
    def get_gaming_phones(self, max_price: Optional[int] = None) -> List[Phone]:
        """Get best phones for gaming"""
        phones = self._phones.copy()
        if max_price:
            phones = [p for p in phones if p.price_inr <= max_price]
        
        # Sort by gaming-relevant specs
        return sorted(phones, key=lambda p: (
            p.ram_gb,
            p.refresh_rate,
            1 if "gaming" in " ".join(p.special_features).lower() else 0,
            p.battery_mah
        ), reverse=True)
    
    def compare_phones(self, phone_ids: List[str]) -> Optional[PhoneComparison]:
        """Compare 2-3 phones"""
        phones = self.get_by_ids(phone_ids)
        if len(phones) < 2:
            return None
        
        # Generate highlights
        highlights = {
            "best_price": min(phones, key=lambda p: p.price_inr).id,
            "best_camera": max(phones, key=lambda p: p.camera.main_mp).id,
            "best_battery": max(phones, key=lambda p: p.battery_mah).id,
            "best_display": max(phones, key=lambda p: p.refresh_rate).id,
            "best_performance": max(phones, key=lambda p: p.ram_gb).id,
            "fastest_charging": max(phones, key=lambda p: p.fast_charging_watts).id,
        }
        
        return PhoneComparison(phones=phones, highlights=highlights)
    
    def get_phones_for_context(self, limit: int = 10) -> str:
        """Get phone summary for AI context"""
        phones = sorted(self._phones, key=lambda p: p.rating, reverse=True)[:limit]
        summaries = []
        for p in phones:
            summaries.append(
                f"- {p.full_name}: ₹{p.price_inr:,}, {p.display_size}\", "
                f"{p.camera.main_mp}MP camera, {p.battery_mah}mAh, {p.ram_gb}GB RAM"
            )
        return "\n".join(summaries)


# Global repository instance
phone_repository = PhoneRepository()
