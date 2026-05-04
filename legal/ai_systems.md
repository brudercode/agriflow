# AI Systems Card (EU AI Act readiness)

AgriFlow uses AI in three places. All fall under the **limited-risk** category of the
EU AI Act (Regulation 2024/1689). Transparency notices are surfaced at point of use.

## 1. Translation & summarisation (LLM)

| Property | Value |
|---|---|
| Provider | Mistral AI (`mistral-small-latest`, EU-hosted) and Groq (`llama-3.3-70b-versatile`) |
| Use | Translate listings EN ⇄ ES/IT/DE; summarise producer bios |
| Inputs | Public listing text, producer-supplied bios |
| Risk class | Limited |
| Mitigation | UI label "AI-generated translation"; opt-out toggle per producer |
| Audit | Prompt + response logged 30 days for QA |

## 2. Semantic search (embeddings)

| Property | Value |
|---|---|
| Provider | OpenAI `text-embedding-3-small` (zero-retention) |
| Use | Convert query + listing text → 1536-dim vectors |
| Inputs | Buyer query (no PII), listing text |
| Risk class | Minimal |
| Mitigation | No personal data ever sent (queries are about commodities) |

## 3. Outreach drafts (LLM)

| Property | Value |
|---|---|
| Provider | Groq Llama 3.3 70B |
| Use | Draft cold emails — *human-reviewed before send* |
| Inputs | Public B2B contact context |
| Risk class | Limited |
| Mitigation | No automated send; ComplianceCheckerTool runs before send |

## Forbidden uses (hard-blocked)

- Profiling or scoring of individuals
- Automated decision-making with legal effect (no contracts auto-signed)
- Generating any "guaranteed deforestation-free" claim — the
  `ComplianceCheckerTool` rejects such phrases at runtime.

## Human oversight

- Outreach Strategist agent never auto-sends. All drafts queue in `outreach_queue` for
  manual approval.
- Compliance Watchdog supervises every other agent in the hierarchical Crew run.
- Daily logs reviewed by the Founders' weekly compliance call.

## Update cadence

This document is reviewed every quarter or whenever an underlying model is changed.
