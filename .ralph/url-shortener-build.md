# Build URL Shortener API

## Checklist
- [x] Project scaffolding: requirements.txt, .env.example, .gitignore
- [x] app/config.py — Settings with pydantic-settings
- [x] app/database.py — Async engine, session, init_db
- [x] app/models.py — Link + Click SQLModel models
- [x] app/schemas.py — Pydantic request/response schemas
- [x] app/utils.py — Base62, IP hashing, QR generation
- [x] app/auth.py — JWT creation + verification
- [x] app/rate_limit.py — In-memory rate limiter
- [x] app/routes/auth.py — POST /auth/login
- [x] app/routes/links.py — CRUD endpoints
- [x] app/routes/redirect.py — GET /{code}, GET /{code}/qr
- [x] app/routes/stats.py — GET /links/{code}/stats
- [x] app/main.py — FastAPI app, lifespan, routers
- [x] Dockerfile + docker-compose.yml
- [x] tests/conftest.py — Fixtures
- [x] tests/test_utils.py
- [x] tests/test_auth.py
- [x] tests/test_links.py
- [x] tests/test_redirect.py
- [x] tests/test_stats.py
- [x] Run all tests, verify passing

## Verification
- All 38 tests passing: `pytest tests/ -v` → 38 passed
- Fixed async session issue: `session.exec()` → `session.execute()` + `.scalars()`
- Fixed naive/aware datetime comparison for expiry checks
- All endpoints working: auth, CRUD, redirect, QR, stats

## Notes
- All items completed in a single pass with two bug fixes applied.
