import uuid
import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from app.core.config import settings
from app.core.database import get_db, clean_doc
from app.api.v1.endpoints.auth import get_current_user
from app.schemas.all_schemas import BrandCreate, BrandUpdate, BrandResponse, Location, LocationCreate, LocationUpdate

# Presets for small businesses and local shops
BUSINESS_PRESETS = {
    "restaurant": {
        "id": "restaurant",
        "name": "Restaurant / Cafe / Eatery",
        "industry": "Food & Beverage",
        "description": "Restaurants, cafes, food trucks, fast food, and local mess",
        "default_topics": ["Food Quality & Taste", "Service Speed", "Cleanliness & Hygiene", "Waiting Time", "Price & Portion", "Staff Behavior", "Ambience", "Parking", "Delivery & Packaging"],
        "default_keywords": ["food", "taste", "service", "menu", "bill", "table", "waiter", "order", "chai", "biryani", "dosa", "coffee", "roast", "sambar"],
        "sample_reviews": [
            "Dosa was crispy and hot, degree filter coffee was authentic! Excellent service.",
            "Ghee roast romba super, but Sunday lunch waiting time was over 35 minutes.",
            "Biryani ka taste lajawab hai aur portion size bhi acha hai. Staff was polite.",
            "Food quality is great but car parking near entrance was very difficult during evening.",
            "Quick parcel delivery and neat packaging. Chutney was fresh."
        ]
    },
    "bakery": {
        "id": "bakery",
        "name": "Bakery & Sweet Shop",
        "industry": "Bakery & Confectionery",
        "description": "Cake shops, traditional sweet stalls, patisseries, and hot snack bakeries",
        "default_topics": ["Taste & Freshness", "Product Quality", "Cleanliness & Hygiene", "Packaging", "Pricing & Value", "Staff Behavior", "Custom Cakes"],
        "default_keywords": ["fresh", "cake", "sweets", "taste", "clean", "price", "snack", "box", "pastry", "cookies", "samosa", "puffs", "laddu"],
        "sample_reviews": [
            "Black forest cake was fresh and spongy. Perfect sweetness and beautiful birthday piping!",
            "Mysurpa pure ghee taste semma. Best traditional sweets for festival gifting.",
            "Evening veg puffs and hot samosas are always fresh and crispy. Polite counter staff.",
            "Pastry taste is good par price thoda high laga compared to nearby bakeries.",
            "Packaging is very hygienic and gift boxes look premium."
        ]
    },
    "retail": {
        "id": "retail",
        "name": "Retail Shop / Store",
        "industry": "Retail & Shopping",
        "description": "Clothing, footwear, gift shops, and general retail stores",
        "default_topics": ["Product Quality", "Price & Discounts", "Staff Behavior", "Store Cleanliness", "Stock Availability", "Billing Speed", "Exchange Policy"],
        "default_keywords": ["quality", "price", "discount", "staff", "collection", "stock", "exchange", "billing", "variety", "cloth", "sizes"],
        "sample_reviews": [
            "Great collection of cotton apparel at reasonable festival discount prices.",
            "Sales staff was very patient and helped us try multiple sizes with a smile.",
            "Collection nalla irukku, but sizes for children were quickly out of stock.",
            "Billing counter pe Sunday ko thoda line tha, overall pleasant shopping experience.",
            "Exchange was handled smoothly without any argument. Trustworthy shop."
        ]
    },
    "supermarket": {
        "id": "supermarket",
        "name": "Supermarket / Grocery / Kirana",
        "industry": "Grocery & Daily Needs",
        "description": "Supermarkets, kirana shops, provision stores, and organic marts",
        "default_topics": ["Stock & Freshness", "Pricing & Offers", "Billing Speed", "Store Cleanliness", "Staff Helpfulness", "Parking & Accessibility", "Home Delivery"],
        "default_keywords": ["fresh", "vegetables", "billing", "offers", "rates", "staff", "parking", "counter", "items", "kirana", "delivery"],
        "sample_reviews": [
            "Fresh organic vegetables every morning and all household daily essentials in one place.",
            "Kirana items are well organized and prices are lower than online delivery apps.",
            "Fast billing with multiple open counters during peak hours. Helpful floor staff.",
            "Parking area is small, but they provide fast doorstep delivery on WhatsApp orders.",
            "Store is very clean and pulses/grains are packed dust-free."
        ]
    },
    "salon": {
        "id": "salon",
        "name": "Salon & Spa / Grooming",
        "industry": "Personal Care & Beauty",
        "description": "Hair salons, beauty parlours, barbershops, and wellness spas",
        "default_topics": ["Service Quality", "Staff Behavior & Politeness", "Hygiene & Sanitization", "Waiting Time", "Pricing & Packages", "Appointment Scheduling"],
        "default_keywords": ["haircut", "styling", "hygiene", "staff", "wait", "appointment", "facial", "clean", "treatment", "beard", "spa"],
        "sample_reviews": [
            "Stylist took time to understand the haircut I wanted. Came out looking sharp!",
            "Facial and detan service romba relaxing. Clean sterilized towels and tools.",
            "Booked appointment in advance and was attended on time without waiting.",
            "Staff behavior is courteous and polite, gentle head massage was wonderful.",
            "Pricing is transparent with no forced product upselling."
        ]
    },
    "clinic": {
        "id": "clinic",
        "name": "Clinic / Healthcare Centre",
        "industry": "Healthcare & Wellness",
        "description": "Dental clinics, diagnostic labs, pharmacies, and consulting doctors",
        "default_topics": ["Doctor Consultation", "Waiting Time", "Staff Behavior", "Cleanliness & Hygiene", "Medicine Availability", "Treatment Cost & Transparency"],
        "default_keywords": ["doctor", "appointment", "wait", "treatment", "staff", "fee", "clean", "care", "diagnosis", "dentist", "prescription"],
        "sample_reviews": [
            "Doctor patiently listened to symptoms and explained the treatment clearly without unnecessary tests.",
            "Very clean and sanitized clinic. Reception staff was courteous and polite.",
            "Dental cleaning was gentle and painless. Reasonable consultation charges.",
            "Prior appointment booked, waiting time was less than 15 minutes.",
            "In-house pharmacy had all medicines ready on the spot."
        ]
    },
    "electronics": {
        "id": "electronics",
        "name": "Electronics & Mobile Shop",
        "industry": "Electronics & Appliances",
        "description": "Mobile sales, accessories, laptop repairs, and consumer appliances",
        "default_topics": ["Product Genuine Quality", "Pricing & Offers", "Repair Turnaround Time", "Staff Technical Knowledge", "Warranty Support", "After-Sales Service"],
        "default_keywords": ["mobile", "screen", "repair", "warranty", "charger", "laptop", "battery", "exchange", "accessories", "phone", "price"],
        "sample_reviews": [
            "Got display replaced in just 45 minutes with genuine parts and 3-month warranty.",
            "Best price for 5G mobile with tempered glass and back case included free.",
            "Staff technically sound and helped transfer all WhatsApp data from old phone to new.",
            "Quick service and honest diagnosis without charging extra inspection fees.",
            "Original branded accessories available at competitive rates."
        ]
    },
    "other": {
        "id": "other",
        "name": "Local Business / Service",
        "industry": "Local Services",
        "description": "Local repair, tailoring, fitness gyms, car wash, and community services",
        "default_topics": ["Service Quality", "Staff Politeness", "Punctuality & Turnaround", "Pricing & Transparency", "Cleanliness", "Customer Support"],
        "default_keywords": ["service", "quality", "cost", "timely", "staff", "helpful", "clean", "support", "work", "repair"],
        "sample_reviews": [
            "Punctual and reliable service. Transparent pricing with clear receipt provided.",
            "Work was completed ahead of promised schedule. Staff was humble and polite.",
            "Very happy with customer support and attention to detail. Will definitely recommend.",
            "Fair rates and honest recommendations without pushing unwanted services."
        ]
    }
}
from app.services.scraper_simulator import scraper_simulator

