/**
 * SynapRx Evaluation Dashboard
 * Interactive metrics, confusion matrices, error categorization, and benchmark verification
 */

let currentSplit = "heldout";
let latestData = null;

const COMPONENT_NAMES = [
  "abbreviation_recognition",
  "full_form_identification",
  "contextual_disambiguation",
  "clinical_status",
  "negation_detection",
  "prescription_extraction",
  "medicine_dose_association",
  "route_frequency_extraction",
  "food_timing_extraction",
  "ocr_accuracy",
  "specialty_detection"
];

const COMPONENT_DISPLAY_NAMES = {
  abbreviation_recognition: "Abbreviation Recognition",
  full_form_identification: "Full-Form Identification",
  contextual_disambiguation: "Contextual Disambiguation",
  clinical_status: "Clinical Status Classification",
  negation_detection: "Negation Detection",
  prescription_extraction: "Prescription Extraction",
  medicine_dose_association: "Medicine-Dose Association",
  route_frequency_extraction: "Route & Frequency",
  food_timing_extraction: "Food Timing Extraction",
  ocr_accuracy: "OCR Character Accuracy",
  specialty_detection: "Specialty Detection"
};

/**
 * Format component key to human-readable title.
 */
function formatComponentName(key) {
  if (!key) return "N/A";
  return COMPONENT_DISPLAY_NAMES[key] || key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

/**
 * Escape HTML characters for safe rendering.
 */
function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/**
 * Format string or JSON object for display in detail panels.
 */
function stringifyValue(val) {
  if (val === null || val === undefined) return '<span class="italic text-slate-400">None</span>';
  if (typeof val === "object") {
    return `<pre class="font-mono text-[10px] bg-slate-50 p-2 rounded border border-slate-200 overflow-x-auto whitespace-pre-wrap">${escapeHtml(JSON.stringify(val, null, 2))}</pre>`;
  }
  return `<span class="font-mono font-semibold">${escapeHtml(String(val))}</span>`;
}

/**
 * Update UI state for split toggle.
 */
function setSplitUI(split) {
  currentSplit = split;
  const heldoutBtn = document.getElementById("splitHeldoutBtn");
  const devBtn = document.getElementById("splitDevBtn");
  const splitSelector = document.getElementById("splitSelector");
  if (splitSelector) splitSelector.value = split;

  if (split === "heldout") {
    heldoutBtn?.classList.add("bg-white", "text-slate-900", "shadow-xs");
    heldoutBtn?.classList.remove("text-slate-600");
    devBtn?.classList.remove("bg-white", "text-slate-900", "shadow-xs");
    devBtn?.classList.add("text-slate-600");
  } else {
    devBtn?.classList.add("bg-white", "text-slate-900", "shadow-xs");
    devBtn?.classList.remove("text-slate-600");
    heldoutBtn?.classList.remove("bg-white", "text-slate-900", "shadow-xs");
    heldoutBtn?.classList.add("text-slate-600");
  }
}

/**
 * Change split and re-run evaluation.
 */
function setSplit(split) {
  setSplitUI(split);
  runEvaluation(split);
}

/**
 * 1. runEvaluation(split)
 * Fetch evaluation results for the specified split and trigger dashboard render.
 */
async function runEvaluation(split) {
  if (split && (split === "heldout" || split === "development")) {
    setSplitUI(split);
  } else {
    const splitSelector = document.getElementById("splitSelector");
    if (splitSelector && splitSelector.value) {
      setSplitUI(splitSelector.value);
    }
  }

  const spinner = document.getElementById("loadingSpinner");
  const runBtn = document.getElementById("runEvaluationButton");
  const errorBox = document.getElementById("evaluationError");
  const errorMsg = document.getElementById("errorMessage");

  if (spinner) spinner.classList.remove("hidden");
  if (runBtn) runBtn.disabled = true;
  if (errorBox) errorBox.classList.add("hidden");

  try {
    const response = await fetch(`/api/evaluation?split=${encodeURIComponent(currentSplit)}`);
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.error || `HTTP error ${response.status}: ${response.statusText}`);
    }
    const data = await response.json();
    renderDashboard(data);
  } catch (err) {
    console.error("Evaluation error:", err);
    if (errorBox && errorMsg) {
      errorMsg.textContent = `Unable to load evaluation: ${err.message}`;
      errorBox.classList.remove("hidden");
    }
  } finally {
    if (spinner) spinner.classList.add("hidden");
    if (runBtn) runBtn.disabled = false;
    if (window.lucide) window.lucide.createIcons();
  }
}

