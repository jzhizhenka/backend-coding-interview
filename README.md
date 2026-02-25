# Photo Management API

A RESTful API for browsing, searching, and managing photos, built with Django 5.2 and Django REST Framework.

## Tech Stack

| Component | Choice |
|-----------|--------|
| Language | Python 3.13 |
| Framework | Django 5.2 (LTS) + Django REST Framework |
| Database | PostgreSQL 17 |
| Auth | JWT via `djangorestframework-simplejwt` |
| API Docs | OpenAPI 3.0 via `drf-spectacular` |
| Containerization | Docker + Docker Compose |

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) (v2+)

That's it — no local Python installation required.

## Quick Start

```bash
# 1. Clone the repository
git clone <repo-url>
cd backend-coding-interview

# 2. Create environment file from the example
cp .env.example .env

# 3. Start the services (PostgreSQL + Django)
docker compose up -d

# 4. Run database migrations
docker compose exec web python manage.py migrate

# 5. Ingest photo data from the Pexels dataset
docker compose exec web python manage.py ingest_photos

# 6. Create a superuser (optional, for admin access)
docker compose exec web python manage.py createsuperuser
```

The API is now running at **http://localhost:8000**.

## Available Services

| Service | URL |
|---------|-----|
| API | http://localhost:8000/api/ |
| Swagger UI (API docs) | http://localhost:8000/api/docs/ |
| OpenAPI schema (JSON) | http://localhost:8000/api/schema/ |
| Django Admin | http://localhost:8000/admin/ |

## API Endpoints

### Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register` | None | Register a new user |
| POST | `/api/auth/login` | None | Login, returns access + refresh tokens |
| POST | `/api/auth/refresh` | None | Exchange refresh token for a new access token |
| GET | `/api/users/me` | Bearer | Get the authenticated user's profile |

#### Register

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepassword"}'
```

```json
{
  "user": { "id": 1, "email": "user@example.com", "role": "user", "created_at": "...", "updated_at": "..." }
}
```

#### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepassword"}'
```

```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

#### Refresh Token

```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGciOi..."}'
```

```json
{
  "access_token": "eyJhbGciOi...",
  "expires_in": 900
}
```

#### Get Current User

```bash
curl http://localhost:8000/api/users/me \
  -H "Authorization: Bearer <access_token>"
```

```json
{
  "id": 1,
  "email": "user@example.com",
  "role": "user",
  "created_at": "2026-02-23T12:00:00Z",
  "updated_at": "2026-02-23T12:00:00Z"
}
```

### Photographers

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/photographers` | None | List photographers (searchable, sortable) |
| GET | `/api/photographers/:id` | None | Get a single photographer |
| POST | `/api/photographers` | Admin | Create a photographer |
| PATCH | `/api/photographers/:id` | Admin | Update a photographer |
| DELETE | `/api/photographers/:id` | Admin | Delete a photographer |

#### List Photographers

```bash
curl "http://localhost:8000/api/photographers?search=Jane&ordering=name"
```

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1001,
      "name": "Jane Doe",
      "profile_url": "https://www.pexels.com/@janedoe",
      "created_at": "2026-02-23T12:00:00Z",
      "updated_at": "2026-02-23T12:00:00Z"
    }
  ]
}
```

#### Create Photographer

```bash
curl -X POST http://localhost:8000/api/photographers \
  -H "Authorization: Bearer <admin_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"id": 1001, "name": "Jane Doe", "profile_url": "https://www.pexels.com/@janedoe"}'
```

```json
{
  "id": 1001,
  "name": "Jane Doe",
  "profile_url": "https://www.pexels.com/@janedoe",
  "created_at": "2026-02-23T12:00:00Z",
  "updated_at": "2026-02-23T12:00:00Z"
}
```

### Photos

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/photos` | None | List photos (paginated, filterable, searchable) |
| GET | `/api/photos/:id` | None | Get a single photo with photographer details |
| POST | `/api/photos` | Admin | Create a photo |
| PATCH | `/api/photos/:id` | Admin | Partially update a photo |
| PUT | `/api/photos/:id` | Admin | Fully update a photo |
| DELETE | `/api/photos/:id` | Admin | Delete a photo |

#### List Photos

```bash
curl "http://localhost:8000/api/photos?search=landscape&ordering=-width&page=1"
```

```json
{
  "count": 42,
  "next": "http://localhost:8000/api/photos?page=2",
  "previous": null,
  "results": [
    {
      "id": 9001,
      "photographer_id": 1001,
      "photographer_name": "Jane Doe",
      "width": 3888,
      "height": 5184,
      "url": "https://www.pexels.com/photo/...",
      "alt": "A beautiful landscape",
      "avg_color": "#333831",
      "src": { "original": "...", "large2x": "...", "large": "...", "medium": "...", "small": "...", "portrait": "...", "landscape": "...", "tiny": "..." }
    }
  ]
}
```

**Query parameters:**

