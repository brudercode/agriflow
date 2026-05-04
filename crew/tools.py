"""CrewAI custom tools for AgriFlow."""
from __future__ import annotations

import os
import re

from crewai.tools import BaseTool
from openai import OpenAI
from pydantic import BaseModel
from supabase import create_client

_sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])
_oa = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


# --------------- Supabase query ------------------------------------------
class _Q(BaseModel):
    table: str
    select: str = "*"
    eq: dict | None = None
    limit: int = 50


class SupabaseQueryTool(BaseTool):
    name: str = "supabase_query"
    description: str = "Read rows from a Supabase table. Args: {table, select, eq, limit}"
    args_schema = _Q

    def _run(self, **kw):
        q = _sb.table(kw["table"]).select(kw.get("select", "*"))
        for k, v in (kw.get("eq") or {}).items():
            q = q.eq(k, v)
        return q.limit(kw.get("limit", 50)).execute().data


# --------------- Supabase upsert -----------------------------------------
class _U(BaseModel):
    table: str
    rows: list[dict]
    on_conflict: str | None = None


class SupabaseUpsertTool(BaseTool):
    name: str = "supabase_upsert"
    description: str = "Upsert rows. Args: {table, rows, on_conflict?}"
    args_schema = _U

    def _run(self, **kw):
        return (
            _sb.table(kw["table"])
            .upsert(kw["rows"], on_conflict=kw.get("on_conflict"))
            .execute()
            .data
        )


# --------------- Embedding -----------------------------------------------
class _E(BaseModel):
    text: str


class EmbeddingTool(BaseTool):
    name: str = "embed_text"
    description: str = "Returns 1536-dim embedding (text-embedding-3-small)."
    args_schema = _E

    def _run(self, text: str):
        v = _oa.embeddings.create(model="text-embedding-3-small", input=text).data[0].embedding
        return v


# --------------- Compliance ----------------------------------------------
class _C(BaseModel):
    text: str


class ComplianceCheckerTool(BaseTool):
    name: str = "compliance_check"
    description: str = (
        "Flag PII leaks and forbidden marketplace/EUDR claims. "
        "Returns {ok: bool, issues: [...]}."
    )
    args_schema = _C

    FORBIDDEN = (
        "guaranteed deforestation-free",
        "EUDR compliant",
        "marketplace",
        "we sell",
        "escrow",
        "we handle payment",
        "we ship",
        "fulfilment by AgriFlow",
    )

    def _run(self, text: str) -> dict:
        bad: list[str] = []
        lt = text.lower()
        for w in self.FORBIDDEN:
            if w.lower() in lt:
                bad.append(f"Forbidden phrase: '{w}'")
        if re.search(r"\b\d{2,4}[-/ .]\d{2}[-/ .]\d{2,4}\b", text):
            bad.append("Possible date-of-birth/PII leak")
        return {"ok": not bad, "issues": bad}


# --------------- Email draft (no auto-send) ------------------------------
class _ED(BaseModel):
    locale: str  # 'es' | 'it' | 'de' | 'en'
    producer_name: str
    region: str
    primary_product: str


class EmailDraftTool(BaseTool):
    name: str = "draft_outreach_email"
    description: str = "Draft a personalised cold email. Returns {subject, body}."
    args_schema = _ED

    def _run(self, locale: str, producer_name: str, region: str, primary_product: str) -> dict:
        templates = {
            "es": {
                "subject": f"AgriFlow — escaparate gratuito para {producer_name}",
                "body": (
                    f"Hola, soy del equipo AgriFlow. Vimos que {producer_name} en {region} "
                    f"trabaja con {primary_product}. Os ofrecemos un perfil multilingüe gratuito, "
                    f"comparativa diaria de precios MercaBarna/POOLRED, y PostcardSSL gratuito. "
                    f"Sin comisiones ni exclusivas. ¿15 minutos esta semana?"
                ),
            },
            "it": {
                "subject": f"AgriFlow — vetrina gratuita per {producer_name}",
                "body": (
                    f"Buongiorno, AgriFlow è una nuova piattaforma di trasparenza per produttori "
                    f"di {primary_product} in {region}. Vetrina multilingue, prezzi POOLRED/ISMEA "
                    f"in tempo reale, PostcardSSL gratuito. Niente commissioni. 15 minuti?"
                ),
            },
            "de": {
                "subject": f"AgriFlow — kostenfreies Schaufenster für {producer_name}",
                "body": (
                    f"Sehr geehrte Damen und Herren, AgriFlow bietet {producer_name} ({region}) "
                    f"eine kostenfreie, mehrsprachige Plattform für transparente Preisinformation "
                    f"zu {primary_product} und freiwillige Herkunftsnachweise. Keine Provision. "
                    f"Hätten Sie 15 Minuten?"
                ),
            },
            "en": {
                "subject": f"AgriFlow — free showcase for {producer_name}",
                "body": (
                    f"Hi, AgriFlow gives {producer_name} ({region}) a free multilingual page, "
                    f"daily {primary_product} reference prices and a free PostcardSSL preparation aid "
                    f"for buyers' EUDR files. No commission. 15 minutes this week?"
                ),
            },
        }
        return templates.get(locale, templates["en"])
