# Khmer AI Customer Assistant

**An AI-powered Telegram assistant that answers customers, captures sales leads, and knows when to call in a human — built for small businesses in Cambodia.**

[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Telegram Bot API](https://img.shields.io/badge/Telegram-Bot%20API-26A5E4?logo=telegram&logoColor=white)](https://core.telegram.org/bots)
[![Gemini API](https://img.shields.io/badge/AI-Google%20Gemini-4285F4?logo=googlegemini&logoColor=white)](https://ai.google.dev/)
[![Status](https://img.shields.io/badge/status-active%20development-yellow)]()

---

## The Problem

Small businesses in Cambodia — clinics, shops, real estate agencies — get most of their
customer contact through Telegram and Facebook Messenger, in Khmer. That traffic is
constant, but the owner isn't. Every question about prices, hours, or location that
comes in at 9 PM either waits until morning or gets a rushed, inconsistent answer. Every
customer who messages with real buying intent is a lead that can slip away if nobody
follows up in time — and hiring a round-the-clock receptionist isn't realistic for a
business this size.

Generic chatbot builders don't solve this well either: they're built for English, they
require the owner to wire up flows and intents by hand, and they have no idea what
"sample business" content is safe to invent versus what must come straight from the
business's own price list.

## The Solution

This bot sits in front of a business's Telegram account and behaves like a well-trained
front-desk employee who never sleeps:

- It answers customer questions **only** from that business's own facts file — no
  hallucinated prices or made-up policies.
- It replies in **whatever language the customer used** — Khmer script, English, or
  Khmer typed in Latin letters ("som sur tlai") — with the tone of a polite Cambodian
  receptionist.
- It notices when a conversation has turned into a real sale opportunity, collects a
  name and phone number, and pings the owner on Telegram instantly.
- It notices when it's out of its depth — an answer it can't find, or a customer who's
  upset or asking for a person — and escalates to the owner with the conversation
  context attached, instead of stalling or guessing.

The result: one Markdown file of business facts and one `.env` value (the owner's chat
ID) is all it takes to stand this up for a brand-new client. No code changes, no
per-client branching logic.

## Key Features

| Feature | What it does |
|---|---|
| **Multilingual understanding** | Detects and mirrors the customer's language — Khmer script, English, or romanized Khmer — and always replies in natural, honorific-correct Khmer by default. |
| **Grounded answers** | Every fact comes from [`business/business_info.md`](business/business_info.md). If it's not written there, the bot says so instead of guessing. |
| **Conversation memory** | Remembers the last several exchanges per customer so follow-up questions ("how much is the second one?") make sense. `/reset` clears a chat's memory. |
| **Lead capture** | Recognizes buying intent, asks for name and phone one question at a time, then saves the lead and messages the owner with the details. |
| **Human handoff** | Escalates to the owner — with recent conversation context — when the customer is upset, explicitly asks for a person, or the bot fails to answer twice in a row. |
| **Resilient by design** | AI calls retry automatically; if the model is still unreachable, the customer gets a polite apology instead of silence or a crash. |
| **Conversation logging** | Every exchange is written to a daily log file for later review and prompt tuning. |

## How It Works

Each incoming message triggers two focused AI calls instead of one overloaded one —
this keeps the customer-facing reply reliable even while the bot is silently deciding
whether to flag a lead or a handoff.

```
Customer message (Telegram)
        │
        ▼
┌───────────────────────┐
│ 1. Generate reply      │  business_info.md + system_prompt.md + recent history
│    (visible to customer)
└───────────────────────┘
        │
        ▼
   Reply sent to customer ──► logged to logs/YYYY-MM-DD.log
        │
        ▼
┌───────────────────────┐
│ 2. Classify (silent)   │  Did this complete a lead? Does this need a human?
└───────────────────────┘
        │
   ┌────┴─────┐
   ▼          ▼
 Lead      Handoff
 found?    needed?
   │          │
   ▼          ▼
leads.json   Owner notified on Telegram
+ owner          with conversation context
notified
```

## Tech Stack

| Layer | Choice |
|---|---|
| Language | Python 3.11+ |
| Messaging platform | Telegram, via [`python-telegram-bot`](https://github.com/python-telegram-bot/python-telegram-bot) (async, polling) |
| AI model | Google Gemini (`google-genai` SDK) — swappable, isolated entirely in [`bot/ai.py`](bot/ai.py) |
| Storage | In-memory conversation state; leads persisted to `leads.json` |
| Config | `.env` via `python-dotenv`, loaded once in [`config.py`](config.py) |

The AI provider is intentionally isolated behind one file. Nothing else in the codebase
knows or cares whether the model behind it is Gemini, Claude, or anything else.

## Project Structure

```
customer-assistant/
├── main.py                 # entry point — starts the bot (polling)
├── bot/
│   ├── handlers.py         # Telegram message handlers (/reset, /myid, message routing)
│   ├── ai.py                # Gemini calls + prompt assembly (the only AI-provider-aware file)
│   ├── leads.py             # lead persistence + owner notification
│   ├── handoff.py           # human handoff notification with conversation context
│   ├── memory.py            # per-chat history + conversation state
│   └── conversation_log.py  # daily exchange logs
├── business/
│   └── business_info.md    # THE CLIENT'S DATA — services, prices, hours, FAQs
├── prompts/
│   └── system_prompt.md    # the bot's personality and behavior rules
├── config.py                # loads and validates settings from .env
├── .env.example              # template of required environment variables
├── leads.json                # captured leads (generated at runtime)
└── logs/                      # daily conversation + error logs (generated at runtime)
```

## Getting Started

**1. Install dependencies**

```bash
pip install -r requirements.txt
```

**2. Configure environment variables**

```bash
cp .env.example .env
```

Fill in `.env` with:

| Variable | Where to get it |
|---|---|
| `TELEGRAM_BOT_TOKEN` | [@BotFather](https://t.me/BotFather) on Telegram |
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com/) |
| `AI_MODEL` | e.g. `gemini-2.5-flash` |
| `OWNER_CHAT_ID` | your numeric Telegram chat ID — message [@userinfobot](https://t.me/userinfobot), or run the bot and send it `/myid` |

**3. Run the bot**

```bash
python main.py
```

Message your bot on Telegram — try asking in Khmer, English, or romanized Khmer.

## Customizing for a New Client

Deploying this for a different business should never touch the Python code. Two edits
are all that's needed:

1. Rewrite [`business/business_info.md`](business/business_info.md) with the new
   client's services, prices, hours, and FAQs.
2. Point `OWNER_CHAT_ID` in `.env` at that client's owner.

The bot's personality and rules in [`prompts/system_prompt.md`](prompts/system_prompt.md)
stay shared across every client.

## Roadmap

- [x] Multilingual AI replies grounded in per-client business data
- [x] Conversation memory
- [x] Lead capture with owner notification
- [x] Human handoff with conversation context
- [x] Conversation logging
- [ ] Facebook Messenger support
- [ ] Persistent storage (SQLite) for conversation history
- [ ] Deployment guide for a low-cost cloud host

## Why This Project Exists

This isn't a tutorial project — it's being built as a real product to sell to small
Cambodian businesses as a monthly service. The priorities reflect that: answers must
never be invented, the owner must never be left in the dark about a hot lead or an
unhappy customer, and onboarding a new client should be a content edit, not a
development task.
