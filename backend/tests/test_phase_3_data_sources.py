import pytest
import pytest_asyncio
import httpx

@pytest.mark.asyncio
async def test_google_business_status_connect_and_sync(client: httpx.AsyncClient, user_factory):
    """
    Verify Google Business Profile endpoints:
    - GET /api/v1/google/status
    - POST /api/v1/google/connect
    - POST /api/v1/google/sync
    """
    user = await user_factory(email="googleowner@gmail.com", role="brand_manager")
    headers = {"Authorization": f"Bearer {user['access_token']}"}

    # 1. Create Brand
    create_res = await client.post(
        "/api/v1/brands",
        json={"name": "Madurai Famous Jigarthanda", "business_type": "restaurant"},
        headers=headers
    )
    assert create_res.status_code == 200
    brand_id = create_res.json()["id"]

    # 2. Check initial status
    status_res = await client.get(f"/api/v1/google/status?brand_id={brand_id}", headers=headers)
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert "is_connected" in status_data

    # 3. Connect Google Place ID
    connect_res = await client.post(
        "/api/v1/google/connect",
        json={
            "brand_id": brand_id,
            "place_id": "ChIJ_sample_place_id",
            "maps_url": "https://maps.google.com/?cid=123456",
            "location_name": "Anna Nagar Branch"
        },
        headers=headers
    )
    assert connect_res.status_code == 200
    assert connect_res.json()["connected"] is True

    # 4. Sync Google Reviews (mock mode)
    sync_res = await client.post(f"/api/v1/google/sync?brand_id={brand_id}", headers=headers)
    assert sync_res.status_code == 200
    sync_data = sync_res.json()
    assert sync_data["success"] is True
    assert sync_data["synced_count"] > 0

    # 5. Verify synced mentions have rating and Google Reviews source
    mentions_res = await client.get(f"/api/v1/monitoring/mentions?brand_id={brand_id}&source=google", headers=headers)
    assert mentions_res.status_code == 200
    mentions = mentions_res.json()
    assert len(mentions) > 0
    first = mentions[0]
    assert first["rating"] is not None
    assert 1 <= first["rating"] <= 5
    assert "google" in (first.get("source") or first.get("platform") or "").lower()



@pytest.mark.asyncio
async def test_facebook_reviews_sync(client: httpx.AsyncClient, user_factory):
    """
    Verify Facebook review sync endpoint:
    - GET /api/v1/facebook/status
    - POST /api/v1/facebook/sync
    """
    user = await user_factory(email="fbowner@gmail.com", role="brand_manager")
    headers = {"Authorization": f"Bearer {user['access_token']}"}

    create_res = await client.post(
        "/api/v1/brands",
        json={"name": "Naturals Salon", "business_type": "salon"},
        headers=headers
    )
    assert create_res.status_code == 200
    brand_id = create_res.json()["id"]

    # Check status
    status_res = await client.get(f"/api/v1/facebook/status?brand_id={brand_id}", headers=headers)
    assert status_res.status_code == 200

    # Sync
    sync_res = await client.post(f"/api/v1/facebook/sync?brand_id={brand_id}", headers=headers)
    assert sync_res.status_code == 200
    sync_data = sync_res.json()
    assert sync_data["success"] is True
    assert sync_data["synced_count"] > 0


@pytest.mark.asyncio
async def test_mention_reply_endpoint(client: httpx.AsyncClient, user_factory):
    """
    Verify replying to a customer review:
    - POST /api/v1/monitoring/mentions/{mention_id}/reply
    """
    user = await user_factory(email="replyowner@gmail.com", role="brand_manager")
    headers = {"Authorization": f"Bearer {user['access_token']}"}

    create_brand_res = await client.post(
        "/api/v1/brands",
        json={"name": "A2B Sweets", "business_type": "restaurant"},
        headers=headers
    )
    brand_id = create_brand_res.json()["id"]

    # Create a mention
    create_mention_res = await client.post(
        "/api/v1/monitoring/mentions",
        json={
            "brand_id": brand_id,
            "content": "Ghee roast was crisp and coffee was super authentic!",
            "author": "Karthik R",
            "platform": "Google Reviews",
            "source": "Google Reviews",
            "rating": 5
        },
        headers=headers
    )
    assert create_mention_res.status_code == 200
    mention = create_mention_res.json()
    mention_id = mention["id"]

    # Post Reply
    reply_res = await client.post(
        f"/api/v1/monitoring/mentions/{mention_id}/reply",
        json={"reply_text": "Thank you Karthik! Glad you loved our ghee roast and coffee."},
        headers=headers
    )
    assert reply_res.status_code == 200
    reply_data = reply_res.json()
    assert reply_data["replied"] is True
    assert "Thank you Karthik" in reply_data["reply_text"]
    assert reply_data["reply_timestamp"] is not None


