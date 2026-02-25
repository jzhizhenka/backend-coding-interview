# Authorization Architecture

## Choice: JWT (JSON Web Tokens)

JWT-based authentication with short-lived access tokens and long-lived refresh tokens.

### Why JWT Over Alternatives

| Approach | Verdict | Reasoning |
|---|---|---|
| **JWT** | **Selected** | Stateless, scalable, self-contained user claims, standard `Authorization: Bearer` header, ideal for RESTful APIs |
| Session-based auth | Passed | Requires server-side session store (Redis or DB), harder to scale horizontally, couples auth to a specific server instance |
| OAuth2 / OpenID Connect | Out of scope | Full OAuth2 is overkill for a first-party API; JWT is commonly used *within* OAuth2 as the token format |
| API keys | Too simple | No user identity or expiration semantics; better suited for service-to-service communication |

### Key Factors

- **Stateless** -- the server validates tokens cryptographically without hitting a database on every request. This aligns with REST principles and simplifies horizontal scaling.
- **Self-contained** -- the token payload carries user claims (`user_id`, `role`), so the API layer knows who is making a request without an extra lookup.
- **Standard** -- every major framework has mature JWT libraries. The `Authorization: Bearer <token>` pattern is universally understood by API consumers.
- **Fits the read-heavy workload** -- most requests are unauthenticated reads (browsing photos) or authenticated reads (viewing favorites). Avoiding a session store lookup on every request reduces latency.

---

## Authentication Flow

### Registration

```
POST /api/auth/register
{
  "email": "user@example.com",
  "password": "securepassword"
}
→ 201 Created
{
  "user": { "id": 1, "email": "user@example.com" }
}
```

- Password is hashed with **bcrypt** (cost factor 12) before storage.
- Email uniqueness is enforced at the database level (UNIQUE constraint).
- Password strength validation: minimum 8 characters.

### Login

