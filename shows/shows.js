// Renders shows.json as a ranked poster grid. Rank comes from the rating alone, so tied
// shows share a number (1, 2, 2, 4, ...) and are listed A–Z. One tag filter is active at a
// time and "Completed" combines with it; the active filters live in the URL hash, e.g.
// /shows/#sitcoms+completed.

const FILTERS = [
  { key: "all", label: "All" },
  { key: "drama", label: "Drama", tag: "Drama" },
  { key: "sitcoms", label: "Sitcoms", tag: "Sitcom" },
  { key: "indian", label: "Indian Shows", tag: "Indian" },
  { key: "documentaries", label: "Documentaries", tag: "Documentary" },
];
const COMPLETED = "completed";
const EAGER_POSTERS = 10; // the first two rows on desktop; the rest load as they scroll into view

const grid = document.getElementById("shows-grid");
const filterBar = document.getElementById("shows-filters");
const count = document.getElementById("shows-count");

let activeFilter = FILTERS[0];
let completedOnly = false;
let cards = [];
const buttons = [];

try {
  const res = await fetch("/shows/shows.json");
  if (!res.ok) throw new Error(`shows.json: HTTP ${res.status}`);
  init(await res.json());
} catch (err) {
  count.textContent = "Couldn't load the list.";
  console.error(err);
}

function init(rows) {
  // shows.json is hand-edited and pushed without checks, so one bad row mustn't blank the page.
  const shows = rows.filter((show) => {
    const valid = typeof show.title === "string" && Number.isFinite(show.rating);
    if (!valid) console.warn("shows.json: skipping a show without a title and numeric rating", show);
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
  document.getElementById("shows-stats").textContent = `${shows.length} shows`;

  for (const filter of FILTERS) {
    addButton(filter.label, () => filter === activeFilter, () => (activeFilter = filter));
  }
  addButton("Completed", () => completedOnly, () => (completedOnly = !completedOnly)).classList.add("shows-toggle");
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
  poster.append(img, el("span", "show-rank", String(show.rank)));

  const meta = el("div", "show-meta");
  meta.append(el("span", "show-rating", show.rating.toFixed(1)));
  if (show.status !== COMPLETED) meta.append(" ", el("span", "show-status", show.status));

  link.append(poster, el("div", "show-title", show.title), meta);
  const item = el("li", "show");
  item.append(link);
  return item;
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

function matches(show) {
  return (
    (!activeFilter.tag || show.labels.includes(activeFilter.tag)) &&
    (!completedOnly || show.status === COMPLETED)
  );
}

function update() {
  for (const { show, node } of cards) node.hidden = !matches(show);
  for (const { button, isPressed } of buttons) button.setAttribute("aria-pressed", String(isPressed()));
  const visible = cards.filter(({ node }) => !node.hidden).length;
  count.textContent =
    visible === cards.length ? "" : visible ? `${visible} of ${cards.length} shows` : "No shows match.";
  writeHash();
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
  completedOnly = parts.includes(COMPLETED);
  update();
}

function writeHash() {
  const parts = activeFilter.tag ? [activeFilter.key] : [];
  if (completedOnly) parts.push(COMPLETED);
  const hash = parts.length ? `#${parts.join("+")}` : "";
  if (hash !== location.hash) history.replaceState(null, "", hash || location.pathname + location.search);
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
