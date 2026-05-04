# GDPR Lawful-Basis Register

_Last updated: 2026-05-01 · maintained by AgriFlow Compliance_

This register satisfies Article 30 GDPR. Every category of personal data processed
by AgriFlow is listed below with its purpose, lawful basis, retention, and recipients.

## 1. Account data (profiles)

| Field | Purpose | Lawful basis | Retention |
|---|---|---|---|
| Email | Authentication, transactional notices | Contract (Art. 6(1)(b)) | Account life + 12 months |
| Phone (E.164) | OTP, optional WhatsApp contact | Contract / Consent | Account life + 12 months |
| Preferred language | UI personalisation | Legitimate interest | Account life |

## 2. Producer profile data

| Field | Purpose | Lawful basis | Retention |
|---|---|---|---|
| Legal name, VAT/CIF | Verification, listing authenticity | Legitimate interest (Recital 47) | 7 years (tax law) |
| Coarse lat/lng (1 decimal ≈ 11 km) | Display on map | Legitimate interest | Account life |
| Plot geohash (6 char ≈ 1.2 km) | Provenance postcard | Legitimate interest | 5 years post-batch |

## 3. Marketing / outreach contacts (B2B)

| Field | Purpose | Lawful basis | Retention |
|---|---|---|---|
| Public coop email scraped from official sources | Cold outreach | Legitimate interest (Art. 6(1)(f)), with documented LIA | 2 years; deletion on opt-out |

## 4. Special categories

We do **not** process special-category data (health, religion, political views, biometrics, sexual orientation).

## 5. Sub-processors

| Sub-processor | Region | DPA signed | Function |
|---|---|---|---|
| Supabase | EU (Frankfurt, eu-central-1) | ✅ | Database, auth, storage |
| Vercel | EU (fra1) | ✅ | Edge hosting |
| Modal | EU (eu-west-1) | ✅ | Async pipeline + crew |
| OpenAI | US (zero-retention header set) | ✅ | Embeddings only (no PII) |
| Mistral AI | EU (Paris) | ✅ | LLM where PII may be present |
| Resend | EU | ✅ | Transactional email |
| Twilio | EU | ✅ | OTP / WhatsApp |

## 6. Data subject rights

- **Access / portability:** `GET /api/dsar` returns a JSON export within 7 days.
- **Erasure:** `DELETE /api/account` cascades all owned rows; audit log retained 12 months for fraud prevention (Art. 6(1)(f)).
- **Rectification:** Self-service via dashboard.
- **Objection / withdraw consent:** Single click in email footer or `POST /api/marketing/opt-out`.

## 7. Breach notification

72-hour notification to the lead supervisory authority (BfDI Germany, primary establishment) and affected users via email + dashboard banner.

## 8. DPO

Below the 250-employee threshold; we maintain a dedicated **GDPR contact**: `dpo@agriflow.eu`.

---

This document is a living artefact. Any change to data flows requires updating this file
and bumping its `Last updated` header before merge.