/**
 * 2. renderDashboard(data)
 * Orchestrate rendering of all evaluation sections.
 */
function renderDashboard(data) {
  if (!data) return;
  latestData = data;

  // A. Render Summary Card
  const summary = data.summary || data.overall_summary || {};
  renderSummaryCard(summary);

  // B. Render 11 Component Cards into #componentGrid
  const componentGrid = document.getElementById("componentGrid");
  if (componentGrid) {
    componentGrid.innerHTML = "";
    COMPONENT_NAMES.forEach(key => {
      const metrics = (data.metrics && data.metrics[key]) || data[key] || { status: "not_evaluated" };
      const card = renderComponentCard(key, metrics);
      if (card instanceof HTMLElement) {
        componentGrid.appendChild(card);
      } else if (typeof card === "string") {
        const temp = document.createElement("div");
        temp.innerHTML = card;
        componentGrid.appendChild(temp.firstElementChild);
      }
    });
  }

  // C. Render Failed Examples into #failedExamples
  const failedExamples = data.failed_examples || [];
  renderFailedExamples(failedExamples);

  // D. Render Confusion Matrices into #confusionMatrices
  const confusionMatricesContainer = document.getElementById("confusionMatrices");
  if (confusionMatricesContainer) {
    confusionMatricesContainer.innerHTML = "";
    const matrixSpecs = [
      { key: "contextual_disambiguation", title: "Contextual Disambiguation Confusion Matrix" },
      { key: "clinical_status", title: "Clinical Status Classification Confusion Matrix" },
      { key: "food_timing_extraction", title: "Food Timing Extraction Confusion Matrix" }
    ];

    let renderedCount = 0;
    matrixSpecs.forEach(({ key, title }) => {
      const metric = (data.metrics && data.metrics[key]) || data[key];
      if (metric && metric.confusion_matrix) {
        const subId = `cm_${key}`;
        const wrapper = document.createElement("div");
        wrapper.className = "bg-slate-50 border border-slate-200 rounded-xl p-4";
        wrapper.innerHTML = `
          <div class="mb-3 flex items-center justify-between">
            <div>
              <h3 class="text-sm font-bold text-slate-800">${title}</h3>
              <p class="text-[11px] text-slate-500 mt-0.5">Vertical rows: Ground Truth (Expected) · Horizontal columns: Predicted</p>
            </div>
            <span class="text-[10px] font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">${formatComponentName(key)}</span>
          </div>
          <div id="${subId}" class="overflow-x-auto"></div>
        `;
        confusionMatricesContainer.appendChild(wrapper);
        renderConfusionMatrix(metric.confusion_matrix, subId);
        renderedCount++;
      }
    });

    if (renderedCount === 0) {
      confusionMatricesContainer.innerHTML = `
        <div class="py-6 text-center text-slate-400 text-xs italic">
          No confusion matrices available for this dataset split.
        </div>
      `;
    }
  }

  // E. Render Error Categories into #errorCategories
  const errorCategories = data.common_error_categories || (data.summary && data.summary.common_error_categories) || [];
  renderErrorCategories(errorCategories);

  if (window.lucide) window.lucide.createIcons();
}

/**
 * 3. renderSummaryCard(summary)
 * Render summary card with total examples, average accuracy, strongest/weakest, and counts.
 */
