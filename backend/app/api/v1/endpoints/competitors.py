import os
import io
import csv
import logging
import urllib.request
import urllib.parse
import json
from typing import Optional, List, Dict, Any, Union
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.database import get_db, clean_doc, clean_docs
from app.api.v1.endpoints.auth import get_current_user
from app.api.v1.endpoints.brands import get_brand_for_user, get_user_brand_ids

logger = logging.getLogger("brandpulse.competitors")

router = APIRouter()


class NearbyShopCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    place_id: Optional[str] = None
    maps_url: Optional[str] = None
    rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    review_count: Optional[int] = Field(None, ge=0)
    praise_topics: Optional[List[str]] = []
    complaint_topics: Optional[List[str]] = []


def _normalize_competitor(comp: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Helper to convert string competitor names or dicts into a uniform NearbyShop structure."""
    if isinstance(comp, str):
        return {
            "name": comp,
            "place_id": None,
            "maps_url": None,
            "rating": 4.1,
            "review_count": 120,
            "praise_topics": ["Quality", "Service"],
            "complaint_topics": ["Wait time"],
            "source": "manual"
        }
    return {
        "name": comp.get("name", "Nearby Shop"),
        "place_id": comp.get("place_id"),
        "maps_url": comp.get("maps_url"),
        "rating": comp.get("rating", 4.0),
        "review_count": comp.get("review_count", 100),
        "praise_topics": comp.get("praise_topics", []),
        "complaint_topics": comp.get("complaint_topics", []),
        "source": comp.get("source", "manual")
    }


def _fetch_google_place_details(place_id: str, api_key: str) -> Optional[Dict[str, Any]]:
    """Fetches public rating and review count from Google Places API if configured."""
    if not api_key or not place_id:
        return None
    try:
        url = (
            f"https://maps.googleapis.com/maps/api/place/details/json"
            f"?place_id={urllib.parse.quote(place_id)}"
            f"&fields=name,rating,user_ratings_total,reviews"
            f"&key={api_key}"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "BrandPulseAI/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("status") == "OK":
                res = data.get("result", {})
                return {
                    "rating": float(res.get("rating", 4.0)),
                    "review_count": int(res.get("user_ratings_total", 0))
                }
    except Exception as e:
        logger.warning(f"Could not fetch Google place details for {place_id}: {e}")
    return None


@router.get("/")
@router.get("/list")
async def list_nearby_shops(
    brand_id: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns list of 2 to 5 nearby shops configured by the owner for comparison.
    """
    brand = await get_brand_for_user(brand_id, current_user)
    raw_list = brand.get("competitors", [])
    normalized = [_normalize_competitor(c) for c in raw_list]
    return {
        "brand_id": brand_id,
        "count": len(normalized),
        "shops": normalized
    }


@router.post("/")
async def add_nearby_shop(
    brand_id: str = Query(...),
    shop: NearbyShopCreate = ...,
    current_user: dict = Depends(get_current_user)
):
    """
    Adds a real nearby business (2-5 shops total).
    Attempts to fetch Google rating and review count if place_id and API key are available,
    otherwise uses user-supplied rating / count or default estimates.
    """
    brand = await get_brand_for_user(brand_id, current_user)
    db = get_db()
    
    current_shops = [_normalize_competitor(c) for c in brand.get("competitors", [])]
    if len(current_shops) >= 5:
        raise HTTPException(
            status_code=400,
            detail="Maximum of 5 nearby shops allowed. Please remove an existing shop before adding a new one."
        )

    # Check for duplicate
    shop_name_clean = shop.name.strip()
    if any(s["name"].lower() == shop_name_clean.lower() for s in current_shops):
        raise HTTPException(
            status_code=400,
            detail=f"Shop '{shop_name_clean}' is already in your comparison list."
        )

    rating = shop.rating
    review_count = shop.review_count
    source = "manual"

    # Attempt Google Places fetch if place_id provided and key available
    if shop.place_id and settings.GOOGLE_PLACES_API_KEY:
        fetched = _fetch_google_place_details(shop.place_id, settings.GOOGLE_PLACES_API_KEY)
        if fetched:
            rating = fetched.get("rating", rating or 4.2)
            review_count = fetched.get("review_count", review_count or 150)
            source = "google_places"

    if rating is None:
        rating = 4.2
    if review_count is None:
        review_count = 120

    new_shop_obj = {
        "name": shop_name_clean,
        "place_id": shop.place_id,
        "maps_url": shop.maps_url,
        "rating": round(float(rating), 1),
        "review_count": int(review_count),
        "praise_topics": shop.praise_topics or ["Good quality", "Friendly staff"],
        "complaint_topics": shop.complaint_topics or ["Peak waiting time"],
        "source": source
    }

    current_shops.append(new_shop_obj)
    await db["brands"].update_one(
        {"id": brand_id},
        {"$set": {"competitors": current_shops}}
    )

    return {
        "status": "added",
        "shop": new_shop_obj,
        "total_shops": len(current_shops)
    }


@router.delete("/{shop_name}")
async def remove_nearby_shop(
    shop_name: str,
    brand_id: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Removes a nearby shop from the brand's comparison list.
    """
    brand = await get_brand_for_user(brand_id, current_user)
    db = get_db()

    current_shops = [_normalize_competitor(c) for c in brand.get("competitors", [])]
    filtered_shops = [s for s in current_shops if s["name"].lower() != shop_name.lower().strip()]

    if len(filtered_shops) == len(current_shops):
        raise HTTPException(status_code=404, detail=f"Shop '{shop_name}' not found in comparison list.")

    await db["brands"].update_one(
        {"id": brand_id},
        {"$set": {"competitors": filtered_shops}}
    )

    return {
        "status": "removed",
        "shop_name": shop_name,
        "remaining_shops": len(filtered_shops)
    }


@router.post("/import-csv")
async def import_nearby_shop_csv(
    brand_id: str = Query(...),
    shop_name: str = Query(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Imports customer reviews from a CSV file for a nearby shop.
    Automatically computes average star rating, review volume, and extracted praise/complaint themes.
    """
    brand = await get_brand_for_user(brand_id, current_user)
    db = get_db()
    content = await file.read()

    try:
        reader = csv.DictReader(io.StringIO(content.decode("utf-8", errors="ignore")))
        ratings = []
        praises = []
        complaints = []
        count = 0

        for row in reader:
            count += 1
            # Check for star or rating column
            for col in ["rating", "stars", "star", "score"]:
                if col in row and row[col]:
                    try:
                        ratings.append(float(row[col]))
                        break
                    except ValueError:
                        pass
            # Collect praise / complaints
            text = row.get("content") or row.get("review") or row.get("text") or ""
            if len(ratings) > 0 and ratings[-1] >= 4 and len(praises) < 3:
                praises.append(text[:40].strip())
            elif len(ratings) > 0 and ratings[-1] <= 2 and len(complaints) < 3:
                complaints.append(text[:40].strip())

        avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else 4.0

        current_shops = [_normalize_competitor(c) for c in brand.get("competitors", [])]
        # Update or add shop
        existing = next((s for s in current_shops if s["name"].lower() == shop_name.lower().strip()), None)
        if existing:
            existing["rating"] = avg_rating
            existing["review_count"] = count
            existing["source"] = "csv"
            if praises: existing["praise_topics"] = praises
            if complaints: existing["complaint_topics"] = complaints
        else:
            if len(current_shops) >= 5:
                raise HTTPException(status_code=400, detail="Maximum 5 nearby shops reached.")
            current_shops.append({
                "name": shop_name.strip(),
                "place_id": None,
                "maps_url": None,
                "rating": avg_rating,
                "review_count": count,
                "praise_topics": praises or ["Quality", "Taste"],
                "complaint_topics": complaints or ["Wait times"],
                "source": "csv"
            })

        await db["brands"].update_one(
            {"id": brand_id},
            {"$set": {"competitors": current_shops}}
        )

        return {
            "status": "imported",
            "shop_name": shop_name,
            "reviews_analyzed": count,
            "calculated_rating": avg_rating
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")


@router.get("/benchmarks")
async def get_competitor_benchmarks(
    brand_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Returns dynamic side-by-side benchmark metrics for primary shop and owner-added nearby shops.
    No hardcoded fake competitor names are used.
    """
    db = get_db()
    brand_name = "My Shop"
    competitors = []

    if brand_id:
        b = await get_brand_for_user(brand_id, current_user)
        brand_name = b["name"]
        competitors = [_normalize_competitor(c) for c in b.get("competitors", [])]
        target_brand_id = brand_id
    else:
        user_brand_ids = await get_user_brand_ids(current_user)
        if user_brand_ids:
            target_brand_id = user_brand_ids[0]
            b = await db["brands"].find_one({"id": target_brand_id})
            if b:
                brand_name = b["name"]
                competitors = [_normalize_competitor(c) for c in b.get("competitors", [])]
        else:
            target_brand_id = None

    # Primary shop metrics from real mentions in DB
    if target_brand_id:
        primary_mentions = await db["mentions"].find({"brand_id": target_brand_id}).to_list(1000)
    else:
        primary_mentions = []
        
    p_total = max(len(primary_mentions), 1)
    p_pos = sum(1 for m in primary_mentions if m.get("sentiment") == "positive")
    p_neg = sum(1 for m in primary_mentions if m.get("sentiment") == "negative")
    p_neu = sum(1 for m in primary_mentions if m.get("sentiment") == "neutral")
    p_nss = round(((p_pos - p_neg) / p_total) * 100, 1)

    # Average stars of primary shop
    ratings_list = [m.get("rating", 5) for m in primary_mentions if m.get("rating")]
    p_avg_stars = round(sum(ratings_list) / len(ratings_list), 1) if ratings_list else 4.4

    # Primary shop benchmark profile
    benchmarks_data = [
        {
            "brand": brand_name,
            "is_primary": True,
            "volume": len(primary_mentions),
            "star_rating": p_avg_stars,
            "net_sentiment": p_nss,
            "positive_pct": round((p_pos / p_total) * 100, 1),
            "neutral_pct": round((p_neu / p_total) * 100, 1),
            "negative_pct": round((p_neg / p_total) * 100, 1),
            "dominant_emotion": "Joy",
            "praise_ratio": round(p_pos / max(p_neg + 1, 1), 2),
            "color": "#2563EB"
        }
    ]

    comp_colors = ["#06b6d4", "#f59e0b", "#10b981", "#ec4899", "#8b5cf6"]

    # Iterate through user-added nearby shops
    for idx, comp in enumerate(competitors):
        color = comp_colors[idx % len(comp_colors)]
        c_rating = float(comp.get("rating", 4.1))
        c_vol = int(comp.get("review_count", 100))
        
        # Estimate sentiment proportions based on star rating (e.g. 4.5 stars -> ~85% positive)
        pos_fraction = min(max((c_rating - 1.0) / 4.0, 0.1), 0.95)
        neg_fraction = max(0.05, (1.0 - pos_fraction) * 0.6)
        neu_fraction = max(0.0, 1.0 - pos_fraction - neg_fraction)
        
        c_pos = int(c_vol * pos_fraction)
        c_neg = int(c_vol * neg_fraction)
        c_neu = max(c_vol - c_pos - c_neg, 0)
        c_nss = round((pos_fraction - neg_fraction) * 100, 1)

        benchmarks_data.append({
            "brand": comp["name"],
            "is_primary": False,
            "volume": c_vol,
            "star_rating": c_rating,
            "net_sentiment": c_nss,
            "positive_pct": round((c_pos / max(c_vol, 1)) * 100, 1),
            "neutral_pct": round((c_neu / max(c_vol, 1)) * 100, 1),
            "negative_pct": round((c_neg / max(c_vol, 1)) * 100, 1),
            "dominant_emotion": "Joy" if c_rating >= 4.0 else "Neutral",
            "praise_ratio": round(c_pos / max(c_neg + 1, 1), 2),
            "praise_topics": comp.get("praise_topics", []),
            "complaint_topics": comp.get("complaint_topics", []),
            "color": color
        })

    return benchmarks_data


@router.get("/sov")
async def get_share_of_voice(
    brand_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Returns review share comparison across user's shop and added nearby businesses.
    """
    benchmarks = await get_competitor_benchmarks(brand_id=brand_id, current_user=current_user)
    total_reviews = sum(b["volume"] for b in benchmarks) or 1
    
    sov_list = []
    for b in benchmarks:
        sov_pct = round((b["volume"] / total_reviews) * 100, 1)
        sov_list.append({
            "brand": b["brand"],
            "is_primary": b["is_primary"],
            "sov_percentage": sov_pct,
            "volume": b["volume"],
            "color": b["color"]
        })

    return {
        "total_market_volume": total_reviews,
        "share_of_voice": sov_list
    }


@router.get("/head-to-head")
async def get_head_to_head(
    brand_id: Optional[str] = None,
    competitor: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Returns side-by-side comparison between the user's shop and a selected nearby business.
    """
    db = get_db()
    primary_name = "My Shop"
    comp_obj = None

    if brand_id:
        b = await get_brand_for_user(brand_id, current_user)
        primary_name = b["name"]
        comps = [_normalize_competitor(c) for c in b.get("competitors", [])]
        if competitor:
            comp_obj = next((c for c in comps if c["name"].lower() == competitor.lower().strip()), None)
        if not comp_obj and comps:
            comp_obj = comps[0]

    comp_name = comp_obj["name"] if comp_obj else (competitor or "Nearby Shop")
    comp_rating = comp_obj.get("rating", 4.1) if comp_obj else 4.1
    comp_praises = comp_obj.get("praise_topics", ["Fast service", "Affordable pricing"]) if comp_obj else ["Fast service", "Affordable pricing"]
    comp_complaints = comp_obj.get("complaint_topics", ["Peak waiting time", "Parking"]) if comp_obj else ["Peak waiting time", "Parking"]

    primary_rating = 4.4
    primary_pos_pct = 88.0
    primary_service_pct = 85.0
    primary_value_pct = 80.0
    primary_clean_pct = 86.0

    if brand_id:
        p_mentions = await db["mentions"].find({"brand_id": brand_id}).to_list(100)
        if p_mentions:
            ratings = [m["rating"] for m in p_mentions if m.get("rating")]
            if ratings:
                primary_rating = round(sum(ratings) / len(ratings), 1)
            pos_count = sum(1 for m in p_mentions if m.get("sentiment") == "positive")
            primary_pos_pct = round((pos_count / len(p_mentions)) * 100, 1)

    comp_pos_pct = round(min(98.0, max(50.0, (comp_rating / 5.0) * 100)), 1)
    comp_service_pct = round(min(98.0, max(45.0, comp_pos_pct - 5.0)), 1)
    comp_value_pct = round(min(98.0, max(50.0, comp_pos_pct + 2.0)), 1)
    comp_clean_pct = round(min(98.0, max(45.0, comp_pos_pct - 3.0)), 1)

    return {
        "primary_brand": primary_name,
        "competitor": comp_name,
        "categories": [
            {"dimension": "Customer Happiness", "primary_val": f"{primary_rating} ★", "comp_val": f"{comp_rating} ★", "winner": "primary" if primary_rating >= comp_rating else "competitor"},
            {"dimension": "Product / Food Taste", "primary_val": f"{int(primary_pos_pct)}% Positive", "comp_val": f"{int(comp_pos_pct)}% Positive", "winner": "primary" if primary_pos_pct >= comp_pos_pct else "competitor"},
            {"dimension": "Service & Staff Courtesy", "primary_val": f"{int(primary_service_pct)}% Positive", "comp_val": f"{int(comp_service_pct)}% Positive", "winner": "primary" if primary_service_pct >= comp_service_pct else "competitor"},
            {"dimension": "Value for Money", "primary_val": f"{int(primary_value_pct)}% Positive", "comp_val": f"{int(comp_value_pct)}% Positive", "winner": "primary" if primary_value_pct >= comp_value_pct else "competitor"},
            {"dimension": "Cleanliness & Hygiene", "primary_val": f"{int(primary_clean_pct)}% Positive", "comp_val": f"{int(comp_clean_pct)}% Positive", "winner": "primary" if primary_clean_pct >= comp_clean_pct else "competitor"}
        ],
        "swot_analysis": {
            "strengths": [
                f"Consistently high customer praise for freshness and taste at {primary_name}",
                "Friendly and responsive floor staff",
                "Strong repeat neighborhood customer loyalty"
            ],
            "vulnerabilities": [
                "Evening and weekend seating queue management",
                "Customer requests for faster order delivery"
            ],
            "competitor_threats": [
                f"{comp_name} offering: {', '.join(comp_praises[:2])}",
                f"{comp_name} customer pain points: {', '.join(comp_complaints[:2])}"
            ]
        }
    }
