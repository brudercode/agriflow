"""
AgriFlow async price ingestion.

Run locally:
    uv run python -m pipeline.ingest --source freshfel
Modal cron (production):
    every 6h via pipeline.modal_app
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
from datetime import date
from typing import Sequence

import httpx
from pydantic import BaseModel, Field, field_validator
from selectolax.parser import HTMLParser
from supabase import Client, create_client
from tenacity import retry, stop_after_attempt, wait_exponential

# --------------------------- config ---------------------------------------
LOG = logging.getLogger("agriflow.ingest")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
HTTP_TIMEOUT = 20
USER_AGENT = (
    f"AgriFlowBot/0.1 (+https://agriflow.eu/bot; "
    f"contact: {os.environ.get('AGRIFLOW_BOT_CONTACT', 'bot@agriflow.eu')})"
)
RATE_LIMIT_PER_HOST_RPS = float(os.environ.get("AGRIFLOW_RATE_LIMIT_RPS", "1"))

sb: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


# --------------------------- models ---------------------------------------
class PriceObservation(BaseModel):
    product_variety: str
    category: str
    region_iso: str
    market: str
    observed_at: date
    price_eur: float = Field(gt=0)
    unit: str
    source: str
    source_url: str
    raw: dict = {}

    @field_validator("price_eur")
    @classmethod
    def _cap(cls, v: float) -> float:
        if v > 10_000:
            raise ValueError("price out of range")
        return round(v, 4)


# --------------------------- helpers --------------------------------------
class HostRateLimiter:
    """1 req/sec per host token-bucket."""

    def __init__(self, rps: float) -> None:
        self.delay = 1.0 / rps
        self._locks: dict[str, asyncio.Lock] = {}
        self._last: dict[str, float] = {}

    async def acquire(self, host: str) -> None:
        lock = self._locks.setdefault(host, asyncio.Lock())
        async with lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self._last.get(host, 0)
            if elapsed < self.delay:
                await asyncio.sleep(self.delay - elapsed)
            self._last[host] = asyncio.get_event_loop().time()


LIMITER = HostRateLimiter(RATE_LIMIT_PER_HOST_RPS)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def fetch(url: str, client: httpx.AsyncClient) -> str:
    host = httpx.URL(url).host
    await LIMITER.acquire(host)
    LOG.info("GET %s", url)
    r = await client.get(url, timeout=HTTP_TIMEOUT, headers={"User-Agent": USER_AGENT})
    r.raise_for_status()
    return r.text


def upsert_prices(rows: Sequence[PriceObservation]) -> int:
    """Idempotent upsert into price_history (relies on unique index)."""
    if not rows:
        return 0
    payload: list[dict] = []
    for r in rows:
        prod = (
            sb.table("products")
            .select("id")
            .eq("variety", r.product_variety)
            .limit(1)
            .execute()
        )
        if not prod.data:
            new = (
                sb.table("products")
                .insert({"category": r.category, "variety": r.product_variety})
                .execute()
            )
            product_id = new.data[0]["id"]
        else:
            product_id = prod.data[0]["id"]
        payload.append(
            {
                "product_id": product_id,
                "region_iso": r.region_iso,
                "market": r.market,
                "observed_at": r.observed_at.isoformat(),
                "price_eur": r.price_eur,
                "unit": r.unit,
                "source": r.source,
                "source_url": r.source_url,
                "raw": r.raw,
            }
        )
    sb.table("price_history").upsert(
        payload,
        on_conflict="product_id,region_iso,market,observed_at,unit,source",
    ).execute()
    LOG.info("upserted %d rows", len(payload))
    return len(payload)


# --------------------------- adapters -------------------------------------
class BaseAdapter:
    name: str

    async def fetch_all(self, client: httpx.AsyncClient) -> list[PriceObservation]:
        raise NotImplementedError


class FreshfelAdapter(BaseAdapter):
    name = "freshfel"
    URL = (
        "https://agridata.ec.europa.eu/api/fav/prices?"
        "products=tomato,strawberry,lemon,peach,lettuce&period=last_4w"
    )

    async def fetch_all(self, client: httpx.AsyncClient) -> list[PriceObservation]:
        text = await fetch(self.URL, client)
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            LOG.warning("freshfel: non-JSON response, skipping")
            return []
        out: list[PriceObservation] = []
        for row in data.get("rows", []):
            try:
                out.append(
                    PriceObservation(
                        product_variety=row["product"].lower(),
                        category=_map_cat(row["product"]),
                        region_iso=row.get("country", "EU"),
                        market="EU-AGRIDATA",
                        observed_at=date.fromisoformat(row["week_end"]),
                        price_eur=float(row["price_eur_kg"]),
                        unit="kg",
                        source="agridata.ec.europa.eu",
                        source_url=self.URL,
                        raw=row,
                    )
                )
            except Exception as e:
                LOG.warning("freshfel row skipped: %s", e)
        return out


class PoolredAdapter(BaseAdapter):
    name = "poolred"
    URL = "https://www.poolred.com/"

    async def fetch_all(self, client: httpx.AsyncClient) -> list[PriceObservation]:
        html = await fetch(self.URL, client)
        tree = HTMLParser(html)
        rows: list[PriceObservation] = []
        for tr in tree.css("table.cotizacion tr"):
            tds = [t.text(strip=True) for t in tr.css("td")]
            if len(tds) >= 3 and "EXTRA" in tds[0].upper():
                try:
                    rows.append(
                        PriceObservation(
                            product_variety="extra virgin olive oil",
                            category="olive_oil",
                            region_iso="ES-AN",
                            market="POOLRED",
                            observed_at=date.today(),
                            price_eur=float(
                                tds[1].replace(",", ".").replace("€", "").strip()
                            ),
                            unit="kg",
                            source="poolred.com",
                            source_url=self.URL,
                            raw={"row": tds},
                        )
                    )
                except Exception as e:
                    LOG.warning("poolred row skipped: %s", e)
        return rows


class MercabarnaAdapter(BaseAdapter):
    name = "mercabarna"
    URL = "https://www.mercabarna.es/precios-mercados/"

    async def fetch_all(self, client: httpx.AsyncClient) -> list[PriceObservation]:
        html = await fetch(self.URL, client)
        tree = HTMLParser(html)
        out: list[PriceObservation] = []
        for tr in tree.css("table.tabla-precios tbody tr"):
            tds = [t.text(strip=True) for t in tr.css("td")]
            if len(tds) < 4:
                continue
            try:
                out.append(
                    PriceObservation(
                        product_variety=tds[0].lower(),
                        category=_map_cat(tds[0]),
                        region_iso="ES-CT",
                        market="MERCABARNA",
                        observed_at=date.today(),
                        price_eur=float(tds[2].replace(",", ".")),
                        unit="kg",
                        source="mercabarna.es",
                        source_url=self.URL,
                        raw={"row": tds},
                    )
                )
            except Exception:
                continue
        return out


ADAPTERS: dict[str, BaseAdapter] = {a().name: a() for a in (FreshfelAdapter, PoolredAdapter, MercabarnaAdapter)}


# --------------------------- category mapper ------------------------------
_CAT_MAP = {
    "tomato": "tomato", "tomate": "tomato",
    "strawberry": "berry", "fresa": "berry", "frutilla": "berry",
    "lemon": "citrus", "limón": "citrus", "orange": "citrus",
    "peach": "stone_fruit", "melocón": "stone_fruit",
    "lettuce": "leafy_green", "lechuga": "leafy_green",
    "olive": "olive_oil", "oliva": "olive_oil",
}


def _map_cat(s: str) -> str:
    s = s.lower()
    for k, v in _CAT_MAP.items():
        if k in s:
            return v
    return "other"


# --------------------------- entry point ----------------------------------
async def run(sources: list[str]) -> int:
    async with httpx.AsyncClient(http2=True, follow_redirects=True) as client:
        coros = [ADAPTERS[s].fetch_all(client) for s in sources if s in ADAPTERS]
        results = await asyncio.gather(*coros, return_exceptions=True)
    flat: list[PriceObservation] = []
    for res in results:
        if isinstance(res, Exception):
            LOG.error("adapter failed: %s", res)
            continue
        flat.extend(res)
    n = upsert_prices(flat)
    LOG.info("ingest complete: %d rows", n)
    return n


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--source",
        action="append",
        default=[],
        help="freshfel | poolred | mercabarna | all",
    )
    args = ap.parse_args()
    srcs = list(ADAPTERS) if "all" in args.source or not args.source else args.source
    asyncio.run(run(srcs))


if __name__ == "__main__":
    main()