function renderSummaryCard(summary) {
  const container = document.getElementById("summaryCard");
  if (!container) return;

  const totalExamples = summary.total_examples ||
    (latestData && latestData.dataset && latestData.dataset.total_cases_in_split) ||
    ((summary.total_correct || 0) + (summary.total_incorrect || 0));

  const rawAccuracy = summary.average_accuracy != null ? summary.average_accuracy : 0;
  const accuracyPct = rawAccuracy > 1 ? rawAccuracy : rawAccuracy * 100;
  const accuracyFormatted = accuracyPct.toFixed(1) + "%";

  let accuracyColorClass = "text-emerald-600 bg-emerald-50 border-emerald-200";
  if (accuracyPct < 70) {
    accuracyColorClass = "text-rose-600 bg-rose-50 border-rose-200";
  } else if (accuracyPct <= 90) {
    accuracyColorClass = "text-amber-600 bg-amber-50 border-amber-200";
  }

  const strongestName = formatComponentName(summary.strongest_component);
  const weakestName = formatComponentName(summary.weakest_component);
  const totalCorrect = summary.total_correct != null ? summary.total_correct.toLocaleString() : "0";
  const totalIncorrect = summary.total_incorrect != null ? summary.total_incorrect.toLocaleString() : "0";

  container.innerHTML = `
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 items-center">
      <!-- Average Accuracy & Total Examples -->
      <div class="flex items-center gap-4 border-b md:border-b-0 md:border-r border-slate-100 pb-4 md:pb-0 md:pr-4">
        <div class="px-4 py-3 rounded-2xl border ${accuracyColorClass} text-center flex-shrink-0 shadow-xs">
          <div class="text-3xl font-extrabold tracking-tight">${accuracyFormatted}</div>
          <div class="text-[10px] font-bold uppercase tracking-wider mt-0.5">Average Accuracy</div>
        </div>
        <div>
          <div class="text-xs text-slate-500 font-medium">Evaluation Corpus</div>
          <div class="text-xl font-extrabold text-slate-900 mt-0.5">${totalExamples.toLocaleString()} <span class="text-xs font-semibold text-slate-500">examples</span></div>
          <div class="text-[11px] text-slate-400 mt-0.5">Independent Ground Truth</div>
        </div>
      </div>

      <!-- Strongest / Weakest Components -->
      <div class="space-y-2.5 border-b md:border-b-0 lg:border-r border-slate-100 pb-4 md:pb-0 lg:pr-4">
        <div>
          <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Strongest Component</span>
          <div class="flex items-center gap-1.5 mt-0.5">
            <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span class="text-xs font-bold text-slate-800">${strongestName}</span>
          </div>
        </div>
        <div>
          <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Weakest Component</span>
          <div class="flex items-center gap-1.5 mt-0.5">
            <span class="w-2 h-2 rounded-full bg-amber-500"></span>
            <span class="text-xs font-bold text-slate-800">${weakestName}</span>
          </div>
        </div>
      </div>

      <!-- Total Correct & Incorrect Counts -->
      <div class="space-y-2 border-b md:border-b-0 md:border-r border-slate-100 pb-4 md:pb-0 md:pr-4">
        <div class="flex items-center justify-between">
          <span class="text-xs text-slate-600 font-medium flex items-center gap-1.5">
            <i data-lucide="check-circle-2" class="w-3.5 h-3.5 text-emerald-600"></i>
            <span>Total Correct:</span>
          </span>
          <span class="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">${totalCorrect}</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-xs text-slate-600 font-medium flex items-center gap-1.5">
            <i data-lucide="alert-octagon" class="w-3.5 h-3.5 text-rose-600"></i>
            <span>Total Incorrect:</span>
          </span>
          <span class="text-xs font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-md border border-rose-200">${totalIncorrect}</span>
        </div>
      </div>

      <!-- Split Details & Status -->
      <div class="bg-slate-50 rounded-xl p-3 border border-slate-100 text-xs space-y-1.5">
        <div class="flex justify-between items-center text-[11px]">
          <span class="text-slate-500 font-medium">Active Split:</span>
          <span class="font-bold text-slate-800 capitalize">${currentSplit}</span>
        </div>
        <div class="flex justify-between items-center text-[11px]">
          <span class="text-slate-500 font-medium">Components:</span>
          <span class="font-bold text-slate-800">11 Evaluated Cards</span>
        </div>
        <div class="flex justify-between items-center text-[11px]">
          <span class="text-slate-500 font-medium">Evaluation Mode:</span>
          <span class="font-semibold text-blue-600">Deterministic Strict Match</span>
        </div>
      </div>
    </div>
  `;
}

/**
 * 4. renderComponentCard(name, metrics)
 * Build and return a card element for an individual component.
 */
