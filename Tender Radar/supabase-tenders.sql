-- ============================================================
-- TenderRadarPK: LIVE TENDERS table.
-- Paste into Supabase -> SQL Editor -> New query -> Run.
-- Run it AFTER supabase-schema.sql.
-- ============================================================

create table if not exists public.radar_tenders (
  id text primary key,                 -- unique per tender, e.g. 'EPADS-P118823'
  title text not null,
  org text not null default '',        -- department / procuring agency
  category text not null default 'General',
  province text not null default 'Federal',   -- Sindh | Punjab | Khyber Pakhtunkhwa | Balochistan | Federal | Islamabad
  city text not null default '',
  type text not null default 'Goods',         -- Goods | Services | Works | Consultancy
  source text not null default '',     -- EPADS | SPPRA | PPRA Punjab | KPPRA | BPPRA | Dawn | Jang ...
  sector text not null default 'GOVERNMENT',  -- GOVERNMENT | SEMI_GOVERNMENT | PRIVATE
  ref text default '',
  published date,
  closing date not null,
  value text default '',               -- e.g. 'PKR 8.2M' or 'Not disclosed'
  fee text default '',                 -- tender document fee
  eligibility text default '',
  docs jsonb not null default '[]',    -- list of document names, e.g. ["Bidding Document.pdf"]
  source_url text default '',          -- link to the original notice / PDF
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists radar_tenders_closing_idx on public.radar_tenders (closing);

alter table public.radar_tenders enable row level security;
-- Everyone (even logged-out visitors) can READ tenders. Nobody can write from the website.
-- Your scraper writes using the secret service_role key, which bypasses these rules.
drop policy if exists "public read tenders" on public.radar_tenders;
create policy "public read tenders" on public.radar_tenders for select using (true);

-- OPTIONAL: three test tenders so you can see the live connection working right away.
insert into public.radar_tenders (id,title,org,category,province,city,type,source,sector,ref,published,closing,value,eligibility,docs,source_url) values
 ('TEST-001','Supply of Solar Panels & Inverters','Sindh Solid Waste Management Board','Electrical','Sindh','Karachi','Goods','SPPRA','GOVERNMENT','SSWMB/SOL/01', current_date-2, current_date+9,'PKR 12M','Authorized solar dealer, 3 similar projects.','["Tender Notice.pdf"]','https://example.com'),
 ('TEST-002','Janitorial Services for Federal Offices','Pakistan Secretariat','Cleaning & Janitorial','Islamabad','Islamabad','Services','EPADS','GOVERNMENT','PS/CL/22', current_date-1, current_date+14,'PKR 6.5M / yr','Minimum 5 years experience.','["RFP.pdf","BOQ.xlsx"]','https://example.com'),
 ('TEST-003','Road Rehabilitation — Multan Bypass','Punjab Highway Department','Construction','Punjab','Multan','Works','PPRA Punjab','GOVERNMENT','PHD/MB/07', current_date-5, current_date+6,'PKR 48M','PEC C-4 or above.','["NIT.pdf","Drawings.pdf"]','https://example.com')
on conflict (id) do nothing;
