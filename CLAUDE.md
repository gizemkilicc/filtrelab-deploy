# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Dev Commands

**Backend** (FastAPI on port 8000):
```bash
cd backend && source .venv/bin/activate && python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
API docs: http://127.0.0.1:8000/docs

**Frontend** (Next.js on port 3000):
```bash
cd frontend && npm run dev
```

**TypeScript check:**
```bash
cd frontend && npx tsc --noEmit
```

**Lint:**
```bash
cd frontend && npx eslint
```

There is no test framework configured. Use the Python venv at `backend/.venv/`; `python` may not be in PATH on macOS — use `.venv/bin/python` directly.

## Key Env Vars

`backend/.env`:
- `DATABASE_URL` — PostgreSQL connection string (required; e.g. `postgresql://user@localhost:5432/filterlab`)
- `MAX_REVIEWS` — pagination limit for review scraping (default 1000, production sets 5000)
- `JWT_SECRET` — JWT signing key
- SMTP vars for password reset emails

`frontend/.env.local`:
- `NEXT_PUBLIC_API_URL` — backend URL (defaults to `http://127.0.0.1:8000`)

## Architecture

### Request Pipeline

`POST /analyze` → `routes/analyze.py` → `mock_ai.generate_analysis(url, include_reviews)` → scraper → scoring → text generation → response

1. **Platform detection** (`services/platform_detector.py`) — maps URL to `trendyol | hepsiburada | amazon_tr` or raises
2. **Scraping** (`services/product_scraper.py`) — routes to platform-specific scraper, returns normalized dict
3. **Category detection** (`services/category_detector.py`) — NLP on product name + breadcrumb
4. **Alternatives** (`services/alternative_scraper.py`) — same-platform search by category
5. **Scoring** (`services/scoring_engine.py`) — data-driven scores (no LLM); `services/scoring.py` is legacy
6. **Text generation** (`services/text_generator.py`) — template-based Turkish copy from scores
7. **Response assembly** (`services/mock_ai.py`) — normalizes everything, builds final JSON

### Scraper Architecture

Each platform scraper (`trendyol_scraper.py`, `hepsiburada_scraper.py`, `amazon_scraper.py`) uses Playwright headless Chromium. They all return a dict with:
- Product fields: `productName, brand, price, image, rating, reviewCount, questionCount, sellerScore, category`
- `reviews: list[dict]` — full objects `{id, text, rating, date, user, source}`
- `reviewStats: dict` — `{reviewCount, reviewsLoaded, dedupedCount, completed, maxReviews, source, reason}` plus optional `apiTotalCount`, `platformLimitReached`
- `dataSource: dict` — per-field extraction method (json_ld, api, dom, etc.)

**Review pagination**: `MAX_REVIEWS` env var controls the ceiling. Scrapers detect platform limits (when API stops at ~3000 even if `totalCount=18403`) and set `platformLimitReached=True, completed=False, reason="platform_limit_reached"`.

**Review format**: Scrapers return `list[dict]`, scoring engine expects `list[str]`. `mock_ai._extract_review_texts()` bridges this.

Amazon gracefully fails review loading — returns `reviewStats.error = "reviews_could_not_be_loaded"`, never crashes.

### Review Endpoints

- `POST /reviews` — returns full reviews for a URL (calls `scrape_product` with `max_reviews`)
- `POST /reviews/export` — AI-team-friendly export: `{product, reviews, reviewStats}` clean dataset

### Auth System

JWT-based, routes in `routes/auth.py`, logic in `services/auth_service.py`, **PostgreSQL** via SQLAlchemy (`services/database.py`). Token stored in `localStorage` as `filtre_token`.

PostgreSQL setup (local dev with Postgres.app): create database `filterlab` and set `DATABASE_URL=postgresql://<user>@localhost:5432/filterlab` in `backend/.env`. `init_db()` on startup runs `create_all` to create/migrate tables. For production use Alembic migrations (`alembic` is installed).

User features (price tracking, favorites, analysis history) in `routes/user_features.py` — all require Bearer token.

### Frontend Architecture

Next.js 16 App Router. Pages: `/` (landing, `app/page.tsx`) and `/dashboard` (`app/dashboard/page.tsx`).

**Data flow**: User submits URL → `apiClient.runAIAnalysis()` → polls animation steps while fetch runs → stores result in `localStorage` as `filtre_last_analysis` → renders result components.

**Chatbot**: `components/ui/Chatbot.tsx` — floating widget on all pages. Reads `filtre_last_analysis` from localStorage to provide product context. Chat history persisted in `filtre_chat_history`. Opens via `window.dispatchEvent(new CustomEvent("filtre:open-chatbot"))`.

**Custom events**:
- `filtre-auth-changed` — fired on login/logout, navbar listens
- `filtre:open-chatbot` — fired by "Asistanı Keşfet" button, Chatbot listens

**Landing page input**: Hidden on load. "Filtrelemeye Başla" button reveals it with `AnimatePresence` animation + smooth scroll + auto-focus. `?url=` query param auto-reveals and pre-fills the input.

All API calls go through `lib/apiClient.ts`. Auth headers injected via `getAuthHeaders()`.