@pytest.mark.asyncio
async def test_paste_reviews_endpoint(client: httpx.AsyncClient, user_factory):
    """
    Verify pasting raw WhatsApp / OCR / screenshot review text:
    - POST /api/v1/dataset/paste-reviews
    """
    user = await user_factory(email="pasteowner@gmail.com", role="brand_manager")
    headers = {"Authorization": f"Bearer {user['access_token']}"}

    create_brand_res = await client.post(
        "/api/v1/brands",
        json={"name": "City Health Clinic", "business_type": "clinic"},
        headers=headers
    )
    brand_id = create_brand_res.json()["id"]

    sample_text = """
    The doctor was very patient and explained the prescription clearly. 5 stars.
    Long waiting time even with appointment. Reception staff was polite though.
    Clean clinic and fast blood test reports on WhatsApp. Highly satisfied.
    """

    res = await client.post(
        "/api/v1/dataset/paste-reviews",
        json={
            "brand_id": brand_id,
            "text": sample_text,
            "source": "WhatsApp Feedback",
            "default_rating": 4,
            "mode": "append"
        },
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["total_reviews_parsed"] >= 3
    assert data["brand_id"] == brand_id


@pytest.mark.asyncio
async def test_feed_filters_rating_and_replied(client: httpx.AsyncClient, user_factory):
    """
    Verify list_mentions filtering by rating and replied status:
    - GET /api/v1/monitoring/mentions?rating=5
    - GET /api/v1/monitoring/mentions?replied=true
    """
    user = await user_factory(email="filterowner@gmail.com", role="brand_manager")
    headers = {"Authorization": f"Bearer {user['access_token']}"}

    create_brand_res = await client.post(
        "/api/v1/brands",
        json={"name": "Nilgiris Supermarket", "business_type": "supermarket"},
        headers=headers
    )
    brand_id = create_brand_res.json()["id"]

    # Mention 1: 5 stars, replied
    m1 = await client.post(
        "/api/v1/monitoring/mentions",
        json={
            "brand_id": brand_id,
            "content": "Fresh vegetables and dairy products always in stock.",
            "author": "Anand S",
            "platform": "Google Reviews",
            "source": "Google Reviews",
            "rating": 5
        },
        headers=headers
    )
    m1_id = m1.json()["id"]
    await client.post(
        f"/api/v1/monitoring/mentions/{m1_id}/reply",
        json={"reply_text": "Thanks Anand!"},
        headers=headers
    )

    # Mention 2: 1 star, not replied
    await client.post(
        "/api/v1/monitoring/mentions",
        json={
            "brand_id": brand_id,
            "content": "Billing queue was too slow during evening rush.",
            "author": "Ravi K",
            "platform": "Google Reviews",
            "source": "Google Reviews",
            "rating": 1
        },
        headers=headers
    )

    # Filter by rating=5 (exclude demo simulated data)
    res_r5 = await client.get(f"/api/v1/monitoring/mentions?brand_id={brand_id}&rating=5&is_simulated=false", headers=headers)
    assert res_r5.status_code == 200
    r5_items = res_r5.json()
    assert len(r5_items) == 1
    assert r5_items[0]["rating"] == 5

    # Filter by replied=true
    res_replied = await client.get(f"/api/v1/monitoring/mentions?brand_id={brand_id}&replied=true&is_simulated=false", headers=headers)
    assert res_replied.status_code == 200
    replied_items = res_replied.json()
    assert len(replied_items) == 1
    assert replied_items[0]["replied"] is True

    # Filter by replied=false
    res_unreplied = await client.get(f"/api/v1/monitoring/mentions?brand_id={brand_id}&replied=false&is_simulated=false", headers=headers)
    assert res_unreplied.status_code == 200
    unreplied_items = res_unreplied.json()
    assert len(unreplied_items) == 1
    assert unreplied_items[0]["replied"] is not True

