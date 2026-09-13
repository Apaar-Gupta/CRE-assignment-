// ---------- Helpers ----------

function parseNumberList(raw) {
  if (!raw) return [];
  return raw
    .split(/[,\n]+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0)
    .map(Number);
}

function fmt(n, digits) {
  if (typeof n !== "number") return n === null || n === undefined ? "&mdash;" : n;
  return n.toFixed(digits === undefined ? 6 : digits);
}

// ---------- Chart ----------

let chartInstance = null;

function renderChart(plot) {
  const wrap = document.getElementById("diff-chart-wrap");
  wrap.innerHTML = '<canvas id="diff-chart-canvas"></canvas>';
  const canvas = document.getElementById("diff-chart-canvas");

  if (chartInstance) chartInstance.destroy();

  chartInstance = new Chart(canvas.getContext("2d"), {
    type: "scatter",
    data: {
      datasets: [
        {
          label: "Data (ln rate vs ln C_A)",
          data: plot.x_data.map((x, i) => ({ x, y: plot.y_data[i] })),
          backgroundColor: "#b4842c",
          pointRadius: 4,
        },
        {
          label: "Best-fit line (slope = order n)",
          data: plot.x_data.map((x, i) => ({ x, y: plot.fit_line[i] })),
          type: "line",
          borderColor: "#1f5c4a",
          backgroundColor: "transparent",
          pointRadius: 0,
          borderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { title: { display: true, text: plot.x_label, color: "#647063" }, ticks: { color: "#647063" }, grid: { color: "#d9ddd0" } },
        y: { title: { display: true, text: plot.y_label, color: "#647063" }, ticks: { color: "#647063" }, grid: { color: "#d9ddd0" } },
      },
      plugins: { legend: { labels: { color: "#1f271f" } } },
    },
  });
}

// ---------- Full calculation table ----------
// Includes EVERY input point, including any excluded from the regression
// (rate <= 0), clearly marked, for full transparency.

function calcTableHtml(table) {
  const rows = table
    .map((row) => {
      const excludedClass = row.used ? "" : ' class="excluded-row"';
      const note = row.used ? "" : "excluded (rate &le; 0)";
      return `<tr${excludedClass}>
        <td>${fmt(row.t, 4)}</td>
        <td>${fmt(row.C_A, 4)}</td>
        <td>${fmt(row.rate, 6)}</td>
        <td>${row.ln_C_A === null ? "&mdash;" : fmt(row.ln_C_A, 6)}</td>
        <td>${row.ln_rate === null ? "&mdash;" : fmt(row.ln_rate, 6)}</td>
        <td>${row.ln_rate_fit === null ? "&mdash;" : fmt(row.ln_rate_fit, 6)}</td>
        <td class="note-cell">${note}</td>
      </tr>`;
    })
    .join("");

  return `
    <div class="calc-table-scroll">
      <table class="calc-table">
        <thead>
          <tr>
            <th>t</th>
            <th>C_A</th>
            <th>-dC_A/dt (rate)</th>
            <th>ln(C_A)</th>
            <th>ln(rate)</th>
            <th>ln(rate) fit</th>
            <th></th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

// ---------- Result rendering ----------

function renderResult(result) {
  const container = document.getElementById("results-content");
  document.getElementById("results-placeholder").style.display = "none";
  container.style.display = "block";

  const excludedNote =
    result.n_points_excluded > 0
      ? `<div class="hint-box" style="margin-top:10px;">${result.n_points_excluded} point(s) were excluded from the regression because their estimated rate came out &le; 0 (see table below) &mdash; this can happen from measurement noise or where C_A briefly flattens out.</div>`
      : "";

  const summaryText = `${result.reaction_type} — k = ${result.k} ${result.k_units} — R² = ${result.r_squared} — ${result.equation}`;

  container.innerHTML = `
    <div class="result-card best-fit">
      <h3>${result.reaction_type} <span class="badge">RESULT</span></h3>
      <div class="result-row"><span>Order (n)</span><strong>${result.order}</strong></div>
      <div class="result-row"><span>k</span><strong>${result.k} ${result.k_units}</strong></div>
      <div class="result-row"><span>R&sup2;</span><strong>${result.r_squared}</strong></div>
      <div class="equation">${result.equation}</div>
      <div class="result-row"><span>slope (= order n)</span><strong>${result.slope}</strong></div>
      <div class="result-row"><span>intercept (= ln k)</span><strong>${result.intercept}</strong></div>
      <div class="result-row"><span>points used / excluded</span><strong>${result.n_points_used} / ${result.n_points_excluded}</strong></div>
      ${excludedNote}
      <div class="mini-chart-wrap" id="diff-chart-wrap" style="height:300px;"></div>
      <details class="calc-details" open>
        <summary>Show full calculation table (${result.table.length} points)</summary>
        ${calcTableHtml(result.table)}
      </details>
      <button type="button" class="copy-btn" data-copy-text="${summaryText.replace(/"/g, "&quot;")}">Copy result</button>
    </div>
  `;

  renderChart(result.plot);
}

function renderError(message) {
  document.getElementById("results-placeholder").style.display = "none";
  const container = document.getElementById("results-content");
  container.style.display = "block";
  container.innerHTML = `<div class="error-box">${message}</div>`;
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }
}

document.getElementById("results-content").addEventListener("click", (e) => {
  const btn = e.target.closest(".copy-btn");
  if (!btn) return;
  const text = btn.dataset.copyText || "";
  navigator.clipboard.writeText(text).then(
    () => {
      const original = btn.textContent;
      btn.textContent = "Copied!";
      setTimeout(() => (btn.textContent = original), 1400);
    },
    () => {
      btn.textContent = "Couldn't copy";
    }
  );
});

// ---------- Form submit ----------

document.getElementById("diff-predictor-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const t = parseNumberList(document.getElementById("t-input").value);
  const C_A = parseNumberList(document.getElementById("ca-input").value);

  if (t.length === 0 || C_A.length === 0) {
    renderError("Please enter both t and C_A data.");
    return;
  }
  if (t.length !== C_A.length) {
    renderError(`t has ${t.length} values but C_A has ${C_A.length} — they must match.`);
    return;
  }

  const submitBtn = document.querySelector(".submit-btn");
  submitBtn.disabled = true;
  submitBtn.textContent = "Solving...";

  try {
    const res = await fetch("/api/predict-differential", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ t, C_A }),
    });
    const data = await res.json();

    if (!res.ok) {
      renderError(data.error || "Something went wrong.");
    } else {
      renderResult(data.result);
    }
  } catch (err) {
    renderError("Could not reach the server: " + err.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Run Solver";
  }
});
