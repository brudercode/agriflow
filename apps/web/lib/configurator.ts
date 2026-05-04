/**
 * Buyer configurator: turns a structured intent into an embedding-friendly
 * query plus discrete filters. Pure function, easy to unit-test.
 */
import { z } from "zod";

export const ConfigInput = z.object({
  category: z.enum([
    "tomato",
    "berry",
    "leafy_green",
    "citrus",
    "stone_fruit",
    "olive_oil",
  ]),
  quantity_kg: z.number().positive().max(50_000),
  required_certs: z.array(z.string()).default([]),
  delivery_window: z.object({
    from: z.string(), // ISO date
    to: z.string(),
  }),
  origin_pref: z.array(z.enum(["ES", "IT", "DE"])).default([]),
  max_eur_per_unit: z.number().positive().optional(),
  notes: z.string().max(500).optional(),
});
export type ConfigInput = z.infer<typeof ConfigInput>;

export interface ConfiguratorQuery {
  semantic_q: string;
  filters: {
    category: ConfigInput["category"];
    country?: "ES" | "IT" | "DE";
    max_price: number | null;
    certs: string[];
    from: string;
    to: string;
  };
}

export function buildConfiguratorQuery(i: ConfigInput): ConfiguratorQuery {
  const parts = [
    i.category.replace(/_/g, " "),
    i.required_certs.length ? `with ${i.required_certs.join(", ")}` : "",
    i.origin_pref.length ? `from ${i.origin_pref.join("/")}` : "",
    `delivery ${i.delivery_window.from}→${i.delivery_window.to}`,
    `~${i.quantity_kg} kg`,
    i.notes ?? "",
  ]
    .filter(Boolean)
    .join(" • ");

  return {
    semantic_q: parts,
    filters: {
      category: i.category,
      country: i.origin_pref[0],
      max_price: i.max_eur_per_unit ?? null,
      certs: i.required_certs,
      from: i.delivery_window.from,
      to: i.delivery_window.to,
    },
  };
}

/** Score a listing 0..1 against intent (post-filter ranker). */
export function scoreListing(
  listing: {
    category: string;
    country_iso2?: string;
    indicative_price_eur?: number;
    certifications?: string[];
    similarity?: number;
  },
  i: ConfigInput,
): number {
  let s = 0;
  if (listing.category === i.category) s += 0.3;
  if (listing.country_iso2 && i.origin_pref.includes(listing.country_iso2 as "ES" | "IT" | "DE"))
    s += 0.2;
  const priceOk =
    !i.max_eur_per_unit ||
    (listing.indicative_price_eur !== undefined &&
      listing.indicative_price_eur <= i.max_eur_per_unit);
  if (priceOk) s += 0.2;
  const certHit = i.required_certs.every((c) => (listing.certifications ?? []).includes(c));
  if (certHit) s += 0.2;
  s += Math.min(listing.similarity ?? 0, 1) * 0.1;
  return Math.min(s, 1);
}
