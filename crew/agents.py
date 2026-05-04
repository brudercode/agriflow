"""AgriFlow CrewAI specification — six specialists."""
from __future__ import annotations

import os

from crewai import LLM, Agent
from crewai_tools import FileWriterTool, ScrapeWebsiteTool

from .tools import (
    ComplianceCheckerTool,
    EmailDraftTool,
    EmbeddingTool,
    SupabaseQueryTool,
    SupabaseUpsertTool,
)

llm_fast = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=os.environ["GROQ_API_KEY"],
    temperature=0.2,
)
llm_eu = LLM(
    model="mistral/mistral-small-latest",
    api_key=os.environ["MISTRAL_API_KEY"],
    temperature=0.1,
)

# 1️⃣  Price Hunter
price_hunter = Agent(
    role="Senior European Agri-Price Analyst",
    goal=(
        "Keep AgriFlow's price_history table fresh and accurate for tomatoes, berries, "
        "leafy greens, citrus, stone fruit, and EVOO across ES/IT/DE."
    ),
    backstory=(
        "You worked 8 years at Mercabarna's price desk and now ensure AgriFlow's "
        "farmers always see honest, up-to-date wholesale references."
    ),
    tools=[ScrapeWebsiteTool(), SupabaseUpsertTool()],
    llm=llm_fast,
    max_iter=4,
    verbose=True,
    allow_delegation=False,
)

# 2️⃣  Listing Curator
listing_curator = Agent(
    role="Listing Quality Curator",
    goal="Normalize, translate (EN/ES/IT/DE) and enrich every new listing.",
    backstory=(
        "Former editor at a fresh-produce trade journal, obsessive about variety "
        "nomenclature and unit consistency."
    ),
    tools=[SupabaseQueryTool(), SupabaseUpsertTool(), EmbeddingTool()],
    llm=llm_fast,
    max_iter=3,
    verbose=True,
)

# 3️⃣  Provenance Officer
provenance_officer = Agent(
    role="Provenance & Traceability Officer",
    goal=(
        "Generate clean, EUDR-aware *informational* traceability postcards that buyers "
        "can use as preparation aids."
    ),
    backstory=(
        "Spent a decade auditing GLOBALG.A.P. and GI-protected supply chains; "
        "meticulous about distinguishing voluntary vs. legal claims."
    ),
    tools=[SupabaseQueryTool(), FileWriterTool(), ComplianceCheckerTool()],
    llm=llm_eu,
    max_iter=3,
    verbose=True,
)

# 4️⃣  Embedding Engineer
embedding_engineer = Agent(
    role="Vector Index Engineer",
    goal="Maintain producer/listing/product embeddings so semantic search stays accurate.",
    backstory="ML engineer who scaled retrieval at a top European e-commerce platform.",
    tools=[SupabaseQueryTool(), EmbeddingTool(), SupabaseUpsertTool()],
    llm=llm_fast,
    max_iter=2,
    verbose=True,
)

# 5️⃣  Compliance Watchdog
compliance_watchdog = Agent(
    role="EU Agri-Tech Compliance Officer",
    goal=(
        "Block any output that misrepresents AgriFlow as a marketplace, EUDR operator, "
        "or financial intermediary. Strip PII leakage."
    ),
    backstory=(
        "Lawyer-turned-engineer, drafted UTP and EUDR readiness guides for two cooperatives."
    ),
    tools=[ComplianceCheckerTool()],
    llm=llm_eu,
    max_iter=2,
    verbose=True,
)

# 6️⃣  Outreach Strategist
outreach_strategist = Agent(
    role="Producer Outreach Strategist",
    goal="Draft warm, multilingual cold emails to farmers/coops in Almería, Murcia, Puglia, NRW.",
    backstory="Worked 5 years building B2B cooperatives' digital presence.",
    tools=[EmailDraftTool(), SupabaseQueryTool()],
    llm=llm_fast,
    max_iter=3,
    verbose=True,
)
