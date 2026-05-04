/**
 * Three-tier producer verification + automatic badge engine.
 *
 *   self_declared    → producer filled profile fully
 *   document_verified → certs uploaded + admin approved
 *   onsite_verified  → AgriFlow team visited (or trusted partner attestation)
 *
 * VAT/CIF check uses the VIES SOAP service (free, EU).
 */
import { createClient } from "@supabase/supabase-js";

const sb = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY!,
);

export const BADGES = {
  vat_verified: "VAT/CIF Verified",
  doc_verified: "Documents Verified",
  onsite_verified: "On-site Visited",
  organic: "EU Organic",
  dop_igp: "DOP/IGP Origin",
  active_journal: "Active Harvest Journal",
  responsive: "Responds <24h",
} as const;
export type BadgeId = keyof typeof BADGES;

export async function recomputeBadges(producer_id: string) {
  const [{ data: prod }, { data: certs }, { data: journals }] = await Promise.all([
    sb.from("producers").select("*").eq("id", producer_id).single(),
    sb
      .from("producer_certifications")
      .select("*")
      .eq("producer_id", producer_id)
      .eq("verified", true),
    sb
      .from("harvest_records")
      .select("id")
      .eq("producer_id", producer_id)
      .gte("harvest_date", new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10)),
  ]);
  if (!prod) throw new Error("not_found");

  const badges: BadgeId[] = [];
  if (prod.vat_id_verified) badges.push("vat_verified");
  if (prod.verification === "document_verified" || prod.verification === "onsite_verified")
    badges.push("doc_verified");
  if (prod.verification === "onsite_verified") badges.push("onsite_verified");
  if (certs?.some((c) => c.cert === "eu_organic")) badges.push("organic");
  if (certs?.some((c) => c.cert === "dop" || c.cert === "igp")) badges.push("dop_igp");
  if ((journals?.length ?? 0) >= 4) badges.push("active_journal");

  await sb.from("producers").update({ badges }).eq("id", producer_id);
  return badges.map((b) => ({ id: b, label: BADGES[b] }));
}

/** VIES VAT check — synchronous, free, EU-hosted SOAP. */
export async function viesCheck(country: string, vat: string) {
  const xml = `<?xml version="1.0"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
  xmlns:urn="urn:ec.europa.eu:taxud:vies:services:checkVat:types">
  <soapenv:Body><urn:checkVat>
    <urn:countryCode>${country}</urn:countryCode>
    <urn:vatNumber>${vat}</urn:vatNumber>
  </urn:checkVat></soapenv:Body></soapenv:Envelope>`;

  const r = await fetch(
    "https://ec.europa.eu/taxation_customs/vies/services/checkVatService",
    {
      method: "POST",
      headers: { "Content-Type": "text/xml" },
      body: xml,
    },
  );
  const t = await r.text();
  const valid = /<valid>true<\/valid>/.test(t);
  const name = /<name>([^<]+)<\/name>/.exec(t)?.[1] ?? "";
  return { valid, name };
}
