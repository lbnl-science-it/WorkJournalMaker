# Authentication System Design

**Date:** 2026-05-08
**Issue:** #87 — No authentication on any web API endpoint
**Approach:** FastAPI dependency injection with pluggable auth providers

## Context

The web application exposes 55+ API endpoints with zero authentication.
Destructive operations (delete entries, reset settings, stop scheduler) are
open to any network client. The application is transitioning from a
single-user local tool to a shared-server deployment at LBNL, with desktop
clients connecting to sync journal entries across machines.

## Requirements

1. **Pluggable auth providers** — swappable authentication backends. Local
   username/password first, LBNL SSO (OIDC or SAML, TBD) later. Other orgs
   can install and plug in their own provider.
2. **Two roles** — `user` (manages own journals) and `admin` (manages system
   settings, sync config, user accounts).
3. **User-scoped data** — each user sees only their own journal entries and
   per-user settings.
4. **Desktop client auth** — browser redirect flow (standard OAuth pattern)
   for desktop clients. Scoped to Cluster D, not implemented here.
5. **Auth-optional mode** — configurable toggle so the app can run without
   auth for local development and backward compatibility.

## Architecture

### Auth Provider Protocol

```python
class AuthProvider(Protocol):
    async def authenticate(self, credentials: dict) -> TokenPair: ...
    async def validate_token(self, token: str) -> User: ...
    async def refresh_token(self, refresh_token: str) -> TokenPair: ...
```

Each provider implements this protocol. The active provider is selected by
config and injected via FastAPI's dependency system.

### User Model

```python
@dataclass
class User:
    id: str         # unique identifier from the provider
    username: str   # display name
    role: str       # "user" or "admin"
```

### Token Strategy

- **Access token (JWT)** — 30-minute TTL, contains `user_id`, `username`,
  `role`, `exp`. Sent as `Authorization: Bearer <token>` header. Stateless
  validation via signature check.
- **Refresh token** — 7-day TTL, stored hashed (SHA-256) in `refresh_tokens`
  table. Revocable server-side. Used by desktop clients to maintain long
  sessions without re-authenticating.

### FastAPI Dependencies

Two dependency functions enforce auth at the endpoint level:

- `get_current_user` — extracts Bearer token from the `Authorization` header,
  calls `provider.validate_token()`, returns `User` or raises HTTP 401.
- `require_admin` — calls `get_current_user`, checks `role == "admin"`,
  raises HTTP 403 if not.

### Auth-Optional Mode

When `auth.enabled` is `false` in config, `get_current_user` returns a default
user (`id="default"`, `role="admin"`) without checking tokens. All existing
behavior is preserved.

## API Endpoints

### New Auth Router (`/api/auth`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/login` | Public | Authenticate, receive token pair |
| POST | `/api/auth/refresh` | Public | Exchange refresh token for new pair |
| POST | `/api/auth/logout` | User | Revoke current refresh token |
| GET | `/api/auth/me` | User | Current user profile |

### Endpoint Classification

| Category | Dependency | Examples |
|----------|-----------|---------|
| Public | None | `/api/auth/login`, `/api/auth/refresh`, `/api/health/` |
| User | `get_current_user` | All entries, calendar, summarization endpoints |
| Admin | `require_admin` | `settings/reset-all`, `settings/import`, `sync/scheduler/*`, `health/config`, `health/metrics` |

### WebSocket Auth

Tokens passed as query parameter (`?token=<jwt>`) on WebSocket connection URL,
validated once at connection time. Standard workaround for the browser
WebSocket API not supporting custom headers during handshake.

## Database Changes

### New Table: `users`

| Column | Type | Notes |
|--------|------|-------|
| id | String (UUID) | Primary key |
| username | String | Unique, indexed |
| password_hash | String | bcrypt hash |
| role | String | "user" or "admin" |
| is_active | Boolean | Soft-disable without deleting |
| created_at | DateTime | Auto-set |
| modified_at | DateTime | Auto-updated |

Used by the local auth provider only. SSO providers will not use this table —
they get user identity from the external IdP.

### New Table: `refresh_tokens`

| Column | Type | Notes |
|--------|------|-------|
| id | String (UUID) | Primary key |
| user_id | String | FK to users.id |
| token_hash | String | SHA-256 of the raw token |
| expires_at | DateTime | When this token expires |
| revoked | Boolean | Set on logout or refresh |
| created_at | DateTime | Auto-set |

Raw refresh tokens are never stored — only their hash. This limits damage if
the database is compromised.

### Modified Table: `journal_entries`

Add `user_id` column — nullable, default `"default"`. Existing entries retain
the default value. New entries created by authenticated users get the real
`user_id`. Queries filter by `user_id` when auth is enabled.

## Configuration

```yaml
auth:
  enabled: true          # false = open access (current behavior)
  provider: local        # or "oidc", "saml" (future)
  secret_key: "..."      # for JWT signing — must be set when enabled
  access_token_ttl: 1800       # seconds (30 min)
  refresh_token_ttl: 604800    # seconds (7 days)
```

The `secret_key` should be set via `WJM_AUTH_SECRET_KEY` environment variable
in production. If `auth.enabled` is `true` and no secret key is configured,
the application should refuse to start.

## New Files

| File | Purpose |
|------|---------|
| `web/auth.py` | AuthProvider protocol, User/TokenPair models, JWT utilities, FastAPI dependencies |
| `web/providers/local.py` | Local username/password provider (bcrypt + SQLite) |
| `web/api/auth.py` | Auth API endpoints (login, refresh, logout, me) |
| `web/manage.py` | CLI tool for user management (create-admin, list-users) |

## CLI Management

```bash
python -m web.manage create-admin --username admin
python -m web.manage list-users
```

The first admin must be created via CLI to avoid a chicken-and-egg problem
where you can't create users through the API without being authenticated.

## Migration Strategy

**Phase 1: Auth-optional.** Deploy with `auth.enabled: false`. All existing
tests pass without modification. Local development stays frictionless.

**Phase 2: Enable auth.** Set `auth.enabled: true`, create an admin via CLI,
start using tokens. Existing entries (with `user_id="default"`) remain
accessible to all users — retroactive assignment is a future data migration.

## Testing Strategy

| Layer | What's tested | Approach |
|-------|--------------|----------|
| Provider unit tests | authenticate, validate_token, refresh_token | Direct calls, test DB, verify bcrypt/JWT behavior |
| Dependency unit tests | get_current_user, require_admin | Valid/expired/missing tokens, role checks |
| API integration tests | Auth endpoints | TestClient, full request/response cycle |
| Protected endpoint tests | Existing endpoints with auth | 401 without token, 200 with token, 403 for admin-only |
| Auth-disabled tests | auth.enabled=false mode | Verify existing behavior unchanged |
| CLI tests | manage.py create-admin | User created with correct role and hashed password |

All tests use isolation patterns from Clusters T1/T2.

## Explicitly Out of Scope

- SSO/OIDC/SAML provider implementation (blocked on LBNL protocol info)
- Browser redirect OAuth flow for desktop client (Cluster D)
- User self-registration UI (admin creates accounts via CLI)
- Password reset flow (manageable via CLI for small user base)
- Retroactive entry ownership migration (future, when multi-user deploys)

## Dependencies

- `PyJWT` — JWT encoding/decoding
- `bcrypt` — password hashing
- No new infrastructure dependencies (uses existing SQLite + FastAPI)
