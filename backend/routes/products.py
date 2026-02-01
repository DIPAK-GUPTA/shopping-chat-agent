"""
Products API Routes
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from models.phone import Phone, PhoneFilter
from models.chat import ProductCard, ComparisonData
from database.repository import phone_repository

router = APIRouter(prefix="/products", tags=["products"])


def phone_to_card(phone: Phone) -> ProductCard:
    """Convert Phone to ProductCard"""
    return ProductCard(
        id=phone.id,
        brand=phone.brand,
        model=phone.model,
        price_inr=phone.price_inr,
        display_size=phone.display_size,
        ram_gb=phone.ram_gb,
        storage_gb=phone.storage_gb,
        battery_mah=phone.battery_mah,
        camera_main_mp=phone.camera.main_mp,
        rating=phone.rating,
        image_url=phone.image_url,
        key_features=phone.special_features[:4]
    )


@router.get("", response_model=List[ProductCard])
async def list_products(
    brand: Optional[str] = Query(None, description="Filter by brand"),
    min_price: Optional[int] = Query(None, description="Minimum price in INR"),
    max_price: Optional[int] = Query(None, description="Maximum price in INR"),
    min_ram: Optional[int] = Query(None, description="Minimum RAM in GB"),
    min_battery: Optional[int] = Query(None, description="Minimum battery in mAh"),
    compact: Optional[bool] = Query(None, description="Compact phones only"),
    sort_by: Optional[str] = Query("rating", description="Sort by: rating, price, battery"),
    limit: Optional[int] = Query(20, description="Number of results")
) -> List[ProductCard]:
    """
    List and filter phones
    """
    filters = PhoneFilter(
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        min_ram=min_ram,
        min_battery=min_battery,
        compact_only=compact
    )
    
    phones = phone_repository.filter_phones(filters)
    
    # Sort
    if sort_by == "price":
        phones = sorted(phones, key=lambda p: p.price_inr)
    elif sort_by == "price_desc":
        phones = sorted(phones, key=lambda p: p.price_inr, reverse=True)
    elif sort_by == "battery":
        phones = sorted(phones, key=lambda p: p.battery_mah, reverse=True)
    elif sort_by == "camera":
        phones = sorted(phones, key=lambda p: p.camera.main_mp, reverse=True)
    else:  # rating (default)
        phones = sorted(phones, key=lambda p: p.rating, reverse=True)
    
    # Limit
    phones = phones[:limit]
    
    return [phone_to_card(p) for p in phones]


@router.get("/brands")
async def list_brands():
    """
    Get list of available brands
    """
    phones = phone_repository.get_all()
    brands = set(p.brand for p in phones)
    return {"brands": sorted(list(brands))}


@router.get("/stats")
async def get_stats():
    """
    Get catalog statistics
    """
    phones = phone_repository.get_all()
    prices = [p.price_inr for p in phones]
    
    return {
        "total_phones": len(phones),
        "brands": len(set(p.brand for p in phones)),
        "min_price": min(prices),
        "max_price": max(prices),
        "avg_price": sum(prices) // len(prices)
    }


@router.get("/{phone_id}")
async def get_product(phone_id: str):
    """
    Get detailed phone information by ID
    """
    phone = phone_repository.get_by_id(phone_id)
    if not phone:
        raise HTTPException(status_code=404, detail="Phone not found")
    
    return {
        "id": phone.id,
        "brand": phone.brand,
        "model": phone.model,
        "full_name": phone.full_name,
        "price_inr": phone.price_inr,
        "display": {
            "size": phone.display_size,
            "type": phone.display_type,
            "refresh_rate": phone.refresh_rate,
            "resolution": phone.resolution
        },
        "performance": {
            "processor": phone.processor,
            "ram_gb": phone.ram_gb,
            "storage_gb": phone.storage_gb,
            "expandable_storage": phone.expandable_storage
        },
        "battery": {
            "capacity_mah": phone.battery_mah,
            "fast_charging_watts": phone.fast_charging_watts,
            "wireless_charging": phone.wireless_charging
        },
        "camera": {
            "main_mp": phone.camera.main_mp,
            "ultra_wide_mp": phone.camera.ultra_wide_mp,
            "telephoto_mp": phone.camera.telephoto_mp,
            "front_mp": phone.camera.front_mp,
            "features": phone.camera.features
        },
        "os_version": phone.os_version,
        "weight_grams": phone.weight_grams,
        "dimensions": phone.dimensions,
        "special_features": phone.special_features,
        "rating": phone.rating,
        "reviews_count": phone.reviews_count,
        "image_url": phone.image_url
    }


@router.post("/compare")
async def compare_products(phone_ids: List[str]):
    """
    Compare 2-3 phones by their IDs
    """
    if len(phone_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 phones to compare")
    
    if len(phone_ids) > 3:
        raise HTTPException(status_code=400, detail="Can compare at most 3 phones")
    
    comparison = phone_repository.compare_phones(phone_ids)
    if not comparison:
        raise HTTPException(status_code=404, detail="Some phones not found")
    
    phones_data = []
    for phone in comparison.phones:
        phones_data.append({
            "id": phone.id,
            "brand": phone.brand,
            "model": phone.model,
            "full_name": phone.full_name,
            "price_inr": phone.price_inr,
            "display_size": phone.display_size,
            "display_type": phone.display_type,
            "refresh_rate": phone.refresh_rate,
            "processor": phone.processor,
            "ram_gb": phone.ram_gb,
            "storage_gb": phone.storage_gb,
            "battery_mah": phone.battery_mah,
            "fast_charging_watts": phone.fast_charging_watts,
            "wireless_charging": phone.wireless_charging,
            "camera_main_mp": phone.camera.main_mp,
            "camera_features": phone.camera.features,
            "special_features": phone.special_features,
            "rating": phone.rating
        })
    
    return {
        "phones": phones_data,
        "highlights": comparison.highlights
    }


@router.get("/search/{query}")
async def search_products(query: str, limit: int = 10):
    """
    Search phones by name or brand
    """
    phones = phone_repository.search(query)[:limit]
    return [phone_to_card(p) for p in phones]
