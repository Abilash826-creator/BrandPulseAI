import uuid
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.database import get_db, clean_doc
from app.api.v1.endpoints.auth import get_current_user
from app.api.v1.endpoints.brands import get_brand_for_user, get_user_brand_ids
from app.schemas.all_schemas import AlertResponse
from app.services.crisis_detector import crisis_detector
from app.services.scraper_simulator import scraper_simulator

router = APIRouter()

@router.get("/alerts", response_model=List[AlertResponse])
async def list_crisis_alerts(
    brand_id: Optional[str] = None,
    status: Optional[str] = "all", # active, acknowledged, resolved, all
    is_simulated: Optional[bool] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    query = {}
    
    if brand_id:
        await get_brand_for_user(brand_id, current_user)
        query["brand_id"] = brand_id
    else:
        user_brand_ids = await get_user_brand_ids(current_user)
        query["brand_id"] = {"$in": user_brand_ids}

    if status and status != "all":
        query["status"] = status

    if is_simulated is not None:
        query["is_simulated"] = is_simulated

    cursor = db["alerts"].find(query).sort("created_at", -1)
    alerts = await cursor.to_list(100)
    return [AlertResponse(**clean_doc(a)) for a in alerts]

@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(alert_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    alert = await db["alerts"].find_one({"id": alert_id})
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Verify that the alert's brand belongs to the user
    await get_brand_for_user(alert.get("brand_id", ""), current_user)

    update_payload = {
        "status": "acknowledged",
        "acknowledged_by": current_user.get("full_name", "Brand Manager")
    }
    await db["alerts"].update_one({"id": alert_id}, {"$set": update_payload})
    alert.update(update_payload)
    return AlertResponse(**clean_doc(alert))

@router.post("/alerts/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(alert_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    alert = await db["alerts"].find_one({"id": alert_id})
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Verify that the alert's brand belongs to the user
    await get_brand_for_user(alert.get("brand_id", ""), current_user)

    update_payload = {
        "status": "resolved",
        "resolved_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    await db["alerts"].update_one({"id": alert_id}, {"$set": update_payload})
    alert.update(update_payload)
    return AlertResponse(**clean_doc(alert))

@router.get("/status")
async def get_crisis_detector_status(
    brand_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    if brand_id:
        await get_brand_for_user(brand_id, current_user)
        query = {"brand_id": brand_id}
    else:
        user_brand_ids = await get_user_brand_ids(current_user)
        query = {"brand_id": {"$in": user_brand_ids}}
    
    recent_mentions = await db["mentions"].find(query).sort("timestamp", -1).limit(30).to_list(30)
    risk_score, severity, _ = crisis_detector.calculate_crisis_risk(recent_mentions)
    
    active_alerts = await db["alerts"].find({**query, "status": "active"}).to_list(50)
    
    counts = {"critical": 0, "medium": 0, "low": 0}
    for a in active_alerts:
        sev = a.get("severity", "low")
        if sev in counts:
            counts[sev] += 1

    return {
        "current_risk_score": risk_score,
        "current_severity": severity,
        "active_alerts_count": len(active_alerts),
        "severity_breakdown": counts,
        "analyzed_window_size": len(recent_mentions),
        "detector_state": "ACTIVE_MONITORING"
    }

@router.post("/simulate-crisis")
async def trigger_simulated_crisis(
    brand_id: str,
    scenario_type: str = "outage_disaster",
    current_user: dict = Depends(get_current_user)
):
    """
    Triggers an instant simulated PR crisis for testing triage and mitigation on a user-owned brand.
    """
    brand = await get_brand_for_user(brand_id, current_user)
    db = get_db()
    brand_name = brand["name"]

    crisis_templates = {
        "outage_disaster": [
            f"All production EU endpoints for {brand_name} are returning 504 Gateway Timeout! Our entire data pipeline is halted.",
            f"Can anyone confirm if {brand_name} is down? Status page still says green but nothing is connecting.",
            f"Losing thousands of dollars an hour while {brand_name} infrastructure is completely unreachable. Zero response from CS.",
            f"Critical severity issue on {brand_name} API gateway. 4th outage this month. Highly unacceptable reliability.",
            f"Migrating our cloud instances away from {brand_name} after this disaster. Absolute incompetence.",
            f"Customer data sync failing across all regions on {brand_name}. Management is furious."
        ],
        "data_leak_rumor": [
            f"Security researcher claiming unauthenticated access to {brand_name} telemetry databases on dark web forums.",
            f"Is there a data breach at {brand_name}? Hearing reports of API keys leaked in plain text.",
            f"Emergency notice: Audit all {brand_name} credentials immediately following suspected credential stuffing breach.",
            f"Cybersecurity alert: Vulnerability CVE-2026-X found in {brand_name} core SDK allowing remote code execution.",
            f"Why is {brand_name} silent about the database leak reports? We need official disclosure.",
            f"Law firm announcing class action investigation into {brand_name} data protection practices."
        ],
        "viral_influencer_backlash": [
            f"Tech influencer @marques_reviews just dropped a brutal review on {brand_name}: 'The worst enterprise experience of 2026.'",
            f"Watch this viral TikTok tearing down {brand_name}'s aggressive auto-renew billing tactics. Over 1.2M views.",
            f"The backlash against {brand_name}'s new TOS policy is completely justified. They are locking customer data behind paywalls.",
            f"Developer community on Hacker News is heavily downvoting {brand_name}'s latest corporate announcement.",
            f"Top LinkedIn engineering voices are boycotting {brand_name} over anti-consumer contract clauses.",
            f"Boycott {brand_name} is trending on X/Twitter after today's pricing hike announcement."
        ]
    }

    raw_posts = crisis_templates.get(scenario_type, crisis_templates["outage_disaster"])
    injected_mentions = []
    
    for idx, text in enumerate(raw_posts):
        doc = {
            "id": f"men_crisis_sim_{uuid.uuid4().hex[:8]}",
            "brand_id": brand_id,
            "brand_name": brand_name,
            "platform": "twitter" if idx % 2 == 0 else "reddit",
            "author": f"Critical_Voice_{idx+1}",
            "author_handle": f"@voice_{idx+1}",
            "author_followers": 45000 + (idx * 25000),
            "author_avatar": f"https://api.dicebear.com/7.x/bottts/svg?seed=crisis_{idx}",
            "content": text,
            "sentiment": "negative",
            "sentiment_score": -0.85 - (idx * 0.02),
            "emotions": {"anger": 0.75, "fear": 0.15, "sadness": 0.05, "surprise": 0.03, "joy": 0.02},
            "dominant_emotion": "anger",
            "intent": "complaint",
            "intent_confidence": 0.98,
            "reach": 85000 + (idx * 40000),
            "engagement_score": 3200 + (idx * 1500),
            "virality_score": 88.5 + (idx * 1.5),
            "topic_cluster": "Outage & Stability" if "outage" in scenario_type else "Security & Privacy",
            "is_crisis_flag": True,
            "is_simulated": True,
            "timestamp": datetime.datetime.now(datetime.timezone.utc),
            "url": "https://brandpulse.ai"
        }
        injected_mentions.append(doc)

    await db["mentions"].insert_many(injected_mentions)

    alert_id = f"alert_sim_{uuid.uuid4().hex[:8]}"
    alert_doc = {
        "id": alert_id,
        "brand_id": brand_id,
        "brand_name": brand_name,
        "title": f"[CRITICAL] {scenario_type.replace('_', ' ').title()} Surge Detected",
        "severity": "critical",
        "metric_type": "negative_sentiment_spike",
        "trigger_value": 89.2,
        "threshold_value": 35.0,
        "description": f"Automated trigger: 6 high-virality hostile mentions detected across Twitter and Reddit within 3 minutes.",
        "ai_root_cause": f"Severe discourse spike tied to {scenario_type.replace('_', ' ')}. Virality velocity exceeds 85/100 threshold.",
        "recommendations": [
            "Deploy executive crisis PR holding statement within 15 minutes.",
            "Activate dedicated Customer Success bridge on primary communication channels.",
            "Brief engineering on-call to isolate affected sub-services immediately."
        ],
        "status": "active",
        "is_simulated": True,
        "created_at": datetime.datetime.now(datetime.timezone.utc)
    }
    await db["alerts"].insert_one(alert_doc)

    return {
        "status": "triggered",
        "alert": AlertResponse(**clean_doc(alert_doc)),
        "injected_mentions_count": len(injected_mentions),
        "message": f"Simulated crisis '{scenario_type}' injected successfully for brand '{brand_name}'."
    }
