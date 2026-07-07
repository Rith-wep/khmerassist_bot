# Khmer AI Customer Assistant — SaaS (v2)

Multi-tenant evolution of the Telegram customer-assistant bot. See [CLAUDE.md](CLAUDE.md)
for the full product plan, schema, and build order.

- **v2 (in progress)** — this repo root: FastAPI backend (`app/`), Alembic migrations
  (`alembic/`), React dashboard (`frontend/`).
- **v1 (working reference)** — [v1_legacy/](v1_legacy/): the original single-tenant
  Telegram bot this project is being refactored from. Still runnable as-is; see
  [v1_legacy/Readme.md](v1_legacy/Readme.md).

## Layout

```
app/
├── main.py        # FastAPI app entry point
├── core/           # settings, security
├── db/             # engine/session setup
├── models/         # SQLAlchemy models
├── schemas/        # Pydantic schemas
├── routers/        # API endpoints
├── services/       # business logic (bot engine, leads, handoff, AI)
└── channels/        # messaging channel adapters (Telegram now, Messenger later)
alembic/             # DB migrations
frontend/             # React dashboard (SPA)
v1_legacy/            # original v1 bot, kept working for reference during refactor
```

## Status

Scaffolding only — no backend logic yet. Next step per `CLAUDE.md`'s build order:
database schema + Alembic migrations.
