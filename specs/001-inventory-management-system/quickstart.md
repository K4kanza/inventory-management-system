# Quickstart: Inventory Management System

Phase 1 output for `/sp.plan` — how to stand up the backend locally. All commands run from `backend/`.

**Stack**: Python 3.12 · Django 5.2 LTS · Django REST Framework 3.17 · PostgreSQL 16 · pytest + ruff

## Prerequisites

- Python 3.12+
- PostgreSQL 16 running locally (any managed equivalent works)
- `pg_trgm` extension available (ships with PostgreSQL contrib)

## 1. Create database & role

```sql
CREATE ROLE inventory WITH LOGIN PASSWORD 'inventory_dev_password';
CREATE DATABASE inventory OWNER inventory;
```

Enable the search extension (once, as a superuser or DB owner):

```sql
\c inventory
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

## 2. Install

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1       # Windows shell as used in this repo
pip install -r requirements.txt    # pinned in pyproject.toml (pip install -e ".[dev]")
```

## 3. Configure environment

Create `backend/.env` (git-ignored; never commit):

```env
DJANGO_SETTINGS_MODULE=config.settings.development
SECRET_KEY=a-long-random-string
DEBUG=True
DATABASE_URL=postgres://inventory:inventory_dev_password@localhost:5432/inventory
```

## 4. Migrate & seed

```powershell
python manage.py migrate
python manage.py createsuperuser        # first user; set role=admin in the shell that follows
python manage.py shell -c "from apps.accounts.models import User; u=User.objects.get(username='<your-name>'); u.role='admin'; u.save()"
python data/seed.py                      # idempotent: sample categories, units, locations, demo users
```

## 5. Run

```powershell
python manage.py runserver
```

Open <http://127.0.0.1:8000/> → login → dashboard (/), catalogue (/items), movements
(/movements), reports (/reports/*), user management (admin only).

API base: `http://127.0.0.1:8000/api/v1/` — schema at `/api/v1/schema/` (drf-spectacular).

## 6. Test & lint

```powershell
python -m pytest                 # unit + integration (concurrency, permission matrix)
python -m pytest tests/performance -k "not slow"   # quick perf smoke
ruff check .
ruff format --check .
```

## Demo data

`data/seed.py` creates (idempotently): three demo users (`admin@demo`, `manager@demo`,
`staff@demo` — password `Demo-password-1`), a handful of categories, units (kg fractional,
pc whole), two locations (`WH-A`, `WH-B`), and sample items with reorder levels so alerts
and reports render immediately.

## Development notes

- The custom `User` model (with `role`) must be created **before** any catalog migrations — it already is, by design (Phase 0).
- Movement endpoints run inside a single transaction with `SELECT ... FOR UPDATE`; never add `.save()` outside that flow for stock quantities.
- Every page and API endpoint is role-gated by default: add a new endpoint and it stays closed until a role is explicitly granted (default-deny).