router = APIRouter()

async def get_brand_for_user(
    brand_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    business_id: Optional[str] = None
) -> dict:
    """
    Loads a business (brand) by ID and ensures it belongs to the current user (owner_id).
    Admins are permitted to access any business.
    Returns 404 if the business does not exist or does not belong to the user.
    """
    target_id = brand_id or business_id
    if not target_id:
        raise HTTPException(status_code=400, detail="Business or Brand ID required")

    db = get_db()
    brand = await db["brands"].find_one({"id": target_id})
    if not brand:
        raise HTTPException(status_code=404, detail="Business not found")

    if current_user.get("role") != "admin" and brand.get("owner_id") != current_user.get("id"):
        raise HTTPException(status_code=404, detail="Business not found")

    return brand

# Alias get_business_for_user as requested
get_business_for_user = get_brand_for_user

async def get_user_brand_ids(current_user: dict) -> List[str]:
    """
    Returns the list of brand IDs owned by the user (or all brands if admin).
    """
    db = get_db()
    if current_user.get("role") == "admin":
        brands = await db["brands"].find({}, {"id": 1}).to_list(1000)
    else:
        brands = await db["brands"].find({"owner_id": current_user["id"]}, {"id": 1}).to_list(1000)
    return [b["id"] for b in brands]

