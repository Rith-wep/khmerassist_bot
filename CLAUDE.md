# Khmer AI Customer Assistant — SaaS Platform (v2)

## What this project is

The multi-tenant SaaS evolution of a working v1 product: an AI customer assistant
(Telegram bot) for small businesses in Cambodia. In v1, one deployment served one
business, configured through files. In v2, ONE system serves MANY businesses:
each business signs up on a web dashboard, registers its own information through
an onboarding wizard, connects its own Telegram bot, and manages everything
self-service — its AI assistant, its leads, its conversations, its settings.

The v1 codebase already works and contains the proven bot logic (Khmer replies,
lead capture, human handoff, memory, error handling, logging). v2 refactors that
logic into a multi-tenant engine and adds the web platform around it.

## The golden rule: tenant isolation

Every piece of data belongs to exactly one business (tenant). Every database
table that holds tenant data MUST have a business_id column, and EVERY query
MUST filter by business_id — enforced by construction (helper functions /
repository layer that require business_id), never left to habit. Business A
must never, under any circumstance, see Business B's leads, conversations,
knowledge, or settings. Any code path that touches tenant data without a
business_id scope is a bug, even if it "works."

## Tech stack

- **Language:** Python 3.11+
- **Web framework:** FastAPI
- **Frontend:** React (single-page dashboard) talking to the FastAPI backend.
  Keep it simple: one SPA, no SSR framework. Built with Vite. Styling is
  Tailwind CSS (v4, via the `@tailwindcss/vite` plugin) — utility classes
  only, no separate component/design-system library beyond the shared
  components in `frontend/src/components/`. Follow the design system below
  on every page, present and future.
- **Database:** PostgreSQL (on Railway). SQLAlchemy ORM + Alembic migrations.
- **Bot framework:** python-telegram-bot (async), running MULTIPLE bots
  (one per business) from one process.
- **AI:** provider-agnostic module (currently Gemini API; must be swappable to
  Claude/other by config). All AI logic stays isolated in one module.
- **Auth:** email + password with secure hashing (bcrypt/argon2), session or
  JWT — pick the simplest secure standard. Google OAuth is a later add-on.
- **Hosting:** Railway (web service + Postgres). No Docker orchestration, no
  microservices, no message queues. Monolith until pain proves otherwise.

## Database schema (initial)

All tenant-owned tables include business_id (FK, indexed, part of uniqueness
where relevant).

- **businesses**: id, name, business_type (clinic/shop/real_estate/other),
  default_language, plan (trial/basic/standard/premium), status
  (active/paused/cancelled), created_at
- **users**: id, business_id, email (unique), password_hash, role (owner/staff),
  created_at
- **bot_configs**: id, business_id (unique — one bot per business in v2),
  telegram_bot_token (encrypted at rest), owner_chat_id, bot_username,
  is_active, last_started_at
- **knowledge_items**: id, business_id, category (service/faq/hours/location/
  policy/other), title, content_km, content_en, price (nullable), sort_order,
  updated_at  — replaces v1's business_info.md with structured rows
- **conversations**: id, business_id, customer_chat_id, customer_name
  (nullable), started_at, last_message_at, handed_off (bool)
- **messages**: id, conversation_id, business_id, direction (customer/bot),
  text, created_at
- **leads**: id, business_id, conversation_id, customer_name, phone, interest,
  created_at, notified_owner (bool)

Composite indexes on (business_id, created_at) style lookups. Bot tokens are
secrets: encrypt at rest, never log them, never return them fully via API
(mask like `12345***`).

## The bot engine (refactor of v1)

- On startup, load all active bot_configs and run each business's Telegram bot
  from the single process. Support adding/removing/restarting a bot at runtime
  when a business connects or pauses (no full redeploy to onboard a client).
- When a message arrives on any bot: resolve which business owns that bot →
  load that business's knowledge_items and settings → assemble the system
  prompt (same proven v1 rules: polite Khmer with correct honorifics, mirror
  the customer's language, understand Latin-letter Khmer, never invent answers,
  short mobile-friendly replies) → include that conversation's recent history →
  answer → persist conversation + message rows.
- Lead capture, human handoff, owner notification, and error handling behave
  exactly as proven in v1, but read/write the database and are scoped by
  business_id.
- Rate-limit and error behavior per v1: never crash, polite apology in the
  customer's language, retry with backoff, log errors with business_id context.

## Frontend design system — "fresh green on deep slate"

Applies to every page, present and future (Dashboard, Leads, Conversations,
Settings, onboarding wizard). Defined as Tailwind v4 theme tokens in
`frontend/src/index.css` (`@theme` block) — never scatter raw hex values in
components; use the token classes (`bg-base`, `text-accent`, etc.).

