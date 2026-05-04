# Contributing to AgriFlow

We're aiming for a tiny, sharp codebase that 1–2 developers can fully hold in their
heads. Small surgical PRs welcome.

## Ground rules

1. **Small PRs.** ≤ 400 lines of diff is the sweet spot. If you need more, split.
2. **Tests where they pay back.** Pure logic (configurator, verify, provenance hash):
   100 % covered. UI: smoke tests are fine.
3. **Compliance check is non-negotiable.** Any change that touches outreach text,
   listing copy, or external claims must pass `ComplianceCheckerTool` in CI.
4. **No PII in embeddings.** If you change what gets embedded, document why.
5. **i18n from day 1.** Any user-visible string goes through `next-intl`.

## Local setup

```bash
git clone https://github.com/brudercode/agriflow.git
cd agriflow
pnpm install
cp .env.example .env.local
supabase start
supabase db push
pnpm -C apps/web dev
```

For the Python crew:

```bash
uv sync
uv run python -m pipeline.ingest --source freshfel
uv run python -m crew.orchestrator
```

## Branch & commit style

- Branch: `feat/<short-handle>`, `fix/<short-handle>`, `chore/...`, `docs/...`
- Commits: Conventional Commits (`feat: …`, `fix: …`). Scope optional.
- PR title mirrors the squash-merge commit title.

## Code style

- TypeScript: enforced by `next lint` + Prettier.
- Python: `ruff` + `mypy --strict`.
- SQL: keep migrations idempotent and forward-only.

## Reviewing

- Every PR needs ≥ 1 approval and a green CI.
- Reviewer checks: correctness, simplicity, compliance, tests.

## Filing issues

- Bug? Reproduction steps + expected vs. actual.
- Feature? Problem statement first, solution second.
- Security? **Do not file publicly.** See [`SECURITY.md`](SECURITY.md).

Thanks for keeping AgriFlow lean and useful. 🌾
