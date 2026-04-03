# AGENTS.md

## Cursor Cloud specific instructions

### Overview

Real Estate KSA is a Django REST API + React (Vite) property management platform for the Saudi Arabia market. See `README.md` for full setup and commands.

### Services

| Service | Command | Port | Notes |
|---------|---------|------|-------|
| Django backend | `source .venv/bin/activate && python manage.py runserver 0.0.0.0:8000` | 8000 | Must start before frontend API calls work |
| Vite frontend | `npm run dev --prefix frontend -- --host 0.0.0.0` | 5173 | Proxies `/api` → backend via `vite.config.js` |
| PostgreSQL | `sudo pg_ctlcluster 16 main start` | 5432 | Must be running before backend starts |
| Celery (optional) | `celery -A core worker -l info` / `celery -A core beat -l info` | — | Requires Redis; not needed for core dev |

### Key non-obvious caveats

- **Auth endpoint** is `POST /api/auth/token/` (SimpleJWT), not `/api/auth/login/`. Returns `{access, refresh}`.
- **Admin superuser**: create with `DJANGO_SUPERUSER_USERNAME=admin DJANGO_SUPERUSER_EMAIL=admin@example.com DJANGO_SUPERUSER_PASSWORD=admin123 python manage.py createsuperuser --noinput`. The admin user gets `role=admin` by default.
- **PDF reports** (cash flow, property income) require the NotoNaskhArabic font. It ships in `reports/fonts/NotoNaskhArabic-Regular.ttf` and is also available system-wide at `/usr/share/fonts/truetype/noto/`.
- **Frontend lint** (`npm run lint --prefix frontend`) has 2 pre-existing errors in `AuthContext.jsx` and `DashboardPage.jsx` — these are in the existing code, not regressions.
- **`.env` file** must exist in project root (copy from `.env.example`). The `SECRET_KEY` must be changed from the placeholder.
- **Tests**: `python manage.py test --verbosity=2` runs 11 contract tests against a temporary PostgreSQL database. No Redis required for tests.
- **Seed data**: `python manage.py seed_data` populates demo data (users, properties, contracts, etc.).
- After pulling new code, always run `python manage.py migrate` before starting the backend in case new migrations were added.
