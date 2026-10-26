import pytest
import datetime
from app.core.database import get_db

@pytest.mark.asyncio
async def test_user_a_cannot_read_update_or_delete_user_b_brand(client, user_factory, test_db):
    """
    User A cannot read, update, or delete User B's brand (returns 404).
    """
    user_a, token_a = await user_factory(email="usera@brandpulse.ai", user_id="user_a_id")
    user_b, token_b = await user_factory(email="userb@brandpulse.ai", user_id="user_b_id")

    # Create brand for User B
    brand_b = {
        "id": "brand_b_secret",
        "owner_id": "user_b_id",
        "name": "User B Confidential Brand",
        "industry": "Defense",
        "created_at": datetime.datetime.now().isoformat()
    }
    await test_db["brands"].insert_one(brand_b)

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. User B can read their own brand
    res_b = await client.get("/api/v1/brands/brand_b_secret", headers=headers_b)
    assert res_b.status_code == 200

    # 2. User A cannot read User B's brand (returns 404)
    res_a_read = await client.get("/api/v1/brands/brand_b_secret", headers=headers_a)
    assert res_a_read.status_code == 404

    # 3. User A cannot update User B's brand (returns 404)
    res_a_update = await client.put(
        "/api/v1/brands/brand_b_secret",
        json={"name": "Hacked Brand Name"},
        headers=headers_a
    )
    assert res_a_update.status_code == 404
    # Verify in DB it didn't change
    doc = await test_db["brands"].find_one({"id": "brand_b_secret"})
    assert doc["name"] == "User B Confidential Brand"

    # 4. User A cannot delete User B's brand (returns 404)
    res_a_del = await client.delete("/api/v1/brands/brand_b_secret", headers=headers_a)
    assert res_a_del.status_code == 404
    # Verify in DB it still exists
    assert await test_db["brands"].find_one({"id": "brand_b_secret"}) is not None

