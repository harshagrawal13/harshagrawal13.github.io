// Renders my shows as a ranked poster grid. The list lives in Postgres on kamaji and is served
// read-only by PostgREST (see README). A show's rating is the one picktwo's duels last committed,
// or else the one I set by hand. Ranks count within the current filters, and tied ratings share a
// number (1, 2, 2, 4, ...). One tag filter and one status can be active at a time; both live in
// the URL hash, e.g. /shows/#sitcoms+watching.

// The same URLs as the preloads in index.html.
const SHOWS_API = "https://api.harsh-agrawal.com/shows?order=rating.desc,title";
const DUELS_API = "https://picktwo.harsh-agrawal.com/public/scores?set=shows";
const DUELS_WAIT_MS = 3000; // past this, show my own ratings rather than keep waiting on picktwo
const FILTERS = [
  { key: "all", label: "All" },
  { key: "drama", label: "Drama", tag: "Drama" },
  { key: "sitcoms", label: "Sitcoms", tag: "Sitcom" },
  { key: "indian", label: "Indian Shows", tag: "Indian" },
  { key: "documentaries", label: "Documentaries", tag: "Documentary" },
];
const STATUSES = { completed: "Completed", watching: "Watching", abandoned: "Abandoned" };
const EAGER_POSTERS = 10; // the top rows; the rest load as they scroll into view
const SMALL_POSTER_WIDTH = 210; // TVmaze's "medium" poster, the size of `poster`

const grid = document.getElementById("shows-grid");
const filterBar = document.getElementById("shows-filters");
const stats = document.getElementById("shows-stats");

let activeFilter = FILTERS[0];
let activeStatus = ""; // "" = any status
let cards = [];
const buttons = [];
const statusMenu = makeStatusMenu();

try {
  // Nothing picktwo answers, or fails to, may stop the list from showing.
  const duels = getJSON(DUELS_API, DUELS_WAIT_MS)
    .then((rows) => {
      if (!Array.isArray(rows)) throw new Error(`${DUELS_API}: not a list`);
      return rows;
    })
    .catch((err) => {
      console.warn("Showing my own ratings: couldn't read picktwo's.", err);
      return [];
    });
  const [shows, standings] = await Promise.all([getJSON(SHOWS_API), duels]);
  init(withDuelRatings(shows, standings));
} catch (err) {
  stats.textContent = "Couldn't load the list.";
  console.error(err);
}

async function getJSON(url, timeoutMs) {
  const res = await fetch(url, timeoutMs ? { signal: AbortSignal.timeout(timeoutMs) } : undefined);
  if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
  return res.json();
}

// picktwo's committed standings, keyed "website:<id>": a show's score there replaces its hand-set
// rating on the page, and its duel rank orders shows that end up level. A show picktwo hasn't
// ranked keeps its own rating, and its place in the API's order. The database's `rating` is never
// written: picktwo starts from it, so writing duel results into it would count the duels twice.
function withDuelRatings(shows, standings) {
  const byKey = new Map(standings.map((s) => [s.item, s]));
  const duel = (show) => byKey.get(`website:${show.id}`);
  for (const show of shows) {
    const score = duel(show)?.score;
    if (typeof score === "number") show.rating = score;
  }
  const rank = (show) => duel(show)?.rank ?? Infinity;
  return shows.sort((a, b) => b.rating - a.rating || rank(a) - rank(b) || 0); // Infinity − Infinity is NaN: keep API order
}

// Rows arrive sorted, and the database guarantees each has a title and rating.
function init(shows) {
  for (const show of shows) show.labels = [...(show.genres ?? []), ...(show.tags ?? [])];
  cards = shows.map((show, i) => {
    const node = renderCard(show, i < EAGER_POSTERS);
    return { show, node, rankBadge: node.querySelector(".show-rank") };
  });
  grid.append(...cards.map((card) => card.node));

  for (const filter of FILTERS) {
    addButton(filter.label, () => filter === activeFilter, () => (activeFilter = filter));
  }
  filterBar.append(statusMenu.wrapper);
  readHash();
  window.addEventListener("hashchange", readHash);
}

function renderCard(show, eager) {
  const link = el("a");
  const url = showUrl(show);
  if (url) {
    link.href = url;
    link.target = "_blank";
    link.rel = "noopener";
  }
  link.title = show.title;

  const img = el("img");
  if (show.poster) img.src = show.poster; // otherwise the grey placeholder shows
  img.alt = "";
  img.loading = eager ? "eager" : "lazy";
  img.decoding = "async";
  const poster = el("div", "show-poster");
  const watched = watchedShare(show);
  if (watched !== null && watched < 1) {
    poster.classList.add("is-unfinished");
    poster.style.setProperty("--watched", watched);
  }
  poster.append(img, el("span", "show-rank"), el("span", "show-rating", show.rating.toFixed(1))); // rank set by update()

  link.append(poster, el("div", "show-title", show.title), el("div", "show-meta", progressText(show)));
  const item = el("li", "show");
  item.append(link);
  return item;
}

