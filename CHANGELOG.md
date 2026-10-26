# Changelog

All notable changes to the **Advanced BrandPulse AI** platform are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.1.0] - 2026-10-15 - Small Business & Local Shop Transformation

### ⚠️ Breaking Changes & Renamed Concepts

#### 1. Concept & Terminology Overhaul (Enterprise to Local Business)
- **"Brands" & "Enterprises" Renamed to "Businesses" & "Local Shops"**:
  - Replaced abstract corporate hierarchy with real-world small business models: `business_type` (restaurant, bakery, salon, clinic, retail/kirana, supermarket).
  - Added physical multi-location support (`locations` array with street address, locality, city, pincode, Google Maps URL, and Place ID).
- **"Crisis Management & SOV" Replaced with Owner-Friendly Questions**:
  - Replaced fear-inducing enterprise metrics ("Threat Level: Critical", "PR Crisis Score", "Share of Voice") with 3 clear, actionable questions:
    1. **"What are customers saying?"** (Real sentiment breakdown, net satisfaction, top praise topics).
    2. **"What is going wrong?"** (Common friction points: cold food, billing delays, wait times, staff rudeness, parking issues).
    3. **"What should I do?"** (Prioritized, plain-English action items with 1-click WhatsApp customer reply templates).
- **"Competitor Intelligence" Replaced with "Nearby Shops"**:
  - Removed fictitious enterprise competitor defaults ("CloudScale AI", "Competitor A").
  - Owners now compare against 2–5 real nearby businesses (added manually, imported via Google Places API, or via CSV) tracking Google Maps ratings, review counts, and top praise/complaints.

#### 2. Authentication, Security & Token Handling
- **Client-Supplied Role Removed**:
  - Removed `role` parameter from client request schemas (`UserCreate`, `FirebaseUserAuth`).
  - Roles are assigned strictly server-side, preventing privilege escalation.
- **Token Security Architecture**:
  - Shortened access token validity to **30 minutes**.
  - Access tokens stored **in-memory only** on the frontend (eliminated localStorage storage).
  - Implemented secure HTTP-only SameSite refresh token cookies with automatic rotation via `/api/v1/auth/refresh`.
- **Mandatory `SECRET_KEY` Validation**:
  - Backend enforces minimum 32-character secret key at startup; fails fast on insecure default values.

#### 3. API Routing Consolidation & Removed Aliases
- **Single Mount Prefix (`/api/v1`)**:
  - Removed deprecated root-level duplicate routers and alias paths (`/listening`, `/conversations`, `/ai-insights`, `/ai_insights`, `/ai`, `/media`).
  - Removed dynamic `/system/db-connect` endpoint in favor of standard environment variable configuration.
- **Tenant Isolation**:
  - Every business, location, review, notification, and competitor endpoint strictly enforces user ownership via `get_brand_for_user()`.
  - Non-authorized cross-tenant requests return HTTP 404 or 403.

---

### 🚀 Major New Features

#### 1. Data Sources for Small Businesses & Local Shops
- **Google Places / Google Business Profile**:
  - Ingests real customer reviews, star ratings, and photo counts.
  - Includes realistic simulated fallback for local restaurants, bakeries, salons, and retail stores when API key is unconfigured.
- **Instagram Business Integration**:
  - Meta Graph API client syncs Reels, posts, and customer comments.
- **Bulk CSV / Excel Review Importer**:
  - Interactive file upload supporting Zomato, Swiggy, Amazon, and Google review exports with column auto-detection and data preview.
- **WhatsApp Voice Note & Audio Feedback Transcripts**:
  - Ingests and transcribes voice notes and spoken audio feedback using multilingual speech-to-text models or simulated transcript fallbacks.

#### 2. Multilingual Analysis (Tanglish, Hinglish, Tamil, Hindi, English)
- **Code-Mixed Sentiment & Intent Analysis**:
  - Built-in lexicon and rules for Romanized Indian languages: Tanglish ("sappaadu semma taste aana bill romba late") and Hinglish ("khana bahut accha tha lekin service thoda slow hai").
  - Language detection for Devanagari Hindi (`hi`), Tamil script (`ta`), and code-mixed Latin scripts.
  - Hybrid LLM support (Groq, Gemini, OpenAI, Claude, Ollama) alongside zero-cost local Scikit-Learn models.

#### 3. AI Chatbot Assistant ("Ask AI")
- **Context-Aware Business Assistant**:
  - Non-technical shop owners can converse in English, Hindi, Tamil, Hinglish, or Tanglish.
  - Answers questions like "Why was my rating low this week?", "What are customers saying about the biryani?", and drafts polite, professional customer responses ready for WhatsApp.

#### 4. Multi-Channel Notifications & Weekly Summaries
- **Instant Alerts for 1–2 Star Reviews**:
  - Automated dispatch via Resend/SMTP email and Twilio WhatsApp/SMS with configurable opt-ins.
- **Complaint Spike Alerts**:
  - Alerts the owner when recurring complaints (e.g., "slow service") surge within a short window.
- **Weekly AI WhatsApp Digest**:
  - Scheduled Monday morning briefing summarizing customer sentiment, top praise, and high-priority action items.

#### 5. Quotas, Plan Limits & Cost Control
- **Tiered Quotas**:
  - Free Tier: 1 business, 100 reviews/month, 20 AI chat queries/month.
  - Pro Tier: 10 businesses, 5,000 reviews/month, 500 AI chat queries/month.
  - User-friendly HTTP 402 Upgrade Required responses with remaining quota headers.
- **Intelligent Response Caching**:
  - In-memory TTL caching for LLM responses and translations to eliminate redundant API expenditures.

#### 6. Mobile-First UI/UX Redesign
- **Phone-First Navigation**:
  - Floating bottom navigation bar on mobile devices (Home, Reviews, Ask AI, Nearby, Settings).
  - High-contrast, large-touch targets optimized for busy shop owners on smartphones.
  - Prominent "Demo Data" indicators on simulated reviews to maintain absolute transparency.

---

## [2.0.0] - 2026-10-14 - Security & Foundation Hardening

### 🔒 Security & Architecture
- Enforced cryptographic verification for Firebase ID tokens.
- Upgraded password hashing to `bcrypt` with per-user salt.
- Configured distributed rate limiting via `slowapi` with Redis backing and trusted proxy IP resolution.
- Separated simulated data via `is_simulated=true` flags and `DEMO_MODE=false` production controls.
- Added structured logging with unique `request_id` tracking across requests.
- Added pluggable storage abstraction (`LocalStorage` and `S3Storage`).
- Created multi-stage Docker builds and root `docker-compose.yml`.
