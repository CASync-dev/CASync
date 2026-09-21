# AGENTS.md

## Working style

- Only write/modify code when explicitly asked. No feature creep; flag bugs/edge cases proactively.
- Vanilla-first: plain HTML5/CSS3/JS + jQuery over frameworks; Tailwind is the only CSS tooling.
- Prefer readable, commented code over clever optimizations; explain the *why* of non-obvious logic.
- If a request is ambiguous, stop and ask instead of guessing.

## Stack

Flask + Flask-SQLAlchemy (SQLite) + Flask-Migrate + Flask-Login + Flask-WTF (CSRF) + Flask-Limiter, Jinja2 templates, jQuery, Tailwind CSS. Frontend deps are npm-only (Tailwind CLI, browser-sync, prettier).

## Commands

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
npm install

flask db upgrade          # apply migrations to local app.db
python seed_demo.py       # seed dev data (see note below)

npm run watch:css         # tailwind -> static/css/output.css (gitignored)
python app.py             # dev server on :8080
npm run dev               # tailwind watch + app.py + browser-sync on :3000
```

- `seed.py` is **outdated and broken** (imports `from app import app, db`). Use `python seed_demo.py`.
- `static/css/output.css` is generated and gitignored — never edit it; edit `static/css/input.css`.

## Tests

```bash
python -m unittest                         # everything
python -m unittest tests.unittests         # unit tests only
python -m unittest tests.systemtests       # Selenium system tests only
python -m unittest tests.unittests.test_app  # single module
```

- **New test files must be imported in `tests/unittests/__init__.py` (or `tests/systemtests/__init__.py`)** or `unittest` discovers zero tests from them.
- System tests need Firefox (Selenium); headless by default. Set `HEADLESS=0` to watch. They boot Flask on `127.0.0.1:9000` in a thread.

## Gotchas

- **CSRF is global** (`CSRFProtect`). Every POST — including `fetch` from `static/js/*.js` — must send the CSRF token.
- **SQLite has no timezone storage.** Always write UTC; the `UTCDateTime` column type and `Event.to_dict()` re-attach UTC on read so the browser converts to local time. Don't compare naive vs aware datetimes.
- **Login requires `email_confirmed`.** The seeded demo accounts set it `True`; the `User` model defaults it `False`.
- **`RESEND_API_KEY` unset → emails logged to console** instead of sent; confirm/reset flows still work. `APP_BASE_URL` must match the port you run on (avoid macOS port 5000 — AirPlay).
- **Rate limiting** uses in-process memory storage (per-gunicorn-worker); only routes with `@limiter.limit` are throttled.
- **Microsoft SSO is optional** — the provider/button only appears if both `MICROSOFT_CLIENT_ID` and `MICROSOFT_CLIENT_SECRET` are set.

## Layout

- `app/` — app factory (`__init__.py`), config, models, forms, blueprints:
  - `app/loggedin/` + `app/loggedout/` — page routes (login, register, dash, settings, friends, groups, schedule)
  - `app/api/` — JSON APIs consumed by `static/js/*.js` (events, friends, groups, users, cal)
  - `app/errors/` — error handlers
- `services/` — non-route logic: `ical.py` (import/sync), `email.py`, `tokens.py` (signed confirm/reset tokens), `delacc.py`
- `templates/` — split into `loggedin/`, `loggedout/`, `email/`, `errors/`
- `migrations/` — Alembic versions; run `flask db migrate` after model changes, then `flask db upgrade`.
- Deployment (not needed locally): gunicorn via `Dockerfile`, `wsgi.py` wraps with `ProxyFix(x_for=2)` (Cloudflare + Caddy in front).