// How much of a show I've seen: all of it when completed; for unfinished shows, the seasons
// before the one I'm on plus half of that one. null when the season isn't known.
function watchedShare(show) {
  if (show.status === "completed") return 1;
  if (!show.season || !show.seasons) return null;
  return Math.min((show.season - 0.5) / show.seasons, 1);
}

function summary(shows) {
  let episodes = 0;
  let minutes = 0;
  for (const show of shows) {
    const seen = (show.episodes ?? 0) * (watchedShare(show) ?? 0);
    episodes += seen;
    minutes += seen * (show.episode_minutes ?? 0);
  }
  const format = (n) => Math.round(n).toLocaleString("en");
  return `${shows.length} Shows · ${format(episodes)} episodes · ${format(minutes / 60)} hours watched`;
}

function progressText(show) {
  const of = show.seasons > 1 ? ` of ${show.seasons}` : "";
  if (show.status === "watching") return show.season ? `Watching Season ${show.season}${of}` : "Watching";
  if (show.status === "abandoned") return show.season ? `Left at Season ${show.season}${of}` : "Abandoned";
  return show.seasons ? `Completed · ${show.seasons} Season${show.seasons === 1 ? "" : "s"}` : "Completed";
}

function showUrl(show) {
  if (show.imdb) return `https://www.imdb.com/title/${show.imdb}/`;
  if (show.tvmaze) return `https://www.tvmaze.com/shows/${show.tvmaze}`;
  return null;
}

function addButton(label, isPressed, apply) {
  const button = el("button", null, label);
  button.type = "button";
  button.addEventListener("click", () => {
    apply();
    update();
  });
  buttons.push({ button, isPressed });
  filterBar.append(button);
  return button;
}

// A native <select> styled as a chip: "Status: Any", "Status: Watching", ...
function makeStatusMenu() {
  const select = el("select");
  select.setAttribute("aria-label", "Status");
  select.append(new Option("Status: Any", ""));
  for (const [value, label] of Object.entries(STATUSES)) select.append(new Option(`Status: ${label}`, value));
  select.addEventListener("change", () => {
    activeStatus = select.value;
    update();
  });
  const wrapper = el("span", "shows-status");
  wrapper.append(select);
  return { wrapper, select };
}

function matches(show) {
  return (
    (!activeFilter.tag || show.labels.includes(activeFilter.tag)) && (!activeStatus || show.status === activeStatus)
  );
}

function update() {
  for (const { show, node } of cards) node.hidden = !matches(show);
  for (const { button, isPressed } of buttons) button.setAttribute("aria-pressed", String(isPressed()));
  statusMenu.select.value = activeStatus;
  statusMenu.wrapper.classList.toggle("is-active", activeStatus !== "");
  const visible = cards.filter(({ node }) => !node.hidden);
  rankWithin(visible);
  visible.forEach(sharpen);
  stats.textContent = visible.length ? summary(visible.map(({ show }) => show)) : "No shows match.";
  writeHash();
}

// Number the visible cards (already sorted by rating) 1, 2, 2, 4, ...: tied ratings share a rank.
function rankWithin(visible) {
  let rank = 0;
  visible.forEach(({ show, rankBadge }, i) => {
    if (show.rating !== visible[i - 1]?.show.rating) rank = i + 1;
    rankBadge.textContent = rank;
  });
}

// A tile drawn wider than the small poster (the big tiles at the top, on desktop) would blur
// it, so swap in the full-size poster once it has downloaded and decoded (decoding first
// avoids a blank flash).
function sharpen({ show, node }) {
  const img = node.querySelector("img");
  if (!show.poster_large || img.dataset.large || img.clientWidth <= SMALL_POSTER_WIDTH) return;
  img.dataset.large = "requested";
  const full = new Image();
  full.src = show.poster_large;
  full.decode().then(
    () => (img.src = full.src),
    () => {} // keep the small poster if the big one fails
  );
}

function readHash() {
  let hash = location.hash.slice(1);
  try {
    hash = decodeURIComponent(hash);
  } catch {
    // a malformed escape such as "#drama%": match against the raw text instead
  }
  const parts = hash.split("+");
  activeFilter = FILTERS.find((filter) => filter.tag && parts.includes(filter.key)) ?? FILTERS[0];
  activeStatus = Object.keys(STATUSES).find((status) => parts.includes(status)) ?? "";
  update();
}

function writeHash() {
  const parts = activeFilter.tag ? [activeFilter.key] : [];
  if (activeStatus) parts.push(activeStatus);
  const hash = parts.length ? `#${parts.join("+")}` : "";
  if (hash !== location.hash) history.replaceState(null, "", hash || location.pathname + location.search);
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
