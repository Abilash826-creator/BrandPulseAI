import pytest
import datetime
from fastapi.testclient import TestClient
from fastapi import HTTPException
from main import app
from app.core.database import get_db
from app.core.config import settings
from app.services.notifications import (
    MockNotificationProvider,
    NotificationDispatcher,
    notification_dispatcher
)
from app.services.plan_limits import (
    check_can_create_business,
    check_can_add_reviews,
    check_can_send_ai_chat,
    record_ai_chat_usage,
    get_plan_usage_summary
)
from app.core.cache import (
    get_cached_translation,
    set_cached_translation,
    get_cached_llm_response,
    set_cached_llm_response
)
from app.core.storage import get_storage, LocalStorage


@pytest.mark.asyncio
async def test_mock_notification_provider():
    mock_prov = MockNotificationProvider()
    
    # Test email dispatch
    ok_email = mock_prov.send_email("owner@bakery.com", "Test Subject", "Hello body")
    assert ok_email is True
    assert len(mock_prov.sent_notifications) == 1
    assert mock_prov.sent_notifications[0]["channel"] == "email"
    assert mock_prov.sent_notifications[0]["to"] == "owner@bakery.com"

    # Test SMS dispatch
    ok_sms = mock_prov.send_sms("+919876543210", "1-star review alert")
    assert ok_sms is True
    assert len(mock_prov.sent_notifications) == 2
    assert mock_prov.sent_notifications[1]["channel"] == "sms"

    # Test WhatsApp dispatch
    ok_wa = mock_prov.send_whatsapp("+919876543210", "WhatsApp weekly summary")
    assert ok_wa is True
    assert len(mock_prov.sent_notifications) == 3
    assert mock_prov.sent_notifications[2]["channel"] == "whatsapp"


@pytest.mark.asyncio
async def test_notification_dispatcher_opt_in_and_alerts():
    mock_prov = MockNotificationProvider()
    dispatcher = NotificationDispatcher(provider=mock_prov)

    brand = {
        "id": "brand_test_123",
        "name": "Sri Murugan Bakery",
        "notification_email": "murugan@bakery.com",
        "notification_phone": "+919876543210",
        "notify_bad_reviews": True,
        "email_opt_in": True,
        "whatsapp_opt_in": True,
        "notify_weekly_summary": True
    }

    # Dispatch bad review alert
    mention = {
        "rating": 1,
        "author": "Karthik",
        "source": "Google Reviews",
        "content": "Puff was cold and salt was too high."
    }
    res = dispatcher.dispatch_bad_review_alert(brand, mention)
    assert res["dispatched"] is True
    assert "email" in res["results"]
    assert "whatsapp" in res["results"]
    assert len(mock_prov.sent_notifications) == 2

    # Respect opt-out: if notify_bad_reviews is False, no alert should be sent
    brand_opted_out = dict(brand, notify_bad_reviews=False)
    res_opt_out = dispatcher.dispatch_bad_review_alert(brand_opted_out, mention)
    assert res_opt_out["dispatched"] is False
    assert res_opt_out["reason"] == "notify_bad_reviews_disabled"

    # Test weekly digest dispatch
    res_digest = dispatcher.dispatch_weekly_digest(brand, "Great week! 45 reviews received.", {"total_reviews": 45})
    assert res_digest["dispatched"] is True


@pytest.mark.asyncio
async def test_plan_limits_business_creation(test_db):
    user_free = {
        "id": "user_free_1",
        "role": "owner",
        "plan": "free"
    }

    # 0 businesses created: should succeed
    await check_can_create_business(user_free, test_db)

    # Insert 1 business for user
    await test_db["brands"].insert_one({
        "id": "brand_1",
        "owner_id": "user_free_1",
        "name": "First Shop"
    })

    # Attempting to create a second business on Free plan must raise 402 with friendly upgrade message
    with pytest.raises(HTTPException) as exc_info:
        await check_can_create_business(user_free, test_db)
    assert exc_info.value.status_code == 402
    assert "upgrade to pro" in exc_info.value.detail.lower()

    # User on Pro plan can create multiple businesses
    user_pro = {
        "id": "user_pro_1",
        "role": "owner",
        "plan": "pro"
    }
    await check_can_create_business(user_pro, test_db)


