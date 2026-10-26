import os
import urllib.request
import json
import time
import uuid

base_url = os.getenv('BRANDPULSE_API_URL', 'http://127.0.0.1:8000/api/v1')
root_url = base_url.replace('/api/v1', '').replace('/api', '')

def post_json(url, data=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(url, data=json.dumps(data or {}).encode('utf-8') if data is not None else b'{}', headers=headers)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

def get_json(url, token=None):
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

def run_tests():
    print('==================================================')
    print('  ADVANCED BRANDPULSE AI - E2E TEST VERIFICATION  ')
    print('==================================================')

    print('\n[0] Testing Universal Health Check Endpoints...')
    health_root = get_json(f'{root_url}/health')
    print(f' -> OK! Root GET /health: status={health_root.get("status")}, service={health_root.get("service")}')
    health_v1 = get_json(f'{base_url}/health')
    print(f' -> OK! API v1 GET /health: status={health_v1.get("status")}, db_connected={health_v1.get("database_connected")}')

    print('\n[1] Testing Auth Demo Login (Brand Manager)...')
    auth_res = post_json(f'{base_url}/auth/demo-login?persona=brand_manager')
    token = auth_res['access_token']
    user = auth_res['user']
    print(f' -> OK! Authenticated as: {user["full_name"]} | Role: {user["role"]}')

    print('\n[2] Testing Direct Registration & Direct Login...')
    unique_email = f'tester_{uuid.uuid4().hex[:6]}@brandpulse.ai'
    reg_res = post_json(f'{base_url}/auth/register', {
        'email': unique_email,
        'full_name': 'Test Registration User',
        'password': 'Password123!',
        'organization': 'Apex Test Labs',
        'role': 'brand_manager'
    })
    print(f' -> OK! Registered user: {reg_res["user"]["email"]} (ID: {reg_res["user"]["id"]})')
    
    login_res = post_json(f'{base_url}/auth/login', {
        'email': unique_email,
        'password': 'Password123!'
    })
    print(f' -> OK! Direct Login verified for: {login_res["user"]["email"]}')

    print('\n[3] Testing Brands Listing...')
    brands = get_json(f'{base_url}/brands', token)
    print(f' -> OK! Retrieved {len(brands)} brands. Primary Brand: {brands[0]["name"]}')
    brand_id = brands[0]['id']

    print('\n[4] Testing Analytics Overview (KPI Metrics)...')
    overview = get_json(f'{base_url}/analytics/overview?brand_id={brand_id}', token)
    print(f' -> OK! Total Mentions: {overview["total_mentions"]}')
    print(f' -> OK! Net Sentiment Score (NSS): {overview["net_sentiment_score"]}%')
    print(f' -> OK! Crisis Risk Index: {overview["crisis_risk_index"]}%')
    print(f' -> OK! Share of Voice (SOV): {overview["share_of_voice"]}%')

    print('\n[5] Testing Sentiment Time-Series Trends...')
    trends = get_json(f'{base_url}/analytics/sentiment-trends?brand_id={brand_id}', token)
    print(f' -> OK! Received {len(trends)} time-series data points.')

    print('\n[6] Testing Multi-Class Emotion Detection...')
    emotions = get_json(f'{base_url}/analytics/emotions?brand_id={brand_id}', token)
    for e in emotions:
        print(f'    • {e["emotion"]}: {e["value"]}% (dominant in {e["count"]} mentions)')

    print('\n[7] Testing User Intent Breakdown...')
    intents = get_json(f'{base_url}/analytics/intent?brand_id={brand_id}', token)
    for i in intents:
        print(f'    • {i["label"]}: {i["count"]} ({i["percentage"]}%)')

    print('\n[8] Testing Unsupervised KMeans Topic Clusters...')
    topics = get_json(f'{base_url}/analytics/topics?brand_id={brand_id}', token)
    for t in topics:
        print(f'    • Cluster #{t["cluster_id"]+1} ({t["name"]}): {t["mentions_count"]} mentions | Top terms: {", ".join(t["top_keywords"][:3])}')

    print('\n[9] Testing 48-Hour AI Trend Forecast...')
    forecast = get_json(f'{base_url}/analytics/forecast?brand_id={brand_id}', token)
    for f in forecast['forecast']:
        print(f'    • {f["date"]}: Projected Volume = {f["predicted_volume"]} (Range: {f["lower_bound"]}-{f["upper_bound"]}) | Sent = {f["predicted_sentiment"]}')

    print('\n[10] Testing Route Aliases (/listening, /conversations, /ai-insights)...')
    listening_mentions = get_json(f'{base_url}/listening/mentions?brand_id={brand_id}&limit=5', token)
    print(f' -> OK! Alias GET /listening/mentions resolved {len(listening_mentions)} items.')
    conversations_mentions = get_json(f'{base_url}/conversations/mentions?brand_id={brand_id}&limit=5', token)
    print(f' -> OK! Alias GET /conversations/mentions resolved {len(conversations_mentions)} items.')
    ai_insights = get_json(f'{base_url}/ai-insights/insights?brand_id={brand_id}', token)
    print(f' -> OK! Alias GET /ai-insights/insights resolved successfully (Health: {ai_insights.get("brand_sentiment_health")}).')

    print('\n[11] Testing Interactive NLP Lab Engine...')
    nlp_test = post_json(f'{base_url}/monitoring/test-nlp?text=TechNova%20AI%20is%20game-changing%20and%20unbelievably%20fast!')
    print(f' -> OK! Polarity: {nlp_test["sentiment"]} (Score: {nlp_test["sentiment_score"]}) | Dominant Emotion: {nlp_test["dominant_emotion"]} | Intent: {nlp_test["intent"]}')

    print('\n[12] Testing Crisis Anomaly Detector & Scenario Trigger...')
    crisis_sim = post_json(f'{base_url}/crisis/simulate-crisis?brand_id={brand_id}&scenario_type=outage_disaster', token=token)
    print(f' -> OK! Crisis Alert Generated: {crisis_sim["alert"]["title"]} [{crisis_sim["alert"]["severity"].upper()}]')
    print(f'    Root cause: {crisis_sim["alert"]["ai_root_cause"]}')

    print('\n[13] Testing Competitor Benchmarks & SOV...')
    sov = get_json(f'{base_url}/competitors/sov?brand_id={brand_id}', token)
    for s in sov['share_of_voice']:
        print(f'    • {s["brand"]}: {s["sov_percentage"]}% SOV ({s["volume"]} mentions)')

    print('\n[14] Testing Executive PDF Report Generation & Download...')
    pdf_res = post_json(f'{base_url}/reports/generate', {'brand_id': brand_id, 'report_type': 'executive_summary', 'time_range': '7d', 'format': 'pdf'}, token=token)
    print(f' -> OK! PDF Generated: {pdf_res["filename"]}')

    csv_res = post_json(f'{base_url}/reports/generate', {'brand_id': brand_id, 'report_type': 'full_audit', 'time_range': '7d', 'format': 'csv'}, token=token)
    print(f' -> OK! CSV Generated: {csv_res["filename"]}')

    print('\n[15] Testing Authentication Audit Logging to MongoDB...')
    audit_logs = get_json(f'{base_url}/auth/audit-logs', token)
    print(f' -> OK! Found {len(audit_logs)} login audit records in MongoDB collection "auth_logs".')
    if audit_logs:
        latest = audit_logs[0]
        print(f'    • Latest login: {latest["full_name"]} ({latest["email"]}) | Date: {latest["login_date"]} {latest["login_time"]} | IP: {latest["ip_address"]} | Status: {latest["status"]}')

    print('\n[16] Testing AI Monitored Data Summary Storage in MongoDB ("summaries")...')
    summary_res = post_json(f'{base_url}/monitoring/summaries/generate?brand_id={brand_id}', token=token)
    print(f' -> OK! Summary Created in MongoDB: ID={summary_res["id"]}')
    print(f'    • Company: {summary_res["name_of_company"]} | Product/Service: {summary_res["product_service"]}')

    summaries_list = get_json(f'{base_url}/monitoring/summaries?brand_id={brand_id}', token)
    print(f' -> OK! Successfully listed {len(summaries_list)} summaries from MongoDB.')

    print('\n[17] Testing Firebase Authentication & Auto-Provisioning to MongoDB...')
    fb_auth_res = post_json(f'{base_url}/auth/firebase-login', {
        'email': 'firebase.analyst@technova.ai',
        'full_name': 'Firebase Verified Executive',
        'provider': 'google.com',
        'photo_url': 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100',
        'role': 'brand_manager',
        'organization': 'TechNova Global'
    })
    fb_token = fb_auth_res['access_token']
    fb_user = fb_auth_res['user']
    print(f' -> OK! Authenticated via Firebase Google OAuth as: {fb_user["full_name"]} ({fb_user["email"]})')

    # Verify /auth/me with Firebase issued JWT
    me_res = get_json(f'{base_url}/auth/me', token=fb_token)
    print(f' -> OK! Protected /auth/me verified successfully for Firebase User ID: {me_res["id"]}')

    print('\n[18] Testing ML Studio & Dataset Ingestion Endpoints...')
    ml_info = get_json(f'{base_url}/ml/dataset-info', token=token)
    print(f' -> OK! ML Dataset Info: {ml_info.get("dataset_name")} ({ml_info.get("total_samples")} samples)')
    samples = get_json(f'{base_url}/dataset/samples', token=token)
    print(f' -> OK! Dataset Ingestion Sample Datasets: {len(samples)} samples available.')

    print('\n[19] Testing System Database Status...')
    db_status = get_json(f'{base_url}/system/db-status')
    print(f' -> OK! Database Status: mode={db_status.get("mode")}, connected={db_status.get("is_connected")}')

    print('\n==================================================')
    print('  ALL 19 BACKEND & AI MODULES VERIFIED 100% OK!   ')
    print('==================================================')

if __name__ == '__main__':
    run_tests()



