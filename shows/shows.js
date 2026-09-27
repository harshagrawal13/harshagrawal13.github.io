// Renders my shows as a ranked poster grid. The list lives in Postgres on kamaji and is served
// read-only by PostgREST (see README). Rank comes from the rating alone, so tied shows share a
// number (1, 2, 2, 4, ...) and are listed A–Z. One tag filter and one status can be active at a
// time; both live in the URL hash, e.g. /shows/#sitcoms+watching.

const SHOWS_API = "https://api.harsh-agrawal.com/shows";
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
const count = document.getElementById("shows-count");

let activeFilter = FILTERS[0];
let activeStatus = ""; // "" = any status
let cards = [];
const buttons = [];
const statusMenu = makeStatusMenu();

try {
  const res = await fetch(SHOWS_API);
  if (!res.ok) throw new Error(`${SHOWS_API}: HTTP ${res.status}`);
  init(await res.json());
} catch (err) {
  count.textContent = "Couldn't load the list.";
  console.error(err);
}

function init(rows) {
  // Postgres enforces the data's rules, but one odd row still mustn't blank the whole page.
  const shows = rows.filter((show) => {
    const valid = typeof show.title === "string" && Number.isFinite(show.rating);
    if (!valid) console.warn("shows: skipping a show without a title and numeric rating", show);
    return valid;
  });
  for (const show of shows) show.labels = [...(show.genres ?? []), ...(show.tags ?? [])];
  shows.sort((a, b) => b.rating - a.rating || a.title.localeCompare(b.title));
  shows.forEach((show, i) => {
    const prev = shows[i - 1];
    show.rank = prev?.rating === show.rating ? prev.rank : i + 1;
  });
  cards = shows.map((show, i) => ({ show, node: renderCard(show, i < EAGER_POSTERS) }));
  grid.append(...cards.map((card) => card.node));
  document.getElementById("shows-stats").textContent = summary(shows);

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
  poster.append(img, el("span", "show-rank", String(show.rank)), el("span", "show-rating", show.rating.toFixed(1)));

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
  visible.forEach(sharpen);
  const n = visible.length;
  count.textContent = n === cards.length ? "" : n ? `${n} of ${cards.length} shows` : "No shows match.";
  writeHash();
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