@pytest.mark.asyncio
async def test_plan_limits_reviews_and_ai_chat(test_db):
    brand_id = "brand_quota_test"
    user_free = {"id": "user_quota_1", "plan": "free", "role": "owner"}

    # Should allow adding 50 reviews (within 100 limit)
    await check_can_add_reviews(brand_id, 50, test_db, user_free)

    # Simulate 100 reviews ingested this month
    now_iso = datetime.datetime.utcnow().isoformat()
    mentions_to_insert = [
        {"brand_id": brand_id, "timestamp": now_iso, "content": f"Review {i}"}
        for i in range(100)
    ]
    await test_db["mentions"].insert_many(mentions_to_insert)

    # Adding even 1 more review should trigger 402 upgrade required
    with pytest.raises(HTTPException) as exc_info:
        await check_can_add_reviews(brand_id, 1, test_db, user_free)
    assert exc_info.value.status_code == 402
    assert "limit of 100 reviews reached" in exc_info.value.detail.lower()

    # Test Ask AI chat limits: up to 20 allowed
    await check_can_send_ai_chat(user_free, brand_id, test_db)

    # Record 20 chats
    for _ in range(20):
        await record_ai_chat_usage(user_free, brand_id, test_db)

    # 21st message must raise 402
    with pytest.raises(HTTPException) as exc_info:
        await check_can_send_ai_chat(user_free, brand_id, test_db)
    assert exc_info.value.status_code == 402
    assert "20 ask ai" in exc_info.value.detail.lower()

    # Usage summary should reflect usage
    summary = await get_plan_usage_summary(brand_id, user_free, test_db)
    assert summary["plan"] == "free"
    assert summary["limits"]["ai_chat_per_month"]["used"] == 20


@pytest.mark.asyncio
async def test_cost_control_caching():
    # Translation Cache test
    sample_text = "Romba nalla irukku dosa"
    set_cached_translation(sample_text, "en", "The dosa is very good")
    cached_val = get_cached_translation(sample_text, "en")
    assert cached_val == "The dosa is very good"
    assert get_cached_translation("Non-existent text", "en") is None

    # LLM Cache test
    prompt = "Summarize top 3 issues for Sri Murugan Bakery"
    set_cached_llm_response(prompt, "1. Weekend wait time. 2. Parking. 3. Cake frosting delay.")
    cached_llm = get_cached_llm_response(prompt)
    assert "Weekend wait time" in cached_llm


@pytest.mark.asyncio
async def test_nearby_shop_management_endpoints(client, user_factory, test_db):
    user, token = await user_factory(email="owner@nearby.com", user_id="owner_test_id")
    await test_db["brands"].insert_one({
        "id": "brand_nearby_1",
        "name": "Sri Murugan Bakery",
        "owner_id": "owner_test_id",
        "competitors": []
    })

    headers = {"Authorization": f"Bearer {token}"}

    # 1. Add first nearby shop
    res = await client.post(
        "/api/v1/competitors/?brand_id=brand_nearby_1",
        json={
            "name": "Sangeetha Vegetarian",
            "rating": 4.4,
            "review_count": 820,
            "praise_topics": ["Ghee roast", "Filter coffee"],
            "complaint_topics": ["Crowded seating"]
        },
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "added"
    assert data["total_shops"] == 1

    # 2. Add second nearby shop
    res2 = await client.post(
        "/api/v1/competitors/?brand_id=brand_nearby_1",
        json={
            "name": "Annapoorna Mess",
            "rating": 4.2,
            "review_count": 450
        },
        headers=headers
    )
    assert res2.status_code == 200
    assert res2.json()["total_shops"] == 2

    # 3. List nearby shops
    list_res = await client.get("/api/v1/competitors/list?brand_id=brand_nearby_1", headers=headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["count"] == 2
    shop_names = [s["name"] for s in list_data["shops"]]
    assert "Sangeetha Vegetarian" in shop_names
    assert "Annapoorna Mess" in shop_names

    # 4. Benchmarks should compare real primary shop with added shops (no hardcoded fake names)
    bench_res = await client.get("/api/v1/competitors/benchmarks?brand_id=brand_nearby_1", headers=headers)
    assert bench_res.status_code == 200
    benchmarks = bench_res.json()
    assert len(benchmarks) == 3 # Primary + 2 nearby shops
    bench_names = [b["brand"] for b in benchmarks]
    assert "Sri Murugan Bakery" in bench_names
    assert "Sangeetha Vegetarian" in bench_names
    assert "Annapoorna Mess" in bench_names

    # 5. Delete a shop
    del_res = await client.delete("/api/v1/competitors/Sangeetha%20Vegetarian?brand_id=brand_nearby_1", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["remaining_shops"] == 1


@pytest.mark.asyncio
async def test_storage_interface():
    storage = get_storage()
    test_filename = f"test_artifact_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
    test_content = b"BrandPulse Storage Interface Test Content"

    # Save
    saved_name = storage.save(test_filename, test_content, content_type="text/plain")
    assert saved_name == test_filename
    assert storage.exists(test_filename) is True

    # Retrieve bytes
    retrieved = storage.get_bytes(test_filename)
    assert retrieved == test_content

    # Clean up
    storage.delete(test_filename)
    assert storage.exists(test_filename) is False
