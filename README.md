# Khmer AI Customer Assistant — SaaS (v2)

Multi-tenant evolution of the Telegram customer-assistant bot for small businesses
in Cambodia. See [CLAUDE.md](CLAUDE.md) for the full product plan, schema, and
build order this project follows.

- **v2 (this repo root)** — FastAPI backend (`app/`), Alembic migrations
  (`alembic/`), React dashboard (`frontend/`).
- **v1 (working reference)** — [v1_legacy/](v1_legacy/): the original single-tenant
  Telegram bot this project was refactored from. Still runnable as-is; see
  [v1_legacy/Readme.md](v1_legacy/Readme.md). The multi-tenant `app/` code below
  ports v1's bot logic (Khmer replies, lead capture, human handoff, memory,
  error handling) onto Postgres, scoped by `business_id`.

## Status

Steps 1–7 of `CLAUDE.md`'s build order are implemented: schema + migrations,
the DB-backed engine, multi-bot support, auth + knowledge editor, leads +
conversations pages, the onboarding wizard, and dashboard/settings/admin
pages. **Not yet done:** step 8 (Railway deployment) and Facebook/other
channels. See [Known gaps](#known-gaps--todos) below for things that are
scaffolded but not fully real yet (dashboard stats are partly mocked).

## Layout

```
app/
├── main.py            # FastAPI app entry point, router registration, CORS
├── run_bot.py          # CLI entry point for the Telegram bot engine process
├── engine.py            # BotEngine: runs every business's bot concurrently
├── core/                 # settings, JWT/password/token-encryption security, deps, time
├── db/                    # SQLAlchemy engine/session setup
├── models/                 # SQLAlchemy models (one table per tenant concept)
├── repositories/             # tenant-scoped data access layer
├── schemas/                    # Pydantic request/response schemas
├── routers/                     # FastAPI endpoints (REST API under /api)
├── services/                     # business logic: AI, leads, handoff, notifications
└── channels/                      # messaging channel adapters (Telegram now)
alembic/                 # DB migrations
frontend/                  # React dashboard (SPA, Vite + Tailwind v4)
prompts/                      # shared system prompt used by the AI service
scripts/                        # one-off/import/seed scripts
v1_legacy/                        # original v1 bot, kept working for reference
```

## Backend

### Entry points

- **`app/main.py`** — FastAPI app. Registers CORS for the local dev frontend
  (`http://localhost:5173`), includes all routers under `/api`, and exposes
  `GET /health`. The web API and the bot engine run as **separate processes**
  (`uvicorn app.main:app` vs `python -m app.run_bot`) — there is no startup
  hook that launches bots from the API process.
- **`app/engine.py` (`BotEngine`)** — Loads every active `BotConfig` (joined
  with its `Business`) and runs each business's Telegram bot as its own
  `python-telegram-bot` `Application`, with `business_id`/`owner_chat_id`
  bound into that application's `bot_data` so handlers never need a global
  lookup. `poll_for_new_bots()` re-checks every 30s and starts/stops bots as
  businesses connect or pause — **no redeploy needed to onboard a client**.
  A single business's bot crashing (bad token, exception) is caught and
  logged with its `business_id`; it doesn't affect other tenants' bots.
- **`app/run_bot.py`** — CLI entry point (`python -m app.run_bot`). Sets up
  console + rotating file logging (`logs/errors.log`, daily rotation, 30-day
  retention) and runs `BotEngine().run_forever()`.
- **`app/channels/telegram_bot.py`** — Builds one business's bot `Application`
  and registers its handlers:
  - `/start` — claims an admin invite if launched via `admin_{token}` deep
    link, otherwise claims bot ownership if unclaimed, else sends the
    business's configured welcome message.
  - `/reset` — clears conversation history + unanswered-question streak.
  - `/myid` — echoes the chat ID (also claims ownership) — this is how an
    owner links their Telegram account during onboarding.
  - catch-all text handler — routes to `services.ai.get_ai_reply`, then
    `services.leads.process_lead` / `services.handoff.notify_owner` as
    needed.
  - error handler — logs and replies with a Khmer apology instead of
    crashing, per the "never crash" rule.

### Core (`app/core/`)

| File | Purpose |
|---|---|
| `config.py` | `Settings` (pydantic-settings, reads `.env`): `database_url`, `secret_key`, `encryption_key`, `gemini_api_key`, `ai_model`, `app_env`. |
| `security.py` | bcrypt password hashing; JWT create/decode (`HS256`, 7-day expiry); Fernet encrypt/decrypt for storing Telegram bot tokens at rest. |
| `deps.py` | `get_current_user` FastAPI dependency — decodes the bearer token **and** re-checks the user against the DB on every request (not just trusting the token), so a deleted user is rejected immediately. |
| `time.py` | `utcnow()` — naive-UTC datetime helper matching the DB column convention. |

### Data model (`app/models/`)

Every tenant table carries `business_id`, per the golden rule in
[CLAUDE.md](CLAUDE.md#the-golden-rule-tenant-isolation):

- **`Business`** — name, type (clinic/shop/real_estate/other), plan, status,
  onboarding progress, profile fields (address/phone/timezone/business hours/
  logo), AI behavior fields (assistant name, welcome messages, tone,
  handoff-on-unsure), notification toggles.
- **`User`** — owner/staff account (email, password hash) tied to a business.
- **`Admin`** — extra Telegram accounts (besides the primary owner) that
  receive owner-style notifications.
- **`AdminInvite`** — one-time, 10-minute-expiry deep-link token consumed by
  `/start admin_{token}`.
- **`BotConfig`** — one Telegram bot per business (encrypted token, owner
  chat id, active flag).
- **`KnowledgeItem`** — structured facts (category, title, Khmer/English
  content, price, sort order) that replace v1's flat `business_info.md`.
- **`Conversation`** / **`Message`** — per-customer chat threads and their
  messages, tagged `customer`/`bot`.
- **`Lead`** — captured name/phone/interest, linked to the conversation it
  came from.

### Repositories (`app/repositories/`)

A `TenantRepository[Model]` base class is bound to a `business_id` at
construction and every method (`list`, `get`, `create`, `delete`) filters by
it automatically — no method accepts `business_id` as a parameter, so it's
architecturally impossible to forget the tenant filter. The two lookups that
legitimately need to cross tenants (finding a user by email before login;
checking a Telegram bot username isn't already claimed by another business)
are explicit module-level functions, not methods on the scoped repository —
making cross-tenant access opt-in and visible in a code review.

### API (`app/routers/`, all under `/api`, auth required except signup/signin)

| Router | Endpoints |
|---|---|
| `auth` | `POST /auth/signup`, `POST /auth/signin` — creates/authenticates a business + owner user, returns a JWT. |
| `onboarding` | `GET /status`, `PUT /step1` (basics), `GET /templates`, `POST /step2/complete` (knowledge), `POST /telegram/validate-token`, `POST /telegram/connect`, `GET /telegram/status`, `POST /step3/complete`, `GET /checklist`, `POST /preview-chat` (sandbox chat, no persistence), `POST /go-live`. |
| `knowledge` | `GET/POST /knowledge`, `PUT/DELETE /knowledge/{id}` — full CRUD on knowledge items. |
| `leads` | `GET /leads` (paginated), `GET /leads/export` (CSV download). |
| `conversations` | `GET /conversations` (paginated, with message counts), `GET /conversations/{id}` (full transcript). |
| `dashboard` | `GET /dashboard/stats?range=7d|30d|90d` — see [Known gaps](#known-gaps--todos). |
| `settings` | `GET /settings`, `PUT /profile`, `POST /telegram/disconnect`, `PUT /ai-behavior`, `PUT /notifications`, `DELETE /knowledge` (bulk), `DELETE /account` (type-to-confirm, cascades). |
| `admins` | `GET /admins`, `POST /admins/invite` (generates a `t.me/{bot}?start=admin_{token}` link), `DELETE /admins/{id}`. |

### Services (`app/services/`)

- **`ai.py`** — the only provider-aware module (currently Google Gemini via
  `google-genai`, model configurable via `AI_MODEL`). Per customer message it
  makes two calls: a reply generation call (system prompt = shared rules in
  `prompts/system_prompt.md` + business tone + rendered knowledge items,
  falls back to a Khmer apology if generation fails) and a silent structured
  classification call that detects completed leads and handoff signals,
  never shown to the customer. Two consecutive unanswered questions trigger
  a handoff. `generate_preview_reply()` is the no-persistence variant used by
  the onboarding "try it out" screen.
- **`leads.py`** — persists a captured `Lead` and notifies the owner/admins.
- **`handoff.py`** — builds a short transcript and notifies the owner/admins
  that a conversation needs a human.
- **`notifications.py`** — shared fan-out: sends a Telegram message to the
  owner chat + all connected `Admin` rows, respecting the business's
  per-category notification toggle.
- **`knowledge.py`** — renders a business's `KnowledgeItem` rows into the
  markdown-ish facts text fed into the AI system prompt.
- **`knowledge_templates.py`** — static suggested services/FAQs per business
  type, used to prefill onboarding step 2.
- **`telegram_api.py`** — direct `getMe` HTTP call for validating a bot token
  during onboarding/settings, outside the bot's own Application lifecycle.
- **`conversation_state.py`** — conversation/message persistence, recent-
  history retrieval (last 10 exchanges), and the in-process unanswered-
  question streak used for handoff-after-2-misses.

### Database migrations (`alembic/versions/`)

1. **`d2c7e9e6fd5f_initial_schema.py`** — initial schema: businesses, users,
   bot_configs, knowledge_items, conversations, messages, leads.
2. **`88e954de5061_onboarding_fields.py`** — adds onboarding step/completion
   tracking to `businesses`; makes `bot_configs.owner_chat_id` nullable
   (owner is linked later via `/start` or `/myid`).
3. **`a3130a8c48ee_settings_fields.py`** — adds business profile fields,
   AI behavior fields, notification toggles, and the `admins` +
   `admin_invites` tables.

## Frontend (`frontend/src/`)

React 19 + react-router-dom 7 SPA, built with Vite, styled with Tailwind CSS
v4 per the design system in [CLAUDE.md](CLAUDE.md#frontend-design-system--fresh-green-on-deep-slate)
("fresh green on deep slate" — dark sidebar shell, light content area,
green accent, Plus Jakarta Sans headings + Inter body with Noto Sans Khmer
fallback everywhere).

- **`App.jsx`** — route table and guard logic: `/signup`/`/signin` redirect
  home if already authenticated; `/onboarding` is only reachable while
  authenticated with onboarding incomplete; the main pages (`/dashboard`,
  `/knowledge`, `/leads`, `/conversations`, `/conversations/:id`,
  `/settings`) require both auth and completed onboarding. `/` redirects
  based on current state.
- **`context/AuthContext.jsx`** — JWT + business name kept in `localStorage`;
  no client-side token refresh (relies on the 7-day JWT and 401 handling).
- **`api/client.js`** — `apiFetch` (JSON fetch to `/api{path}` with bearer
  auth, throws `ApiError` on failure) and `downloadFile` (blob download,
  used for CSV export).

### Pages

| Page | What it does |
|---|---|
| `Dashboard.jsx` | Stat cards, conversations chart, recent leads/conversations, a "finish setup" checklist, and an empty state with a copyable bot link for brand-new businesses. |
| `Conversations.jsx` / `ConversationDetail.jsx` | Paginated conversation list with handoff badges → chat-bubble transcript view. |
| `KnowledgeEditor.jsx` | Full CRUD on knowledge items with category badges and inline add/edit forms. |
| `Leads.jsx` | Paginated leads table/cards with `tel:` links and CSV export. |
| `Settings.jsx` | Loads and renders the five settings sections below with shared toast notifications. |
| `SignIn.jsx` / `SignUp.jsx` | Auth forms. |

### Onboarding wizard (`pages/onboarding/`)

`Onboarding.jsx` orchestrates a 4-step flow (own header, no dashboard chrome)
matching the business's `onboarding_step`:

1. **`Step1Basics.jsx`** — name, business type, customer language.
2. **`Step2Knowledge.jsx`** — guided knowledge setup: required location +
   hours, plus suggested services/FAQs pulled from templates that can be
   added, skipped, or replaced with custom items.
3. **`Step3Telegram.jsx`** — BotFather instructions, token validate/connect,
   then polls connection status every 3s waiting for the owner to run
   `/start` or `/myid` on their new bot.
4. **`Step4GoLive.jsx`** — checklist recap, a live "try it out" preview chat
   against the real prompt + knowledge, then `go-live` and redirect to the
   dashboard.

### Settings sections (`pages/settings/`)

`ProfileSection`, `TelegramSection` (connect/disconnect), `AdminsSection`
(invite links + notification toggles), `AiBehaviorSection` (assistant name,
welcome messages, tone, handoff-on-unsure), `DangerZoneSection` (bulk-delete
knowledge / delete account, both behind a type-to-confirm dialog).

### Shared components (`frontend/src/components/`)

`Button`, `Layout`, `Sidebar` (desktop rail + mobile bottom tab bar),
`Skeleton` (+ `RowListSkeleton`/`KnowledgeListSkeleton`), `PageHeader`,
`EmptyState`, `CategoryBadge`, `ConfirmTypeDialog`, `ConversationsChart`
(recharts, 7d/30d/90d switcher), `KnowledgeItemForm`, `Modal`, `Pagination`,
`SectionCard`, `StatCard`, `Stepper`, `Toast` (+ `useToasts`). Route
protection lives inline in `App.jsx`'s `Protected` wrapper, not as a
separate component.

## Scripts (`scripts/`)

- **`import_v1_client.py`** — one-time import of a v1 client's
  `business_info.md` and `leads.json` into the v2 `knowledge_items`/`leads`
  tables.
- **`verify_import.py`** — sanity-checks an import ran correctly.
- **`seed_test_business.py`** — creates a throwaway business + user for local
  testing.

## Running locally

Backend:

```
pip install -r requirements.txt
cp .env.example .env   # fill in DATABASE_URL, SECRET_KEY, ENCRYPTION_KEY, GEMINI_API_KEY
alembic upgrade head
uvicorn app.main:app --reload         # web API on :8000
python -m app.run_bot                 # Telegram bot engine, separate process
```

Frontend:

```
cd frontend
npm install
npm run dev                            # dashboard on :5173 (proxies /api to :8000)
```

## Known gaps / TODOs

- **Dashboard stats are partly mocked** (`app/routers/dashboard.py`):
  onboarding-checklist booleans and recent leads/conversations are real, but
  conversation/lead/payment counts, percent-change, and the chart series are
  seeded random data pending real aggregation queries.
- **Railway deployment** (build-order step 8) not started: no Procfile/deploy
  docs yet, env-var wiring is local-only.
- **Facebook Messenger / other channels**: not built, per `CLAUDE.md` — the
  channel layer is Telegram-only by design at this stage.
- **Internal admin page** (`CLAUDE.md`'s "list businesses, mark paid, pause
  account" page for the platform operator) is not built yet — `app/routers/admins.py`
  and `pages/settings/AdminsSection.jsx` only cover a *business's own*
  Telegram admin accounts, which is a different feature with a similar name.
  Billing stays manual-only by design (no payment gateway) until this lands.