```
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "securepassword"
}
→ 200 OK
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

- Returns a **short-lived access token** (15 minutes) and a **long-lived refresh token** (7 days).
- Access token is sent on subsequent requests via the `Authorization: Bearer <token>` header.

### Token Refresh

```
POST /api/auth/refresh
{
  "refresh_token": "eyJhbGciOi..."
}
→ 200 OK
{
  "access_token": "eyJhbGciOi...",
  "expires_in": 900
}
```

- Issues a new access token without requiring the user to re-enter credentials.
- The refresh token itself is **not rotated** on each use (simplicity), but this could be changed to rotating refresh tokens for stricter security.

---

## Token Structure

### Access Token Payload

```json
{
  "sub": 1,
  "email": "user@example.com",
  "role": "user",
  "iat": 1700000000,
  "exp": 1700000900
}
```

| Claim | Purpose |
|---|---|
| `sub` | User ID (subject) |
| `email` | User email for convenience in logs/debugging |
| `role` | Authorization role (`user` or `admin`) |
| `iat` | Issued-at timestamp |
| `exp` | Expiration timestamp (15 min from `iat`) |

### Signing Algorithm

**HS256** (HMAC-SHA256) with a server-side secret key.

- Symmetric signing is sufficient for a single-service architecture.
- For a microservices setup, RS256 (asymmetric) would be preferred so that services can verify tokens without sharing the signing secret.

---

## Authorization Model

### Roles

| Role | Permissions |
|---|---|
| **Anonymous** | Browse and search photos, view photographer profiles |
| **User** | Everything anonymous can do, plus: manage own favorites, view own profile |
| **Admin** | Everything user can do, plus: CRUD on photos, manage photographers, manage users |

### Resource-Level Rules

| Resource | Rule |
|---|---|
| `GET /api/photos` | Public -- no auth required |
| `GET /api/photos/:id` | Public -- no auth required |
| `POST /api/photos` | Admin only |
| `PUT /api/photos/:id` | Admin only |
| `DELETE /api/photos/:id` | Admin only |
| `GET /api/favorites` | Authenticated -- returns own favorites only |
| `POST /api/favorites/:photo_id` | Authenticated -- adds to own favorites |
| `DELETE /api/favorites/:photo_id` | Authenticated -- removes from own favorites |
| `GET /api/users/me` | Authenticated -- own profile only |

Authorization is enforced at the middleware/decorator level. Each endpoint declares its required role, and the middleware extracts the JWT, verifies it, and checks the `role` claim before the handler executes.

---

## Password Handling

| Aspect | Decision |
|---|---|
| **Hashing algorithm** | bcrypt with cost factor 12 |
| **Storage** | Only the hash is stored; plaintext is never persisted or logged |
| **Validation** | Minimum 8 characters; checked server-side before hashing |

**Why bcrypt over argon2**: bcrypt is battle-tested, widely supported, and sufficient for this use case. Argon2 is technically superior (memory-hard), but bcrypt has broader library support and is the default in frameworks like Django and Rails. Either would be acceptable.

---

## Trade-offs

### Short-lived access tokens + refresh tokens vs. long-lived tokens

| Approach | Pros | Cons |
|---|---|---|
| **Short access + refresh (chosen)** | Limits exposure if an access token leaks; refresh token can be revoked | More complex flow; client must handle token refresh |
| Single long-lived token | Simpler client logic | A leaked token is valid for days/weeks; no way to revoke without a blocklist |

**Decision**: the two-token approach. A 15-minute access token limits the blast radius of a token leak, and the refresh token provides session continuity.

### Stateless JWT vs. server-side token validation

| Approach | Pros | Cons |
|---|---|---|
| **Stateless JWT (chosen)** | No DB lookup per request, horizontally scalable | Cannot revoke individual access tokens before expiry |
| DB-backed token check | Immediate revocation on logout/ban | Extra DB query on every authenticated request |

**Decision**: stateless. The short access token lifetime (15 minutes) makes immediate revocation less critical. For logout, the client simply discards the tokens. For ban/compromise scenarios, a lightweight in-memory blocklist of token `jti` claims could be added without a full DB lookup.

### HS256 vs. RS256 signing

| Algorithm | Pros | Cons |
|---|---|---|
| **HS256 (chosen)** | Simple, fast, single secret to manage | All services that verify tokens must share the secret |
| RS256 | Services can verify without the signing key; better for microservices | Key pair management, slightly slower verification |

**Decision**: HS256. This is a single-service application. If the architecture grew to multiple services, migrating to RS256 would be straightforward.

### bcrypt vs. argon2 for password hashing

| Algorithm | Pros | Cons |
|---|---|---|
| **bcrypt (chosen)** | Battle-tested, universal library support, framework default | Not memory-hard; vulnerable to GPU attacks at low cost factors |
| argon2 | Memory-hard, winner of the Password Hashing Competition | Newer, less library support in some ecosystems |

**Decision**: bcrypt at cost factor 12. Widely supported and sufficient for this application. Argon2 would be a valid upgrade path.

---

## Security Considerations

- **Tokens are never stored server-side** -- validation is purely cryptographic.
- **Refresh tokens should be stored securely by the client** (e.g., HttpOnly cookie or secure storage on mobile).
- **HTTPS is required** in production to prevent token interception.
- **Rate limiting** on `/api/auth/login` to prevent brute-force attacks.
- **Password hashes only** -- plaintext passwords are never logged, cached, or persisted.
- **Token secret rotation** -- the signing key should be rotatable. During rotation, both old and new keys are accepted for a grace period.

---

## Future Considerations

- **Rotating refresh tokens** -- issue a new refresh token on each use and invalidate the old one, detecting token reuse as a compromise signal.
- **OAuth2 provider integration** -- allow "Sign in with Google/GitHub" alongside email/password.
- **Scoped tokens** -- fine-grained permission scopes (e.g., `photos:read`, `favorites:write`) for third-party API consumers.
- **Token blocklist** -- a Redis-backed set of revoked `jti` claims for immediate access token invalidation on logout or account compromise.
