"""Hierarchical run — Compliance Watchdog supervises every other agent."""
from __future__ import annotations

import logging
import os
import sys

import sentry_sdk
from crewai import Crew, Process, Task

from .agents import (
    compliance_watchdog,
    embedding_engineer,
    listing_curator,
    outreach_strategist,
    price_hunter,
    provenance_officer,
)

LOG = logging.getLogger("agriflow.crew")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")

if dsn := os.environ.get("SENTRY_DSN"):
    sentry_sdk.init(dsn=dsn, traces_sample_rate=0.1, profiles_sample_rate=0.1)


def daily_crew_run():
    tasks = [
        Task(
            description=(
                "Refresh price_history for tomatoes, berries, leafy greens, citrus, "
                "stone fruit, EVOO from MercaBarna, MercaMadrid, POOLRED, ISMEA, BLE, "
                "and the EU agri-data dashboards."
            ),
            expected_output="JSON summary {rows_inserted, sources_ok, errors}.",
            agent=price_hunter,
        ),
        Task(
            description="Re-embed any listings/producers updated in last 24h.",
            expected_output="JSON {rows_embedded}.",
            agent=embedding_engineer,
        ),
        Task(
            description=(
                "Generate PostcardSSL provenance PDFs for every traceability_record "
                "created today; upload to /storage/postcards/."
            ),
            expected_output="List of {record_id, pdf_path}.",
            agent=provenance_officer,
        ),
        Task(
            description=(
                "Pre-run compliance check on outreach drafts queued for the next 24h."
            ),
            expected_output="JSON {ok_drafts, blocked_drafts:[{id,issues}]}.",
            agent=compliance_watchdog,
        ),
        Task(
            description=(
                "Pull last 24h of new listings, normalise units and translate to EN/ES/IT/DE."
            ),
            expected_output="JSON {rows_curated}.",
            agent=listing_curator,
        ),
    ]

    crew = Crew(
        agents=[
            price_hunter,
            listing_curator,
            provenance_officer,
            embedding_engineer,
            compliance_watchdog,
            outreach_strategist,
        ],
        tasks=tasks,
        process=Process.hierarchical,
        manager_llm=compliance_watchdog.llm,
        verbose=True,
    )
    return crew.kickoff()


def main() -> None:
    try:
        result = daily_crew_run()
        LOG.info("crew finished: %s", result)
    except Exception as e:
        LOG.exception("crew failed: %s", e)
        sentry_sdk.capture_exception(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
