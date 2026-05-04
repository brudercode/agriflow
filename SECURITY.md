# Security Policy

## Reporting a vulnerability

Please **do not** open a public GitHub issue.

Email **`security@agriflow.eu`** with:

- A clear description of the issue
- Reproduction steps or proof-of-concept
- Affected versions / commit SHAs if known
- Your name + GitHub handle if you'd like public credit

We aim to acknowledge within **48 hours** and to issue a fix or coordinated disclosure
within **30 days** for high-severity findings.

## Supported versions

Only the `main` branch is supported during the beta. Once we tag `v1.0.0`, we will
maintain the latest minor for at least 6 months.

## Scope

In scope:

- This repository (`apps/web`, `pipeline`, `crew`, `supabase`)
- Production hosts: `agriflow.eu`, `*.vercel.app` deployments
- Supabase project (do not run intrusive tests; report theoretical issues)

Out of scope:

- Third-party services (Supabase, Vercel, Modal) — report to their respective programmes
- Social engineering, physical attacks, denial-of-service

## Safe harbour

We will not pursue legal action against researchers who:

- Make a good-faith effort to avoid privacy violations and service disruption
- Only access data necessary to demonstrate the issue
- Give us reasonable time to fix before any public disclosure
