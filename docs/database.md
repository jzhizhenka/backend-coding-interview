# Database Architecture

## Choice: PostgreSQL

PostgreSQL is the primary database for this project. The decision was driven by the nature of the data and the requirements of a production-ready photo management API.

### Why PostgreSQL Over Alternatives

| Database | Verdict | Reasoning |
|---|---|---|
| **PostgreSQL** | **Selected** | Native relational model, JSONB for flexible source URLs, built-in full-text search, rich indexing (B-tree, GIN, partial) |
| SQLite | Runner-up | Zero-setup convenience, but lacks JSONB indexing, full-text search, and concurrent write support. Signals "prototype" over "production-ready" |
| MySQL | Passed | Capable but no advantage over Postgres; weaker JSON support |
| MongoDB | Poor fit | Data is clearly relational. Denormalized photographer data creates update anomalies; M:N relationships (user favorites) are awkward in a document model |
| Redis / DynamoDB | Not applicable | Not suited as a primary store; Redis could layer on top as a cache |

### Key Factors

- **Structured, predictable schema** -- every photo and photographer has the same fields. No polymorphism or deeply nested documents.
- **Relational by nature** -- photos belong to photographers, users can favorite photos. Classic FK relationships.
- **Read-heavy workload** -- a photo gallery API is overwhelmingly reads (browse, search, filter) with occasional writes.
- **Stack alignment** -- Postgres is the canonical choice for Django and Rails, the frameworks used at Clever.
- **Containerization** -- a single `docker-compose.yml` gives reviewers a one-command setup.

---

## Schema Design

### Entity-Relationship Overview

```
users ──< user_favorites >── photos >── photographers
```

- `photographers` 1:N `photos` (a photographer has many photos)
- `users` M:N `photos` through `user_favorites` (users can bookmark/favorite photos)

### Tables

#### `photographers`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | BIGINT | PRIMARY KEY | From Pexels `photographer_id` |
| `name` | VARCHAR(255) | NOT NULL | |
| `profile_url` | VARCHAR(2048) | | Pexels profile link |
| `created_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |

#### `photos`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | BIGINT | PRIMARY KEY | From Pexels photo `id` |
| `photographer_id` | BIGINT | FK → photographers(id), NOT NULL | |
| `width` | INTEGER | NOT NULL | |
| `height` | INTEGER | NOT NULL | |
| `url` | VARCHAR(2048) | NOT NULL | Pexels page URL |
| `alt` | TEXT | | Description / alt text |
| `avg_color` | CHAR(7) | | Hex color, e.g. `#333831` |
| `src` | JSONB | NOT NULL | All image size variants (see below) |
| `created_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |

The `src` JSONB column stores all image source URLs in a single field:

```json
{
  "original":  "https://images.pexels.com/photos/123/photo.jpeg",
  "large2x":   "https://...?dpr=2&h=650&w=940",
  "large":     "https://...?h=650&w=940",
  "medium":    "https://...?h=350",
  "small":     "https://...?h=130",
  "portrait":  "https://...?fit=crop&h=1200&w=800",
  "landscape": "https://...?fit=crop&h=627&w=1200",
  "tiny":      "https://...?fit=crop&h=200&w=280"
}
```

#### `users`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | BIGINT | PRIMARY KEY, GENERATED | |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | Login identifier |
| `password_hash` | VARCHAR(255) | NOT NULL | bcrypt/argon2 hash |
| `created_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | |

#### `user_favorites`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `user_id` | BIGINT | FK → users(id), NOT NULL | |
| `photo_id` | BIGINT | FK → photos(id), NOT NULL | |
| `created_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() | When the favorite was added |
| | | PRIMARY KEY (user_id, photo_id) | Prevents duplicate favorites |

---

## Trade-offs

### Source URLs: JSONB column vs. separate table vs. individual columns

| Approach | Pros | Cons |
|---|---|---|
| **JSONB column (chosen)** | Single column, flexible if sizes change, no JOINs, queryable in Postgres | Not portable to databases without JSON support |
| Separate `photo_sources` table | Fully normalized, easy to add/remove sizes | Requires JOIN on every photo fetch; overhead for data always accessed together |
| Individual columns (`src_original`, `src_large`, ...) | Simple, fast, explicit | Rigid schema; migration required if Pexels adds a size |

**Decision**: JSONB. The source URLs are tightly coupled to a photo and are always fetched together. A JSONB column keeps the query simple (`SELECT * FROM photos`) while remaining flexible if image size variants change.

### Photographer normalization vs. embedding

Photographer data is extracted into its own table rather than repeated on every photo row. This avoids update anomalies (changing a photographer's name requires updating one row, not N) and enables "photos by photographer" queries with a simple FK join.

**Trade-off**: an extra JOIN when fetching photos with photographer details. At this data scale, the cost is negligible, and correctness outweighs the minor query complexity.

### External IDs as primary keys

The Pexels `id` and `photographer_id` are used directly as primary keys rather than generating surrogate UUIDs. This simplifies ingestion (no mapping table), makes debugging easier (IDs match the source), and avoids index bloat from UUID PKs.

**Trade-off**: if two data sources ever had colliding IDs, this would break. Acceptable for a single-source system like this.

---

## Indexing Strategy

| Index | Type | Purpose |
|---|---|---|
| `photos.photographer_id` | B-tree | FK lookups, "photos by photographer" queries |
| `photos.alt` | GIN (full-text) | Search photos by description |
| `photos.avg_color` | B-tree | Filter/sort by dominant color |
| `photos.src` | GIN | Query specific sizes within JSONB |
| `users.email` | B-tree (UNIQUE) | Login lookups, enforced by UNIQUE constraint |
| `user_favorites(user_id, photo_id)` | B-tree (composite PK) | Fast favorite lookups in both directions |

---

## Future Considerations

- **Tags / Categories**: a `tags` table with a `photo_tags` M:N join table for structured categorization beyond free-form `alt` text.
- **Soft deletes**: add `deleted_at TIMESTAMPTZ` to `photos` and `users` for non-destructive deletion.
- **Computed orientation**: a generated column `orientation` (`landscape`, `portrait`, `square`) derived from `width` and `height`.
- **Caching layer**: Redis for hot photo listings and search results, with cache invalidation on writes.
- **Read replicas**: for scaling the read-heavy workload beyond a single Postgres instance.
