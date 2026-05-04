-- =========================================================================
-- AgriFlow MVP schema  •  PostgreSQL 16 + pgvector + RLS
-- 0001_init.sql — applied via `supabase db push`
-- =========================================================================
create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";
create extension if not exists "vector";
create extension if not exists "pg_trgm";
create extension if not exists "btree_gin";

-- ---------- ENUMS -------------------------------------------------------
create type product_category as enum (
  'tomato','berry','leafy_green','citrus','stone_fruit','olive_oil','other'
);
create type producer_role as enum ('farmer','cooperative','packhouse','miller','other');
create type verification_level as enum ('unverified','self_declared','document_verified','onsite_verified');
create type cert_type as enum (
  'eu_organic','demeter','globalgap','dop','igp','rainforest','fair_for_life','other'
);
create type unit as enum ('kg','tonne','litre','case_5kg','case_10kg','pallet');
create type currency as enum ('EUR');

-- ---------- USERS / PRODUCERS ------------------------------------------
create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text,
  phone_e164 text,
  preferred_lang text default 'en' check (preferred_lang in ('en','es','it','de')),
  is_producer boolean default false,
  is_buyer boolean default false,
  created_at timestamptz default now()
);

create table public.producers (
  id uuid primary key default uuid_generate_v4(),
  owner_id uuid references public.profiles(id) on delete set null,
  legal_name text not null,
  trade_name text,
  role producer_role not null,
  country_iso2 text not null check (length(country_iso2)=2),
  region text,
  postal_code text,
  -- coarse lat/lng only (privacy-preserving, ~1 km grid)
  lat_coarse numeric(7,4),
  lng_coarse numeric(7,4),
  vat_id text,                       -- collected, never displayed publicly
  vat_id_verified boolean default false,
  website text,
  whatsapp_e164 text,
  bio text,
  hectares numeric(8,2),
  founded_year int,
  verification verification_level default 'unverified',
  badges text[] default '{}',
  embedding vector(1536),            -- semantic profile
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
create index producers_country_idx on public.producers(country_iso2);
create index producers_embedding_idx on public.producers
  using hnsw (embedding vector_cosine_ops);
create index producers_trgm on public.producers using gin (legal_name gin_trgm_ops);

create table public.producer_certifications (
  id uuid primary key default uuid_generate_v4(),
  producer_id uuid references public.producers(id) on delete cascade,
  cert cert_type not null,
  cert_number text,
  issuer text,
  valid_from date,
  valid_until date,
  document_path text,                -- supabase storage path
  verified boolean default false,
  created_at timestamptz default now()
);
create index pc_producer_idx on public.producer_certifications(producer_id);

-- ---------- PRODUCT CATALOG --------------------------------------------
create table public.products (
  id uuid primary key default uuid_generate_v4(),
  category product_category not null,
  variety text not null,
  common_names jsonb default '{}'::jsonb,
  description text,
  origin_country text,
  origin_region text,
  embedding vector(1536),
  created_at timestamptz default now()
);
create index products_category_idx on public.products(category);
create index products_variety_trgm on public.products using gin (variety gin_trgm_ops);
create index products_embedding_idx on public.products
  using hnsw (embedding vector_cosine_ops);

-- ---------- LISTINGS (informational only) ------------------------------
create table public.listings (
  id uuid primary key default uuid_generate_v4(),
  producer_id uuid references public.producers(id) on delete cascade,
  product_id uuid references public.products(id) on delete restrict,
  unit unit not null,
  indicative_price_eur numeric(10,4) not null check (indicative_price_eur > 0),
  min_quantity numeric(12,2),
  available_from date,
  available_until date,
  harvest_window text,
  notes text,
  certifications text[] default '{}',
  is_active boolean default true,
  source text default 'producer',
  source_url text,
  embedding vector(1536),
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
create index listings_active_idx on public.listings(is_active, product_id);
create index listings_producer_idx on public.listings(producer_id);
create index listings_embedding_idx on public.listings
  using hnsw (embedding vector_cosine_ops);

-- ---------- PRICE HISTORY ----------------------------------------------
create table public.price_history (
  id bigserial primary key,
  product_id uuid references public.products(id) on delete cascade,
  region_iso text not null,
  market text,
  observed_at date not null,
  price_eur numeric(10,4) not null,
  unit unit not null,
  source text not null,
  source_url text,
  raw jsonb,
  created_at timestamptz default now()
);
create unique index price_history_unique
  on public.price_history(product_id, region_iso, market, observed_at, unit, source);
create index price_history_recent_idx
  on public.price_history(product_id, observed_at desc);

-- ---------- TRACEABILITY-LITE (PostcardSSL) ----------------------------
create table public.traceability_records (
  id uuid primary key default uuid_generate_v4(),
  producer_id uuid references public.producers(id) on delete cascade,
  product_id uuid references public.products(id) on delete restrict,
  batch_code text not null,
  harvest_date date,
  plot_geohash text,
  area_hectares numeric(6,2),
  practices text[] default '{}',
  inputs jsonb default '{}',
  ssl_hash text not null,
  pdf_path text,
  qr_token text unique not null,
  is_public boolean default true,
  created_at timestamptz default now()
);
create index trace_producer_idx on public.traceability_records(producer_id);
create index trace_qr_idx on public.traceability_records(qr_token);

-- ---------- HARVEST JOURNAL --------------------------------------------
create table public.harvest_records (
  id uuid primary key default uuid_generate_v4(),
  producer_id uuid references public.producers(id) on delete cascade,
  product_id uuid references public.products(id) on delete restrict,
  harvest_date date not null,
  quantity numeric(12,2),
  unit unit not null,
  field_label text,
  weather_note text,
  photo_path text,
  notes text,
  created_at timestamptz default now()
);
create index harvest_recent_idx on public.harvest_records(producer_id, harvest_date desc);

-- ---------- REFERRAL INTENTS -------------------------------------------
create table public.referral_intents (
  id uuid primary key default uuid_generate_v4(),
  buyer_profile_id uuid references public.profiles(id) on delete set null,
  producer_id uuid references public.producers(id) on delete cascade,
  product_id uuid references public.products(id),
  message text,
  desired_quantity numeric(12,2),
  desired_unit unit,
  status text default 'sent' check (status in ('sent','seen','reciprocated','closed')),
  consent_to_share_contact boolean default false,
  created_at timestamptz default now()
);

-- ---------- COMPLIANCE / AUDIT -----------------------------------------
create table public.audit_log (
  id bigserial primary key,
  actor_id uuid,
  action text not null,
  entity text,
  entity_id uuid,
  payload jsonb,
  ip inet,
  created_at timestamptz default now()
);
create index audit_recent on public.audit_log(created_at desc);

-- =========================================================================
-- VIEW + RPC for semantic search
-- =========================================================================
create or replace view public.v_searchable_listings as
select
  l.id            as listing_id,
  l.product_id,
  p.category,
  p.variety,
  pr.id           as producer_id,
  pr.trade_name,
  pr.country_iso2,
  pr.region,
  pr.verification,
  pr.badges,
  l.unit,
  l.indicative_price_eur,
  l.available_from,
  l.available_until,
  l.embedding
from public.listings l
join public.products p on p.id = l.product_id
join public.producers pr on pr.id = l.producer_id
where l.is_active = true;

create or replace function public.match_listings(
  query_embedding vector(1536),
  match_count int default 20,
  filter_category product_category default null,
  filter_country text default null,
  min_verification verification_level default 'unverified'
)
returns table (
  listing_id uuid,
  producer_id uuid,
  trade_name text,
  category product_category,
  variety text,
  country_iso2 text,
  region text,
  unit unit,
  price numeric,
  similarity float
)
language sql stable as $$
  select
    v.listing_id,
    v.producer_id,
    v.trade_name,
    v.category,
    v.variety,
    v.country_iso2,
    v.region,
    v.unit,
    v.indicative_price_eur,
    1 - (v.embedding <=> query_embedding) as similarity
  from public.v_searchable_listings v
  where (filter_category is null or v.category = filter_category)
    and (filter_country is null or v.country_iso2 = filter_country)
    and v.verification >= min_verification
  order by v.embedding <=> query_embedding
  limit match_count;
$$;

-- =========================================================================
-- ROW LEVEL SECURITY
-- =========================================================================
alter table public.profiles                enable row level security;
alter table public.producers               enable row level security;
alter table public.producer_certifications enable row level security;
alter table public.products                enable row level security;
alter table public.listings                enable row level security;
alter table public.price_history           enable row level security;
alter table public.traceability_records    enable row level security;
alter table public.harvest_records         enable row level security;
alter table public.referral_intents        enable row level security;

create policy profiles_self on public.profiles
  for all using (auth.uid() = id) with check (auth.uid() = id);

create policy producers_select_public on public.producers
  for select using (true);
create policy producers_owner_modify on public.producers
  for update using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy producers_owner_insert on public.producers
  for insert with check (owner_id = auth.uid());
create policy producers_owner_delete on public.producers
  for delete using (owner_id = auth.uid());

create policy certs_owner on public.producer_certifications
  for all using (
    exists(select 1 from public.producers p
           where p.id = producer_id and p.owner_id = auth.uid())
  );
create policy certs_public_read_verified on public.producer_certifications
  for select using (verified = true);

create policy products_read on public.products for select using (true);

create policy listings_public_read on public.listings
  for select using (is_active = true);
create policy listings_owner_write on public.listings
  for all using (
    exists(select 1 from public.producers p
           where p.id = producer_id and p.owner_id = auth.uid())
  );

create policy price_history_read on public.price_history for select using (true);

create policy trace_owner_write on public.traceability_records
  for all using (
    exists(select 1 from public.producers p
           where p.id = producer_id and p.owner_id = auth.uid())
  );
create policy trace_public_read on public.traceability_records
  for select using (is_public = true);

create policy harvest_owner on public.harvest_records
  for all using (
    exists(select 1 from public.producers p
           where p.id = producer_id and p.owner_id = auth.uid())
  );

create policy referral_visibility on public.referral_intents
  for select using (
    auth.uid() = buyer_profile_id
    or exists(select 1 from public.producers p
              where p.id = producer_id and p.owner_id = auth.uid())
  );
create policy referral_buyer_insert on public.referral_intents
  for insert with check (auth.uid() = buyer_profile_id);

-- =========================================================================
-- TRIGGERS
-- =========================================================================
create or replace function public.tg_set_updated_at() returns trigger
language plpgsql as $$
begin new.updated_at = now(); return new; end $$;

create trigger trg_producers_updated before update on public.producers
  for each row execute procedure public.tg_set_updated_at();
create trigger trg_listings_updated before update on public.listings
  for each row execute procedure public.tg_set_updated_at();
