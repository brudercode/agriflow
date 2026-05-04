/**
 * PostcardSSL — voluntary provenance "preparation aid".
 * Hash + QR + PDF; stored in Supabase storage.
 *
 * IMPORTANT: This is *not* a regulated EUDR Due Diligence Statement.
 * Buyers may use it as an input into their own DDS process; legal
 * responsibility stays with them.
 */
import { createHash, randomBytes } from "node:crypto";
import { createClient } from "@supabase/supabase-js";
import QRCode from "qrcode";
import { jsPDF } from "jspdf";
import geohash from "ngeohash";

const sb = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY!,
);

export interface ProvenanceInput {
  producer_id: string;
  product_id: string;
  batch_code: string;
  harvest_date: string; // ISO date
  lat: number;
  lng: number;
  area_hectares?: number;
  practices?: string[];
  inputs?: Record<string, unknown>;
  is_public?: boolean;
}

function canonicalize(o: Record<string, unknown>): string {
  return JSON.stringify(
    Object.keys(o)
      .sort()
      .reduce<Record<string, unknown>>((a, k) => {
        a[k] = o[k];
        return a;
      }, {}),
  );
}

export async function recordProvenance(p: ProvenanceInput) {
  const plot_geohash = geohash.encode(p.lat, p.lng, 6);
  const qr_token = randomBytes(12).toString("base64url");
  const canonical = canonicalize({
    producer_id: p.producer_id,
    product_id: p.product_id,
    batch_code: p.batch_code,
    harvest_date: p.harvest_date,
    plot_geohash,
    area_hectares: p.area_hectares,
    practices: (p.practices ?? []).slice().sort(),
    inputs: p.inputs ?? {},
  });
  const ssl_hash = createHash("sha256").update(canonical).digest("hex");

  const publicUrl = `${process.env.NEXT_PUBLIC_APP_URL}/p/${qr_token}`;
  const qrPng = await QRCode.toBuffer(publicUrl, { width: 256, margin: 1 });

  const pdf = new jsPDF({ unit: "mm", format: "a6" });
  pdf.setFont("helvetica", "bold");
  pdf.setFontSize(14);
  pdf.text("AgriFlow Provenance Postcard", 5, 12);
  pdf.setFontSize(9);
  pdf.setFont("helvetica", "normal");
  pdf.text(
    [
      `Batch: ${p.batch_code}`,
      `Harvest: ${p.harvest_date}`,
      `Geohash: ${plot_geohash}`,
      `Hash: ${ssl_hash.slice(0, 16)}…`,
      "Voluntary preparation aid — not a legal EUDR DDS.",
    ],
    5,
    22,
  );
  pdf.addImage(qrPng, "PNG", 70, 5, 30, 30);
  const pdfBuf = Buffer.from(pdf.output("arraybuffer"));

  const pdf_path = `postcards/${p.producer_id}/${qr_token}.pdf`;
  const { error: upErr } = await sb.storage.from("public").upload(pdf_path, pdfBuf, {
    contentType: "application/pdf",
    upsert: true,
  });
  if (upErr) throw upErr;

  const { data, error } = await sb
    .from("traceability_records")
    .insert({
      producer_id: p.producer_id,
      product_id: p.product_id,
      batch_code: p.batch_code,
      harvest_date: p.harvest_date,
      plot_geohash,
      area_hectares: p.area_hectares,
      practices: p.practices ?? [],
      inputs: p.inputs ?? {},
      ssl_hash,
      pdf_path,
      qr_token,
      is_public: p.is_public ?? true,
    })
    .select()
    .single();

  if (error) throw error;
  return { ...data, public_url: publicUrl };
}
