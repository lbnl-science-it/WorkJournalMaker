# Plan: Local-First Multi-User Sync for WorkJournalMaker

> **Supersedes:** `server_synch_spec.md` (prior spec included zero-knowledge PGP encryption, billing/subscription, and cloud-only deployment — all deferred or dropped in favor of a simpler, self-hostable MVP).

## Vision

Transform WorkJournalMaker into a local-first, multi-user journaling platform with remote sync. Users run the app locally for offline access. A central server provides sync between devices and (eventually) phone apps. Text files remain the canonical data format — users can always bail out with their data intact.

## Architecture: One Codebase, Two Modes

The same application runs in two modes, controlled by configuration:

| | Local Mode (default) | Server Mode |
|---|---|---|
| Auth | Disabled | Google Workspace SSO (or API key) |
| Files | `~/Desktop/worklogs/` | `/data/{user_id}/worklogs/` |
| Database | SQLite (local index) | SQLite (multi-user index) |
| Sync | Client (pushes/pulls to server) | Server (accepts push/pull) |
| Web UI | Full (local use) | Full (remote access) |

**No PostgreSQL needed for MVP.** SQLite handles concurrent reads well, and writes are infrequent (journal entries, not high-throughput). Each user's files are isolated. If scale becomes an issue later, the SQLAlchemy abstraction makes switching trivial.

## Core Design Principles

1. **Files are the source of truth.** Database is always a rebuildable index.
2. **Server stores files per user** in the same directory structure as local instances.
3. **Sync is file-level** — compare inventories, transfer file contents.
4. **Auth is pluggable** — disabled locally, Google SSO or API keys for hosted.
5. **Same codebase** — no separate server project.

## Sync Protocol (Simple File-Level)

### Manifest
Each side maintains a manifest: `{date → (relative_path, sha256_hash, modified_at)}`

### Sync Flow
```
Client                          Server
  |                                |
  |── POST /api/sync/manifest ──→ |  (send local manifest + last_sync_at)
  |                                |  (server compares manifests)
  |←── {to_upload, to_download} ──|  (server returns diff)
  |                                |
  |── POST /api/sync/upload ────→ |  (client sends files server needs)
  |←── GET /api/sync/download ────|  (client fetches files it needs)
  |                                |
  |── POST /api/sync/complete ──→ |  (update last_sync_at on both sides)
  |                                |
```

### Conflict Resolution (MVP)
- If same date modified on both sides since last sync: **last-write-wins** (by `modified_at` timestamp).
- Conflict is logged. User can view conflict history.
- Future: user-choosable resolution.

## Implementation Phases

### Phase 1: Multi-User Schema
Add `user_id` to `JournalEntryIndex`. Change unique constraint from `(date)` to `(user_id, date)`. Add `User` model. Default all existing data to `user_id = "local"`.

**Files to modify:**
- `web/database.py` — Add `User` model, add `user_id` column to `JournalEntryIndex`, update unique constraint

**Schema additions:**
```python
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)  # UUID or email
    email = Column(String, unique=True, nullable=True)
    display_name = Column(String)
    storage_path = Column(String)  # per-user file directory
    created_at = Column(DateTime)
    last_sync_at = Column(DateTime)

# JournalEntryIndex changes:
# - Add: user_id = Column(String, default="local", index=True)
# - Change: unique constraint from (date) to (user_id, date)
```

### Phase 2: User-Scoped Services
Thread `user_id` through `EntryManager` and all services. Default to `"local"` so existing single-user behavior is unchanged.

**Files to modify:**
- `web/services/entry_manager.py` — Accept `user_id` parameter, scope file paths per user
- `web/services/calendar_service.py` — Accept `user_id` parameter
- `web/services/web_summarizer.py` — Accept `user_id` parameter
- `web/services/sync_service.py` — Accept `user_id` parameter
- `web/services/settings_service.py` — Accept `user_id` parameter

### Phase 3: Server Mode Configuration
Add `ServerConfig` to `config_manager.py` with mode (`local`/`server`), auth settings, and per-user storage root.

**Files to modify:**
- `config_manager.py` — Add `ServerConfig` and `AuthConfig` dataclasses
- `web/app.py` — Conditionally enable auth middleware, configure per-user storage

**Config additions:**
```yaml
server:
  mode: local  # or "server"
  storage_root: /data/users/  # only used in server mode

auth:
  enabled: false  # true in server mode
  provider: google  # or "api_key"
  google_client_id: "..."
  allowed_domains: ["example.com"]
```

### Phase 4: Authentication Middleware
Add auth middleware that's only active in server mode. Google Workspace SSO via OAuth2 for hosted deployments. API key fallback for simpler setups.

**Files to create:**
- `web/services/auth_service.py` — Google OAuth2 + API key auth
- `web/middleware.py` — Add `AuthMiddleware` class

**Files to modify:**
- `web/app.py` — Conditionally add auth middleware
- `web/api/entries.py` — Extract `user_id` from auth context
- All API routers — Accept user context from middleware

### Phase 5: Sync API Endpoints
The core sync protocol. Server-side endpoints for manifest comparison, file upload, and file download.

**Files to create:**
- `web/api/remote_sync.py` — Sync API router with manifest/upload/download/complete endpoints
- `web/services/remote_sync_service.py` — Sync logic: manifest comparison, conflict detection, file I/O

**Files to modify:**
- `web/app.py` — Include remote sync router

### Phase 6: Sync Client
Client-side logic for local instances to sync with a remote server.

**Files to create:**
- `sync_client.py` — HTTP client that implements the sync protocol (manifest → upload → download → complete)

**Files to modify:**
- `config_manager.py` — Add `SyncConfig` with remote server URL and credentials
- `web/app.py` — Optional sync client initialization

**Config additions:**
```yaml
sync:
  enabled: false
  remote_url: "https://journal.example.com"
  auth_token: "..."  # obtained from server login
  auto_sync_interval: 300  # seconds, 0 = manual only
```

### Phase 7: Docker Deployment
Containerize for easy self-hosting and hosted deployment.

**Files to create:**
- `Dockerfile` — Python app with uvicorn
- `docker-compose.yml` — App + volume mount for user data
- `docker-compose.server.yml` — Override with server mode config

## What We Are NOT Building (YAGNI)

- PostgreSQL (SQLite is sufficient for MVP scale)
- Zero-knowledge encryption (from prior spec — deferred, add when needed)
- Billing/subscription system (from prior spec — deferred)
- Automatic text-level conflict merging
- Collaborative/shared journals
- Mobile apps (future phase)
- Rate limiting (add when needed)
- User roles/permissions
- File versioning beyond conflict detection

## Migration Path

- Existing single-user installations continue to work unchanged (`mode: local`, `user_id: "local"`)
- All new parameters default to current behavior
- No breaking changes to CLI or web UI
- Server mode is opt-in via configuration

## Testing Strategy

Each phase gets:
- **Unit tests**: Service methods with mocked dependencies
- **Integration tests**: API endpoints with real SQLite database
- **E2E tests**: Full sync flow between two instances (local ↔ server)

## Implementation Order Recommendation

Phases 1-2 first (multi-user schema + services) — these are the foundation everything else builds on. Then Phase 3 (config). Then Phase 5 (sync API) in parallel with Phase 4 (auth). Phase 6 (sync client) after Phase 5. Phase 7 (Docker) last.

Critical path: **1 → 2 → 3 → 5 → 6 → 7** (auth can be done in parallel with sync)
