
/**
 * SynapRx Client Application Logic
 * Displays abbreviations with their context-selected meanings
 * and simple explanations. Clinical status is hidden.
 */

const API_BASE = "";
let currentInputMode = "upload";
let selectedFile = null;
let sampleData = [];
let isAdvancedOpen = false;

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, character => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  })[character]);
}

// Initialize
document.addEventListener("DOMContentLoaded", () => {
  lucide.createIcons();
  setupDragAndDrop();
  setupTextSync();
  loadInitialSamples();
});

// Advanced mode
function toggleAdvancedMode() {
  isAdvancedOpen = !isAdvancedOpen;

  const advSection = document.getElementById("advancedSection");
  const label = document.getElementById("advModeLabel");

  if (advSection) {
    if (isAdvancedOpen) {
      advSection.classList.remove("hidden");
      label.textContent = "Hide Clinical / CASI View";
    } else {
      advSection.classList.add("hidden");
      label.textContent = "Show Clinical / CASI View";
    }
  }
}

// Input mode
function setInputMode(mode) {
  currentInputMode = mode;

  const btnUpload = document.getElementById("btnModeUpload");
  const btnText = document.getElementById("btnModeText");
  const containerUpload = document.getElementById("modeUploadContainer");
  const containerText = document.getElementById("modeTextContainer");

  if (mode === "upload") {
    btnUpload.className =
      "flex-1 py-1.5 px-3 rounded-md bg-white text-slate-900 shadow-xs flex items-center justify-center gap-1.5 transition-all";

    btnText.className =
      "flex-1 py-1.5 px-3 rounded-md hover:text-slate-900 flex items-center justify-center gap-1.5 transition-all text-slate-600";

    containerUpload.classList.remove("hidden");
    containerText.classList.add("hidden");
  } else {
    btnText.className =
      "flex-1 py-1.5 px-3 rounded-md bg-white text-slate-900 shadow-xs flex items-center justify-center gap-1.5 transition-all";

    btnUpload.className =
      "flex-1 py-1.5 px-3 rounded-md hover:text-slate-900 flex items-center justify-center gap-1.5 transition-all text-slate-600";

    containerText.classList.remove("hidden");
    containerUpload.classList.add("hidden");
  }
}

// Text synchronization
function setupTextSync() {
  const manual = document.getElementById("manualText");
  const activeEditor = document.getElementById("activeTextEditor");

  if (manual) {
    manual.addEventListener("input", () => {
      activeEditor.value = manual.value;
      updateCharCount();
    });
  }

  if (activeEditor) {
    activeEditor.addEventListener("input", () => {
      if (manual) manual.value = activeEditor.value;
      updateCharCount();
    });
  }
}

function updateCharCount() {
  const activeEditor = document.getElementById("activeTextEditor");
  const charLabel = document.getElementById("charCountLabel");

  if (activeEditor && charLabel) {
    const len = activeEditor.value.length;
    charLabel.textContent =
      `${len} character${len === 1 ? "" : "s"}`;
  }
}

function clearInput() {
  const manual = document.getElementById("manualText");
  const activeEditor = document.getElementById("activeTextEditor");
  const previewCard = document.getElementById("previewCard");
  const resultsContainer = document.getElementById("resultsContainer");

  if (manual) manual.value = "";
  if (activeEditor) activeEditor.value = "";
  if (previewCard) previewCard.classList.add("hidden");
  if (resultsContainer) resultsContainer.classList.add("hidden");

  selectedFile = null;
  updateCharCount();
}

// Drag and drop
function setupDragAndDrop() {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");

  if (!dropzone || !fileInput) return;

  ["dragenter", "dragover"].forEach(name => {
    dropzone.addEventListener(name, e => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add("border-blue-500", "bg-blue-50/60");
    });
  });

  ["dragleave", "drop"].forEach(name => {
    dropzone.addEventListener(name, e => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove("border-blue-500", "bg-blue-50/60");
    });
  });

  dropzone.addEventListener("drop", e => {
    e.preventDefault();
    e.stopPropagation();

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleSelectedFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", e => {
    if (e.target.files && e.target.files.length > 0) {
      handleSelectedFile(e.target.files[0]);
      e.target.value = "";
    }
  });
}