**Palette (kept intentionally tight — no new colors without updating this
section):**
- `bg-base` (#1E2130) — dark shell: sidebar, auth pages.
- `bg-surface` (#282C3E) — cards/panels/inputs on the dark shell.
- `bg-page` (#F6F7F9) — light main content area background.
- `accent` (#22C55E) / `accent-dark` (#16A34A hover) / `accent-soft`
  (#DCFCE7 tint) — primary buttons, active nav item, prices, key stats.
- `warning` (amber, #F59E0B) and `error` (red, #EF4444) — the only other
  semantic colors. Nothing else.
- `ink` (#111827) / `ink-muted` (#6B7280) — text on light surfaces.
  `shell-text` (near-white) / `shell-text-muted` — text on the dark shell.

**Typography:** headings use `font-heading` (Plus Jakarta Sans — bold,
rounded, distinctive), body text uses `font-sans` (Inter). Both stacks
include Noto Sans Khmer so Khmer content renders correctly everywhere
without a separate Khmer-only style.

**Layout:** dark sidebar (desktop) with the business name/logo top, nav
items with `lucide-react` icons, active item highlighted in green. On
mobile the sidebar becomes a fixed bottom tab bar (icons + tiny labels) —
not a hamburger drawer — since owners primarily use phones. Light content
area with a `PageHeader` (`frontend/src/components/PageHeader.jsx`): big
title + description left, primary green action button right. Cards are
white, `rounded-xl`, subtle border/shadow, consistent padding.

**Shared components** (`frontend/src/components/`) — reuse these rather
than re-styling inline: `Button` (variants: primary/secondary/destructive/
ghost), `CategoryBadge` (colored chips), `PageHeader`, `EmptyState`
(icon + message + CTA, never bare gray text), `Skeleton` (loading
placeholders — no spinners), `Sidebar`, `Layout`.

**Polish rules:** generous whitespace, consistent spacing scale, every
interactive element has a hover/focus state, transitions are 150–200ms
(`transition-colors duration-150` etc). No gradients-everywhere, no
glassmorphism — distinctiveness comes from the navy+green identity and
the heading font, not visual effects.

## Web app pages

1. **Sign up / Sign in** — creates a business + owner user in one flow.
2. **Onboarding wizard** (must be finishable by a non-technical Cambodian
   business owner, in English first, Khmer UI later):
   - Step 1: business basics (name, type, languages)
   - Step 2: business knowledge — friendly forms to add services with prices,
     opening hours, location, FAQs (in Khmer and/or English)
   - Step 3: connect Telegram — clear instructions with screenshots-style
     guidance: create bot via @BotFather, paste token; capture owner_chat_id
     by having the owner press /myid on their new bot (the engine provides
     this command)
   - Step 4: test screen — a web-based preview chat that exercises the real
     prompt + knowledge so the owner can try their assistant before going live
3. **Dashboard** — conversations today/this week, leads this week, after-hours
   messages handled, handoffs. Simple cards + one chart.
4. **Leads** — table (name, phone, interest, date), CSV export.
5. **Conversations** — list + read-only transcript view.
6. **Knowledge editor** — CRUD on knowledge_items; changes take effect on the
   next customer message (no restart needed).
7. **Settings** — bot connection status, pause/resume bot, business profile,
   plan display. Billing is MANUAL in v2: an admin (me) marks a business as
   paid; the UI only shows plan + status. No payment gateway yet.
8. **Internal admin page** (just for me): list businesses, status, mark paid,
   pause account.

## API design conventions

- REST endpoints under /api, all tenant endpoints derive business_id from the
  authenticated user — NEVER from a client-supplied parameter.
- Validation on all inputs; consistent error responses.
- Auth required on everything except signup/signin.

## Build order (strict — one step at a time, test before next)

1. **Database + migration**: schema above, Alembic set up, plus a one-time
   script that imports my current v1 client (business info file → knowledge
   rows, existing leads file → leads table).
2. **Engine on DB**: v1 bot logic refactored to read knowledge/config from
   Postgres and write conversations/leads to it. Still ONE business. Verify
   identical behavior to v1 (same test script as v1 steps 3–6).
3. **Multi-bot**: run 2+ bots from one process (test with a second dummy
   BotFather bot + fake business row). Prove tenant isolation with parallel
   conversations.
4. **Auth + knowledge editor**: signup/signin, and the first real UI page —
   editing knowledge_items live.
5. **Leads + conversations pages.**
6. **Onboarding wizard** (including runtime bot attach when a token is added).
7. **Dashboard stats + settings + internal admin page.**
8. **Deployment**: Railway web service + Postgres, env-var config, deployment
   docs for a first-timer.

Do not skip ahead. After each step, give me manual test instructions
(including what to check from my phone in Telegram where relevant).

## Development conventions (carried over from v1)

- Explain new concepts simply — I am learning as we build.
- Small functions, clear names, no over-engineering, no premature abstraction.
- Never crash: log, apologize in the customer's language, keep running.
- Secrets only via environment variables; .env in .gitignore; customer data
  (DB dumps, logs, exports) never committed.
- Log conversations and errors with business_id context.

## What NOT to do in v2

- No payment gateway integration (manual billing flag only).
- No Facebook Messenger yet (design the channel layer so it can be added, but
  build Telegram only).
- No Docker/Kubernetes/microservices/queues.
- No per-tenant databases or schemas — shared schema with business_id is the
  chosen pattern at this stage.
- No feature that a real pilot client hasn't asked for or that isn't listed
  above.