function renderComponentCard(name, metrics) {
  const card = document.createElement("div");
  card.className = "bg-white rounded-2xl border border-slate-200 shadow-sm p-4 hover:shadow-md transition-shadow flex flex-col justify-between";

  const displayName = formatComponentName(name);
  const isNotEvaluated = !metrics || metrics.status === "not_evaluated";

  let accuracyBadge = "";
  if (isNotEvaluated) {
    accuracyBadge = `<span class="px-2.5 py-1 text-xs font-semibold rounded-full bg-slate-100 text-slate-500 border border-slate-200">not_evaluated</span>`;
  } else {
    const rawAcc = metrics.accuracy != null ? metrics.accuracy : 0;
    const accPct = rawAcc > 1 ? rawAcc : rawAcc * 100;
    const accStr = accPct.toFixed(1) + "%";

    let colorClass = "text-emerald-700 bg-emerald-50 border-emerald-200";
    if (accPct < 70) {
      colorClass = "text-rose-700 bg-rose-50 border-rose-200";
    } else if (accPct <= 90) {
      colorClass = "text-amber-700 bg-amber-50 border-amber-200";
    }
    accuracyBadge = `<span class="px-2.5 py-1 text-xs font-extrabold rounded-lg border ${colorClass}">${accStr}</span>`;
  }

  const fmtPercent = val => {
    if (val == null) return "N/A";
    const num = val > 1 ? val : val * 100;
    return num.toFixed(1) + "%";
  };

  const precision = isNotEvaluated ? "—" : fmtPercent(metrics.precision);
  const recall = isNotEvaluated ? "—" : fmtPercent(metrics.recall);
  const f1 = isNotEvaluated ? "—" : fmtPercent(metrics.f1_score ?? metrics.f1);

  const tp = isNotEvaluated ? "—" : (metrics.true_positives ?? metrics.tp ?? 0);
  const fp = isNotEvaluated ? "—" : (metrics.false_positives ?? metrics.fp ?? 0);
  const fn = isNotEvaluated ? "—" : (metrics.false_negatives ?? metrics.fn ?? 0);
  const total = isNotEvaluated ? 0 : (metrics.total_evaluated ?? metrics.evaluated_examples ?? 0);

  card.innerHTML = `
    <div>
      <div class="flex items-start justify-between gap-2 mb-3">
        <h3 class="text-xs font-bold text-slate-900 tracking-tight leading-snug">${displayName}</h3>
        ${accuracyBadge}
      </div>

      <!-- Precision, Recall, F1 -->
      <div class="grid grid-cols-3 gap-1 py-2 px-2 bg-slate-50 rounded-xl border border-slate-100 text-center mb-3">
        <div>
          <span class="text-[9px] uppercase font-bold text-slate-400 block">Precision</span>
          <span class="text-xs font-bold text-slate-800">${precision}</span>
        </div>
        <div class="border-x border-slate-200">
          <span class="text-[9px] uppercase font-bold text-slate-400 block">Recall</span>
          <span class="text-xs font-bold text-slate-800">${recall}</span>
        </div>
        <div>
          <span class="text-[9px] uppercase font-bold text-slate-400 block">F1</span>
          <span class="text-xs font-bold text-slate-800">${f1}</span>
        </div>
      </div>
    </div>

    <!-- TP / FP / FN & Total Evaluated -->
    <div class="space-y-1.5 pt-2 border-t border-slate-100 text-[11px]">
      <div class="flex justify-between items-center text-slate-600">
        <span>TP / FP / FN:</span>
        <span class="font-mono font-semibold text-slate-800">${tp} / ${fp} / ${fn}</span>
      </div>
      <div class="flex justify-between items-center text-slate-600">
        <span>Total Evaluated:</span>
        <span class="font-bold text-slate-900">${total}</span>
      </div>
    </div>
  `;

  return card;
}

/**
 * 5. renderFailedExamples(examples)
 * Render collapsible failed examples with ID, input text (truncated 80 chars), expected, actual, error type.
 */