function handleSelectedFile(file) {
  selectedFile = file;

  const previewCard = document.getElementById("previewCard");
  const previewImg = document.getElementById("imagePreview");
  const filename = document.getElementById("previewFilename");
  const filesize = document.getElementById("previewFilesize");

  filename.textContent = file.name;
  filesize.textContent = `${(file.size / 1024).toFixed(1)} KB`;

  if (file.type.startsWith("image/")) {
    const reader = new FileReader();

    reader.onload = e => {
      previewImg.src = e.target.result;
    };

    reader.readAsDataURL(file);
  } else {
    previewImg.src =
      "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 24 24' fill='none' stroke='%233b82f6' stroke-width='2'><path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/><polyline points='14 2 14 8 20 8'/></svg>";
  }

  previewCard.classList.remove("hidden");
  triggerOcr();
}

// OCR
async function triggerOcr() {
  if (!selectedFile) return;

  const ocrLoader = document.getElementById("ocrLoader");
  const btnRunOcr = document.getElementById("btnRunOcr");

  ocrLoader.classList.remove("hidden");

  if (btnRunOcr) {
    btnRunOcr.disabled = true;
    btnRunOcr.classList.add("opacity-50");
  }

  const formData = new FormData();
  formData.append("file", selectedFile);

  try {
    const response = await fetch(`${API_BASE}/api/ocr`, {
      method: "POST",
      body: formData
    });

    const res = await response.json();

    if (res.success && res.full_text) {
      document.getElementById("activeTextEditor").value = res.full_text;

      const manual = document.getElementById("manualText");
      if (manual) manual.value = res.full_text;

      updateCharCount();
      runInterpretation();
    } else {
      alert(
        `OCR Notice: ${res.error || "Could not read text from this image. You can type or paste the text directly."}`
      );
    }
  } catch (err) {
    console.error("OCR request failed:", err);
    alert("OCR extraction failed. You can paste or type the text directly.");
  } finally {
    ocrLoader.classList.add("hidden");

    if (btnRunOcr) {
      btnRunOcr.disabled = false;
      btnRunOcr.classList.remove("opacity-50");
    }
  }
}

// Load samples
async function loadInitialSamples() {
  try {
    const res = await fetch(`${API_BASE}/api/samples`);
    sampleData = await res.json();
  } catch (err) {
    console.warn("Could not load samples:", err);
  }
}

function loadSample(sampleId) {
  const sample = sampleData.find(s => s.id === sampleId);
  if (!sample) return;

  document.getElementById("activeTextEditor").value = sample.text;

  const manual = document.getElementById("manualText");
  if (manual) manual.value = sample.text;

  updateCharCount();

  const previewCard = document.getElementById("previewCard");
  const previewImg = document.getElementById("imagePreview");
  const filename = document.getElementById("previewFilename");
  const filesize = document.getElementById("previewFilesize");

  filename.textContent = `${sample.title}.png`;
  filesize.textContent = "Verified Prescription Image";
  previewImg.src = sample.image_url;
  previewCard.classList.remove("hidden");

  runInterpretation();
}

// Interpretation runner
async function runInterpretation() {
  const activeText =
    document.getElementById("activeTextEditor").value.trim();

  if (!activeText) {
    alert("Please upload a prescription image or enter text to explain.");
    return;
  }

  const loadingState =
    document.getElementById("resultsLoadingState");

  const resultsContainer =
    document.getElementById("resultsContainer");

  const btnInterpret =
    document.getElementById("btnInterpret");

  resultsContainer.classList.add("hidden");
  loadingState.classList.remove("hidden");
  btnInterpret.disabled = true;

  try {
    const response = await fetch(`${API_BASE}/api/interpret`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: activeText })
    });

    const data = await response.json();

    if (data.success) {
      renderCleanResults(data);
      resultsContainer.classList.remove("hidden");

      resultsContainer.scrollIntoView({
        behavior: "smooth",
        block: "start"
      });
    } else {
      alert(
        `Interpretation Error: ${data.error || "Unable to interpret text."}`
      );
    }
  } catch (err) {
    console.error("Interpretation failed:", err);
    alert("Connection to interpretation server failed.");
  } finally {
    loadingState.classList.add("hidden");
    btnInterpret.disabled = false;
    lucide.createIcons();
  }
}

