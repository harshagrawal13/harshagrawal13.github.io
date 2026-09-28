-- migrate:up
-- The "personal_website" database on kamaji, which holds the /shows/ list. PostgREST
-- serves the api schema read-only at https://api.harsh-agrawal.com as personal_website_anon.
--
-- The database and both roles already exist before this runs: kamaji-server's add-app
-- creates them, along with personal_website_authenticator's password and the connect
-- grants. This file only builds what is inside the database.
--
-- On kamaji this baseline was recorded as applied rather than run: it reproduces what
-- db/web.sql had built there before the database was renamed from "web".

create table public.shows (
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
create schema api;
comment on schema api is 'Served read-only by PostgREST at https://api.harsh-agrawal.com as role personal_website_anon.';
create view api.shows as
  select title, rating, status, season, tags, seasons, episodes, episode_minutes,
         genres, tvmaze, imdb, poster, poster_large
  from public.shows;

-- personal_website_anon is what PostgREST switches to: it can only read the view, and only briefly.
alter role personal_website_anon set statement_timeout = '2s';
grant usage on schema api to personal_website_anon;
grant select on api.shows to personal_website_anon;

-- Tell PostgREST to reload its cached schema (it listens on this channel).
notify pgrst, 'reload schema';

-- migrate:down
drop view api.shows;
drop schema api;
drop table public.shows;
alter role personal_website_anon reset statement_timeout;