@pytest.mark.asyncio
async def test_brands_list_scoped_to_current_user(client, user_factory, test_db):
    """
    GET /brands returns only the current user's brands.
    """
    user_a, token_a = await user_factory(email="list_a@brandpulse.ai", user_id="user_list_a")
    user_b, token_b = await user_factory(email="list_b@brandpulse.ai", user_id="user_list_b")

    await test_db["brands"].delete_many({})
    await test_db["brands"].insert_one({
        "id": "brand_a_1",
        "owner_id": "user_list_a",
        "name": "Brand A1",
        "industry": "Tech",
        "created_at": datetime.datetime.now().isoformat()
    })
    await test_db["brands"].insert_one({
        "id": "brand_b_1",
        "owner_id": "user_list_b",
        "name": "Brand B1",
        "industry": "Retail",
        "created_at": datetime.datetime.now().isoformat()
    })

    # User A listing brands sees only Brand A1
    res_a = await client.get("/api/v1/brands", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a.status_code == 200
    brand_ids_a = [b["id"] for b in res_a.json()]
    assert brand_ids_a == ["brand_a_1"]

    # User B listing brands sees only Brand B1
    res_b = await client.get("/api/v1/brands", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b.status_code == 200
    brand_ids_b = [b["id"] for b in res_b.json()]
    assert brand_ids_b == ["brand_b_1"]

@pytest.mark.asyncio
async def test_user_a_cannot_access_or_tamper_user_b_mentions(client, user_factory, test_db):
    """
    User A cannot read User B's mentions by brand_id, and unscoped queries only return User A's mentions.
    """
    user_a, token_a = await user_factory(email="men_a@brandpulse.ai", user_id="user_men_a")
    user_b, token_b = await user_factory(email="men_b@brandpulse.ai", user_id="user_men_b")

    await test_db["brands"].delete_many({})
    await test_db["brands"].insert_one({"id": "brand_a", "owner_id": "user_men_a", "name": "Brand A"})
    await test_db["brands"].insert_one({"id": "brand_b", "owner_id": "user_men_b", "name": "Brand B"})

    await test_db["mentions"].delete_many({})
    await test_db["mentions"].insert_one({
        "id": "men_b_secret",
        "brand_id": "brand_b",
        "brand_name": "Brand B",
        "content": "Secret information regarding Brand B",
        "author": "Insider",
        "author_handle": "@insider",
        "platform": "twitter",
        "sentiment": "negative",
        "sentiment_score": -0.8,
        "emotions": {"fear": 0.8},
        "dominant_emotion": "fear",
        "intent": "complaint",
        "intent_confidence": 0.9,
        "reach": 500,
        "engagement_score": 50,
        "virality_score": 12.5,
        "timestamp": datetime.datetime.now().isoformat()
    })
    await test_db["mentions"].insert_one({
        "id": "men_a_public",
        "brand_id": "brand_a",
        "brand_name": "Brand A",
        "content": "Public mention for Brand A",
        "author": "Customer",
        "author_handle": "@customer",
        "platform": "twitter",
        "sentiment": "positive",
        "sentiment_score": 0.85,
        "emotions": {"joy": 0.9},
        "dominant_emotion": "joy",
        "intent": "praise",
        "intent_confidence": 0.95,
        "reach": 200,
        "engagement_score": 20,
        "virality_score": 5.0,
        "timestamp": datetime.datetime.now().isoformat()
    })

    headers_a = {"Authorization": f"Bearer {token_a}"}

    # User A tries to query mentions with brand_id=brand_b -> 404
    res_query_b = await client.get("/api/v1/monitoring/mentions?brand_id=brand_b", headers=headers_a)
    assert res_query_b.status_code == 404

    # User A queries mentions without brand_id -> only sees Brand A mentions
    res_unscoped = await client.get("/api/v1/monitoring/mentions", headers=headers_a)
    assert res_unscoped.status_code == 200
    mention_ids = [m["id"] for m in res_unscoped.json()]
    assert "men_a_public" in mention_ids
    assert "men_b_secret" not in mention_ids

    # User A tries to ingest mention into Brand B -> 404
    res_post_b = await client.post("/api/v1/monitoring/mentions", json={
        "brand_id": "brand_b",
        "content": "Malicious injection",
        "author": "Attacker",
        "author_handle": "@attacker",
        "platform": "twitter"
    }, headers=headers_a)
    assert res_post_b.status_code == 404

@pytest.mark.asyncio
async def test_user_a_cannot_acknowledge_resolve_or_read_user_b_alerts(client, user_factory, test_db):
    """
    Alerts: User A cannot acknowledge, resolve, or read User B's alerts.
    """
    user_a, token_a = await user_factory(email="alert_a@brandpulse.ai", user_id="user_alert_a")
    user_b, token_b = await user_factory(email="alert_b@brandpulse.ai", user_id="user_alert_b")

    await test_db["brands"].delete_many({})
    await test_db["brands"].insert_one({"id": "brand_b_alert", "owner_id": "user_alert_b", "name": "Brand B"})
    
    await test_db["alerts"].delete_many({})
    await test_db["alerts"].insert_one({
        "id": "alert_b_confidential",
        "brand_id": "brand_b_alert",
        "brand_name": "Brand B",
        "title": "Confidential Security Breach",
        "status": "active",
        "created_at": datetime.datetime.now().isoformat()
    })

    headers_a = {"Authorization": f"Bearer {token_a}"}

    # User A query alerts with brand_id=brand_b_alert -> 404
    res_read = await client.get("/api/v1/crisis/alerts?brand_id=brand_b_alert", headers=headers_a)
    assert res_read.status_code == 404

    # User A acknowledge -> 404
    res_ack = await client.post("/api/v1/crisis/alerts/alert_b_confidential/acknowledge", headers=headers_a)
    assert res_ack.status_code == 404

    # User A resolve -> 404
    res_res = await client.post("/api/v1/crisis/alerts/alert_b_confidential/resolve", headers=headers_a)
    assert res_res.status_code == 404

@pytest.mark.asyncio
async def test_user_a_cannot_read_update_or_delete_user_b_summaries(client, user_factory, test_db):
    """
    Summaries: User A cannot read, update, or delete User B's summary.
    """
    user_a, token_a = await user_factory(email="sum_a@brandpulse.ai", user_id="user_sum_a")
    user_b, token_b = await user_factory(email="sum_b@brandpulse.ai", user_id="user_sum_b")

    await test_db["brands"].delete_many({})
    await test_db["brands"].insert_one({"id": "brand_b_sum", "owner_id": "user_sum_b", "name": "Brand B"})
    
    await test_db["summaries"].delete_many({})
    await test_db["summaries"].insert_one({
        "id": "summary_b_confidential",
        "brand_id": "brand_b_sum",
        "name_of_company": "Brand B",
        "cause_of_feedback": "Private feedback audit",
        "status": "generated",
        "timestamp": datetime.datetime.now().isoformat()
    })

    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Read by ID -> 404
    res_get = await client.get("/api/v1/monitoring/summaries/summary_b_confidential", headers=headers_a)
    assert res_get.status_code == 404

    # Update -> 404
    res_patch = await client.patch(
        "/api/v1/monitoring/summaries/summary_b_confidential",
        json={"status": "tampered"},
        headers=headers_a
    )
    assert res_patch.status_code == 404

    # Delete -> 404
    res_del = await client.delete("/api/v1/monitoring/summaries/summary_b_confidential", headers=headers_a)
    assert res_del.status_code == 404

@pytest.mark.asyncio
async def test_user_a_cannot_download_user_b_reports(client, user_factory, test_db):
    """
    Reports: User A cannot download User B's report file or read User B's history.
    """
    user_a, token_a = await user_factory(email="rep_a@brandpulse.ai", user_id="user_rep_a")
    user_b, token_b = await user_factory(email="rep_b@brandpulse.ai", user_id="user_rep_b")

    await test_db["brands"].delete_many({})
    await test_db["brands"].insert_one({"id": "brand_b_rep", "owner_id": "user_rep_b", "name": "Brand B"})
    
    await test_db["reports"].delete_many({})
    await test_db["reports"].insert_one({
        "id": "report_b_id",
        "brand_id": "brand_b_rep",
        "filename": "confidential_financial_report_b.pdf",
        "created_at": datetime.datetime.now().isoformat()
    })

    headers_a = {"Authorization": f"Bearer {token_a}"}

    # History scoped query for User B brand -> 404
    res_hist = await client.get("/api/v1/reports/history?brand_id=brand_b_rep", headers=headers_a)
    assert res_hist.status_code == 404

    # Direct download attempt by User A -> 404
    res_dl = await client.get("/api/v1/reports/download/confidential_financial_report_b.pdf", headers=headers_a)
    assert res_dl.status_code == 404

    # Unauthenticated download attempt -> 401
    res_anon = await client.get("/api/v1/reports/download/confidential_financial_report_b.pdf")
    assert res_anon.status_code == 401

@pytest.mark.asyncio
async def test_system_and_firewall_authentication_and_admin_guards(client, user_factory):
    """
    Test 4: Authentication and admin checks on system & firewall endpoints.
    /system/* and /auth/firewall-* are admin-only; /system/db-connect is removed; /monitoring/test-nlp requires auth.
    """
    # Unauthenticated calls
    assert (await client.get("/api/v1/system/db-status")).status_code == 401
    assert (await client.post("/api/v1/system/db-connect", json={"uri": "mongodb://localhost:27017"})).status_code == 404
    assert (await client.get("/api/v1/auth/firewall-status")).status_code == 401
    assert (await client.get("/api/v1/auth/firewall-logs")).status_code == 401
    assert (await client.post("/api/v1/auth/firewall-test", json={"test": "payload"})).status_code == 401
    assert (await client.post("/api/v1/monitoring/test-nlp?text=hello")).status_code == 401

    # Regular user calls (owner / non-admin)
    _, user_token = await user_factory(email="regular@brandpulse.ai", role="owner", user_id="reg_01")
    reg_headers = {"Authorization": f"Bearer {user_token}"}
    
    # Authenticated non-admin endpoints
    assert (await client.post("/api/v1/monitoring/test-nlp?text=hello", headers=reg_headers)).status_code == 200

    # Admin only endpoints return 403 for regular user
    assert (await client.get("/api/v1/system/db-status", headers=reg_headers)).status_code == 403
    assert (await client.get("/api/v1/auth/firewall-status", headers=reg_headers)).status_code == 403
    assert (await client.get("/api/v1/auth/firewall-logs", headers=reg_headers)).status_code == 403
    assert (await client.post("/api/v1/auth/firewall-test", json={"test": "payload"}, headers=reg_headers)).status_code == 403

    # Admin user calls succeed with 200
    _, admin_token = await user_factory(email="admin_sys@brandpulse.ai", role="admin", user_id="adm_01")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    assert (await client.get("/api/v1/system/db-status", headers=admin_headers)).status_code == 200
    assert (await client.get("/api/v1/auth/firewall-status", headers=admin_headers)).status_code == 200
    assert (await client.get("/api/v1/auth/firewall-logs", headers=admin_headers)).status_code == 200

@pytest.mark.asyncio
async def test_audit_logs_user_scoping(client, user_factory, test_db):
    """
    Test 5: Admins see all audit logs, regular users see only their own.
    """
    user_a, token_a = await user_factory(email="audit_user_a@brandpulse.ai", role="brand_manager", user_id="usr_audit_a")
    user_b, token_b = await user_factory(email="audit_user_b@brandpulse.ai", role="brand_manager", user_id="usr_audit_b")
    _, admin_token = await user_factory(email="audit_admin@brandpulse.ai", role="admin", user_id="usr_audit_adm")

    await test_db["auth_logs"].delete_many({})
    await test_db["auth_logs"].insert_one({
        "id": "log_a",
        "user_id": "usr_audit_a",
        "email": "audit_user_a@brandpulse.ai",
        "full_name": "Audit User A",
        "role": "brand_manager",
        "status": "AUTHENTICATED",
        "login_date": "2026-01-01",
        "login_time": "10:00:00",
        "login_timestamp": "2026-01-01T10:00:00",
        "ip_address": "127.0.0.1",
        "user_agent": "PytestClient",
        "auth_method": "credentials"
    })
    await test_db["auth_logs"].insert_one({
        "id": "log_b",
        "user_id": "usr_audit_b",
        "email": "audit_user_b@brandpulse.ai",
        "full_name": "Audit User B",
        "role": "brand_manager",
        "status": "AUTHENTICATED",
        "login_date": "2026-01-01",
        "login_time": "10:05:00",
        "login_timestamp": "2026-01-01T10:05:00",
        "ip_address": "127.0.0.1",
        "user_agent": "PytestClient",
        "auth_method": "credentials"
    })

    # User A only sees log_a
    res_a = await client.get("/api/v1/auth/audit-logs", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a.status_code == 200
    ids_a = [l["id"] for l in res_a.json()]
    assert ids_a == ["log_a"]

    # Admin sees all logs
    res_admin = await client.get("/api/v1/auth/audit-logs", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 200
    ids_admin = [l["id"] for l in res_admin.json()]
    assert "log_a" in ids_admin
    assert "log_b" in ids_admin

@pytest.mark.asyncio
async def test_mention_search_regex_escaping_and_length_cap(client, user_factory, test_db):
    """
    Test 6: In mention search, wrap user input in re.escape() and cap at 100 characters.
    """
    user, token = await user_factory(email="search_user@brandpulse.ai", user_id="usr_search")
    await test_db["brands"].delete_many({})
    await test_db["brands"].insert_one({"id": "search_brand", "owner_id": "usr_search", "name": "SearchBrand"})

    await test_db["mentions"].delete_many({})
    await test_db["mentions"].insert_one({
        "id": "men_spec",
        "brand_id": "search_brand",
        "content": "Special chars test: (query.*+?^$[]) should not break regex",
        "author": "tester",
        "author_handle": "@tester",
        "platform": "twitter",
        "timestamp": datetime.datetime.now().isoformat()
    })

    headers = {"Authorization": f"Bearer {token}"}

    # Pass unescaped regex special characters that would cause a ReDoS or regex parse error if raw
    dangerous_search = "(query.*+?^$[])" + "A" * 200
    res = await client.get(f"/api/v1/monitoring/mentions?search={dangerous_search}", headers=headers)
    assert res.status_code == 200
    # Search should execute safely without crashing MongoDB regex engine
