-- migrate:up
-- Expose each show's row id. It exists from the moment a show is inserted and is never
-- edited, unlike tvmaze (filled in later by scripts/shows.py, and corrected by hand when a
-- match is wrong). picktwo stores its duels against this id, so fixing a title or a TVmaze
-- match here never orphans them.
-- `create or replace view` can only add columns at the end, which also leaves every
-- existing reader of the view untouched. The grant on the view carries over.
create or replace view api.shows as
  select title, rating, status, season, tags, seasons, episodes, episode_minutes,
         genres, tvmaze, imdb, poster, poster_large, id
  from public.shows;

notify pgrst, 'reload schema';

-- migrate:down
-- A column can't be dropped from a view in place, so rebuild it as the baseline had it.
drop view api.shows;
create view api.shows as
  select title, rating, status, season, tags, seasons, episodes, episode_minutes,
         genres, tvmaze, imdb, poster, poster_large
  from public.shows;
grant select on api.shows to personal_website_anon;

notify pgrst, 'reload schema';
