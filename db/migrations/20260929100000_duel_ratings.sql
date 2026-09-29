-- migrate:up
-- The standings picktwo last committed for these shows (its "Commit results" button),
-- copied here by scripts/duels.py so /shows/ can read them from this database's own
-- public API. picktwo keeps the originals; this copy is replaced whole whenever picktwo
-- commits. A show's own `rating` is never touched: picktwo starts from it, so writing
-- duel results into it would count the same duels twice.
create table public.duel_ratings (
  show_id      integer primary key references public.shows (id) on delete cascade,
  rank         integer not null check (rank >= 1),
  score        numeric(3,1) check (score between 0 and 10),
  committed_at timestamptz not null   -- when picktwo committed them, not when they were copied
);

-- Appended at the end, as id was: `create or replace view` can only add columns there,
-- which leaves every existing reader (the page, picktwo) untouched. The grant carries over.
create or replace view api.shows as
  select s.title, s.rating, s.status, s.season, s.tags, s.seasons, s.episodes, s.episode_minutes,
         s.genres, s.tvmaze, s.imdb, s.poster, s.poster_large, s.id,
         d.score as duel_rating, d.rank as duel_rank
  from public.shows s left join public.duel_ratings d on d.show_id = s.id;

notify pgrst, 'reload schema';

-- migrate:down
-- A column can't be dropped from a view in place, so rebuild it as 20260928150000 left it.
drop view api.shows;
create view api.shows as
  select title, rating, status, season, tags, seasons, episodes, episode_minutes,
         genres, tvmaze, imdb, poster, poster_large, id
  from public.shows;
grant select on api.shows to personal_website_anon;
drop table public.duel_ratings;

notify pgrst, 'reload schema';
