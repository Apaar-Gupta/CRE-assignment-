// ---------- Helpers ----------

function parseNumberList(raw) {
  if (!raw) return [];
  return raw
    .split(/[,\n]+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0)
    .map(Number);
}

function getVal(id) {
  const el = document.getElementById(id);
  const v = el.value.trim();
  return v === "" ? null : Number(v);
}

// ---------- Dynamic field show/hide ----------

const reactionTypeSelect = document.getElementById("reaction-type");
const reactionTypeGroup = document.getElementById("reaction-type-group");
const modeRadios = document.querySelectorAll('input[name="mode"]');
const extraFields = document.querySelectorAll(".extra-field");
const optionalHint = document.getElementById("optional-hint");

function updateVisibleFields() {
  const mode = document.querySelector('input[name="mode"]:checked').value;
  reactionTypeGroup.style.display = mode === "manual" ? "block" : "none";
  optionalHint.style.display = mode === "auto" ? "block" : "none";

  if (mode === "manual") {
    const selected = reactionTypeSelect.value;
    extraFields.forEach((field) => {
      field.classList.toggle("visible", field.dataset.for === selected);
    });
  } else {
    // Auto mode: show ALL optional fields, since any of them being filled
    // in unlocks the corresponding model.
    extraFields.forEach((field) => field.classList.add("visible"));
  }
}

modeRadios.forEach((r) => r.addEventListener("change", updateVisibleFields));
reactionTypeSelect.addEventListener("change", updateVisibleFields);
updateVisibleFields();

// ---------- Chart handling ----------

let chartInstance = null;

