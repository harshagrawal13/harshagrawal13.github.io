-- Schema for the "web" Postgres database on kamaji, which holds the /shows/ list.
-- PostgREST serves the api schema read-only at https://api.harsh-agrawal.com as role web_anon.
--
-- Safe to re-run. Apply as the kamaji superuser (the macOS user, via peer auth):
--   ssh kamaji psql -X -v ON_ERROR_STOP=1 -d web < db/web.sql
-- First-time setup also needs, once:
--   ssh kamaji psql -d postgres -c 'create database web'
--   ssh kamaji psql -d web -c "alter role authenticator password '<the password in ~/.config/postgrest/web.conf>'"
-- Column changes to an existing table need their own ALTER TABLE; "create table if not exists" won't apply them.

begin;

create table if not exists public.shows (
  id                integer generated always as identity primary key,
  -- my fields
  title             text not null check (title <> ''),
  rating            numeric(3,1) not null check (rating between 0 and 10),
  status            text not null check (status in ('completed', 'watching', 'abandoned')),
  season            smallint check (season >= 1),
  tags              text[] not null default '{}',
  -- filled from TVmaze by scripts/shows.py (only where null)
  seasons           smallint check (seasons >= 0),
  episodes          integer check (episodes >= 0),
  episode_minutes   smallint check (episode_minutes >= 0),
  genres            text[],
  tvmaze            integer unique,
  imdb              text,
  poster            text,
  poster_large      text,
  tvmaze_checked_at timestamptz,
  constraint season_within_seasons check (season <= seasons)
);
comment on column public.shows.season is 'For watching/abandoned shows: the season I am on or left at.';
comment on column public.shows.tvmaze_checked_at is
  'When scripts/shows.py last filled this row; null = look it up. Set it with tvmaze null for a show TVmaze does not have.';

-- The public API: one row per show. The page ranks whichever shows its filters leave visible.
create schema if not exists api;
comment on schema api is 'Served read-only by PostgREST at https://api.harsh-agrawal.com as role web_anon.';
drop view if exists api.shows;
create view api.shows as
  select title, rating, status, season, tags, seasons, episodes, episode_minutes,
         genres, tvmaze, imdb, poster, poster_large
  from public.shows;

-- Roles: PostgREST logs in as authenticator (no privileges of its own) and switches to
-- web_anon, which can only read the view and only briefly.
do $$
begin
  if not exists (select from pg_roles where rolname = 'web_anon') then
    create role web_anon nologin;
  end if;
  if not exists (select from pg_roles where rolname = 'authenticator') then
    create role authenticator login noinherit;
  end if;
end $$;
grant web_anon to authenticator;
alter role web_anon set statement_timeout = '2s';
revoke all on database web from public;
grant connect on database web to authenticator;
grant usage on schema api to web_anon;
grant select on api.shows to web_anon;

commit;

-- Tell PostgREST to reload its cached schema (it listens on this channel).
notify pgrst, 'reload schema';
