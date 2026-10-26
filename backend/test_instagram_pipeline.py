"""
Test Suite for Instagram / Meta Graph API Integration, Relevance Filter & NLP Pipeline.
"""
import sys
import os

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from app.integrations.instagram import instagram_client
from app.services.relevance_filter import relevance_filter
from app.services.ai_engine import ai_engine

def test_instagram_oauth_url():
    url = instagram_client.get_authorization_url(brand_id="brand_apple_123")
    print(f"[*] OAuth URL generated: {url[:60]}...")
    assert "brand_apple_123" in url
    assert "mock_auth" in url or "dialog/oauth" in url
    print("[PASS] Instagram OAuth URL test passed.")

def test_disambiguation_fruit_vs_brand():
    # 1. Food / Fruit context (Irrelevant)
    fruit_text = "I had an apple for breakfast with yogurt."
    res1 = relevance_filter.analyze(fruit_text, brand_name="Apple", tracked_products=["iPhone 16", "AirPods"])
    print(f"\nFruit Text: '{fruit_text}'")
    print(f" -> Brand Detected: {res1['brand_detected']}, Relevance: {res1['relevance_score']}, Reason: {res1['reason']}")
    assert res1["brand_detected"] is False
    assert res1["relevance_score"] < 0.20

    # 2. Commercial / Product context (Relevant)
    brand_text = "Apple released a new iPhone and the battery is amazing."
    res2 = relevance_filter.analyze(brand_text, brand_name="Apple", tracked_products=["iPhone 16", "AirPods"], tracked_keywords=["battery", "camera"])
    print(f"\nBrand Text: '{brand_text}'")
    print(f" -> Brand Detected: {res2['brand_detected']}, Product: {res2['product_detected']}, Relevance: {res2['relevance_score']}")
    print(f" -> Matched Keywords: {res2['matched_keywords']}, Aspects: {[a['aspect'] for a in res2['aspects']]}")
    assert res2["brand_detected"] is True
    assert res2["product_detected"] == "iPhone" or "iPhone" in res2["detected_products"]
    assert res2["relevance_score"] >= 0.85
    assert any(a["aspect"] == "battery" for a in res2["aspects"])
    print("[PASS] Disambiguation & Brand/Product detection test passed.")

def test_sarcasm_and_context_sentiment():
    # 1. Straightforward positive
    pos_text = "The battery life is amazing."
    pos_sent, pos_score = ai_engine.analyze_sentiment(pos_text)
    print(f"\nPositive Text: '{pos_text}' -> Sentiment: {pos_sent} ({pos_score})")
    assert pos_sent == "positive"

    # 2. Sarcasm / Irony negative
    sarcastic_text = "Wow, what a battery life! It died in 2 hours."
    res_sarcasm = relevance_filter.analyze(sarcastic_text, brand_name="Apple", tracked_keywords=["battery"])
    print(f"\nSarcastic Text: '{sarcastic_text}'")
    print(f" -> Sarcasm Flag: {res_sarcasm['context']['sarcasm']}")
    print(f" -> Aspects: {res_sarcasm['aspects']}")
    assert res_sarcasm["context"]["sarcasm"] is True
    battery_aspect = next((a for a in res_sarcasm["aspects"] if a["aspect"] == "battery"), None)
    assert battery_aspect is not None
    assert battery_aspect["sentiment"] == "negative"
    print("[PASS] Context & Sarcasm analysis test passed.")

def test_reels_mock_data():
    media_items = instagram_client.fetch_account_media(ig_user_id="17841405928374192", access_token="mock_token")
    print(f"\n[*] Fetched {len(media_items)} mock Instagram media items.")
    reels = [m for m in media_items if m.get("media_product_type") == "REELS" or m.get("media_type") == "VIDEO"]
    print(f" -> Found {len(reels)} Reels/Videos.")
    assert len(reels) > 0
    # Check that transcript is available on at least one Reel
    transcripts = [r.get("mock_transcript") for r in reels if r.get("mock_transcript")]
    assert len(transcripts) > 0
    print(f" -> Sample Reel Transcript: '{transcripts[0][:80]}...'")
    print("[PASS] Reels & Video mock data test passed.")

if __name__ == "__main__":
    print("=== RUNNING BRANDPULSE INSTAGRAM PIPELINE TESTS ===")
    test_instagram_oauth_url()
    test_disambiguation_fruit_vs_brand()
    test_sarcasm_and_context_sentiment()
    test_reels_mock_data()
    print("\n>>> ALL BACKEND INSTAGRAM TESTS PASSED SUCCESSFULLY! <<<")