@router.get("", response_model=List[BrandResponse])
async def list_brands(current_user: dict = Depends(get_current_user)):
    """
    Returns only the brands owned by the current user (admins see all).
    Avoids N+1 queries by using a single aggregation pipeline for counts and average sentiment.
    """
    db = get_db()
    query = {} if current_user.get("role") == "admin" else {"owner_id": current_user["id"]}
    brands = await db["brands"].find(query).to_list(100)
    if not brands:
        return []
    
    brand_ids = [b["id"] for b in brands]

    pipeline = [
        {"$match": {"brand_id": {"$in": brand_ids}}},
        {
            "$group": {
                "_id": "$brand_id",
                "count": {"$sum": 1},
                "avg_sentiment": {"$avg": "$sentiment_score"}
            }
        }
    ]
    metrics_list = await db["mentions"].aggregate(pipeline).to_list(len(brand_ids))
    metrics_map = {
        m["_id"]: {
            "count": m.get("count", 0),
            "avg_sentiment": round(m.get("avg_sentiment", 0.0) or 0.0, 2)
        }
        for m in metrics_list
    }

    result = []
    for b in brands:
        b_dict = clean_doc(b)
        stats = metrics_map.get(b["id"], {"count": 0, "avg_sentiment": 0.0})
        b_dict["mentions_count"] = stats["count"]
        b_dict["sentiment_score"] = stats["avg_sentiment"]
        result.append(BrandResponse(**b_dict))
    
    return result

@router.get("/presets", response_model=Dict[str, Any])
async def get_business_presets():
    """
    Returns preset business categories and topic taxonomies for small businesses and local shops.
    """
    return BUSINESS_PRESETS

