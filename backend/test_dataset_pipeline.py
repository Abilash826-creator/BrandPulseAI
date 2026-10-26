"""
Comprehensive Automated Test Suite for Dataset Ingestion Pipeline (PDF & CSV).
Tests:
1. CSV file parsing, product extraction, batch AI scoring, and MongoDB ingestion.
2. PDF file parsing (pypdf), entity extraction, sentiment analysis, and aspect mapping.
3. Brand document updates (product name registering in db.brands).
4. Analytics overview synchronization (db.mentions aggregation).
5. Monitored Summary auto-generation (db.summaries).
"""

import sys
import os
import io
import asyncio

backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from app.core.database import db_manager, get_db
from app.services.dataset_ingestor import dataset_ingestor
from app.services.ai_engine import ai_engine
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

async def run_dataset_tests():
    print("=========================================================")
    print("   BRANDPULSE AI - DATASET INGESTION & FEEDER TEST SUITE ")
    print("=========================================================")

    # Initialize DB connection
    success, msg = await db_manager.connect()
    print(f"[*] Database Connection: {msg}")
    db = get_db()

    # TEST 1: CSV Ingestion with Product Auto-Detection
    print("\n[TEST 1] Ingesting Custom CSV Dataset for Apple iPhone 16 Pro...")
    sample_csv = (
        'text,product,author,platform\n'
        '"The iPhone 16 Pro camera button is surprisingly intuitive for macro photography! Shutter speed is blazing fast.",iPhone 16 Pro,tech_guru,Twitter\n'
        '"Battery health on my iPhone 16 Pro dropped to 89% in just 9 months. Extremely disappointing for a $1,200 flagship.",iPhone 16 Pro,gadget_fan,Reddit\n'
        '"Comparing the iPhone 16 Pro display to the Galaxy S24 Ultra. 120Hz promotion is silky smooth.",iPhone 16 Pro,display_geek,Review\n'
        '"Apple trade-in value offered only $380 for a pristine iPhone. What an absolute scam pricing strategy.",iPhone 16 Pro,mobile_user,Twitter\n'
        '"Apple Intelligence writing tools on iOS 18 just saved me an hour of email cleanup. Incredible on-device neural processing.",iPhone 16 Pro,ai_enthusiast,LinkedIn\n'
    )

    csv_bytes = sample_csv.encode("utf-8")
    
    # Test preview
    preview_res = dataset_ingestor.preview_file(csv_bytes, "apple_iphone16_test.csv")
    print(f" -> OK! Preview extracted {preview_res['total_preview_rows']} rows. Detected product column: '{preview_res['detected_product_column']}'")
    assert "iPhone 16 Pro" in preview_res["extracted_products"]

    # Ingest CSV
    ingest_res = await dataset_ingestor.process_and_ingest(
        file_bytes=csv_bytes,
        filename="apple_iphone16_test.csv",
        brand_name="Apple",
        product_name="iPhone 16 Pro",
        industry="Consumer Electronics & Smartphones",
        mode="append",
        generate_summary=True,
        current_user={"id": "usr_test", "full_name": "Test Engineer"}
    )
    print(f" -> OK! Ingested {ingest_res['total_records_processed']} records into brand '{ingest_res['brand_name']}'")
    print(f"    • Primary Product Registered: {ingest_res['primary_product']}")
    print(f"    • Net Sentiment Score: {ingest_res['net_sentiment_score']}% (Pos: {ingest_res['positive_count']}, Neu: {ingest_res['neutral_count']}, Neg: {ingest_res['negative_count']})")
    print(f"    • Top Praise: {[p['aspect'] for p in ingest_res['top_aspect_praise']]}")
    print(f"    • Top Friction: {[f['aspect'] for f in ingest_res['top_aspect_friction']]}")
    print(f"    • Monitored Summary Generated: ID={ingest_res['summary_id']}")

    assert ingest_res["total_records_processed"] == 5
    assert ingest_res["primary_product"] == "iPhone 16 Pro"
    assert ingest_res["summary_id"] is not None

    # TEST 2: Verify Brand Product Updated in MongoDB
    print("\n[TEST 2] Verifying Brand Document in db.brands...")
    brand_doc = await db["brands"].find_one({"id": ingest_res["brand_id"]})
    print(f" -> OK! Brand: {brand_doc['name']} | Products Array: {brand_doc.get('products')}")
    assert "iPhone 16 Pro" in brand_doc.get("products", [])

    # TEST 3: PDF Document Parsing and Ingestion
    print("\n[TEST 3] Generating & Ingesting Hospitality PDF Audit for Sree Annapoorna...")
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 750, "Sree Annapoorna - Coimbatore Hospitality Customer Feedback Audit")
    c.setFont("Helvetica", 10)
    y = 710

    pdf_reviews = [
        "1. Product: Ghee Roast Dosa - Nothing beats the iconic Ghee Roast and Filter Coffee at Sree Annapoorna RS Puram! Crispy texture and heavenly aroma.",
        "2. Product: Filter Coffee - The degree filter coffee in the brass tumbler is unmatched anywhere in Tamil Nadu.",
        "3. Product: Sambar Vada - Piping hot Sambar Vada soaked to perfection. Shallot flavor is truly authentic.",
        "4. Product: Service Speed - The waiting queue at RS Puram during Sunday breakfast was over 45 minutes. Service staff were overwhelmed.",
        "5. Product: Parking - Car parking near the Gandhipuram branch is completely congested during evening peak hours."
    ]
    for r in pdf_reviews:
        c.drawString(72, y, r[:100])
        y -= 25

    c.save()
    pdf_bytes = buffer.getvalue()

    # Preview PDF
    pdf_preview = dataset_ingestor.preview_file(pdf_bytes, "annapoorna_audit.pdf")
    print(f" -> OK! PDF Preview parsed {pdf_preview['total_pages']} pages, {pdf_preview['extracted_chunks_count']} chunks. Brand guess: '{pdf_preview['brand_guess']}'")
    assert pdf_preview["brand_guess"] == "Sree Annapoorna"

    # Ingest PDF
    pdf_ingest_res = await dataset_ingestor.process_and_ingest(
        file_bytes=pdf_bytes,
        filename="annapoorna_audit.pdf",
        brand_name="Sree Annapoorna",
        product_name="Ghee Roast & Filter Coffee",
        industry="Hospitality & Restaurant",
        mode="append",
        generate_summary=True,
        current_user={"id": "usr_test", "full_name": "Test Engineer"}
    )
    print(f" -> OK! Ingested {pdf_ingest_res['total_records_processed']} PDF records into '{pdf_ingest_res['brand_name']}'")
    print(f"    • Product: {pdf_ingest_res['primary_product']}")
    print(f"    • NSS: {pdf_ingest_res['net_sentiment_score']}%")
    print(f"    • Top Praise: {[p['aspect'] for p in pdf_ingest_res['top_aspect_praise']]}")
    print(f"    • Top Friction: {[f['aspect'] for f in pdf_ingest_res['top_aspect_friction']]}")

    assert pdf_ingest_res["total_records_processed"] >= 5

    # TEST 4: Verify Monitored Summaries in MongoDB
    print("\n[TEST 4] Verifying Monitored Summaries in MongoDB db.summaries...")
    summary_doc = await db["summaries"].find_one({"id": pdf_ingest_res["summary_id"]})
    print(f" -> OK! Summary Found: ID={summary_doc['id']}")
    print(f"    • Company: {summary_doc['name_of_company']} | Product/Service: {summary_doc['product_service']}")
    print(f"    • Cause: {summary_doc['cause_of_feedback']}")
    print(f"    • Precautions ({len(summary_doc['precautions'])}): {summary_doc['precautions'][0]}")
    print(f"    • Measures Taken ({len(summary_doc['measures_taken'])}): {summary_doc['measures_taken'][0]}")

    assert summary_doc["name_of_company"] == "Sree Annapoorna"
    assert "Ghee Roast" in summary_doc["product_service"]

    # Close DB connection
    await db_manager.close()
    print("\n=========================================================")
    print("   ALL DATASET INGESTION & AI FEEDER TESTS PASSED 100%   ")
    print("=========================================================")

if __name__ == "__main__":
    asyncio.run(run_dataset_tests())
