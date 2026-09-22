# Spend Tracker API

A mini spend tracking API built with FastAPI, SQLAlchemy, and JWT authentication. Track expenses, view spending summaries with month-over-month comparisons, and get insights on categories with significant spend increases.

## Features

- **Expense CRUD** — Create and list expenses with category and date range filtering
- **Summary** — Total spend, breakdown by category, month-over-month change
- **Insights** (bonus) — Flags categories with >20% spend increase vs previous month
- **JWT Authentication** (bonus) — Register, login, token-protected routes
- **Frontend** — Single-page UI served via StaticFiles

## Tech Stack

| Component | Technology |
|---|---|
| Web Framework | FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 |
| Database | SQLite (configurable via env) |
| Validation | Pydantic v2 |
| Auth | python-jose (JWT) + passlib (bcrypt) |
| Server | Uvicorn (dev) / Gunicorn (prod) |
| Testing | pytest + httpx + pytest-cov |

## Project Structure

```
spend_tracker_app/
├── app/
│   ├── __init__.py          # App factory (create_app)
│   ├── config.py            # Settings via pydantic-settings
│   ├── database.py          # SQLAlchemy engine, session, Base
│   ├── models.py            # User + Expense ORM models
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── auth.py              # JWT creation, get_current_user dependency
│   ├── errors.py            # JSON exception handlers
│   ├── routes/
│   │   ├── __init__.py      # Router registration
│   │   ├── auth.py          # POST /register, POST /login, GET /me
│   │   ├── expenses.py      # POST /expenses, GET /expenses
│   │   ├── summary.py       # GET /summary
│   │   └── insights.py      # GET /insights
│   └── services/
│       ├── expense_service.py  # DB logic for expenses
│       └── summary_service.py # Aggregation, MoM, insights logic
├── static/
│   └── index.html           # Frontend SPA
├── tests/
│   ├── conftest.py          # Fixtures (in-memory DB, client, auth)
│   ├── test_expenses.py     # CRUD + validation + filtering
│   ├── test_summary.py     # Total, category, MoM edge cases
│   ├── test_insights.py    # Threshold, sorting, year boundary
│   └── test_auth.py        # Register, login, protected routes
├── requirements.txt
├── pytest.ini
├── run.py
└── .gitignore
```

## Setup

### Prerequisites

- Python 3.11+

### Installation

```bash
# Clone and enter project
cd spend_tracker_app

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt
```

## Running the App

### Development server

```bash
python run.py
```

Server starts at `http://localhost:8000`.

- **Frontend UI**: `http://localhost:8000/`
- **API docs (Swagger)**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Production (with Gunicorn)

```bash
gunicorn app:create_app --factory --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## API Endpoints

### Authentication

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | No | Register new user, returns JWT |
| `POST` | `/api/v1/auth/login` | No | Login existing user, returns JWT |
| `GET` | `/api/v1/auth/me` | Yes | Get current authenticated user |

### Expenses

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/expenses/` | Yes | Create a new expense |
| `GET` | `/api/v1/expenses/` | Yes | List expenses (filterable) |

**Query parameters for GET /expenses:**
- `category` — Filter by category name
- `start_date` — Filter start date (YYYY-MM-DD)
- `end_date` — Filter end date (YYYY-MM-DD)

### Summary & Insights

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/summary/` | Yes | Total spend, by category, MoM change |
| `GET` | `/api/v1/insights/` | Yes | Categories with >20% spend increase |

**Query parameter for GET /insights:**
- `ref_date` — Reference date for month comparison (YYYY-MM-DD), defaults to today

### Example Requests

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demopass123"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=demo&password=demopass123"

# Create expense
curl -X POST http://localhost:8000/api/v1/expenses/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"amount": 50.0, "category": "food", "date": "2024-03-15", "note": "lunch"}'

# List expenses filtered by category
curl "http://localhost:8000/api/v1/expenses/?category=food" \
  -H "Authorization: Bearer <token>"

# Get summary
curl http://localhost:8000/api/v1/summary/ \
  -H "Authorization: Bearer <token>"

# Get insights
curl "http://localhost:8000/api/v1/insights/?ref_date=2024-03-22" \
  -H "Authorization: Bearer <token>"
```

## Testing

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_expenses.py

# Run with verbose output
pytest -v

# Run without coverage
pytest --no-cov
```

### Test Coverage

The test suite covers:

- **Expense CRUD** (17 tests) — Creation, validation (amount, category, date, note), listing, filtering by category and date range, ordering
- **Summary** (12 tests) — Total spend, spend by category, MoM change with edge cases (no data, new spending, decrease, year boundary)
- **Insights** (8 tests) — Threshold boundary (exactly 20% vs >20%), sorting, 100% decrease, year boundary, excluded categories
- **Auth** (17 tests) — Register, login, duplicate prevention, validation, all protected routes with/without token
- **User Isolation** (5 tests) — Expenses, summary, insights, category filter, and MoM change isolated between users

**Coverage: 95%**

## Configuration

Settings are loaded from environment variables or `.env` file:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./spend_tracker.db` | SQLAlchemy database URL |
| `SECRET_KEY` | `dev-secret-key-change-in-production` | JWT signing key (must be changed in production) |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT token expiry |
| `APP_NAME` | `Spend Tracker API` | App name in docs |
| `DEBUG` | `False` | Debug mode |

Create a `.env` file for local development:

```env
DATABASE_URL=sqlite:///./spend_tracker.db
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

## Design Decisions

### Architecture
- **Layered separation**: Routes (HTTP) → Services (DB logic) → Models (ORM) → Schemas (validation). Each layer has one responsibility.
- **App factory pattern**: `create_app()` allows multiple instances (testing, production) and deferred initialization.
- **Dependency injection**: FastAPI `Depends()` for DB sessions and auth — no global state.

### Validation
- **Pydantic schemas** handle input validation automatically (amount > 0, string lengths, date format). Invalid input returns 422.
- **DB CHECK constraint** on `amount > 0` as a second layer of defense.

### MoM Change Calculation
- Uses calendar month boundaries (not rolling 30 days) for intuitive comparison.
- Handles edge cases: no previous spend (returns `note` instead of `change_percent`), no spend in either month, year boundary (Jan → Dec).

### Insights Threshold
- Strictly greater than 20% (`> 20.0`), not `>= 20.0`. Exactly 20% is not flagged.
- Only categories with previous month spend are included — new categories can't have a meaningful percentage increase.

### Data Isolation
- **User-specific expenses** — Each expense has a `user_id` foreign key linking it to the user who created it. All queries (expenses, summary, insights) filter by `user_id`, so users cannot see or access each other's data.

### Security
- **Fail-fast secret key** — If `SECRET_KEY` is left as the default and `DEBUG=False`, the app refuses to start with a `RuntimeError`. This prevents accidental deployment with an insecure signing key.
- **Password hashing** — bcrypt via passlib, never stored in plaintext.

### Testing
- **In-memory SQLite** per test via `StaticPool` — no file I/O, fast, isolated.
- **Dependency override** for `get_db` — tests use the same in-memory DB as the app.
- **Single app instance** per test — no duplicate operation ID warnings.

## Future Improvements

- **Password reset** — Email-based password reset flow.
- **Token refresh** — Implement refresh tokens for longer sessions.
- **Pagination** — Add `limit`/`offset` for expense listing.
- **Export** — CSV/PDF export of expenses and summary.
- **Budget alerts** — Set monthly budgets per category, alert when approaching limit.
- **Multi-currency** — Support different currencies with conversion.
