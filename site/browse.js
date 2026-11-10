/* Browse page: open postings with role switch, filters, search, sort and a shortlist. */
(async function () {
  "use strict";
  const { esc, fmt, daysBetween, shortDate, shortlist } = JW;
  const $ = id => document.getElementById(id);
  const PAGE = 100;

  let rows;
  try {
    ({ rows } = await JW.loadHistoryWithDfw());
  } catch (err) {
    JW.showError(err);
    $("count").textContent = "";
    return;
  }

  const lastRun = JW.maxDate(rows);
  const open = rows.filter(r => r.status === "open");
  for (const r of open) r.days_open = daysBetween(r.first_seen, lastRun);

  const state = { role: true, dfw: true, shown: PAGE };

  // employer and location choices come from the open postings
  const employers = [...new Set(open.map(r => r.employer))].sort();
  $("employer").insertAdjacentHTML("beforeend", employers.map(e => `<option>${esc(e)}</option>`).join(""));
  const locCounts = JW.countBy(open.filter(r => r.location), "location");
  $("locations").innerHTML = [...locCounts.entries()]
    .sort((a, b) => b[1] - a[1]).slice(0, 300)
    .map(([loc]) => `<option value="${esc(loc)}">`).join("");

  function filtered() {
    const q = $("q").value.trim().toLowerCase();
    const emp = $("employer").value;
    const loc = $("location").value.trim().toLowerCase();
    const [lo, hi] = ($("days").value || "-").split("-").map(x => (x === "" ? null : +x));
    const starredOnly = $("starred").checked;
    const saved = shortlist.all();
    const out = open.filter(r =>
      (!state.role || r.in_role) &&
      (!state.dfw || r.in_dfw) &&
      (!q || r.title.toLowerCase().includes(q)) &&
      (!emp || r.employer === emp) &&
      (!loc || r.location.toLowerCase().includes(loc)) &&
      (lo === null || r.days_open >= lo) &&
      (hi === null || r.days_open <= hi) &&
      (!starredOnly || r.posting_id in saved));
    const dir = $("sort").value === "asc" ? 1 : -1;
    out.sort((a, b) => dir * a.first_seen.localeCompare(b.first_seen) || a.employer.localeCompare(b.employer) || a.title.localeCompare(b.title));
    return out;
  }

  function item(r) {
    const on = shortlist.has(r.posting_id);
    const days = `${r.days_open}${r.first_run ? "+" : ""} day${r.days_open === 1 && !r.first_run ? "" : "s"} open`;
    return `
      <li class="posting">
        <button type="button" class="star" data-id="${esc(r.posting_id)}" aria-pressed="${on}"
          aria-label="${on ? "Remove from" : "Add to"} shortlist: ${esc(r.title)}" title="Shortlist">${on ? "★" : "☆"}</button>
        <div class="body">
          <a class="title" href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.title)}</a>
          ${r.in_role ? '<span class="tag role">In role</span>' : ""}
          ${r.in_dfw ? '<span class="tag dfw">DFW</span>' : ""}
          <div class="meta">${esc(r.employer)}${r.location ? " · " + esc(r.location) : ""}${r.department ? " · " + esc(r.department) : ""}</div>
          <a class="apply" href="${esc(r.url)}" target="_blank" rel="noopener">Apply ↗</a>
        </div>
        <div class="side">first seen ${esc(shortDate(r.first_seen))}<br>${days}</div>
      </li>`;
  }

  function render() {
    const list = filtered();
    $("count").textContent = `${fmt(list.length)} open posting${list.length === 1 ? "" : "s"}` +
      (state.role ? " in finance-analyst roles" : "") + (state.dfw ? " in the DFW Metroplex" : "") + ` · last run ${lastRun}`;
    $("list").innerHTML = list.length
      ? list.slice(0, state.shown).map(item).join("")
      : '<li class="empty">No open postings match these filters.</li>';
    $("more").hidden = list.length <= state.shown;
    $("more").textContent = `Show more (${fmt(list.length - state.shown)} left)`;
    $("star-count").textContent = `(${Object.keys(shortlist.all()).length})`;
  }

  function setRole(role) {
    state.role = role;
    $("mode-role").setAttribute("aria-pressed", role);
    $("mode-all").setAttribute("aria-pressed", !role);
    state.shown = PAGE;
    render();
  }

  function setRegion(dfw) {
    state.dfw = dfw;
    $("region-dfw").setAttribute("aria-pressed", dfw);
    $("region-all").setAttribute("aria-pressed", !dfw);
    state.shown = PAGE;
    render();
  }

  $("region-dfw").addEventListener("click", () => setRegion(true));
  $("region-all").addEventListener("click", () => setRegion(false));
  $("mode-role").addEventListener("click", () => setRole(true));
  $("mode-all").addEventListener("click", () => setRole(false));
  for (const id of ["q", "employer", "location", "days", "sort", "starred"]) {
    $(id).addEventListener(id === "q" || id === "location" ? "input" : "change", () => { state.shown = PAGE; render(); });
  }
  $("more").addEventListener("click", () => { state.shown += PAGE; render(); });
  $("reset").addEventListener("click", () => {
    for (const id of ["q", "employer", "location", "days"]) $(id).value = "";
    $("sort").value = "desc";
    $("starred").checked = false;
    state.dfw = true;
    $("region-dfw").setAttribute("aria-pressed", true);
    $("region-all").setAttribute("aria-pressed", false);
    setRole(true);
  });
  $("list").addEventListener("click", e => {
    const btn = e.target.closest(".star");
    if (!btn) return;
    const rec = open.find(r => r.posting_id === btn.dataset.id);
    const on = shortlist.toggle(rec);
    btn.setAttribute("aria-pressed", on);
    btn.textContent = on ? "★" : "☆";
    $("star-count").textContent = `(${Object.keys(shortlist.all()).length})`;
    if (!on && $("starred").checked) render();
  });

  render();
})();
