# Real Estate KSA

Django REST API + React (Vite) property management: properties and units, lease contracts with office-held tenants, rent payments, debts, finance, vouchers, ownership records, and reporting.

## Prerequisites

- **Python** 3.12+ (matches Django 6.x)
- **Node.js** 18+ (for the frontend)
- **PostgreSQL** (configured in `.env`)
- **Redis** (optional for local dev; required if you run Celery workers)

## Backend setup

1. **Clone and virtual environment**

   ```bash
   cd realestate-ksa
   python -m venv .venv
   .venv\Scripts\activate
   # Linux/macOS: source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Environment variables**

   Copy the example file and edit values:

   ```bash
   copy .env.example .env
   # Linux/macOS: cp .env.example .env
   ```

   | Variable | Purpose |
   |----------|---------|
   | `SECRET_KEY` | Django secret; required |
   | `DEBUG` | `True` in development |
   | `ALLOWED_HOSTS` | Comma-separated hostnames |
   | `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL connection |
   | `CORS_ALLOWED_ORIGINS` | Frontend origins (default includes Vite `http://localhost:5173`) |
   | `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | Redis URLs for Celery |

3. **Database**

   Create an empty PostgreSQL database matching `DB_NAME`, then:

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. **Run the API**

   ```bash
   python manage.py runserver
   ```

   API base URL: `http://127.0.0.1:8000/api/`. Admin: `http://127.0.0.1:8000/admin/`.

## Frontend setup

From the repository root:

```bash
npm install --prefix frontend
npm run dev --prefix frontend
```

Or use the root scripts:

```bash
npm run install:frontend
npm run dev
```

The dev server defaults to **http://localhost:5173**. Requests to `/api` are proxied to **http://127.0.0.1:8000** (see `frontend/vite.config.js`).

For production builds, set `VITE_API_URL` to your API origin (see `frontend/.env.example`).

## Celery (background tasks)

Scheduled jobs (e.g. expiring contracts, overdue debt installments) are defined in `core/celery.py`. You need Redis and two processes:

```bash
# Terminal 1 — worker
celery -A core worker -l info

# Terminal 2 — beat (scheduler)
celery -A core beat -l info
```

If Redis is not running, Celery will fail to start; the Django app and frontend still run without it.

## Tests

```bash
python manage.py test
```

`contracts/tests.py` covers tenant references, `ContractService`, and **API** `POST /api/contracts/` (including `tenant_data`, auth, and role checks). Other apps still use placeholder test modules unless extended.

## Continuous integration

On push or pull request to `main` or `master`, [GitHub Actions](.github/workflows/ci.yml) installs dependencies and runs `python manage.py test` against PostgreSQL 16 (service container). No Redis is required for the test job.

## Project layout

| Path | Role |
|------|------|
| `core/` | Django settings, URLs, Celery app |
| `accounts/` | Users, JWT auth, roles |
| `properties/` | Properties and units |
| `contracts/` | Tenants (office records), contracts, payments |
| `debts/`, `finance/`, `vouchers/`, `ownership/` | API apps; **Debts**, **Finance**, **Vouchers** pages in the SPA |
| `reports/` | Reporting endpoints |
| `frontend/` | React SPA |

## Time zone

Server default time zone is **Asia/Riyadh** (`core/settings.py`).
