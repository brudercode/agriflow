"""
Modal scheduled wrapper for AgriFlow ingestion.

Deploy:
    modal deploy pipeline/modal_app.py
"""
import modal

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "httpx[http2]>=0.27",
        "selectolax>=0.3.21",
        "supabase>=2.9",
        "pydantic>=2.9",
        "tenacity>=9.0",
        "orjson>=3.10",
    )
    .add_local_python_source("pipeline")
)

app = modal.App(
    "agriflow-ingest",
    image=image,
    secrets=[modal.Secret.from_name("agriflow-env")],
)


@app.function(schedule=modal.Cron("0 */6 * * *"), timeout=900)
def cron_ingest():
    """Every 6 hours, refresh price_history from all adapters."""
    import asyncio
    from pipeline.ingest import run

    return asyncio.run(run(["freshfel", "poolred", "mercabarna"]))


@app.function(timeout=900)
def manual_ingest(sources: list[str] | None = None):
    """One-off run, callable via `modal run pipeline/modal_app.py::manual_ingest`."""
    import asyncio
    from pipeline.ingest import ADAPTERS, run

    return asyncio.run(run(sources or list(ADAPTERS)))