| Parameter | Example | Description |
|-----------|---------|-------------|
| `search` | `landscape` | Full-text search on alt text |
| `photographer_id` | `1001` | Filter by photographer |
| `avg_color` | `#333831` | Filter by dominant color (case-insensitive) |
| `width_min` / `width_max` | `1920` | Filter by width range |
| `height_min` / `height_max` | `1080` | Filter by height range |
| `ordering` | `-width`, `height`, `created_at` | Sort results |
| `page` | `2` | Pagination (20 results per page) |

#### Get Photo Detail

```bash
curl http://localhost:8000/api/photos/9001
```

```json
{
  "id": 9001,
  "photographer": {
    "id": 1001,
    "name": "Jane Doe",
    "profile_url": "https://www.pexels.com/@janedoe",
    "created_at": "...",
    "updated_at": "..."
  },
  "width": 3888,
  "height": 5184,
  "url": "https://www.pexels.com/photo/...",
  "alt": "A beautiful landscape",
  "avg_color": "#333831",
  "src": { "original": "...", "large2x": "...", "large": "...", "medium": "...", "small": "...", "portrait": "...", "landscape": "...", "tiny": "..." },
  "created_at": "2026-02-23T12:00:00Z",
  "updated_at": "2026-02-23T12:00:00Z"
}
```

#### Create Photo

Requires an existing `photographer_id` — create the photographer first via `POST /api/photographers` if needed.

```bash
curl -X POST http://localhost:8000/api/photos \
  -H "Authorization: Bearer <admin_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "id": 9001,
    "photographer_id": 1001,
    "width": 3888,
    "height": 5184,
    "url": "https://www.pexels.com/photo/a-beautiful-landscape-9001/",
    "alt": "A beautiful landscape",
    "avg_color": "#333831",
    "src": {
      "original": "https://images.pexels.com/photos/9001/photo.jpeg",
      "large2x": "https://images.pexels.com/photos/9001/photo.jpeg?dpr=2&h=650&w=940",
      "large": "https://images.pexels.com/photos/9001/photo.jpeg?h=650&w=940",
      "medium": "https://images.pexels.com/photos/9001/photo.jpeg?h=350",
      "small": "https://images.pexels.com/photos/9001/photo.jpeg?h=130",
      "portrait": "https://images.pexels.com/photos/9001/photo.jpeg?fit=crop&h=1200&w=800",
      "landscape": "https://images.pexels.com/photos/9001/photo.jpeg?fit=crop&h=627&w=1200",
      "tiny": "https://images.pexels.com/photos/9001/photo.jpeg?fit=crop&h=200&w=280"
    }
  }'
```

### Favorites

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/favorites` | Bearer | List the authenticated user's favorited photos |
| POST | `/api/favorites/:photo_id` | Bearer | Add a photo to favorites |
| DELETE | `/api/favorites/:photo_id` | Bearer | Remove a photo from favorites |

#### Add Favorite

```bash
curl -X POST http://localhost:8000/api/favorites/9001 \
  -H "Authorization: Bearer <access_token>"
```

```json
{ "detail": "Photo added to favorites." }
```

#### List Favorites

```bash
curl http://localhost:8000/api/favorites \
  -H "Authorization: Bearer <access_token>"
```

```json
{
  "count": 1,
  "results": [
    {
      "photo": {
        "id": 9001,
        "photographer_name": "Jane Doe",
        "width": 3888,
        "height": 5184,
        "url": "...",
        "alt": "A beautiful landscape",
        "avg_color": "#333831",
        "src": { "original": "...", "large2x": "..." }
      },
      "created_at": "2026-02-23T12:00:00Z"
    }
  ]
}
```

#### Remove Favorite

```bash
curl -X DELETE http://localhost:8000/api/favorites/9001 \
  -H "Authorization: Bearer <access_token>"
# → 204 No Content
```

### Authorization Roles

| Role | Permissions |
|------|-------------|
| **Anonymous** | Browse and search photos, view photographer profiles |
| **User** | Everything anonymous can do, plus: manage own favorites, view own profile |
| **Admin** | Everything user can do, plus: CRUD on photos, manage photographers and users |

## Common Commands

```bash
# Start services in the background
docker compose up -d

# View logs (follow mode)
docker compose logs -f web

# Run migrations
docker compose exec web python manage.py migrate

# Ingest photo data from photos.json
docker compose exec web python manage.py ingest_photos

# Create new migrations after model changes
docker compose exec web python manage.py makemigrations

# Open a Django shell
docker compose exec web python manage.py shell

# Run tests
docker compose exec web pytest

# Stop services
docker compose down