function renderFailedExamples(examples) {
  const container = document.getElementById("failedExamples");
  const countBadge = document.getElementById("failedCountBadge");
  if (!container) return;

  const totalCount = examples ? examples.length : 0;
  if (countBadge) {
    countBadge.textContent = `${totalCount} Item${totalCount === 1 ? '' : 's'}`;
  }

  container.innerHTML = "";
  if (!examples || examples.length === 0) {
    container.innerHTML = `
      <div class="py-8 text-center text-slate-500">
        <i data-lucide="check-circle-2" class="w-8 h-8 text-emerald-500 mx-auto mb-2"></i>
        <p class="text-xs font-semibold">Zero discrepancies found!</p>
        <p class="text-[11px] text-slate-400 mt-0.5">All evaluated test cases matched the ground truth expectations.</p>
      </div>
    `;
    return;
  }

  examples.forEach(ex => {
    const id = ex.id || ex.case_id || "N/A";
    const inputText = ex.input_text || "";
    const truncatedText = inputText.length > 80 ? inputText.slice(0, 80) + "…" : inputText;
    const errorType = ex.error_type || ex.component || "discrepancy";

    const item = document.createElement("details");
    item.className = "group bg-slate-50 border border-slate-200 rounded-xl overflow-hidden text-xs transition-all";

    item.innerHTML = `
      <summary class="flex items-center justify-between p-3 cursor-pointer hover:bg-slate-100/80 transition-colors list-none select-none">
        <div class="flex items-center gap-2 overflow-hidden mr-2">
          <i data-lucide="chevron-right" class="w-3.5 h-3.5 text-slate-400 group-open:rotate-90 transition-transform flex-shrink-0"></i>
          <span class="font-mono font-bold text-slate-800 flex-shrink-0 text-[11px]">${escapeHtml(id)}</span>
          <span class="px-2 py-0.5 rounded-full bg-rose-100 text-rose-700 text-[10px] font-semibold flex-shrink-0">${escapeHtml(errorType)}</span>
          <span class="text-slate-600 truncate text-[11px]">${escapeHtml(truncatedText)}</span>
        </div>
        <span class="text-[10px] text-blue-600 font-semibold group-open:hidden flex-shrink-0">Details</span>
      </summary>
      <div class="p-3.5 bg-white border-t border-slate-200 space-y-2.5">
        <div>
          <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-0.5">Input Text</span>
          <div class="p-2 bg-slate-50 rounded-lg text-slate-800 font-mono text-[11px] border border-slate-100 whitespace-pre-wrap">${escapeHtml(inputText)}</div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
          <div>
            <span class="text-[10px] font-bold uppercase tracking-wider text-emerald-700 block mb-0.5">Expected Benchmark</span>
            <div class="p-2 bg-emerald-50/70 border border-emerald-200 rounded-lg text-emerald-900">${stringifyValue(ex.expected)}</div>
          </div>
          <div>
            <span class="text-[10px] font-bold uppercase tracking-wider text-rose-700 block mb-0.5">Actual Prediction</span>
            <div class="p-2 bg-rose-50/70 border border-rose-200 rounded-lg text-rose-900">${stringifyValue(ex.actual)}</div>
          </div>
        </div>
      </div>
    `;
    container.appendChild(item);
  });
}

/**
 * 6. renderConfusionMatrix(matrix, containerId)
 * Render an HTML table with colored cells representing a confusion matrix.
 */
