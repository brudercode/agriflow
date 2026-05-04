/**
 * AgriFlow semantic-search route.
 * POST /api/search
 *
 * Uses pgvector via the `match_listings` Postgres RPC, with a small
 * IP-based rate limit (Upstash) to keep abuse off the free tier.
 */
import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";
import OpenAI from "openai";
import { z } from "zod";
import { Ratelimit } from "@upstash/ratelimit";
import { Redis } from "@upstash/redis";

export const runtime = "edge";
export const preferredRegion = ["fra1"]; // Frankfurt

const Body = z.object({
  q: z.string().min(2).max(200),
  category: z
    .enum(["tomato", "berry", "leafy_green", "citrus", "stone_fruit", "olive_oil"])
    .optional(),
  country: z.enum(["ES", "IT", "DE"]).optional(),
  min_verification: z
    .enum(["unverified", "self_declared", "document_verified", "onsite_verified"])
    .default("unverified"),
  limit: z.number().int().min(1).max(50).default(20),
});

const sb = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY!,
  { auth: { persistSession: false } },
);

const oa = new OpenAI({ apiKey: process.env.OPENAI_API_KEY! });

const limiter = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(30, "1 m"),
  analytics: true,
  prefix: "agriflow:search",
});

export async function POST(req: NextRequest) {
  const ip = req.headers.get("x-forwarded-for") ?? "anon";
  const { success, limit, remaining } = await limiter.limit(`search:${ip}`);
  if (!success) {
    return NextResponse.json({ error: "rate_limited", limit, remaining }, { status: 429 });
  }

  const parsed = Body.safeParse(await req.json().catch(() => ({})));
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 });
  }
  const { q, category, country, min_verification, limit: n } = parsed.data;

  // 1. Embed query
  let vec: number[];
  try {
    const emb = await oa.embeddings.create({
      model: "text-embedding-3-small",
      input: q,
    });
    vec = emb.data[0].embedding;
  } catch (err) {
    console.error("[search] embed failed", err);
    return NextResponse.json({ error: "embedding_failed" }, { status: 502 });
  }

  // 2. Query DB
  const { data, error } = await sb.rpc("match_listings", {
    query_embedding: vec,
    match_count: n,
    filter_category: category ?? null,
    filter_country: country ?? null,
    min_verification,
  });
  if (error) {
    console.error("[search] rpc failed", error);
    return NextResponse.json({ error: "search_failed" }, { status: 500 });
  }

  return NextResponse.json({
    q,
    results: data,
    meta: { count: data?.length ?? 0, ts: new Date().toISOString() },
  });
}
