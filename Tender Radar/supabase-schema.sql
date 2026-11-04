-- ============================================================
-- TenderRadarPK database setup. Paste ALL of this into
-- Supabase -> SQL Editor -> New query -> Run.  (Safe to run once.)
-- ============================================================

-- 1) One profile per user (holds their plan)
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  full_name text,
  account_type text not null default 'COMPANY',   -- COMPANY | SUPPLIER | ORGANIZATION
  plan text not null default 'free',              -- free | pro | business
  is_admin boolean not null default false,
  created_at timestamptz not null default now()
);

-- 2) Pipeline tracking (My Tenders)
create table if not exists public.tracking (
  user_id uuid not null references auth.users(id) on delete cascade,
  tender_id text not null,
  status text not null default 'interested',
  notes text default '',
  updated_at timestamptz not null default now(),
  primary key (user_id, tender_id)
);

-- 3) Manual payment requests
create table if not exists public.payment_requests (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  email text not null,
  plan text not null check (plan in ('pro','business')),
  txn text not null,
  status text not null default 'PENDING',         -- PENDING | APPROVED | REJECTED
  created_at timestamptz not null default now()
);

-- Helper: is the current user an admin?
create or replace function public.is_admin() returns boolean
language sql security definer set search_path = public stable
as $$ select coalesce((select is_admin from public.profiles where id = auth.uid()), false) $$;

-- Auto-create a profile when someone signs up
create or replace function public.handle_new_user() returns trigger
language plpgsql security definer set search_path = public
as $$
begin
  insert into public.profiles (id, email, full_name, account_type)
  values (new.id, new.email,
          coalesce(new.raw_user_meta_data->>'full_name',''),
          coalesce(new.raw_user_meta_data->>'account_type','COMPANY'));
  return new;
end $$;
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users
  for each row execute function public.handle_new_user();

-- Security: Row Level Security (each user sees only their own data)
alter table public.profiles enable row level security;
alter table public.tracking enable row level security;
alter table public.payment_requests enable row level security;

create policy "read own profile or admin" on public.profiles
  for select using (id = auth.uid() or public.is_admin());
-- Users may edit their name/type but NOT plan or admin flag (blocked by trigger below)
create policy "update own profile or admin" on public.profiles
  for update using (id = auth.uid() or public.is_admin());

create or replace function public.protect_plan() returns trigger
language plpgsql security definer set search_path = public
as $$
begin
  if not public.is_admin() then
    new.plan := old.plan;
    new.is_admin := old.is_admin;
  end if;
  return new;
end $$;
drop trigger if exists protect_plan_trg on public.profiles;
create trigger protect_plan_trg before update on public.profiles
  for each row execute function public.protect_plan();

create policy "own tracking" on public.tracking
  for all using (user_id = auth.uid()) with check (user_id = auth.uid());

create policy "insert own payment request" on public.payment_requests
  for insert with check (user_id = auth.uid() and status = 'PENDING');
create policy "read own or admin payment requests" on public.payment_requests
  for select using (user_id = auth.uid() or public.is_admin());
create policy "admin updates payment requests" on public.payment_requests
  for update using (public.is_admin());

-- ============================================================
-- AFTER you sign up on your own site once, make yourself admin:
--   update public.profiles set is_admin = true where email = 'YOUR-EMAIL-HERE';
-- ============================================================
