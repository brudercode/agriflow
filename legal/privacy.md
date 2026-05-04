# AgriFlow — Privacy Notice

_Last updated: 2026-05-01_

This notice explains how AgriFlow processes personal data. The detailed Article 30
register is in [`gdpr_basis.md`](gdpr_basis.md). The AI-specific notice is in
[`ai_systems.md`](ai_systems.md).

## Controller

AgriFlow UG (i.G.), Berlin, Germany. Contact: `dpo@agriflow.eu`.

## What we collect

- Account: email, optional phone, preferred language.
- Producer profile: legal name, VAT/CIF, coarse location (1-decimal lat/lng), bio,
  optional website + WhatsApp number.
- Provenance records: 6-character plot geohash (~1.2 km), batch code, harvest date.
- Usage analytics: anonymised page views (PostHog EU host), error traces (Sentry).

We deliberately collect minimum-viable PII. We **never** collect exact farm coordinates,
biometric data, or special-category data.

## Why we collect it

- Operate the service (contract).
- Verify producer authenticity (legitimate interest, Recital 47 GDPR).
- Improve the product (legitimate interest, with opt-out).

## Where it's stored

EU only. Supabase Frankfurt, Vercel `fra1`, Modal `eu-west-1`, Mistral Paris. OpenAI is
used solely for embeddings of non-personal commodity text, with the zero-retention header
set on every request.

## Your rights

Access, rectification, erasure, portability, objection, restriction, and withdrawal of
consent. Exercise via the dashboard, or email `dpo@agriflow.eu`. Response within 30
days (often 7).

## Cookies

Strictly necessary cookies only. PostHog runs in cookieless EU mode.

## Marketing

Cooperative outreach is based on legitimate interest with documented LIA. Every email
includes a one-click opt-out that takes effect immediately.

## Complaints

You may lodge a complaint with the Berlin Beauftragte für Datenschutz und
Informationsfreiheit, or any EU supervisory authority of your residence.

## Changes

Material changes are notified by email + dashboard banner 14 days in advance.