function renderSingleSeriesChart(plot) {
  const canvas = document.getElementById("chart-canvas");
  canvas.style.display = "block";
  if (chartInstance) chartInstance.destroy();

  chartInstance = new Chart(canvas.getContext("2d"), {
    type: "scatter",
    data: {
      datasets: [
        {
          label: "Data (linearized)",
          data: plot.x_data.map((x, i) => ({ x, y: plot.y_data[i] })),
          backgroundColor: "#b4842c",
          pointRadius: 4,
        },
        {
          label: "Best-fit line",
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

function renderMultiSeriesChart(plot) {
  const canvas = document.getElementById("chart-canvas");
  canvas.style.display = "block";
  if (chartInstance) chartInstance.destroy();

  const colors = ["#b4842c", "#1f5c4a", "#3d7a9e", "#a83e3e"];
  const datasets = plot.series.map((s, i) => ({
    label: s.name,
    data: plot.x_data.map((x, idx) => ({ x, y: s.y_data[idx] })),
    type: s.type === "line" ? "line" : "scatter",
    borderColor: colors[i % colors.length],
    backgroundColor: colors[i % colors.length],
    pointRadius: s.type === "line" ? 0 : 4,
    borderWidth: 2,
    showLine: s.type === "line",
  }));

  chartInstance = new Chart(canvas.getContext("2d"), {
    type: "scatter",
    data: { datasets },
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

// ---------- Result card rendering ----------

function kRowsHtml(result) {
  if (result.k !== undefined) {
    return `<div class="result-row"><span>k</span><strong>${result.k} ${result.k_units || ""}</strong></div>`;
  }
  let rows = "";
  if (result.k1 !== undefined) {
    rows += `<div class="result-row"><span>k1</span><strong>${result.k1} ${result.k_units || ""}</strong></div>`;
  }
  if (result.k2 !== undefined) {
    rows += `<div class="result-row"><span>k2</span><strong>${result.k2} ${result.k_units || ""}</strong></div>`;
  }
  if (result.K_eq !== undefined) {
    rows += `<div class="result-row"><span>K_eq (k1/k2)</span><strong>${result.K_eq}</strong></div>`;
  }
  return rows;
}

function resultCardHtml(result, isBest) {
  const partialNote =
    result.uses_full_dataset === false
      ? '<div class="result-row" style="color:#b4842c;"><span></span><span>fits C_A only — ignores any extra data you provided</span></div>'
      : "";
  const priorityNote = result.priority_note
    ? `<div class="hint-box" style="margin-top:10px; margin-bottom:0;">${result.priority_note}</div>`
    : "";
  const summaryText = `${result.reaction_type} — ${kRowsPlainText(result)}R² = ${result.r_squared} — ${result.equation}`;

  return `
    <div class="result-card ${isBest ? "best-fit" : ""}">
      <h3>${result.reaction_type} ${isBest ? '<span class="badge">BEST FIT</span>' : ""}</h3>
      ${kRowsHtml(result)}
      <div class="result-row"><span>R&sup2;</span><strong>${result.r_squared}</strong></div>
      <div class="equation">${result.equation}</div>
      ${partialNote}
      ${priorityNote}
      <button type="button" class="copy-btn" data-copy-text="${summaryText.replace(/"/g, "&quot;")}">Copy result</button>
    </div>
  `;
}

function kRowsPlainText(result) {
  if (result.k !== undefined) return `k = ${result.k} ${result.k_units || ""} — `;
  let out = "";
  if (result.k1 !== undefined) out += `k1 = ${result.k1} ${result.k_units || ""} `;
  if (result.k2 !== undefined) out += `k2 = ${result.k2} ${result.k_units || ""} `;
  if (result.K_eq !== undefined) out += `K_eq = ${result.K_eq} `;
  return out ? out + "— " : "";
}

function renderResults(payload) {
  const container = document.getElementById("results-content");
  document.getElementById("results-placeholder").style.display = "none";
  container.style.display = "block";

  let html = "";
  let mainResultForChart = null;

  if (payload.mode === "auto") {
    const { best_fit, all_results, errors } = payload.result;

    if (best_fit) {
      html += resultCardHtml(best_fit, true);
      mainResultForChart = best_fit;
    }

    const others = all_results.filter((r) => r !== best_fit);
    if (others.length > 0) {
      html += '<div class="other-results-title">Other models tried</div>';
      others.forEach((r) => (html += resultCardHtml(r, false)));
    }

    if (errors && errors.length > 0) {
      errors.forEach((e) => {
        html += `<div class="error-box"><strong>${e.reaction_type}:</strong> ${e.error}</div>`;
      });
    }
  } else {
    html += resultCardHtml(payload.result, false);
    mainResultForChart = payload.result;
  }

  container.innerHTML = html;

  if (mainResultForChart && mainResultForChart.plot) {
    if (mainResultForChart.plot.series) {
      renderMultiSeriesChart(mainResultForChart.plot);
    } else {
      renderSingleSeriesChart(mainResultForChart.plot);
    }
  }
}

function renderError(message) {
  document.getElementById("results-placeholder").style.display = "none";
  const container = document.getElementById("results-content");
  container.style.display = "block";
  container.innerHTML = `<div class="error-box">${message}</div>`;
  document.getElementById("chart-canvas").style.display = "none";
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

document.getElementById("predictor-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const mode = document.querySelector('input[name="mode"]:checked').value;
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

  const body = {
    mode,
    reaction_type: mode === "manual" ? reactionTypeSelect.value : null,
    t,
    C_A,
    C_B0: getVal("cb0-input") ?? getVal("cb0-rev-input"),
    C_P0: getVal("cp0-input"),
    C_B_data: parseNumberList(document.getElementById("cb-data-input").value),
    C_Ae: getVal("cae-input"),
  };

  const submitBtn = document.querySelector(".submit-btn");
  submitBtn.disabled = true;
  submitBtn.textContent = "Solving...";

  try {
    const res = await fetch("/api/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();

    if (!res.ok) {
      renderError(data.error || "Something went wrong.");
    } else {
      renderResults(data);
    }
  } catch (err) {
    renderError("Could not reach the server: " + err.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Run Solver";
  }
});
