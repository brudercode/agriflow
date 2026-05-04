<div align="center">

# 🌾 AgriFlow

**A lean, GDPR-compliant European agricultural goods middleware platform.**

Real-time price transparency · Semantic discovery · Smart configurator · Traceability-lite · Referral connections

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)
[![Next.js](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org/)
[![Supabase](https://img.shields.io/badge/Supabase-Postgres%2Bpgvector-3ECF8E)](https://supabase.com/)
[![CrewAI](https://img.shields.io/badge/CrewAI-0.80%2B-orange)](https://crewai.com/)

</div>

---

## What this is

AgriFlow is **informational middleware** for the fragmented European fresh-produce + EVOO market.
We do **not** hold inventory, process payments, or take legal title — we publish public, indicative
listings and provenance "preparation aids," and we connect producers and buyers directly.

**Phase 1 focus:** tomatoes, berries, leafy greens, citrus, stone fruit + Extra Virgin Olive Oil
across Spain (Almería/Murcia/Andalucía), Italy, and Germany.

## Why the world needs this

- Small farmers and cooperatives have **no honest, real-time view** of EU wholesale prices.
- Buyers (specialty importers, distributors) waste days on email chains discovering origins.
- EUDR + UTP regulations are scaring small actors. AgriFlow gives them voluntary,
  well-structured **preparation aids** — without taking on operator obligations ourselves.

## What's in the box

| Layer | Stack |
|---|---|
| Frontend | Next.js 15 (App Router, RSC) · Tailwind v4 · shadcn/ui · next-intl (EN/ES/IT/DE) |
| Backend | Next.js Route Handlers · Supabase Edge Functions |
| DB / Auth / Storage | Supabase (Postgres 16 · pgvector · RLS · Auth · Realtime) |
| Vector store | `pgvector` (HNSW, halfvec) |
| Agents | CrewAI 0.80+ on Modal · Groq Llama 3.3 70B · Mistral Small (EU) |
| Scraping | `httpx[http2]` + `selectolax` + Playwright (only when JS-required) |
| Hosting | Vercel · Supabase EU (`eu-central-1`) · Modal `eu-west-1` · Cloudflare DNS |
| Email | Resend (DKIM/SPF) · React Email |
| Observability | Sentry · Axiom · Supabase logs · PostHog (EU) |

**Estimated MVP run-rate: ~€20/month.** Free tiers cover everything except domain + tiny LLM spend.

## Repository layout

```
agriflow/
├── apps/web/              # Next.js 15 application
│   ├── app/               # App Router routes (search, dashboard, /p/[token])
│   ├── lib/               # configurator.ts · provenance.ts · verify.ts
│   └── prompts/           # LLM prompt templates
├── supabase/
│   ├── migrations/        # 0001_init.sql (schema + RLS + pgvector)
│   └── config.toml
├── pipeline/              # Async price ingestion (Python 3.12)
│   ├── ingest.py
│   ├── modal_app.py       # Modal scheduled cron
│   └── adapters/          # FreshFel, POOLRED, MercaBarna, ISMEA, BLE
├── crew/                  # CrewAI agent specifications
│   ├── agents.py          # 6 specialists
│   ├── tools.py           # Supabase + embedding + compliance tools
│   └── orchestrator.py
├── legal/                 # ToS, privacy, GDPR basis register, AI systems card
├── docs/                  # ROADMAP, OUTREACH templates
└── .github/workflows/     # CI: lint, typecheck, supabase migration check
```

## Quick start

### Prerequisites

- Node 20+ and `pnpm` 9+
- Python 3.12 + [`uv`](https://docs.astral.sh/uv/) (or `pip`)
- Supabase CLI 1.180+
- Free accounts on: Supabase, Vercel, Modal, Groq, OpenAI, Resend, Upstash

### 5-command bootstrap

```bash
git clone https://github.com/brudercode/agriflow.git && cd agriflow
pnpm install                                     # installs apps/web deps
cp .env.example .env.local                       # fill in your keys
supabase start && supabase db push               # applies 0001_init.sql locally
pnpm -C apps/web dev                             # http://localhost:3000
```

### Production deploy

```bash
# 1. Frontend
pnpm dlx vercel link
pnpm dlx vercel env pull
pnpm dlx vercel --prod

# 2. Database
supabase link --project-ref <your-ref>
supabase db push

# 3. Async pipeline + agent crew
uv sync                                          # or: pip install -e .[pipeline,crew]
modal token new                                  # one-time
modal deploy pipeline/modal_app.py
modal deploy crew/orchestrator.py
```

### First-day verification

After deploy, you should see:

1. `https://your-app.vercel.app` loads the multilingual landing page.
2. `supabase.from("price_history").select("count")` returns rows within 6 hours of first cron tick.
3. `POST /api/search` with `{"q": "organic San Marzano tomato"}` returns ≤ 400 ms.
4. Creating a producer → uploading a cert → recomputing badges shows ≥ 1 badge.
5. Creating a `traceability_record` → public `/p/[token]` page renders + PDF downloads.

## Daily-useful features (built into the MVP)

- **Harvest journal** — phone-first, one tap to record today's pick (qty, photo, notes).
- **Price ticker** — your products' wholesale prices across MercaBarna · POOLRED · ISMEA · BLE.
- **PostcardSSL** — auto-generated QR + PDF "preparation aid" for any harvest batch.
- **Smart configurator** — buyers describe what they need in plain language; we surface matches.
- **Multilingual outreach drafts** — pre-tailored cold emails for ES/IT/DE in your voice.

## Core APIs

| Route | Method | Purpose |
|---|---|---|
| `/api/search` | POST | Semantic search across active listings (rate-limited 30/min/IP) |
| `/api/configurator` | POST | Convert structured intent → query + filters |
| `/api/provenance` | POST | Issue a PostcardSSL traceability record (auth required) |
| `/api/verify/vies` | POST | VIES VAT check (free, EU) |
| `/api/dsar` | GET | GDPR data export for the authenticated user |
| `/p/[qr_token]` | GET | Public provenance postcard view |

## Compliance posture (read this!)

AgriFlow is intentionally **not** a marketplace, **not** an EUDR operator, **not** a payment intermediary.

- **GDPR**: All data resides in EU regions. We collect minimum viable PII; coarse geohash only.
- **EUDR**: PostcardSSL is a *voluntary preparation aid*, never asserted as a Due Diligence Statement.
  We hard-block forbidden phrases like "guaranteed deforestation-free" via `ComplianceCheckerTool`.
- **UTP**: We facilitate discovery only. Title transfer, payment terms, and contracts are 100% between
  producer and buyer.
- **AI Act**: Limited-risk transparency notices on AI-generated translations and summaries.

See [`legal/gdpr_basis.md`](legal/gdpr_basis.md) and [`legal/ai_systems.md`](legal/ai_systems.md).

## 8-week MVP roadmap

| Week | Theme | Exit criteria |
|---|---|---|
| 1 | Foundations · auth · schema | RLS attack-tested, 1 producer signs up |
| 2 | Producer onboarding · badges | 10 friendly coops onboarded |
| 3 | Price ingestion crew | ≥ 1k price rows/day, 95% job success |
| 4 | Semantic search + configurator | Median latency < 400 ms, 50 listings live |
| 5 | Traceability-lite + harvest journal | 30 PostcardSSLs issued |
| 6 | Outreach + referral intents | 200 emails sent, 5% reply, 20 intents |
| 7 | Polish + analytics + i18n QA | TTI < 2.5 s on 3G, WCAG AA |
| 8 | Beta launch | 100 producers, 500 listings, 25 buyers |

Full breakdown in [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Contributing

We love small, surgical PRs. Read [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`SECURITY.md`](SECURITY.md).

If you're a producer, cooperative, or buyer interested in piloting AgriFlow, email
**hello@agriflow.eu** — we onboard cooperatives white-glove.

## License

AGPL-3.0-or-later. See [`LICENSE`](LICENSE). Commercial licensing for hosted forks: email us.

---

<div align="center">
<sub>Built with care for European farmers. Made in the EU. 🇪🇺</sub>
</div>
