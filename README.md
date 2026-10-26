# BrandPulse AI 🏪
### Real-World AI Customer Feedback & Reputation Intelligence for Small Businesses & Local Shops

BrandPulse AI turns customer reviews, social media posts, and voice notes into simple, actionable answers for small business owners (restaurants, bakeries, salons, clinics, kirana stores, and supermarkets). Built with a high-performance **FastAPI** backend, **React 18** mobile-first frontend, **MongoDB** database, and hybrid **Multilingual NLP / LLM** intelligence, BrandPulse AI helps non-technical owners instantly answer three fundamental questions:

1. **What are customers saying?** (Real sentiment, net satisfaction score, top praise)
2. **What is going wrong?** (Top friction points like billing delays, cold food, wait times, staff rudeness)
3. **What should I do?** (Prioritized action items and 1-click WhatsApp customer reply templates)

---

## 🌟 Key Features

- **📱 Phone-First Design for Busy Owners**: Clean, high-contrast UI with a mobile bottom navigation bar designed for quick one-handed check-ins. No corporate jargon or confusing dashboards.
- **🇮🇳 Multilingual & Code-Mixed Feedback**: Native support for feedback written in English, Tamil, Tanglish (*"sappaadu semma taste aana bill romba late"*), Hindi, and Hinglish (*"khana accha tha lekin service slow hai"*).
- **🗺️ Real Local Data Sources**:
  - **Google Places / Business Profile**: Direct sync for Google Maps reviews, ratings, and photos (with realistic simulated mock mode).
  - **Instagram Business (Meta Graph API)**: Syncs Instagram Reels, posts, and customer comments.
  - **Bulk CSV / Excel Review Importer**: Auto-detects columns from Zomato, Swiggy, Amazon, and Google review exports.
  - **WhatsApp Voice Note Transcripts**: Transcribes spoken audio feedback and customer voice messages into structured sentiment.
- **🤖 "Ask AI" Shop Assistant**: An intelligent chatbot that answers shop-specific questions ("Why did ratings drop this week?", "What do people think of the filter coffee?") and generates polite customer replies ready to copy into WhatsApp.
- **📍 Nearby-Shop Comparisons**: Benchmark against 2–5 real nearby shops (added manually, via Google Places, or via CSV) without fake or hardcoded competitor names.
- **🔔 Real-Time Notifications**: Instant alerts for 1–2 star negative reviews and recurring complaint spikes via Email (Resend / SMTP) and WhatsApp/SMS (Twilio), plus an automated Monday morning AI summary.
- **🛡️ Tenant Isolation & Plan Quotas**: Strict multi-tenant isolation, tiered monthly usage quotas (Free vs Pro), and intelligent response caching to minimize LLM and translation API costs.
- **🐳 Full Docker & Compose Stack**: Production-ready multi-stage containers (FastAPI, React + Nginx, MongoDB, optional Redis) with integrated automated healthchecks.

---

## 🏗️ Architecture & Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | React 18, Vite 6, Tailwind CSS, TanStack React Query, Lucide Icons, Recharts, Axios |
| **Backend** | Python 3.10+, FastAPI, Motor (Async MongoDB), Pydantic v2 Settings, PyJWT, Bcrypt, SlowAPI |
| **NLP & AI Engine** | Local Scikit-Learn models, VADER Sentiment, Indic/Code-mixed lexicons, XLM-RoBERTa, plus optional Hybrid LLM (Groq, Gemini, OpenAI, Claude, Ollama) |
| **Database & Cache** | MongoDB 6.0+ (Atlas or local), In-memory TTL cache & optional Redis |
| **Storage Layer** | Local Filesystem or AWS S3 / MinIO / LocalStack (via Boto3) |
| **Notifications** | Resend / SMTP for Email, Twilio for WhatsApp & SMS |
| **DevOps / Containers**| Multi-stage Docker, Nginx, Docker Compose with healthchecks |

---

## 📂 Project Structure

```text
Advanced Brandpulse AI/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST Endpoints (auth, brands, monitoring, assistant, competitors, notifications, billing)
│   │   ├── core/            # Config, Security/JWT, Database, Logging, Storage, Firewall, Caching
│   │   ├── datasets/        # Datasets (Apple Kaggle, Annapoorna Hospitality)
│   │   ├── integrations/    # Meta/Instagram Graph API client
│   │   ├── ml/              # Model pipelines, retraining studio, and evaluation metrics
│   │   ├── models/          # Serialized ML models (.joblib) and vectorizers
│   │   ├── schemas/         # Pydantic schemas and DTOs
│   │   └── services/        # AI engine, notifications, plan limits, assistant RAG, dataset ingestor
│   ├── scripts/             # Model training, dataset generation, and Git LFS download script
│   ├── storage/             # Runtime local report and upload storage
│   ├── tests/               # 69 automated Pytest unit and integration tests
│   ├── Dockerfile           # Backend container (Python 3.10-slim)
│   ├── main.py              # Backend application entry point
│   ├── requirements.txt     # Production dependencies
│   ├── requirements-dev.txt # Testing dependencies
│   └── .env.example         # Backend environment configuration template
├── frontend/
│   ├── src/
│   │   ├── components/      # Modular UI components (dashboard, assistant, settings, dataset, competitors)
│   │   ├── context/         # AuthContext & BrandContext providers
│   │   ├── hooks/           # Custom React Query hooks
│   │   ├── pages/           # Views (Dashboard, Ask AI, SocialListening, CompetitorAnalysis, BrandSettings, etc.)
│   │   └── services/        # Centralized Axios API client and Firebase integration
│   ├── Dockerfile           # Multi-stage frontend container (Node 20 build -> Nginx Alpine)
│   ├── nginx.conf           # Production Nginx reverse proxy configuration
│   ├── package.json         # Frontend dependencies and build scripts
│   ├── vite.config.js       # Vite configuration
│   └── .env.example         # Frontend environment configuration template
├── docker-compose.yml       # Complete stack orchestration (api, mongo, frontend, redis)
├── .gitattributes           # Git LFS tracking for .joblib models and datasets
├── CHANGELOG.md             # Version history and breaking change log
├── README.md                # Project documentation and setup guide
└── test_e2e.py              # End-to-end verification script
```

