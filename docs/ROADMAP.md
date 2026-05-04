# AgriFlow MVP Roadmap (8 weeks)

| Week | Theme | Deliverables | Exit criteria |
|---|---|---|---|
| **1** | Foundations | Supabase project (`eu-central-1`), schema + RLS, Next.js 15 scaffold, i18n EN/ES/IT/DE, magic-link + WhatsApp OTP auth, public landing page. | A producer can sign up and create a profile. RLS verified by attack tests. |
| **2** | Producer onboarding | Profile editor, certification uploads, VIES check, badge engine, public producer page, 5 internal seed producers. | 10 friendly-coop producers onboarded; all show ≥ 1 badge. |
| **3** | Price ingestion | `pipeline/ingest.py` for FreshFel + POOLRED + MercaBarna. Modal cron live. Public price-trend chart per product. | ≥ 1k price rows/day; 95 % job success. |
| **4** | Semantic search + configurator | Embedding job, `match_listings` RPC, `/search`, configurator UI, listing CRUD. | Median search latency < 400 ms; ≥ 50 listings live. |
| **5** | Traceability-lite + harvest journal | PostcardSSL flow, public `/p/[token]` page, harvest journal mobile screen, photo upload. | 30 traceability records issued; 5 farmers using journal weekly. |
| **6** | Outreach + referral intents | Cold-email templates (DE/ES/IT), Resend integration, referral form, producer notifications. | 200 outreach emails sent; 5 % reply rate; 20 intents created. |
| **7** | Polish + analytics | PostHog (EU) events, weekly digest emails, Spanish/Italian UI QA, mobile audit, accessibility (WCAG AA). | TTI < 2.5 s on 3G mid-range Android. |
| **8** | Beta launch | Press kit, 3 cooperative case studies, ProductHunt + LinkedIn launch, security checklist (Supabase scan, Snyk). | 100 producers, 500 listings, 25 verified buyers. |

Each Friday: live demo + commit a changelog entry.
