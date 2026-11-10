/* Today page: last run, source status, the four counts, new and removed postings. */
(async function () {
  "use strict";
  const { esc, fmt } = JW;
  const $ = id => document.getElementById(id);
  const LIMIT = 150;

  let status, rows;
  try {
    [status, { rows }] = await Promise.all([JW.loadStatus(), JW.loadHistoryWithDfw()]);
  } catch (err) {
    JW.showError(err);
    return;
  }

  const runDate = status.run_date || status.run_time.slice(0, 10);
  const runTime = new Date(status.run_time);
  $("run-line").innerHTML =
    `Last run <strong>${esc(runTime.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" }))}</strong> ` +
    `(${esc(status.run_time.replace("T", " ").replace("Z", " UTC"))}) · watching since ${esc(status.first_run_date)}`;

  $("t-days").textContent = fmt(status.days_with_success);
  $("t-days-sub").textContent = `since ${status.first_run_date}`;
  $("t-open").textContent = fmt(status.open);
  $("t-open-sub").textContent = `${fmt(rows.filter(r => r.status === "open" && r.in_role).length)} in finance-analyst roles`;
  $("t-new").textContent = fmt(status.new_today);
  $("t-removed").textContent = fmt(status.removed_today);

  const newRows = rows.filter(r => r.first_seen === runDate && !r.first_run);
  const removedRows = rows.filter(r => r.removed_date === runDate);
  $("t-new-sub").textContent = `${fmt(newRows.filter(r => r.in_role).length)} in role`;
  $("t-removed-sub").textContent = `${fmt(removedRows.filter(r => r.in_role).length)} in role`;
  const openDfw = rows.filter(r => r.status === "open" && r.in_dfw);
  $("t-dfw").textContent = fmt(openDfw.length);
  $("t-dfw-sub").innerHTML = `${fmt(openDfw.filter(r => r.in_role).length)} in role · <a href="browse.html">browse</a>`;
  $("t-new-sub").textContent += ` · ${fmt(newRows.filter(r => r.in_dfw).length)} DFW`;
  $("t-removed-sub").textContent += ` · ${fmt(removedRows.filter(r => r.in_dfw).length)} DFW`;
  const firstRunToday = rows.filter(r => r.first_seen === runDate && r.first_run).length;

  function renderList(listId, countId, roleBoxId, list, emptyText) {
    const box = $(roleBoxId), dfwBox = $(roleBoxId.replace("-role", "-dfw"));
    const draw = () => {
      const shown = list
        .filter(r => (!box.checked || r.in_role) && (!dfwBox.checked || r.in_dfw))
        .sort((a, b) => (b.in_role - a.in_role) || (b.in_dfw - a.in_dfw) || a.employer.localeCompare(b.employer) || a.title.localeCompare(b.title));
      $(countId).textContent = `(${fmt(shown.length)})`;
      const ul = $(listId);
      if (!shown.length) {
        ul.innerHTML = `<li class="empty">${esc(list.length ? "No postings match these filters." : emptyText)}</li>`;
        return;
      }
      ul.innerHTML = shown.slice(0, LIMIT).map(r => `
        <li class="posting">
          <div class="body">
            <a class="title" href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.title)}</a>
            ${r.in_role ? '<span class="tag role">In role</span>' : ""}
            ${r.in_dfw ? '<span class="tag dfw">DFW</span>' : ""}
            <div class="meta">${esc(r.employer)}${r.location ? " · " + esc(r.location) : ""}</div>
          </div>
        </li>`).join("") +
        (shown.length > LIMIT ? `<li class="posting muted small">…and ${fmt(shown.length - LIMIT)} more. See <a href="browse.html">Browse</a>.</li>` : "");
    };
    box.addEventListener("change", draw);
    dfwBox.addEventListener("change", draw);
    draw();
  }

  renderList("new-list", "new-count", "new-role", newRows,
    firstRunToday ? `No new postings: today was the first run for ${fmt(firstRunToday)} postings, which count as already open.` : "No new postings in the latest run.");
  renderList("removed-list", "removed-count", "removed-role", removedRows, "No postings were removed in the latest run.");

  const ok = status.sources.filter(s => s.ok).length;
  $("sources-line").textContent = `${ok} of ${status.sources.length} sources answered in the latest run. A source that fails keeps its postings as they were until it answers again.`;
  $("sources").innerHTML = status.sources
    .slice()
    .sort((a, b) => (a.ok - b.ok) || a.employer.localeCompare(b.employer))
    .map(s => `
      <tr>
        <td>${esc(s.employer)}</td>
        <td><code>${esc(s.name)}</code></td>
        <td>${esc(s.ats)}</td>
        <td>${s.ok ? '<span class="badge ok">✓ OK</span>' : '<span class="badge fail">✕ Failed</span>'}</td>
        <td class="r">${s.ok ? fmt(s.count) : "–"}</td>
        <td class="small muted">${esc(s.error || "")}</td>
      </tr>`).join("");
})();