function renderConfusionMatrix(matrix, containerId) {
  const container = typeof containerId === "string" ? document.getElementById(containerId) : containerId;
  if (!container || !matrix) return;

  let labels = [];
  let grid = [];

  if (Array.isArray(matrix.labels) && Array.isArray(matrix.matrix)) {
    labels = matrix.labels;
    grid = matrix.matrix;
  } else if (typeof matrix === "object") {
    // Nested dictionary format: { rowLabel: { colLabel: count } }
    const labelSet = new Set();
    Object.keys(matrix).forEach(k => {
      labelSet.add(k);
      if (typeof matrix[k] === "object" && matrix[k] !== null) {
        Object.keys(matrix[k]).forEach(subK => labelSet.add(subK));
      }
    });
    labels = Array.from(labelSet).sort();
    grid = labels.map(rLabel => {
      return labels.map(cLabel => {
        return (matrix[rLabel] && matrix[rLabel][cLabel]) || 0;
      });
    });
  }

  if (labels.length === 0) {
    container.innerHTML = `<p class="text-xs text-slate-400 italic">No matrix data available</p>`;
    return;
  }

  const table = document.createElement("table");
  table.className = "w-full text-xs border-collapse border border-slate-200 rounded-lg overflow-hidden";

  let thead = `
    <thead class="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
      <tr>
        <th class="p-2 text-left font-bold text-[10px] uppercase tracking-wider text-slate-500 border-r border-slate-200 bg-slate-100/90 whitespace-nowrap">Expected \\ Predicted</th>
        ${labels.map(l => `<th class="p-2 text-center text-[10px] font-semibold border-r border-slate-200 last:border-r-0 max-w-[120px] truncate" title="${escapeHtml(l)}">${escapeHtml(l)}</th>`).join("")}
      </tr>
    </thead>
  `;

  let tbody = `<tbody class="divide-y divide-slate-100 bg-white">`;
  labels.forEach((rLabel, rIdx) => {
    tbody += `<tr>`;
    tbody += `<th class="p-2 text-left font-bold text-[11px] text-slate-700 bg-slate-50 border-r border-slate-200 whitespace-nowrap" title="${escapeHtml(rLabel)}">${escapeHtml(rLabel)}</th>`;

    labels.forEach((cLabel, cIdx) => {
      const val = (grid[rIdx] && grid[rIdx][cIdx]) || 0;
      const isDiagonal = (rIdx === cIdx);
      let cellClass = "text-slate-300 bg-slate-50/20";

      if (isDiagonal) {
        if (val > 0) {
          cellClass = "font-bold text-emerald-800 bg-emerald-100/80 border border-emerald-300";
        }
      } else {
        if (val > 0) {
          cellClass = "font-bold text-rose-800 bg-rose-100/80 border border-rose-300";
        }
      }

      tbody += `
        <td class="p-2 text-center border-r border-slate-200 last:border-r-0 ${cellClass}" title="Expected: ${escapeHtml(rLabel)} | Predicted: ${escapeHtml(cLabel)} (${val})">
          ${val}
        </td>
      `;
    });
    tbody += `</tr>`;
  });
  tbody += `</tbody>`;

  table.innerHTML = thead + tbody;
  container.innerHTML = "";
  container.appendChild(table);
}

/**
 * 7. renderErrorCategories(errors)
 * Render a simple CSS bar chart for common error categories.
 */
function renderErrorCategories(errors) {
  const container = document.getElementById("errorCategories");
  if (!container) return;

  container.innerHTML = "";
  if (!errors || errors.length === 0) {
    container.innerHTML = `<p class="text-xs text-slate-400 italic">No common errors recorded.</p>`;
    return;
  }

  const maxCount = Math.max(...errors.map(e => e.count || 0), 1);
  const totalErrors = errors.reduce((acc, cur) => acc + (cur.count || 0), 0);

  errors.forEach(err => {
    const rawType = err.error_type || err.component || "Unknown Error";
    const name = rawType.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
    const count = err.count || 0;
    const barPct = Math.max(Math.round((count / maxCount) * 100), 3);
    const totalPct = totalErrors > 0 ? ((count / totalErrors) * 100).toFixed(1) + "%" : "";

    const row = document.createElement("div");
    row.className = "space-y-1";
    row.innerHTML = `
      <div class="flex items-center justify-between text-xs">
        <span class="font-semibold text-slate-800">${escapeHtml(name)}</span>
        <div class="flex items-center gap-1.5">
          <span class="text-[10px] text-slate-400 font-medium">${totalPct}</span>
          <span class="px-2 py-0.5 rounded-md bg-slate-100 font-bold text-slate-700 text-[11px] border border-slate-200">${count}</span>
        </div>
      </div>
      <div class="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
        <div class="bg-blue-600 h-2.5 rounded-full transition-all duration-500 ease-out" style="width: ${barPct}%"></div>
      </div>
    `;
    container.appendChild(row);
  });
}

/**
 * 8. exportResults(format)
 * Export evaluation results in JSON or CSV format.
 */
function exportResults(format) {
  const fmt = (format || "json").toLowerCase();
  const url = `/api/evaluation/export?split=${encodeURIComponent(currentSplit)}&format=${encodeURIComponent(fmt)}`;
  const a = document.createElement("a");
  a.href = url;
  a.download = `synaprx-evaluation-${currentSplit}.${fmt}`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

// Attach all required functions to window object
window.runEvaluation = runEvaluation;
window.renderDashboard = renderDashboard;
window.renderSummaryCard = renderSummaryCard;
window.renderComponentCard = renderComponentCard;
window.renderFailedExamples = renderFailedExamples;
window.renderConfusionMatrix = renderConfusionMatrix;
window.renderErrorCategories = renderErrorCategories;
window.exportResults = exportResults;
window.setSplit = setSplit;

// Auto-run evaluation on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) window.lucide.createIcons();
  runEvaluation("heldout");
});
