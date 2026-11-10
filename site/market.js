/* Market page: six findings computed from history.csv in the browser.
 *
 * Definitions (first_run postings were already open when watching began, so
 * their start date is unknown and they are left out where noted):
 *  1 new per day      first_seen == day, first_run false (all postings and in role)
 *  2 removed per day  removed_date == day
 *  3 open by employer status == open
 *  4 days open        removed, first_run false: removed_date - first_seen; median reported
 *  5 removed <= 7d    first_run false and first_seen <= last run - 7 days:
 *                     share with removed_date - first_seen <= 7
 *  6 top locations    status == open, grouped by location
 * "Last run" is the latest last_seen date in the history.
 */
(async function () {
  "use strict";
  const { esc, fmt, pct, median, countBy, daysBetween, addDays, dateRange, shortDate, cssVar } = JW;

  let rows;
  try {
    rows = await JW.loadHistory();
  } catch (err) {
    JW.showError(err);
    return;
  }
  if (!rows.length) {
    document.getElementById("sections").innerHTML = '<div class="empty">The history is empty – the first run has not happened yet.</div>';
    return;
  }

  const lastRun = JW.maxDate(rows);
  const firstDay = rows.reduce((m, r) => (r.first_seen < m ? r.first_seen : m), lastRun);
  const days = dateRange(firstDay, lastRun);
  const open = rows.filter(r => r.status === "open");
  const tracked = rows.filter(r => !r.first_run);

  document.getElementById("intro").insertAdjacentHTML("beforeend",
    ` History covers <strong>${days.length}</strong> day${days.length === 1 ? "" : "s"} (${firstDay} to ${lastRun}) and <strong>${fmt(rows.length)}</strong> postings.`);

  // ------------------------------------------------------------------ chart helpers
  Chart.defaults.font.family = getComputedStyle(document.body).fontFamily;
  Chart.defaults.color = cssVar("--text-2");
  Chart.defaults.borderColor = cssVar("--grid");
  Chart.defaults.plugins.legend.display = false;
  Chart.defaults.maintainAspectRatio = false;
  Chart.defaults.animation = false;

  const C1 = cssVar("--series-1"), C2 = cssVar("--series-2");
  const barStyle = color => ({ backgroundColor: color, hoverBackgroundColor: color, borderRadius: 4, borderSkipped: "start", maxBarThickness: 36 });
  const intAxis = title => ({ beginAtZero: true, ticks: { precision: 0 }, title: { display: !!title, text: title }, grid: { color: cssVar("--grid") } });

  const container = document.getElementById("sections");
  let n = 0;

  function section({ heading, text, table, empty }) {
    n += 1;
    const el = document.createElement("section");
    el.className = "card finding";
    el.innerHTML = `
      <div class="kicker">Finding ${n}</div>
      <h2>${heading}</h2>
      <p>${text}</p>
      <div class="charts"></div>
      ${table && !empty ? `<details class="data"><summary>Show the numbers</summary><div class="table-wrap">${table}</div></details>` : ""}`;
    container.appendChild(el);
    if (empty) el.querySelector(".charts").innerHTML = `<div class="empty">${empty}</div>`;
    return el.querySelector(".charts");
  }

  function canvas(parent, { tall = false, label = "" } = {}) {
    const wrap = document.createElement("div");
    if (label) wrap.innerHTML = `<h3 class="small muted" style="margin-top:8px">${label}</h3>`;
    const box = document.createElement("div");
    box.className = "chart-box" + (tall ? " tall" : "");
    const cv = document.createElement("canvas");
    cv.setAttribute("role", "img");
    box.appendChild(cv);
    wrap.appendChild(box);
    parent.appendChild(wrap);
    return cv;
  }

  function htmlTable(headers, data) {
    return `<table><thead><tr>${headers.map((h, i) => `<th${i ? ' class="r"' : ""}>${esc(h)}</th>`).join("")}</tr></thead>
      <tbody>${data.map(r => `<tr>${r.map((c, i) => `<td${i ? ' class="r"' : ""}>${esc(c)}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
  }

  const dayLabels = days.map(shortDate);
  const perDay = list => { const m = countBy(list, x => x); return days.map(d => m.get(d) || 0); };
  // days after each source's baseline: the first day is all first-run postings
  const watchDays = days.slice(1);

  // ------------------------------------------------------------------ 1. new postings per day
  {
    const all = perDay(tracked.map(r => r.first_seen));
    const role = perDay(tracked.filter(r => r.in_role).map(r => r.first_seen));
    const totAll = all.reduce((a, b) => a + b, 0), totRole = role.reduce((a, b) => a + b, 0);
    const avg = x => (watchDays.length ? x / watchDays.length : 0);
    const heading = watchDays.length
      ? `Employers added about ${fmt(Math.round(avg(totAll)))} new postings a day – ${avg(totRole).toFixed(1)} a day in finance-analyst roles`
      : "No new postings yet: the first day is the baseline";
    const charts = section({
      heading,
      text: `A posting is new on the day the watcher first sees it. Postings that were already open on a source's first day are left out, because they were not new that day. ` +
        `Over ${watchDays.length} day${watchDays.length === 1 ? "" : "s"} after the first run, the watcher found ${fmt(totAll)} new postings, of which ${fmt(totRole)} (${totAll ? pct(totRole / totAll, 1) : "0%"}) match the finance-analyst title rule. ` +
        `The two charts use their own scales: role postings are a small slice of all postings.`,
      table: htmlTable(["Day", "All postings", "Finance-analyst roles"], days.map((d, i) => [d, all[i], role[i]])),
      empty: watchDays.length ? "" : "The chart starts on the second day of watching.",
    });
    if (watchDays.length) {
    charts.classList.add("grid-2");
    new Chart(canvas(charts, { label: "All postings" }), {
      type: "bar",
      data: { labels: dayLabels, datasets: [{ label: "New postings", data: all, ...barStyle(C1) }] },
      options: { scales: { y: intAxis("Postings") } },
    });
    new Chart(canvas(charts, { label: "Finance-analyst roles" }), {
      type: "bar",
      data: { labels: dayLabels, datasets: [{ label: "New in-role postings", data: role, ...barStyle(C2) }] },
      options: { scales: { y: intAxis("Postings") } },
    });
    }
  }

  // ------------------------------------------------------------------ 2. removed postings per day
  {
    const removed = rows.filter(r => r.removed_date);
    const counts = perDay(removed.map(r => r.removed_date));
    const total = counts.reduce((a, b) => a + b, 0);
    let peak = 0;
    counts.forEach((c, i) => { if (c > counts[peak]) peak = i; });
    const heading = total
      ? `${fmt(total)} postings came down in ${days.length} days; the busiest day was ${shortDate(days[peak])} with ${fmt(counts[peak])}`
      : "No postings have been removed yet";
    const charts = section({
      heading,
      text: `A posting is removed on the first day its source answers without listing it. A source that fails to answer removes nothing that day. ` +
        (total ? `On average ${fmt(Math.round(total / Math.max(watchDays.length, 1)))} postings a day were removed after the first run; ${fmt(removed.filter(r => r.in_role).length)} of the ${fmt(total)} were in finance-analyst roles.` : "Removals start to appear from the second day of watching."),
      table: htmlTable(["Day", "Removed"], days.map((d, i) => [d, counts[i]])),
      empty: watchDays.length ? "" : "The chart starts on the second day of watching.",
    });
    if (watchDays.length) new Chart(canvas(charts), {
      type: "bar",
      data: { labels: dayLabels, datasets: [{ label: "Removed postings", data: counts, ...barStyle(C1) }] },
      options: { scales: { y: intAxis("Postings") } },
    });
  }

  // ------------------------------------------------------------------ 3. open postings per employer
  {
    const byEmp = [...countBy(open, "employer").entries()].sort((a, b) => b[1] - a[1]);
    const roleByEmp = countBy(open.filter(r => r.in_role), "employer");
    const [topName, topCount] = byEmp[0] || ["–", 0];
    const charts = section({
      heading: `${esc(topName)} lists the most open postings: ${fmt(topCount)} of ${fmt(open.length)} (${pct(topCount / Math.max(open.length, 1))})`,
      text: `Open postings per employer as of the last run on ${lastRun}. Employers' boards differ a lot in size, so a large employer can dominate the totals; ` +
        `for finance-analyst roles the leader is ${esc([...roleByEmp.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] || "none yet")} with ${fmt(Math.max(0, ...roleByEmp.values()))} open.`,
      table: htmlTable(["Employer", "Open postings", "In role"], byEmp.map(([e, c]) => [e, c, roleByEmp.get(e) || 0])),
    });
    new Chart(canvas(charts, { tall: true }), {
      type: "bar",
      data: { labels: byEmp.map(x => x[0]), datasets: [{ label: "Open postings", data: byEmp.map(x => x[1]), ...barStyle(C1), maxBarThickness: 18 }] },
      options: { indexAxis: "y", scales: { x: intAxis("Open postings"), y: { grid: { display: false } } } },
    });
  }

  // ------------------------------------------------------------------ 4. days open (median)
  {
    const closed = tracked.filter(r => r.status === "removed" && r.removed_date);
    const durations = closed.map(r => daysBetween(r.first_seen, r.removed_date));
    const med = median(durations);
    const maxD = durations.length ? Math.max(...durations) : 0;
    const hist = Array.from({ length: maxD + 1 }, (_, d) => durations.filter(x => x === d).length);
    const charts = section({
      heading: med === null
        ? "Days open: no posting has opened and closed while being watched yet"
        : `Postings that closed were up for a median of ${med} day${med === 1 ? "" : "s"}`,
      text: `Days open is the removed date minus the first-seen date, for removed postings that were first seen after their source's first run (${fmt(closed.length)} postings). ` +
        `Postings that were already open when watching began are left out because their start date is unknown. ` +
        (med === null ? "This number appears once a posting the watcher saw appear is taken down." : `Half of these postings came down within ${med} days; the longest lasted ${maxD} days.`),
      table: htmlTable(["Days open", "Postings"], hist.map((c, d) => [d, c])),
      empty: med === null ? "Waiting for postings that open and close while being watched." : "",
    });
    if (med !== null) {
      new Chart(canvas(charts), {
        type: "bar",
        data: {
          labels: hist.map((_, d) => String(d)),
          datasets: [{ label: "Postings", data: hist, ...barStyle(C1), backgroundColor: hist.map((_, d) => (d === Math.round(med) ? C2 : C1)) }],
        },
        options: {
          scales: { x: { title: { display: true, text: "Days open (orange = median)" }, grid: { display: false } }, y: intAxis("Postings") },
          plugins: { tooltip: { callbacks: { title: items => `${items[0].label} days open` } } },
        },
      });
    }
  }

  // ------------------------------------------------------------------ 5. share removed within seven days
  {
    const cutoff = addDays(lastRun, -7);
    const eligible = tracked.filter(r => r.first_seen <= cutoff);
    const quick = r => r.removed_date && daysBetween(r.first_seen, r.removed_date) <= 7;
    const nQuick = eligible.filter(quick).length;
    const share = eligible.length ? nQuick / eligible.length : null;
    const byEmp = [...countBy(eligible, "employer").entries()]
      .map(([e, c]) => [e, eligible.filter(r => r.employer === e && quick(r)).length, c])
      .sort((a, b) => b[1] / b[2] - a[1] / a[2]);
    const charts = section({
      heading: share === null
        ? "Share removed within seven days: needs postings first seen at least seven days ago"
        : `${pct(share)} of postings came down within seven days`,
      text: `Counted among postings first seen on or before ${cutoff} (seven days before the last run) that were not already open when watching began – ${fmt(eligible.length)} postings. ` +
        `A posting counts as removed within seven days when its removed date minus its first-seen date is seven days or less. ` +
        (share === null ? `The first postings become eligible on ${addDays(firstDay, 8)}.` : `${fmt(nQuick)} of ${fmt(eligible.length)} met that test. The chart breaks the share out by employer.`),
      table: htmlTable(["Employer", "Removed ≤ 7 days", "Eligible", "Share"], byEmp.map(([e, q, c]) => [e, q, c, pct(q / c, 1)])),
      empty: share === null ? "Waiting for seven days of history after the first run." : "",
    });
    if (share !== null) {
      new Chart(canvas(charts, { tall: byEmp.length > 8 }), {
        type: "bar",
        data: { labels: byEmp.map(x => x[0]), datasets: [{ label: "Share removed within 7 days", data: byEmp.map(x => x[1] / x[2] * 100), ...barStyle(C1), maxBarThickness: 18 }] },
        options: {
          indexAxis: "y",
          scales: { x: { beginAtZero: true, max: 100, ticks: { callback: v => v + "%" }, title: { display: true, text: "Share removed within 7 days" } }, y: { grid: { display: false } } },
          plugins: { tooltip: { callbacks: { label: c => `${c.parsed.x.toFixed(1)}% (${byEmp[c.dataIndex][1]} of ${byEmp[c.dataIndex][2]})` } } },
        },
      });
    }
  }

  // ------------------------------------------------------------------ 6. top locations among open postings
  {
    // Workday lists a multi-site posting as "2 Locations", which is not a place; those are counted apart.
    const multi = r => /^\d+ Locations$/i.test(r.location);
    const placed = open.filter(r => r.location && !multi(r));
    const nMulti = open.filter(multi).length, nBlank = open.filter(r => !r.location).length;
    const byLoc = [...countBy(placed, "location").entries()].sort((a, b) => b[1] - a[1]);
    const top = byLoc.slice(0, 15);
    const roleTop = [...countBy(placed.filter(r => r.in_role), "location").entries()].sort((a, b) => b[1] - a[1])[0];
    const charts = section({
      heading: `${esc(top[0]?.[0] || "–")} has the most open postings (${fmt(top[0]?.[1] || 0)})`,
      text: `The 15 most common locations among the ${fmt(open.length)} open postings, written as each employer's board writes them. ` +
        `${fmt(nMulti)} Workday postings list only “N Locations” and ${fmt(nBlank)} give no location; they are left out of the ranking. ` +
        `The top 15 hold ${pct(top.reduce((a, x) => a + x[1], 0) / Math.max(open.length, 1))} of all open postings` +
        (roleTop ? `; among finance-analyst roles the top location is ${esc(roleTop[0])} with ${fmt(roleTop[1])}.` : "."),
      table: htmlTable(["Location", "Open postings"], [...byLoc.slice(0, 50), ["(N Locations)", nMulti], ["(not given)", nBlank]]),
    });
    new Chart(canvas(charts, { tall: true }), {
      type: "bar",
      data: { labels: top.map(x => x[0]), datasets: [{ label: "Open postings", data: top.map(x => x[1]), ...barStyle(C1), maxBarThickness: 18 }] },
      options: { indexAxis: "y", scales: { x: intAxis("Open postings"), y: { grid: { display: false } } } },
    });
  }
})();
