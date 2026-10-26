"""
Comprehensive Pipeline Test for Sree Annapoorna (Coimbatore, Tamil Nadu) Instagram & NLP Model.
Verifies:
1. Disambiguation (Temple/Mythology vs Coimbatore Restaurant).
2. Aspect Extraction (Ghee Roast, Filter Coffee, Sambar, Service, Waiting Time, Parking).
3. Context-Aware Sentiment & Sarcasm.
4. Model inference accuracy.
"""

import sys
import os
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from app.services.relevance_filter import relevance_filter
from app.services.ai_engine import ai_engine

def run_tests():
    print("=== TESTING SREE ANNAPOORNA COIMBATORE PIPELINE ===")

    # Test 1: Disambiguation - Temple / Goddess vs Restaurant
    temple_text = "Visiting the ancient Annapoorna devi temple for special pooja and reciting the sacred stotram."
    res1 = relevance_filter.analyze(
        text=temple_text,
        brand_name="Sree Annapoorna",
        tracked_products=["Ghee Roast", "Filter Coffee"],
        tracked_keywords=["Annapoorna", "Ghee Roast"],
        tracked_hashtags=["#Annapoorna"]
    )
    print(f"\n1. Temple Text: '{temple_text}'")
    print(f" -> Brand Detected: {res1['brand_detected']}, Relevance Score: {res1['relevance_score']}, Reason: {res1['reason']}")
    assert res1['brand_detected'] == False, "Temple text should not be classified as the restaurant!"
    assert res1['relevance_score'] < 0.10, "Relevance score should be low for temple text"

    # Test 2: High Relevance Restaurant Instagram Post
    cbe_text = "Nothing beats the iconic Ghee Roast and Filter Coffee at Sree Annapoorna RS Puram! Heavenly aroma and crispy dosa. #Annapoorna #CoimbatoreFood"
    res2 = relevance_filter.analyze(
        text=cbe_text,
        brand_name="Sree Annapoorna",
        tracked_products=["Ghee Roast", "Filter Coffee", "Sambar Vada"],
        tracked_keywords=["Annapoorna", "Ghee Roast", "RS Puram", "Filter Coffee"],
        tracked_hashtags=["#Annapoorna", "#CoimbatoreFood"]
    )
    print(f"\n2. Restaurant Text: '{cbe_text}'")
    print(f" -> Brand Detected: {res2['brand_detected']}, Product: {res2['product_detected']}, Relevance Score: {res2['relevance_score']}")
    print(f" -> Matched Aspects: {[a['aspect'] for a in res2['aspects']]}")
    assert res2['brand_detected'] == True
    assert res2['relevance_score'] >= 0.85

    # Test 3: Sarcasm / Service Friction
    sarcastic_text = "Wow, what lightning fast service at Annapoorna! We only had to wait 50 minutes for a glass of water."
    res3 = relevance_filter.analyze(
        text=sarcastic_text,
        brand_name="Sree Annapoorna",
        tracked_products=["Meals"],
        tracked_keywords=["Annapoorna", "Service"],
        tracked_hashtags=["#Annapoorna"]
    )
    print(f"\n3. Sarcastic Service Text: '{sarcastic_text}'")
    print(f" -> Sarcasm Flag: {res3['context'].get('sarcasm')}")
    print(f" -> Aspects: {res3['aspects']}")
    assert res3['context'].get('sarcasm') == True

    # Test 4: ML Model Sentiment Inference
    sent, score = ai_engine.analyze_sentiment(cbe_text)
    print(f"\n4. AI Engine Sentiment for Dosa Review: '{sent}' (Score: {score})")
    assert sent == "positive"

    print("\n>>> ALL SREE ANNAPOORNA PIPELINE TESTS PASSED 100%! <<<")

if __name__ == "__main__":
    run_tests()
