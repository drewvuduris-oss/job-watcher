/* Shared by every page: navigation bar, data loading, date helpers, service worker. */
(function () {
  "use strict";

  const PAGES = [
    { href: "index.html", label: "Today" },
    { href: "browse.html", label: "Browse" },
    { href: "market.html", label: "Market" },
  ];

  function renderNav() {
    const here = location.pathname.split("/").pop() || "index.html";
    const nav = document.createElement("nav");
    nav.className = "nav";
    nav.innerHTML = `
      <div class="nav-inner">
        <a class="brand" href="index.html"><img src="icons/icon.svg" alt=""><span>Job Watcher</span></a>
        <div class="nav-links">
          ${PAGES.map(p => `<a href="${p.href}"${p.href === here ? ' aria-current="page"' : ""}>${p.label}</a>`).join("")}
        </div>
        <div class="nav-status" id="net-status"></div>
      </div>`;
    document.body.prepend(nav);
    const status = nav.querySelector("#net-status");
    const update = () => {
      status.textContent = navigator.onLine ? "" : "Offline – showing saved data";
      status.classList.toggle("offline", !navigator.onLine);
    };
    addEventListener("online", update);
    addEventListener("offline", update);
    update();
  }

  // ------------------------------------------------------------------ data
  async function fetchText(path) {
    // The service worker answers from the network when online and from its cache offline.
    const resp = await fetch(path, { cache: "no-cache" });
    if (!resp.ok) throw new Error(`${path}: HTTP ${resp.status}`);
    return resp.text();
  }

  async function loadStatus() {
    return JSON.parse(await fetchText("data/status.json"));
  }

  async function loadHistory() {
    const text = await fetchText("data/history.csv");
    const parsed = Papa.parse(text, { header: true, skipEmptyLines: true });
    return parsed.data.map(r => ({
      ...r,
      in_role: r.in_role === "true",
      first_run: r.first_run === "true",
    }));
  }

  // ------------------------------------------------------------------ dates (UTC 'YYYY-MM-DD')
  const DAY = 86400000;
  const toMs = d => Date.UTC(+d.slice(0, 4), +d.slice(5, 7) - 1, +d.slice(8, 10));
  const daysBetween = (a, b) => Math.round((toMs(b) - toMs(a)) / DAY);
  const addDays = (d, n) => new Date(toMs(d) + n * DAY).toISOString().slice(0, 10);
  function dateRange(start, end) {
    const out = [];
    for (let d = start; d <= end; d = addDays(d, 1)) out.push(d);
    return out;
  }
  const maxDate = rows => rows.reduce((m, r) => (r.last_seen > m ? r.last_seen : m), "");
  const shortDate = d => new Date(toMs(d)).toLocaleDateString(undefined, { month: "short", day: "numeric", timeZone: "UTC" });

  // ------------------------------------------------------------------ misc
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const fmt = n => Number(n).toLocaleString();
  const pct = (x, digits = 0) => `${(x * 100).toFixed(digits)}%`;
  const median = xs => {
    if (!xs.length) return null;
    const s = [...xs].sort((a, b) => a - b), m = s.length >> 1;
    return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
  };
  const countBy = (rows, key) => {
    const m = new Map();
    for (const r of rows) { const k = typeof key === "function" ? key(r) : r[key]; m.set(k, (m.get(k) || 0) + 1); }
    return m;
  };
  const cssVar = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

  function showError(err) {
    console.error(err);
    const main = document.querySelector("main");
    const div = document.createElement("div");
    div.className = "banner";
    div.textContent = `Could not load the data (${err.message}). If you are offline, open this page once while online so it can be saved.`;
    main.prepend(div);
  }

  // ------------------------------------------------------------------ shortlist (localStorage)
  const SHORTLIST_KEY = "jobwatcher.shortlist";
  const shortlist = {
    all() {
      try { return JSON.parse(localStorage.getItem(SHORTLIST_KEY)) || {}; } catch { return {}; }
    },
    has(id) { return id in this.all(); },
    toggle(rec) {
      const all = this.all();
      if (rec.posting_id in all) delete all[rec.posting_id];
      else all[rec.posting_id] = { title: rec.title, employer: rec.employer, url: rec.url, saved: new Date().toISOString() };
      try { localStorage.setItem(SHORTLIST_KEY, JSON.stringify(all)); } catch { /* storage blocked */ }
      return rec.posting_id in all;
    },
  };

  // ------------------------------------------------------------------ service worker
  if ("serviceWorker" in navigator) {
    addEventListener("load", () => navigator.serviceWorker.register("sw.js").catch(e => console.warn("SW", e)));
  }

  document.addEventListener("DOMContentLoaded", renderNav);

  window.JW = {
    loadStatus, loadHistory, daysBetween, addDays, dateRange, maxDate, shortDate,
    esc, fmt, pct, median, countBy, cssVar, showError, shortlist,
  };
})();
