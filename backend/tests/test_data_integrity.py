import pytest
import datetime
from app.core.config import settings
from app.core.database import get_db, utc_now, format_iso_z, clean_doc
from app.services.ai_engine import ai_engine
from app.services.scraper_simulator import scraper_simulator

@pytest.mark.asyncio
async def test_brand_creation_does_not_seed_history_when_demo_mode_false(client, user_factory, test_db, monkeypatch):
    """
    When DEMO_MODE is False, brand creation does NOT auto-seed 7-day history,
    and mentions_count is 0, sentiment_score is 0.0.
    """
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    user, token = await user_factory(email="nodemo@brandpulse.ai", user_id="usr_nodemo")

    res = await client.post(
        "/api/v1/brands",
        json={"name": "Clean Slate Brand", "industry": "Technology"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    brand_data = res.json()
    assert brand_data["mentions_count"] == 0
    assert brand_data["sentiment_score"] == 0.0

    # Verify no mentions were inserted into DB for this brand
    brand_id = brand_data["id"]
    count = await test_db["mentions"].count_documents({"brand_id": brand_id})
    assert count == 0

@pytest.mark.asyncio
async def test_hardcoded_sentiment_removed_and_computed_from_real_data(client, user_factory, test_db):
    """
    Brand sentiment is computed from actual mentions, not hardcoded (0.42 / 0.35).
    """
    user, token = await user_factory(email="sent_calc@brandpulse.ai", user_id="usr_sent_calc")
    
    brand_doc = {
        "id": "brand_calc_test",
        "owner_id": "usr_sent_calc",
        "name": "Sentiment Calc Brand",
        "industry": "FinTech",
        "created_at": utc_now()
    }
    await test_db["brands"].insert_one(brand_doc)

    # Insert two mentions with known sentiment scores: 0.8 and 0.4 -> average = 0.60
    await test_db["mentions"].insert_one({
        "id": "men_calc_1",
        "brand_id": "brand_calc_test",
        "content": "Awesome experience",
        "author": "Alice",
        "author_handle": "@alice",
        "platform": "twitter",
        "sentiment": "positive",
        "sentiment_score": 0.80,
        "emotions": {"joy": 0.8},
        "dominant_emotion": "joy",
        "intent": "praise",
        "intent_confidence": 0.9,
        "reach": 100,
        "engagement_score": 10,
        "virality_score": 10.0,
        "is_simulated": False,
        "timestamp": utc_now()
    })
    await test_db["mentions"].insert_one({
        "id": "men_calc_2",
        "brand_id": "brand_calc_test",
        "content": "Pretty good service",
        "author": "Bob",
        "author_handle": "@bob",
        "platform": "twitter",
        "sentiment": "positive",
        "sentiment_score": 0.40,
        "emotions": {"joy": 0.5},
        "dominant_emotion": "joy",
        "intent": "praise",
        "intent_confidence": 0.8,
        "reach": 200,
        "engagement_score": 20,
        "virality_score": 15.0,
        "is_simulated": False,
        "timestamp": utc_now()
    })

    headers = {"Authorization": f"Bearer {token}"}

    # GET /brands/{id} computes 0.60 (not 0.42 or 0.35)
    res_get = await client.get("/api/v1/brands/brand_calc_test", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["sentiment_score"] == 0.6
    assert res_get.json()["mentions_count"] == 2

    # PUT /brands/{id} also computes 0.60 (not 0.35)
    res_put = await client.put(
        "/api/v1/brands/brand_calc_test",
        json={"description": "Updated FinTech description"},
        headers=headers
    )
    assert res_put.status_code == 200
    assert res_put.json()["sentiment_score"] == 0.6

@pytest.mark.asyncio
async def test_list_brands_aggregation_without_n_plus_one(client, user_factory, test_db):
    """
    list_brands correctly computes counts and average sentiment across multiple brands.
    """
    user, token = await user_factory(email="agg_user@brandpulse.ai", user_id="usr_agg")

    await test_db["brands"].delete_many({"owner_id": "usr_agg"})
    await test_db["brands"].insert_one({"id": "brand_agg_1", "owner_id": "usr_agg", "name": "Brand One", "created_at": utc_now()})
    await test_db["brands"].insert_one({"id": "brand_agg_2", "owner_id": "usr_agg", "name": "Brand Two", "created_at": utc_now()})

    await test_db["mentions"].insert_one({
        "id": "men_b1_1",
        "brand_id": "brand_agg_1",
        "content": "Good",
        "author": "A",
        "author_handle": "@a",
        "platform": "twitter",
        "sentiment": "positive",
        "sentiment_score": 0.50,
        "emotions": {},
        "dominant_emotion": "joy",
        "intent": "general",
        "intent_confidence": 0.5,
        "reach": 10,
        "engagement_score": 1,
        "virality_score": 5.0,
        "timestamp": utc_now()
    })

    headers = {"Authorization": f"Bearer {token}"}
    res = await client.get("/api/v1/brands", headers=headers)
    assert res.status_code == 200
    brands_data = {b["id"]: b for b in res.json()}

    assert brands_data["brand_agg_1"]["mentions_count"] == 1
    assert brands_data["brand_agg_1"]["sentiment_score"] == 0.5
    assert brands_data["brand_agg_2"]["mentions_count"] == 0
    assert brands_data["brand_agg_2"]["sentiment_score"] == 0.0

@pytest.mark.asyncio
async def test_stream_endpoint_does_not_insert_fake_data_to_db(client, user_factory, test_db, monkeypatch):
    """
    GET /monitoring/stream should NEVER write to the DB.
    """
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    user, token = await user_factory(email="stream_user@brandpulse.ai", user_id="usr_stream")

    await test_db["brands"].delete_many({"owner_id": "usr_stream"})
    await test_db["brands"].insert_one({"id": "brand_stream", "owner_id": "usr_stream", "name": "Stream Brand", "created_at": utc_now()})
    await test_db["mentions"].delete_many({"brand_id": "brand_stream"})

    initial_count = await test_db["mentions"].count_documents({"brand_id": "brand_stream"})
    assert initial_count == 0

    # Hit the stream endpoint with token
    headers = {"Authorization": f"Bearer {token}"}
    async with client.stream("GET", "/api/v1/monitoring/stream?brand_id=brand_stream&limit=1", headers=headers) as stream_resp:
        assert stream_resp.status_code == 200
        # Read first SSE chunk
        async for line in stream_resp.aiter_lines():
            if line:
                break

    # Verify no documents were inserted into MongoDB
    after_count = await test_db["mentions"].count_documents({"brand_id": "brand_stream"})
    assert after_count == 0

@pytest.mark.asyncio
async def test_simulation_flags_and_filtering(client, user_factory, test_db):
    """
    Real mentions have is_simulated=False, simulated mentions have is_simulated=True,
    and GET /monitoring/mentions filters by is_simulated.
    """
    user, token = await user_factory(email="sim_flag@brandpulse.ai", user_id="usr_sim_flag")
    await test_db["brands"].delete_many({"owner_id": "usr_sim_flag"})
    await test_db["brands"].insert_one({"id": "brand_sim_test", "owner_id": "usr_sim_flag", "name": "Sim Test", "created_at": utc_now()})

    headers = {"Authorization": f"Bearer {token}"}

    # 1. Real mention creation
    res_real = await client.post("/api/v1/monitoring/mentions", json={
        "brand_id": "brand_sim_test",
        "author": "Real User",
        "author_handle": "@realuser",
        "content": "This is real customer feedback",
        "platform": "twitter"
    }, headers=headers)
    assert res_real.status_code == 200
    real_data = res_real.json()
    assert real_data["is_simulated"] is False

    # 2. Simulated mention creation
    res_sim = await client.post("/api/v1/monitoring/simulate?brand_id=brand_sim_test", headers=headers)
    assert res_sim.status_code == 200
    sim_data = res_sim.json()["mention"]
    assert sim_data["is_simulated"] is True

    # 3. Crisis simulation sets is_simulated=True on alert and mentions
    res_crisis = await client.post(
        "/api/v1/crisis/simulate-crisis?brand_id=brand_sim_test&scenario_type=outage_disaster",
        headers=headers
    )
    assert res_crisis.status_code == 200
    assert res_crisis.json()["alert"]["is_simulated"] is True

    # 4. Filter mentions by is_simulated=false -> only returns real
    res_real_only = await client.get("/api/v1/monitoring/mentions?brand_id=brand_sim_test&is_simulated=false", headers=headers)
    assert res_real_only.status_code == 200
    for m in res_real_only.json():
        assert m["is_simulated"] is False

    # 5. Filter mentions by is_simulated=true -> only returns simulated
    res_sim_only = await client.get("/api/v1/monitoring/mentions?brand_id=brand_sim_test&is_simulated=true", headers=headers)
    assert res_sim_only.status_code == 200
    for m in res_sim_only.json():
        assert m["is_simulated"] is True

@pytest.mark.asyncio
async def test_forecast_insufficient_data_and_deterministic_output(client, user_factory, test_db):
    """
    When historical data has fewer than 3 days, /forecast returns explicit status: 'insufficient_data'
    and empty forecast list without generating random numbers.
    When >= 3 days exist, output is strictly deterministic.
    """
    user, token = await user_factory(email="forecast_user@brandpulse.ai", user_id="usr_fc")
    await test_db["brands"].delete_many({"owner_id": "usr_fc"})
    await test_db["brands"].insert_one({"id": "brand_fc", "owner_id": "usr_fc", "name": "Forecast Brand", "created_at": utc_now()})
    await test_db["mentions"].delete_many({"brand_id": "brand_fc"})

    headers = {"Authorization": f"Bearer {token}"}

    # 0 days of data -> insufficient_data
    res = await client.get("/api/v1/analytics/forecast?brand_id=brand_fc", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "insufficient_data"
    assert data["forecast"] == []

    # Direct test of ai_engine.forecast_trends determinism
    hist_sample = [
        {"date": "2026-08-01", "volume": 100, "sentiment_score": 0.50},
        {"date": "2026-08-02", "volume": 120, "sentiment_score": 0.55},
        {"date": "2026-08-03", "volume": 140, "sentiment_score": 0.60}
    ]
    run_1 = ai_engine.forecast_trends(hist_sample, forecast_days=3)
    run_2 = ai_engine.forecast_trends(hist_sample, forecast_days=3)
    # Must be 100% deterministic (no random jitter)
    assert run_1 == run_2
    assert len(run_1) == 3

@pytest.mark.asyncio
async def test_topic_clusters_returns_empty_when_insufficient_data():
    """
    ai_engine.extract_topics_and_clusters returns [] when insufficient data,
    without returning fake hardcoded keywords like ['service', 'platform', 'update'].
    """
    # Empty texts
    assert ai_engine.extract_topics_and_clusters([]) == []
    # Fewer than n_clusters texts
    few_texts = [{"content": "hello world"}]
    assert ai_engine.extract_topics_and_clusters(few_texts, n_clusters=4) == []

@pytest.mark.asyncio
async def test_timestamps_serialize_with_z_in_api(client, user_factory, test_db):
    """
    Timestamps serialize to ISO 8601 with trailing 'Z'.
    """
    user, token = await user_factory(email="tz_user@brandpulse.ai", user_id="usr_tz")
    await test_db["brands"].delete_many({"owner_id": "usr_tz"})
    await test_db["brands"].insert_one({
        "id": "brand_tz",
        "owner_id": "usr_tz",
        "name": "TZ Brand",
        "created_at": datetime.datetime(2026, 8, 15, 12, 30, 0, tzinfo=datetime.timezone.utc)
    })

    headers = {"Authorization": f"Bearer {token}"}
    res = await client.get("/api/v1/brands/brand_tz", headers=headers)
    assert res.status_code == 200
    assert res.json()["created_at"].endswith("Z")
