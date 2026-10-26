# Official Meta / Instagram Graph API Integration Guide

This document provides complete instructions for configuring and deploying the official **Meta / Instagram Graph API** integration within BrandPulse AI.

---

## 1. Meta Developer Application Setup

To connect live Instagram accounts to BrandPulse AI:

1. Navigate to the [Meta for Developers Portal](https://developers.facebook.com/).
2. Log in with your Facebook account and click **My Apps** > **Create App**.
3. Select **Other** as the use case, then choose **Business** as the App Type.
4. Name your application (e.g. `BrandPulse AI Social Listening`) and link it to your Meta Business Manager.
5. In the App Dashboard, under **Add products to your app**, locate **Instagram Graph API** and click **Set Up**.
6. Also add **Facebook Login for Business**.

---

## 2. Required Instagram Account Type

The Instagram Graph API **does not support personal Instagram accounts**.

Your account must satisfy the following prerequisites:
1. **Professional / Business Account**: Convert your Instagram account to a Professional (Business or Creator) account in the Instagram Mobile App (`Settings > Account > Switch to Professional Account`).
2. **Linked Facebook Page**: Link your Instagram Professional account to a Facebook Page managed by your Meta Business Manager account (`Page Settings > Linked Accounts > Instagram > Connect Account`).

---

## 3. Required Permissions & Scopes

When initiating the Meta OAuth 2.0 flow, BrandPulse AI requests the following official scopes:

| Permission Scope | Purpose |
| :--- | :--- |
| `instagram_basic` | Read basic Instagram profile info, business account ID, and published media metadata. |
| `pages_show_list` | Discover user Facebook Pages that have linked Instagram Professional accounts. |
| `pages_read_engagement` | Read page engagement metrics and manage token handshakes. |
| `pages_manage_posts` | Access media streams and manage business post interactions. |
| `instagram_manage_comments` | Retrieve and analyze public user comments left on published Instagram media posts. |
| `instagram_manage_insights` | Access aggregated analytics, video view counts, and engagement metrics. |
| `public_profile` | Authenticate the Facebook Page administrator. |

---

## 4. OAuth 2.0 Flow Architecture

BrandPulse AI implements standard Meta OAuth 2.0 authorization with automatic 60-day token upgrading:

```
[ React Frontend ]
      ↓  1. Clicks "Connect Instagram" (GET /api/v1/instagram/auth-url)
[ Meta OAuth Dialog ]
      ↓  2. User approves permissions on Facebook / Instagram
[ Meta Redirect ]
      ↓  3. Redirects to backend callback with temporary authorization code
[ FastAPI Backend ]
      ↓  4. Exchanges code for short-lived access token
      ↓  5. Upgrades to long-lived 60-day access token (grant_type=fb_exchange_token)
      ↓  6. Discovers connected Instagram Business Account ID via /me/accounts
      ↓  7. Stores credentials securely in MongoDB Atlas (instagram_connections)
[ React Dashboard ]
      ↓  8. Displays "Instagram Connected" with active handle and sync controls
```

---

## 5. Backend Environment Variables Configuration

Create or update your backend `.env` file (`backend/.env`):

```bash
# Meta / Instagram Graph API Configuration
INSTAGRAM_APP_ID="your_meta_app_id"
INSTAGRAM_APP_SECRET="your_meta_app_secret"
INSTAGRAM_REDIRECT_URI="http://localhost:5173/brand-settings"
INSTAGRAM_ACCESS_TOKEN=""
INSTAGRAM_GRAPH_VERSION="v19.0"
INSTAGRAM_MOCK_MODE=false
```

> [!WARNING]
> **Security Notice**: Never expose `INSTAGRAM_APP_SECRET` or access tokens in frontend JavaScript. All token exchanges and API queries are performed server-side in Python FastAPI.

---

## 6. Valid OAuth Redirect URI Configuration

In the [Meta Developer Dashboard](https://developers.facebook.com/):
1. Navigate to **Facebook Login for Business** > **Settings**.
2. Under **Client OAuth Settings**, add your redirect URI to **Valid OAuth Redirect URIs**:
   - For local development: `http://localhost:5173/brand-settings`
   - For production: `https://your-brandpulse-domain.com/brand-settings`
3. Ensure **Enforce HTTPS** is enabled for production deployments.

---

## 7. Development & Testing Requirements (Mock Mode)

Because Meta requires formal App Review for production live business permissions:

- **Mock Mode (`INSTAGRAM_MOCK_MODE=true`)**: Enabled by default in development. Allows full simulation of the OAuth flow, data ingestion, Reel video transcripts, customer comments, and disambiguation test cases without needing live Meta API keys.
- **Development App Testing (`INSTAGRAM_MOCK_MODE=false`)**:
  - In Meta Developer Dashboard, go to **App Roles** > **Roles**.
  - Add the Facebook account of your testers/developers as **Administrators**, **Developers**, or **Testers**.
  - Testers can connect their own real Instagram Business accounts immediately without waiting for Meta App Review approval.

---

## 8. Production Requirements (Meta App Review)

Before launching BrandPulse AI to external business customers:
1. Submit your App for **Meta App Review** for the required permissions (`instagram_basic`, `pages_show_list`, `instagram_manage_comments`, `pages_read_engagement`).
2. Provide a screen recording demonstration of how BrandPulse AI uses the data for social listening and brand sentiment analysis.
3. Provide your Privacy Policy URL and Terms of Service URL in the Meta App settings.
4. Toggle App mode from **Development** to **Live**.

---

## 9. API Rate Limits & Quotas

The official Instagram Graph API imposes the following platform rate limits:
- **User-Level Limit**: 200 calls per user per hour in a rolling window.
- **Hashtag Search Limit**: Maximum of 30 unique hashtags per Instagram Business Account within any 7-day rolling window.
- **Error Handling**: BrandPulse AI monitors Graph API error response codes (`code: 4`, `code: 17`, `code: 190`) and gracefully throttles sync requests to prevent temporary API bans.

---

## 10. Data Access Boundaries: What the System Can and Cannot Access

### ✅ Permitted & Accessible Data:
- Published feed posts (images, carousels, video posts) on connected Instagram Business accounts.
- Published Instagram Reels (metadata, captions, like counts, view counts).
- Audio speech-to-text transcripts for permitted videos where accessible.
- Top-level public comments and replies left on the business's media.
- Public media where the connected Instagram Business account is `@mentioned` or tagged.
- Public recent media matching tracked brand `#hashtags`.

### ❌ Inaccessible & Prohibited (Zero-Scraping Compliance):
- Private Direct Messages (DMs) of other users.
- Private personal Instagram accounts that have not granted permission.
- Non-public stories that have expired or are restricted to Close Friends.
- Private audio streams protected by copyright or restricted permissions.
- Mass scraping of unrelated personal user profiles without authorization.

---

## 11. Pipeline Integration Verification

To test the entire pipeline:
```bash
cd backend
python test_instagram_pipeline.py
```
This runs automated unit and integration tests verifying:
- OAuth URL construction and simulated callback handling.
- Entity disambiguation (e.g. food fruit vs Apple technology).
- Context-aware sentiment and sarcasm classification.
- Video / Reel audio transcript ingestion.
- Granular aspect sentiment mapping (Battery, Camera, Display, Performance, Support).
