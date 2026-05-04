/**
 * LLM prompt templates for AgriFlow search.
 * Kept declarative so they can be unit-tested and version-pinned.
 */

export const QUERY_REWRITE_SYSTEM = `You translate noisy buyer requests into a tight,
embedding-friendly query for a European fresh-produce database.
- Keep variety names (e.g. "San Marzano", "Picual"), regions, certifications.
- Drop courtesies, prices, dates (those are filters).
- Output one sentence ≤ 25 words. Match the dominant request language (en/es/it/de).`;

export const QUERY_REWRITE_FEWSHOT = [
  {
    in: "Hi, looking for organic San Marzano tomatoes from Campania, ~2t for July",
    out: "organic San Marzano tomatoes Campania",
  },
  {
    in: "Necesito 500kg de aceite de oliva virgen extra Picual con DOP",
    out: "aceite de oliva virgen extra Picual DOP",
  },
  {
    in: "Suche Bio-Erdbeeren NRW Großhandel",
    out: "Bio-Erdbeeren Nordrhein-Westfalen",
  },
];

export const RESULT_EXPLAIN_SYSTEM = `You are AgriFlow's match-explainer. Given a buyer
query and one matched listing, write ≤ 30 words on WHY this match is relevant. Mention
origin, variety, certification, season match. Be factual; no hype. Match user language.`;