@router.post("", response_model=BrandResponse)
async def create_brand(brand_in: BrandCreate, current_user: dict = Depends(get_current_user)):
    from app.services.plan_limits import check_can_create_business
    db = get_db()
    await check_can_create_business(current_user, db)
    brand_id = f"brand_{uuid.uuid4().hex[:8]}"
    
    b_type = brand_in.business_type or "retail"
    preset = BUSINESS_PRESETS.get(b_type, {})
    
    # Sensible default topics from preset if not explicitly supplied
    topics = brand_in.topics or preset.get("default_topics", ["Service", "Price", "Quality", "Cleanliness", "Waiting Time", "Staff Behavior"])
    
    # Default primary branch location if not provided
    locations = [loc.model_dump() for loc in brand_in.locations] if brand_in.locations else [
        {
            "id": f"loc_{uuid.uuid4().hex[:6]}",
            "name": "Main Branch",
            "address": "",
            "city": "",
            "phone": "",
            "google_place_id": "",
            "is_primary": True
        }
    ]
    
    brand_doc = {
        "id": brand_id,
        "owner_id": current_user["id"],
        "name": brand_in.name,
        "business_type": b_type,
        "industry": brand_in.industry or preset.get("industry", "Local Business"),
        "description": brand_in.description or f"{preset.get('name', 'Local Business')} serving customers.",
        "locations": locations,
        "topics": topics,
        "products": brand_in.products or [],
        "keywords": brand_in.keywords or [brand_in.name],
        "address": brand_in.address or "",
        "city": brand_in.city or "",
        "phone": brand_in.phone or "",
        "languages": brand_in.languages or ["en"],
        "google_maps_url": brand_in.google_maps_url or "",
        "google_place_id": brand_in.google_place_id or brand_in.place_id or "",
        "place_id": brand_in.place_id or brand_in.google_place_id or "",
        "instagram_handle": brand_in.instagram_handle or "",
        "social_handles": brand_in.social_handles or {},
        "competitors": brand_in.competitors or [], # Neutral empty defaults
        "crisis_threshold_negative": brand_in.crisis_threshold_negative or 0.35,
        "is_primary": brand_in.is_primary,
        "created_at": datetime.datetime.now(datetime.timezone.utc)
    }
    
    await db["brands"].insert_one(brand_doc)
    
    # Pre-seed 7-day historical data ONLY when DEMO_MODE is true
    m_count = 0
    avg_sent = 0.0
    if settings.DEMO_MODE:
        historical = scraper_simulator.generate_historical_dataset(
            brand_name=brand_in.name,
            brand_id=brand_id,
            days=7,
            mentions_per_day=20,
            competitors=brand_doc["competitors"]
        )
        if historical:
            await db["mentions"].insert_many(historical)
            m_count = len(historical)
            avg_sent = sum(m.get("sentiment_score", 0.0) for m in historical) / max(m_count, 1)

    brand_doc["mentions_count"] = m_count
    brand_doc["sentiment_score"] = round(avg_sent, 2)
    return BrandResponse(**clean_doc(brand_doc))

@router.post("/{brand_id}/locations", response_model=BrandResponse)
async def add_location_to_brand(
    location_in: LocationCreate,
    brand: dict = Depends(get_brand_for_user),
    current_user: dict = Depends(get_current_user)
):
    """
    Add a new branch / location under a business.
    """
    db = get_db()
    brand_id = brand["id"]
    loc_id = f"loc_{uuid.uuid4().hex[:6]}"
    loc_dict = {
        "id": loc_id,
        "name": location_in.name,
        "address": location_in.address or "",
        "city": location_in.city or "",
        "phone": location_in.phone or "",
        "google_place_id": location_in.google_place_id or "",
        "is_primary": location_in.is_primary
    }
    
    existing_locations = brand.get("locations", [])
    if loc_dict["is_primary"]:
        for loc in existing_locations:
            loc["is_primary"] = False
            
    existing_locations.append(loc_dict)
    await db["brands"].update_one({"id": brand_id}, {"$set": {"locations": existing_locations}})
    brand["locations"] = existing_locations
    return BrandResponse(**clean_doc(brand))

@router.put("/{brand_id}/locations/{location_id}", response_model=BrandResponse)
async def update_brand_location(
    location_id: str,
    location_in: LocationUpdate,
    brand: dict = Depends(get_brand_for_user),
    current_user: dict = Depends(get_current_user)
):
    """
    Update details for a specific branch / location.
    """
    db = get_db()
    brand_id = brand["id"]
    existing_locations = brand.get("locations", [])
    
    found = False
    for loc in existing_locations:
        if loc.get("id") == location_id:
            found = True
            update_data = {k: v for k, v in location_in.model_dump().items() if v is not None}
            if update_data.get("is_primary"):
                for other in existing_locations:
                    other["is_primary"] = False
            loc.update(update_data)
            break
            
    if not found:
        raise HTTPException(status_code=404, detail="Location not found")
        
    await db["brands"].update_one({"id": brand_id}, {"$set": {"locations": existing_locations}})
    brand["locations"] = existing_locations
    return BrandResponse(**clean_doc(brand))