---

## ⚙️ Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Default | Description |
| :--- | :---: | :--- | :--- |
| `SECRET_KEY` | **Yes** | *None* | JWT signing secret (**must be at least 32 characters**). |
| `MONGODB_URI` | **Yes** | `mongodb://localhost:27017` | MongoDB connection URI (Local or MongoDB Atlas). |
| `DATABASE_NAME` | No | `brandpulse_ai` | Target MongoDB database name. |
| `PORT` | No | `8000` | Backend listening port. |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| No | `30` | JWT Access Token lifetime in minutes. |
| `CORS_ORIGINS` | No | `http://localhost:5173,...` | Comma-separated list of allowed CORS origins. |
| `DEMO_MODE` | No | `false` | When `false`, disables fake synthetic data generation. |
| `REDIS_URL` | No | `redis://localhost:6379/0` | Optional Redis URL for distributed rate limiting & caching. |
| `ANALYSIS_BACKEND` | No | `local` | `local` (fast ML), `hybrid` (local + LLM fallback), or `llm`. |
| `LLM_PROVIDER` | No | `local` | `local`, `groq`, `gemini`, `openai`, `claude`, or `ollama`. |
| `LLM_API_KEY` | If LLM | *Empty* | API key for selected LLM provider. |
| `LLM_MODEL` | If LLM | *Empty* | Model name (e.g., `llama-3.3-70b-versatile` or `gemini-1.5-flash`). |
| `GOOGLE_PLACES_API_KEY` | No | *Empty* | Google Places API key for real Maps reviews. |
| `GOOGLE_BUSINESS_MOCK_MODE`| No | `true` | When `true`, provides realistic simulated reviews. |
| `RESEND_API_KEY` | No | *Empty* | Resend API key for email notification delivery. |
| `NOTIFICATION_FROM_EMAIL` | No | `alerts@brandpulse.local` | From email address for customer review alerts. |
| `TWILIO_ACCOUNT_SID` | No | *Empty* | Twilio Account SID for WhatsApp and SMS alerts. |
| `TWILIO_AUTH_TOKEN` | No | *Empty* | Twilio Auth Token. |
| `NOTIFICATION_MOCK_MODE`| No | `true` | When `true`, records notifications in memory without third-party API keys. |
| `STORAGE_BACKEND` | No | `local` | Storage driver: `local` (disk) or `s3` (AWS S3 / MinIO). |

### Frontend (`frontend/.env`)

| Variable | Required | Default | Description |
| :--- | :---: | :--- | :--- |
| `VITE_API_URL` | No | `http://127.0.0.1:8000/api/v1` | Backend API Base URL (`/api/v1` in Docker). |
| `VITE_FIREBASE_*` | No | *Empty* | Optional Firebase client credentials for OAuth. |

---

## 🚀 Quick Start with Docker Compose

Run the entire application stack (MongoDB, Redis, FastAPI backend, and Nginx-served React frontend) with a single command:

1. **Clone the repository and prepare environment files:**
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   ```
   *Edit `backend/.env` to provide a secure `SECRET_KEY` (minimum 32 characters).*

2. **Launch all services:**
   ```bash
   docker compose up --build
   ```

3. **Access the application:**
   - **Frontend Application**: [http://localhost](http://localhost) (Port 80)
   - **Backend API**: [http://localhost:8000](http://localhost:8000)
   - **Interactive Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **System Healthcheck**: [http://localhost:8000/health](http://localhost:8000/health)

4. **Stop services:**
   ```bash
   docker compose down
   ```

---

## 💻 Manual Local Development

### 1. Backend Setup

```bash
cd backend

# Create and activate Python virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Download ML models or pull via Git LFS
python scripts/download_models.py

# Configure environment
cp .env.example .env

# Run FastAPI backend server
uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend

# Install Node dependencies
npm install

# Configure environment
cp .env.example .env

# Start Vite development server
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🧪 Testing & Verification

### Run Pytest Test Suite
The backend features 69 automated unit, integration, and security tests covering authentication, tenant isolation, multilingual sentiment, nearby-shop comparisons, plan limits, and notifications:

```bash
cd backend
pytest -v
```

### Run Frontend Build Validation
Verify production bundling and asset compilation:

```bash
cd frontend
npm run build
```

---

## 🔒 Security & Data Integrity

- **Tenant Isolation**: Every business, location, review, notification, and competitor record enforces user ownership via `get_brand_for_user()`.
- **In-Memory JWT & Secure Cookies**: Access tokens are kept in-memory; refresh tokens are stored in secure HTTP-only cookies with automatic rotation.
- **Cryptographic Verification**: Third-party OAuth tokens (e.g., Firebase) are cryptographically validated against provider keys; client-specified roles are discarded.
- **Simulated Data Transparency**: Any synthetic or demo review carries `is_simulated: true` and displays a visible "Demo data" badge in the UI.

---

## 📄 License

This project is licensed under the MIT License.