// Render results
function renderCleanResults(data) {

  // 1. Specialty header
  const spec = data.specialty || { primary: "General Medicine" };

  document.getElementById("detectedSpecialtyBadge").textContent =
    spec.primary;

  const secBadge =
    document.getElementById("secondarySpecialtyBadge");

  if (spec.secondary) {
    secBadge.textContent = spec.secondary;
    secBadge.classList.remove("hidden");
  } else {
    secBadge.classList.add("hidden");
  }

  // 2. Diagnoses - show names only, no clinical status
  const diagContainer = document.getElementById("diagnosesList");
  diagContainer.innerHTML = "";

  if (data.diagnoses && data.diagnoses.length > 0) {
    data.diagnoses.forEach(d => {
      const pill = document.createElement("span");

      pill.className =
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-800 border border-blue-200";

      pill.textContent =
        `${d.full_name || ""} (${d.abbreviation || ""})`;

      diagContainer.appendChild(pill);
    });
  } else {
    diagContainer.innerHTML =
      `<span class="text-xs text-slate-700 italic">Clinical general follow-up.</span>`;
  }

  // 3. Abbreviation table
  // Only abbreviation, full form and simple explanation.
  const abbrTbody =
    document.getElementById("abbreviationsTableBody");

  const abbrCount =
    document.getElementById("abbreviationCountBadge");

  abbrTbody.innerHTML = "";

  const abbreviations = data.abbreviations || [];

  if (abbreviations.length > 0) {
    abbrCount.textContent = `${abbreviations.length} identified`;

    abbreviations.forEach(abbr => {
      const tr = document.createElement("tr");
      tr.className = "hover:bg-slate-50 transition-colors";

      const token = abbr.token || abbr.abbreviation || "";
      const meaning =
        abbr.meaning || abbr.full_form || "Meaning unavailable";

      const explanation =
        abbr.plain_english || abbr.description || "";
      const contextSnippet = abbr.context_snippet || "";
      const whySelected = abbr.why_selected || "";
      const occIdx = abbr.occurrence_index;
      const totalOcc = abbr.total_occurrences;
      const occLabel = (totalOcc && totalOcc > 1)
        ? `<div class="mt-1"><span class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">Occurrence ${occIdx || 1} of ${totalOcc}</span></div>`
        : "";

      let detailsHtml = `<div class="font-bold text-slate-900 text-xs">${escapeHtml(meaning)}</div>`;
      if (explanation) {
        detailsHtml += `<div class="text-[11px] text-slate-700 mt-0.5">${escapeHtml(explanation)}</div>`;
      }
      if (contextSnippet) {
        detailsHtml += `<div class="text-[11px] text-slate-600 bg-slate-50 rounded p-1.5 mt-1 border border-slate-100 font-mono"><span class="font-sans font-semibold text-slate-700">Context:</span> "${escapeHtml(contextSnippet)}"</div>`;
      }
      if (whySelected) {
        detailsHtml += `<div class="text-[11px] text-slate-500 mt-0.5"><span class="font-semibold text-slate-600">Why:</span> ${escapeHtml(whySelected)}</div>`;
      }
      if (abbr.clarification_required) {
        detailsHtml += `<div class="mt-1"><span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-amber-50 text-amber-800 border border-amber-200">⚠️ Needs Clinical Clarification (Ambiguous in context)</span></div>`;
      }

      tr.innerHTML = `
        <td class="py-2.5 px-3 align-top">
          <span class="px-2 py-0.5 rounded-md font-mono font-bold text-xs bg-slate-900 text-white">
            ${escapeHtml(token)}
          </span>
          ${occLabel}
        </td>

        <td class="py-2.5 px-3 align-top">
          ${detailsHtml}
        </td>
      `;

      abbrTbody.appendChild(tr);
    });
  } else {
    abbrCount.textContent = "0 abbreviations";

    abbrTbody.innerHTML = `
      <tr>
        <td colspan="2" class="py-4 text-center text-xs text-slate-700">
          No medical abbreviations detected in text.
        </td>
      </tr>
    `;
  }

  // 4. Prescription details
  const medicationCard =
    document.getElementById("prescriptionDetailsCard");

  const medicationCount =
    document.getElementById("prescriptionCountBadge");

  const medicationTbody =
    document.getElementById("prescriptionDetailsTableBody");

  medicationTbody.innerHTML = "";

  const medications = data.medications || [];

  if (medications.length > 0) {
    medicationCard.classList.remove("hidden");

    medicationCount.textContent =
      `${medications.length} medicine${medications.length === 1 ? "" : "s"}`;

    medications.forEach(medication => {
      const tr = document.createElement("tr");

      const frequency =
        medication.frequency_code &&
          medication.frequency_code !== "Unspecified"
          ? `${medication.frequency_code} (${medication.frequency_english})`
          : "Not specified in text";

      const route =
        medication.route_code &&
          medication.route_code !== "Unspecified"
          ? `${medication.route_code} (${medication.route_english})`
          : "Not specified in text";

      const foodTiming =
        medication.food_timing_code &&
          medication.food_timing_code !== "Unspecified"
          ? `${medication.food_timing_instruction} [${medication.food_timing_code}]`
          : "Not specified in text";

      const additionalInstructions =
        (medication.additional_instructions || []).length > 0
          ? medication.additional_instructions.join("; ")
          : "None stated";

      tr.innerHTML = `
        <td class="py-2.5 px-3 font-semibold text-slate-900">
          ${escapeHtml(medication.drug_name)}
        </td>

        <td class="py-2.5 px-3">
          ${escapeHtml(medication.dosage_strength)}
        </td>

        <td class="py-2.5 px-3">${escapeHtml(route)}</td>

        <td class="py-2.5 px-3">${escapeHtml(frequency)}</td>

        <td class="py-2.5 px-3">${escapeHtml(foodTiming)}</td>

        <td class="py-2.5 px-3">
          ${escapeHtml(additionalInstructions)}
        </td>
      `;

      medicationTbody.appendChild(tr);
    });
  } else {
    medicationCard.classList.add("hidden");
  }

  // 5. Plain-English summary
  const summaryBox =
    document.getElementById("patientSummaryContent");

  summaryBox.innerHTML = "";

  if (data.patient_summary && data.patient_summary.length > 0) {
    data.patient_summary.forEach(pt => {
      const p = document.createElement("p");

      p.className = "text-xs text-slate-700 leading-relaxed";

      // Safely display summary text
      p.textContent = pt.replace(/\*\*(.*?)\*\*/g, "$1");

      summaryBox.appendChild(p);
    });
  }

  // 6. Safety warnings
  const safetyCard =
    document.getElementById("safetyAlertsCard");

  const safetyList =
    document.getElementById("safetyAlertsList");

  safetyList.innerHTML = "";

  if (data.safety_alerts && data.safety_alerts.length > 0) {
    data.safety_alerts.forEach(a => {
      const li = document.createElement("li");

      const strong = document.createElement("strong");
      strong.textContent = `${a.flagged_token}: `;

      li.appendChild(strong);
      li.appendChild(
        document.createTextNode(
          `${a.risk} (${a.recommendation})`
        )
      );

      safetyList.appendChild(li);
    });

    safetyCard.classList.remove("hidden");
  } else {
    safetyCard.classList.add("hidden");
  }

  lucide.createIcons();
}