# Stop services and delete database volume
docker compose down -v
```

## Project Structure

```
.
├── config/              # Django project settings
│   ├── settings.py      # Main configuration
│   ├── urls.py          # Root URL routing
│   ├── wsgi.py
│   └── asgi.py
├── users/               # User model & auth endpoints
│   ├── models.py        # Custom User model (email-based auth)
│   ├── views.py         # Register, Login, Refresh, Me views
│   ├── serializers.py   # Request/response serializers
│   ├── token.py         # Custom JWT claims (sub, email, role)
│   ├── urls.py          # Auth URL routing
│   ├── admin.py         # User admin configuration
│   └── tests.py         # 25 pytest tests
├── photographers/       # Photographer profiles
│   ├── models.py        # Photographer model (Pexels ID as PK)
│   ├── views.py         # Photographer list/detail/CRUD views
│   ├── serializers.py   # Photographer serializer
│   ├── urls.py          # Photographer URL routing
│   ├── admin.py         # Photographer admin configuration
│   ├── tests.py         # 16 pytest tests
│   └── ...
├── photos/              # Photo management & favorites
│   ├── models.py        # Photo and UserFavorite models
│   ├── views.py         # Photo CRUD, Favorites list/toggle
│   ├── serializers.py   # Photo and Favorite serializers
│   ├── filters.py       # FilterSet for photo queries
│   ├── permissions.py   # IsAdminOrReadOnly permission
│   ├── urls.py          # Photo & Favorites URL routing
│   ├── tests.py         # 47 pytest tests
│   ├── management/commands/ingest_photos.py  # Data ingestion command
│   └── ...
├── docs/                # Architecture & design documentation
│   ├── authorization.md # Auth design decisions
│   └── database.md      # Database design decisions
├── conftest.py          # Shared pytest fixtures
├── docker-compose.yml   # PostgreSQL + Django dev server
├── Dockerfile           # Python 3.13-slim image
├── manage.py
├── requirements.txt
├── pyproject.toml       # pytest configuration
└── photos.json          # Source dataset (Pexels)
```

## Environment Variables

All configuration is driven by environment variables defined in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `photos` | Database name |
| `POSTGRES_USER` | `photos` | Database user |
| `POSTGRES_PASSWORD` | `photos` | Database password |
| `POSTGRES_HOST` | `db` | Database host (`db` = Docker service name) |
| `POSTGRES_PORT` | `5432` | Database port |
| `DJANGO_SECRET_KEY` | *(insecure default)* | Django secret key — **must be changed in production** |
| `DJANGO_DEBUG` | `True` | Enable debug mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hosts |

## Architecture Decisions

Detailed write-ups are in the `docs/` folder:

- **[Authorization](docs/authorization.md)** — JWT-based auth with short-lived access tokens (15 min) and long-lived refresh tokens (7 days). Roles: anonymous, user, admin.
- **[Database](docs/database.md)** — PostgreSQL with normalized schema (photographers, photos, users, favorites). JSONB for image source variants, GIN indexes for full-text search.

## Running Tests

```bash
# Via Docker
docker compose exec web pytest

# Locally (with virtualenv activated)
pytest
```

**88 tests** across three apps:

### `users` app — 25 tests

| Area | Tests |
|------|-------|
| User model | Creation, email normalization, superuser, validation |
| Registration | Success, duplicates, weak password, missing/invalid fields |
| Login | Success, case-insensitive email, wrong password, unknown user |
| JWT claims | Custom payload (sub, email, role), admin role |
| Token refresh | Valid refresh, invalid/missing token |
| `/users/me` | Authenticated, unauthenticated, returns own data only |

### `photographers` app — 16 tests

| Area | Tests |
|------|-------|
| List | Public access, search by name, ordering |
| Detail | Public access, 404 for missing |
| Create | Admin succeeds, regular user forbidden, anonymous unauthorized, validation |
| Update | Admin patch, regular user forbidden, anonymous unauthorized |
| Delete | Admin succeeds, regular user forbidden, anonymous unauthorized, 404 for missing |

### `photos` app — 47 tests

| Area | Tests |
|------|-------|
| Models | Photographer/Photo/UserFavorite creation, str repr, FK cascade, unique constraint |
| Photo list | Public access, pagination, search by alt, filters (photographer, color, dimensions), ordering |
| Photo detail | Public access, 404 for missing |
| Photo create | Admin succeeds, regular user forbidden, anonymous unauthorized, nonexistent photographer rejected, validation |
| Photo update | Admin patch/multi-field update, regular user forbidden, anonymous unauthorized |
| Photo delete | Admin succeeds, regular user forbidden, anonymous unauthorized, 404 for missing |
| Favorites list | Authenticated empty/with items, user isolation, includes photo data, unauthenticated rejected |
| Favorites toggle | Add, duplicate conflict (409), nonexistent photo (404), remove, independent per user |
| Ingest command | Creates photographers + photos, idempotent on re-run |

## What I Would Add With More Time

- Rate limiting on authentication endpoints
- Redis caching layer for hot photo listings
- Rotating refresh tokens for stricter security
- CI/CD pipeline with GitHub Actions
- Production Docker configuration (multi-stage build, Gunicorn, Nginx)