@router.delete("/{brand_id}/locations/{location_id}", response_model=BrandResponse)
async def delete_brand_location(
    location_id: str,
    brand: dict = Depends(get_brand_for_user),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a specific branch / location from a business.
    """
    db = get_db()
    brand_id = brand["id"]
    existing_locations = [loc for loc in brand.get("locations", []) if loc.get("id") != location_id]
    
    if existing_locations and not any(loc.get("is_primary") for loc in existing_locations):
        existing_locations[0]["is_primary"] = True
        
    await db["brands"].update_one({"id": brand_id}, {"$set": {"locations": existing_locations}})
    brand["locations"] = existing_locations
    return BrandResponse(**clean_doc(brand))

@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand(
    brand: dict = Depends(get_brand_for_user),
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    brand_id = brand["id"]
    
    pipeline = [
        {"$match": {"brand_id": brand_id}},
        {
            "$group": {
                "_id": "$brand_id",
                "count": {"$sum": 1},
                "avg_sentiment": {"$avg": "$sentiment_score"}
            }
        }
    ]
    stats = await db["mentions"].aggregate(pipeline).to_list(1)
    m_count = stats[0].get("count", 0) if stats else 0
    avg_sent = stats[0].get("avg_sentiment", 0.0) if stats else 0.0
    
    b_dict = clean_doc(brand)
    b_dict["mentions_count"] = m_count
    b_dict["sentiment_score"] = round(avg_sent or 0.0, 2)
    return BrandResponse(**b_dict)

@router.put("/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_in: BrandUpdate,
    brand: dict = Depends(get_brand_for_user),
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    brand_id = brand["id"]
    update_data = {k: v for k, v in brand_in.model_dump().items() if v is not None}
    if update_data:
        await db["brands"].update_one({"id": brand_id}, {"$set": update_data})
        brand.update(update_data)

    pipeline = [
        {"$match": {"brand_id": brand_id}},
        {
            "$group": {
                "_id": "$brand_id",
                "count": {"$sum": 1},
                "avg_sentiment": {"$avg": "$sentiment_score"}
            }
        }
    ]
    stats = await db["mentions"].aggregate(pipeline).to_list(1)
    m_count = stats[0].get("count", 0) if stats else 0
    avg_sent = stats[0].get("avg_sentiment", 0.0) if stats else 0.0

    b_dict = clean_doc(brand)
    b_dict["mentions_count"] = m_count
    b_dict["sentiment_score"] = round(avg_sent or 0.0, 2)
    return BrandResponse(**b_dict)

@router.delete("/{brand_id}")
async def delete_brand(
    brand: dict = Depends(get_brand_for_user),
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    brand_id = brand["id"]
    await db["brands"].delete_one({"id": brand_id})
    await db["mentions"].delete_many({"brand_id": brand_id})
    await db["alerts"].delete_many({"brand_id": brand_id})
    await db["summaries"].delete_many({"brand_id": brand_id})
    await db["instagram_connections"].delete_many({"brand_id": brand_id})
    return {"message": "Brand and associated records deleted successfully"}

@router.post("/{brand_id}/seed")
async def seed_brand_history(
    days: int = 7,
    brand: dict = Depends(get_brand_for_user),
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    brand_id = brand["id"]
    historical = scraper_simulator.generate_historical_dataset(
        brand_name=brand["name"],
        brand_id=brand_id,
        days=days,
        mentions_per_day=25,
        competitors=brand.get("competitors", [])
    )
    if historical:
        await db["mentions"].insert_many(historical)

    count = len(historical) if historical else 0
    return {"message": f"Successfully generated {count} historical mentions", "count": count}
