import pytest
import datetime
from app.services.ai_engine import ai_engine, SentimentResult
from app.core.config import settings
from app.core.database import utc_now

@pytest.mark.asyncio
async def test_health_and_ml_metrics_expose_model_statuses(client, user_factory):
    """
    /health and /ml/metrics expose model operational statuses (loaded or fallback, per model).
    """
    user, token = await user_factory(email="ml_viewer@brandpulse.ai", user_id="usr_ml_view")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. /health endpoint
    res_health = await client.get("/health")
    assert res_health.status_code == 200
    health_data = res_health.json()
    assert "model_statuses" in health_data
    statuses = health_data["model_statuses"]
    assert "apple_sentiment" in statuses
    assert "apple_emotion" in statuses
    assert "apple_intent" in statuses
    assert "annapoorna_sentiment" in statuses
    assert statuses["apple_sentiment"] in ["loaded", "fallback"]

    # 2. /ml/metrics endpoint
    res_metrics = await client.get("/api/v1/ml/metrics", headers=headers)
    assert res_metrics.status_code == 200
    metrics_data = res_metrics.json()
    assert "model_statuses" in metrics_data
    assert metrics_data["model_statuses"]["apple_sentiment"] in ["loaded", "fallback"]

@pytest.mark.asyncio
async def test_apple_metrics_naming_versioning_and_data_hash(client, user_factory):
    """
    apple_model_metrics describes actual model (TF-IDF + Calibrated LinearSVC),
    contains model_version, trained_at, sklearn_version, data_hash, 5-fold CV, and negative threshold.
    """
    user, token = await user_factory(email="apple_ml@brandpulse.ai", user_id="usr_apple_ml")
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/ml/metrics", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert "TF-IDF + Calibrated LinearSVC" in data.get("model_name", "")
    assert "Transformer/Ensemble" not in data.get("model_name", "")
    assert "model_version" in data
    assert "trained_at" in data
    assert "sklearn_version" in data
    assert "data_hash" in data
    assert len(data["data_hash"]) == 64  # SHA-256 hex digest
    assert "cross_validation_5fold" in data
    assert "decision_threshold_negative" in data
    assert "negative_recall_tuned" in data

@pytest.mark.asyncio
async def test_annapoorna_model_synthetic_data_labeling_and_honest_metrics():
    """
    Annapoorna model is explicitly labeled as 'Trained on synthetic data',
    and reports honest metrics (not artificial 100% accuracy).
    """
    metrics = ai_engine.metrics_data
    # Check annapoorna metrics json
    import os, json
    anna_path = os.path.join(ai_engine.models_dir, "annapoorna_model_metrics.json")
    if os.path.exists(anna_path):
        with open(anna_path, 'r', encoding='utf-8') as f:
            anna_metrics = json.load(f)
        assert anna_metrics.get("is_synthetic") is True
        assert "synthetic" in anna_metrics.get("dataset_label", "").lower()
        # Honest metrics: accuracy should not be 1.0 (100%)
        assert anna_metrics.get("sentiment_accuracy", 0.0) < 0.99

@pytest.mark.asyncio
async def test_background_retraining_job_lifecycle(client, user_factory):
    """
    POST /ml/train starts background job returning job_id,
    and GET /ml/train/{job_id} tracks status. Non-admin is rejected with 403.
    """
    # 1. Non-admin rejected
    member_user, member_token = await user_factory(
        email="regular_member@brandpulse.ai",
        user_id="usr_reg_mem",
        role="viewer"
    )
    res_unauth = await client.post("/api/v1/ml/train", headers={"Authorization": f"Bearer {member_token}"})
    assert res_unauth.status_code == 403

    # 2. Admin starts background training
    admin_user, admin_token = await user_factory(
        email="admin_trainer@brandpulse.ai",
        user_id="usr_adm_train",
        role="admin"
    )
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    res_start = await client.post("/api/v1/ml/train", headers=admin_headers)
    assert res_start.status_code == 200
    start_data = res_start.json()
    assert start_data["status"] == "queued"
    job_id = start_data["job_id"]
    assert job_id.startswith("job_train_")

    # 3. GET /ml/train/{job_id} queries status
    res_status = await client.get(f"/api/v1/ml/train/{job_id}", headers=admin_headers)
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data["job_id"] == job_id
    assert status_data["status"] in ["queued", "running", "completed"]

    # 4. Unknown job returns 404
    res_404 = await client.get("/api/v1/ml/train/job_invalid_id", headers=admin_headers)
    assert res_404.status_code == 404

@pytest.mark.asyncio
async def test_multilingual_language_detection_and_low_confidence(client, user_factory, test_db):
    """
    Non-English text is detected, not blindly scored with English VADER,
    and marked with low confidence.
    """
    user, token = await user_factory(email="multiling_user@brandpulse.ai", user_id="usr_multi")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Test language detection directly
    assert ai_engine.detect_language("This is a fantastic iPhone with superb battery life") == "en"
    french_lang = ai_engine.detect_language("Ce produit est absolument terrible et le service client ne répond pas")
    assert french_lang == "fr"

    spanish_lang = ai_engine.detect_language("La batería de este teléfono no dura nada, pésima experiencia")
    assert spanish_lang == "es"

    # 2. analyze_sentiment on non-English text without multilingual model returns low confidence
    french_res = ai_engine.analyze_sentiment("Ce produit est absolument terrible")
    assert french_res.confidence <= 0.50

    english_res = ai_engine.analyze_sentiment("The iPhone 16 Pro camera button is surprisingly intuitive for macro photography! Shutter speed is blazing fast.")
    assert english_res.confidence >= 0.70
    assert french_res.confidence < english_res.confidence

    # 3. Ingestion endpoint sets language and sentiment_confidence
    await test_db["brands"].insert_one({
        "id": "brand_multi_test",
        "owner_id": "usr_multi",
        "name": "Global Brand",
        "created_at": utc_now()
    })

    res_post = await client.post("/api/v1/monitoring/mentions", json={
        "brand_id": "brand_multi_test",
        "author": "Carlos",
        "author_handle": "@carlos",
        "content": "La batería de este teléfono no dura nada, pésima experiencia",
        "platform": "twitter"
    }, headers=headers)
    assert res_post.status_code == 200
    data = res_post.json()
    assert data["language"] == "es"
    assert data["sentiment_confidence"] <= 0.50

@pytest.mark.asyncio
async def test_sentiment_result_backwards_compatibility():
    """
    ai_engine.analyze_sentiment unpacks cleanly as (sentiment, score),
    while also exposing .confidence property.
    """
    res = ai_engine.analyze_sentiment("The display and camera on this phone are gorgeous!")
    # Can unpack as 2-tuple:
    sentiment, score = res
    assert sentiment in ["positive", "neutral", "negative"]
    assert isinstance(score, float)
    assert hasattr(res, "confidence")
    assert res.confidence > 0.0

@pytest.mark.asyncio
async def test_predict_full_nlp_threadpool(client, user_factory):
    """
    POST /ml/predict runs via threadpool and returns language, confidence, and model_statuses.
    """
    user, token = await user_factory(email="pred_test@brandpulse.ai", user_id="usr_pred")
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.post(
        "/api/v1/ml/predict",
        json={"text": "The camera button on the iPhone 16 Pro is surprisingly useful!"},
        headers=headers
    )
    assert res.status_code == 200
    pred = res.json()
    assert pred["language"] == "en"
    assert "confidence" in pred
    assert "model_statuses" in pred
    assert "model_engine" in pred
    assert "TF-IDF + Calibrated LinearSVC" in pred["model_engine"]
