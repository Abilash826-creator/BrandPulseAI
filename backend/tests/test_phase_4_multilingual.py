import pytest
import asyncio
from app.services.ai_engine import ai_engine
from app.services.analysis_backends import (
    AnalysisBackend,
    LocalMultilingualBackend,
    LLMAnalysisBackend,
    get_analysis_backend,
    _MONTHLY_BUSINESS_COSTS
)
from app.core.config import settings

def test_language_detection_indian_dialects():
    """
    Test language detection for English, Tamil script, Hindi script, Tanglish, and Hinglish.
    """
    # 1. English
    en_text = "The filter coffee was hot and perfectly brewed with great aroma."
    assert ai_engine.detect_language(en_text) == "en"

    # 2. Tamil script
    ta_text = "காபி மிகவும் அருமை, சாம்பார் வடை சூப்பர் சுவை."
    assert ai_engine.detect_language(ta_text) == "ta"

    # 3. Hindi script
    hi_text = "खाना बहुत ही स्वादिष्ट और ताज़ा था, सेवा बेहतरीन थी।"
    assert ai_engine.detect_language(hi_text) == "hi"

    # 4. Tanglish (Romanized Tamil)
    tanglish_text = "Sombu coffee romba nalla irukku, idli semma taste."
    assert ai_engine.detect_language(tanglish_text) == "tanglish"

    # 5. Hinglish (Romanized Hindi)
    hinglish_text = "Khana bahut accha tha, lekin service thoda slow tha."
    assert ai_engine.detect_language(hinglish_text) == "hinglish"


def test_translate_to_english():
    """
    Test translation heuristics for Tamil, Hindi, Tanglish, and Hinglish into English.
    """
    # Tanglish translation
    tanglish = "romba nalla irukku, semma taste"
    translated = ai_engine.translate_to_english(tanglish, "tanglish")
    assert "very good" in translated.lower() or "delicious" in translated.lower()

    # Hinglish translation
    hinglish = "khana bahut accha tha lekin service bekar"
    translated_hi = ai_engine.translate_to_english(hinglish, "hinglish")
    assert "good" in translated_hi.lower() or "bad" in translated_hi.lower()

    # English text returns unmodified
    en = "Great experience overall."
    assert ai_engine.translate_to_english(en, "en") == en


def test_multilingual_sentiment_without_blind_vader():
    """
    Ensure non-English Indian text is scored accurately by the multilingual engine,
    and returns an honest confidence score instead of blind English VADER.
    """
    # Tanglish positive
    tanglish_pos = "Idli romba nalla irukku, chutney super, semma taste!"
    res_pos = ai_engine.analyze_sentiment(tanglish_pos, lang="tanglish")
    assert res_pos.sentiment == "positive"
    assert res_pos.score > 0.2
    assert 0.50 <= res_pos.confidence <= 0.85  # honest confidence

    # Hinglish negative
    hinglish_neg = "Khana bilkul bekar tha, ganda smell and bahut kharab experience."
    res_neg = ai_engine.analyze_sentiment(hinglish_neg, lang="hinglish")
    assert res_neg.sentiment == "negative"
    assert res_neg.score < -0.2
    assert 0.50 <= res_neg.confidence <= 0.85

    # Tamil script positive
    ta_pos = "சாப்பாடு மிகவும் அருமை மற்றும் சுவை அற்புதம்."
    res_ta = ai_engine.analyze_sentiment(ta_pos, lang="ta")
    assert res_ta.sentiment == "positive"
    assert res_ta.score > 0.0


def test_tag_preset_topics():
    """
    Test deterministic preset topic tagging for small businesses.
    """
    restaurant_rev = "The ghee roast dosa was crispy and delicious, but the waiter took 30 minutes to bring the bill."
    topics = ai_engine.tag_preset_topics(restaurant_rev, preset_key="restaurant_veg")
    assert "Food Quality" in topics
    assert "Service & Staff" in topics

    clinic_rev = "Dr. Sharma was very caring and explained diagnosis clearly, but wait time in reception was high."
    clinic_topics = ai_engine.tag_preset_topics(clinic_rev, preset_key="clinic_dental")
    assert "Doctor Care" in clinic_topics
    assert "Wait Time" in clinic_topics

    salon_rev = "Loved the haircut and styling, salon was very clean and hygienic."
    salon_topics = ai_engine.tag_preset_topics(salon_rev, preset_key="salon_spa")
    assert "Hair Services" in salon_topics or "Stylist Skill" in salon_topics
    assert "Cleanliness & Hygiene" in salon_topics or "Hygiene & Cleanliness" in salon_topics


def test_extract_preset_topics_and_clusters_under_100_mentions():
    """
    For small shops with < 100 mentions, preset keyword topic clustering must be used.
    """
    mentions = [
        {"content": "Crispy masala dosa and hot sambar, superb food quality!"},
        {"content": "Staff was very slow and arrogant at the counter."},
        {"content": "Very affordable price and reasonable billing."},
        {"content": "Ambience was clean and peaceful with good AC."}
    ]
    clusters = ai_engine.extract_preset_topics_and_clusters(mentions, preset_key="restaurant_veg")
    assert len(clusters) >= 2
    topic_names = [c["topic"] for c in clusters]
    assert any("Food" in t or "Service" in t or "Price" in t for t in topic_names)


@pytest.mark.asyncio
async def test_local_analysis_backend():
    """
    Verify LocalMultilingualBackend interface and result contract.
    """
    backend = LocalMultilingualBackend()
    text = "Filter coffee romba nalla irukku, service is quick."
    result = await backend.analyze_mention(text, business_id="biz_123", business_type="restaurant_veg")

    assert isinstance(result, dict)
    assert result["backend"] == "local_multilingual"
    assert result["language"] in ["tanglish", "en"]
    assert result["sentiment"] in ["positive", "neutral", "negative"]
    assert isinstance(result["topics"], list)
    assert "Food Quality" in result["topics"] or "Service & Staff" in result["topics"]


@pytest.mark.asyncio
async def test_llm_analysis_backend_cost_cap_fallback():
    """
    Verify LLMAnalysisBackend respects monthly cost cap and falls back to local backend.
    """
    backend = LLMAnalysisBackend()
    business_id = "test_cap_shop_99"

    # 1. Normal call within budget
    res1 = await backend.analyze_mention("The dosa was awesome and hot!", business_id=business_id, business_type="restaurant_veg")
    assert res1["sentiment"] in ["positive", "neutral", "negative"]

    # 2. Exceed monthly budget for this business
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc)
    key = f"{business_id}_{now.year}_{now.month:02d}"
    _MONTHLY_BUSINESS_COSTS[key] = settings.MONTHLY_LLM_COST_CAP + 10.0

    # 3. Next call should seamlessly fallback to local multilingual backend without crashing
    res2 = await backend.analyze_mention("Food was very bad and stale.", business_id=business_id, business_type="restaurant_veg")
    assert res2["backend"] == "local_multilingual"
    assert res2["sentiment"] == "negative"
