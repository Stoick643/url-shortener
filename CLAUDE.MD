# Advanced URL Shortener API

Self-hosted TinyURL competitor with analytics – lightweight and private.

## Tech Stack

- **Framework**: FastAPI (async, auto-generates OpenAPI docs at `/docs`)
- **ORM**: async SQLAlchemy + SQLModel
- **Database**: SQLite (single file `db.sqlite3`, mounted as volume)
- **QR codes**: `qrcode` + Pillow
- **Short codes**: Base62 encoding, 8 characters (62⁸ ≈ 218 trillion codes)
- **Containerization**: Docker + docker-compose

## Features

### URL Shortening
- Shorten any URL → get 8-char Base62 short code (e.g. `myapp.com/dK9xQ2aB`)
- Custom vanity slugs: 3-30 chars, alphanumeric + hyphens (`^[a-zA-Z0-9-]+$`)
- Reserved slugs blocklist: `docs`, `api`, `admin`, `auth`, `health`, `static`
- Unique constraint on all slugs (generated + vanity)
- Base URL configured via `BASE_URL` env var (e.g. `https://myapp.com`)

### Redirects
- `GET /{code}` → **302 (temporary)** redirect to original URL
- Temporary redirect ensures every click is tracked (no browser caching)
- No rate limiting on redirects — keep them fast and frictionless

### QR Codes
- `GET /{code}/qr` → returns **PNG image** (300×300px, `image/png`)
- Also available as base64 string in API responses
- Library: `qrcode` + Pillow

### Click Analytics
- Total clicks per link
- Unique clicks (approximate, via hashed IP)
- Referrer (from `Referer` header)
- Country: from `CF-IPCountry` header (Cloudflare), fallback `X-Country`, else `unknown`
- Timestamp per click

### Link Management (Dashboard)
- List all links: offset-based pagination, default 20 per page (`?page=1&per_page=20`)
- Edit link expiry
- Soft delete: sets `is_active=false`, returns **410 Gone** on redirect (preserves analytics)
- View stats per link

### Expiry Options
- Never (default)
- Custom expiry date
- Max clicks reached (auto-expire after N clicks)

### Authentication
- Single admin user via env vars: `ADMIN_USERNAME` + `ADMIN_PASSWORD`
- `POST /auth/login` → returns JWT
- Admin-only routes protected by JWT
- API key support deferred to v2

### Rate Limiting
- Public shorten endpoint: **5 requests per minute per IP**
- In-memory or DB-based (no external cache needed)
- Admin (JWT-authenticated) requests exempt from rate limit

## Database Schema

### Table: `links`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` PK | Auto-increment |
| `short_code` | `VARCHAR(30)` | Unique, indexed. 8-char generated or vanity slug |
| `original_url` | `TEXT` | The target URL |
| `is_vanity` | `BOOLEAN` | `false` for generated, `true` for custom slugs |
| `is_active` | `BOOLEAN` | `true` by default, `false` = soft deleted |
| `expires_at` | `DATETIME` | Nullable. `null` = never expires |
| `max_clicks` | `INTEGER` | Nullable. `null` = unlimited |
| `total_clicks` | `INTEGER` | Default `0`. Denormalized counter for fast reads |
| `created_at` | `DATETIME` | Auto-set |
| `updated_at` | `DATETIME` | Auto-updated |

### Table: `clicks`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` PK | Auto-increment |
| `link_id` | `INTEGER` FK | References `links.id`, indexed |
| `ip_hash` | `VARCHAR(64)` | SHA-256 of IP. For unique click approximation |
| `referrer` | `TEXT` | Nullable. From `Referer` header |
| `country` | `VARCHAR(10)` | `unknown` if not available |
| `clicked_at` | `DATETIME` | Auto-set |

### Design Notes
- `total_clicks` on `links`: denormalized counter, avoids `COUNT(*)` on every stats request
- `ip_hash`: SHA-256 of IP, never store raw IPs. Unique clicks = `COUNT(DISTINCT ip_hash)`
- Indexes: `short_code` (unique), `link_id` on clicks, `clicked_at` on clicks
- No cache layer: SQLite is fast enough for hobby-scale traffic
- Rate limiting: simple in-memory dict (IP → timestamps), no DB table needed

## Requirements

- Clean Swagger/OpenAPI docs at `/docs`
- Full pytest coverage (unit + integration tests)
- Deployment-friendly: single container, persistent volume for `db.sqlite3`
- Docker + docker-compose for local dev/testing

## Project Structure

```
url-shortener/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, lifespan, middleware
│   ├── config.py            # Settings from env vars (pydantic-settings)
│   ├── database.py          # Async engine, session factory, init_db
│   ├── models.py            # SQLModel: Link, Click
│   ├── auth.py              # JWT creation, verification, admin login
│   ├── rate_limit.py        # In-memory rate limiter middleware
│   ├── utils.py             # Base62 encoding, IP hashing, QR generation
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py          # POST /auth/login
│   │   ├── links.py         # CRUD: create, list, update, delete links
│   │   ├── redirect.py      # GET /{code} → 302, GET /{code}/qr → PNG
│   │   └── stats.py         # GET /links/{code}/stats
│   └── schemas.py           # Pydantic request/response models
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Fixtures: test client, test DB
│   ├── test_auth.py
│   ├── test_links.py
│   ├── test_redirect.py
│   ├── test_stats.py
│   └── test_utils.py
├── data/
│   └── db.sqlite3           # Created at runtime, gitignored
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── CLAUDE.md
```

- Database path defaults to `data/db.sqlite3` (configured in `config.py`)
- `data/` mounted as Docker volume for persistence, excluded from git

## Deferred to v2
- API key support for programmatic shortening
- Multi-tenant custom domain routing
- Configurable QR code size
- GeoIP lookup (instead of header-based country detection)
