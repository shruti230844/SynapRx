"""SynapRx Evaluation Engine.

Evaluates the SynapRx prescription and clinical note parser against independent
ground truth across 11 key clinical and technical components:
  1. abbreviation_recognition - Token detection (TP/FP/FN)
  2. full_form_identification - Meaning matches expected full_form
  3. contextual_disambiguation - Disambiguation examples with confusion matrix
  4. clinical_status - Matching clinical status strings with confusion matrix
  5. negation_detection - Precision/Recall/F1 for clinical negation
  6. prescription_extraction - Exact match of drug_name, dosage_strength, form
  7. medicine_dose_association - Correct drug-dose pairs
  8. route_frequency_extraction - frequency_code and route_code accuracy
  9. food_timing_extraction - food_timing_code accuracy with confusion matrix
  10. ocr_accuracy - Levenshtein CER and WER (pure Python)
  11. specialty_detection - Primary specialty match
"""

import csv
import io
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GROUND_TRUTH_PATH = ROOT / "data" / "evaluation" / "ground_truth.json"

COMPONENT_NAMES = [
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
    "specialty_detection",
]


# ---------------------------------------------------------------------------
# Required Helper Functions
# ---------------------------------------------------------------------------

def _levenshtein_distance(s1, s2):
    """Compute character or token Levenshtein edit distance between s1 and s2.
    
    Supports both strings (for CER) and sequences of words/tokens (for WER).
    Implemented in pure Python without external dependencies.
    """
    if len(s1) < len(s2):
        s1, s2 = s2, s1
    if len(s2) == 0:
        return len(s1)
    previous = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1, 1):
        current = [i]
        for j, c2 in enumerate(s2, 1):
            cost = 0 if c1 == c2 else 1
            current.append(min(
                current[-1] + 1,        # Insertion
                previous[j] + 1,        # Deletion
                previous[j - 1] + cost  # Substitution
            ))
        previous = current
    return previous[-1]


def _safe_divide(num, den):
    """Safely divide num by den, returning 0.0 if den is zero or falsy."""
    if not den:
        return 0.0
    return round(float(num) / float(den), 4)


def _compute_metrics(tp, fp, fn, total=None):
    """Compute accuracy, precision, recall, and f1_score from TP, FP, FN.
    
    Returns a dict with: accuracy, precision, recall, f1_score.
    """
    precision = _safe_divide(tp, tp + fp)
    recall = _safe_divide(tp, tp + fn)
    f1_score = _safe_divide(2 * precision * recall, precision + recall)
    if total is not None and total > 0:
        accuracy = _safe_divide(tp, total)
    else:
        accuracy = _safe_divide(tp, tp + fp + fn)
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
    }


def _build_confusion_matrix(predictions, ground_truths):
    """Build confusion matrix dictionary: {"labels": [...], "matrix": [[...]]}.
    
    Rows correspond to ground truth labels; columns correspond to predicted labels.
    """
    labels_set = set()
    for gt in ground_truths:
        labels_set.add(str(gt) if gt is not None else "(Missing)")
    for pred in predictions:
        labels_set.add(str(pred) if pred is not None else "(Missing)")

    labels = sorted(list(labels_set))
    label_to_idx = {label: i for i, label in enumerate(labels)}
    matrix = [[0 for _ in range(len(labels))] for _ in range(len(labels))]

    for gt, pred in zip(ground_truths, predictions):
        gt_str = str(gt) if gt is not None else "(Missing)"
        pred_str = str(pred) if pred is not None else "(Missing)"
        row = label_to_idx[gt_str]
        col = label_to_idx[pred_str]
        matrix[row][col] += 1

    return {"labels": labels, "matrix": matrix}


def _normalize(s):
    """Lowercase stripped string with collapsed whitespace for comparison."""
    if s is None:
        return ""
    return re.sub(r"\s+", " ", str(s)).strip().casefold()


def _fuzzy_match(predicted, expected):
    """Case-insensitive containment check both ways."""
    if predicted is None or expected is None:
        return False
    norm_p = _normalize(predicted)
    norm_e = _normalize(expected)
    if not norm_p or not norm_e:
        return False
    return norm_p == norm_e or norm_p in norm_e or norm_e in norm_p


# ---------------------------------------------------------------------------
# Backward-compatibility Helper (for legacy tests)
# ---------------------------------------------------------------------------

def _classification_metrics(pairs, extras=()):
    """Micro classification metrics retaining missing and unexpected predictions."""
    if not pairs and not extras:
        return {
            "status": "not_evaluated",
            "reason": "No examples in dataset",
            "evaluated_examples": 0,
            "correct": 0,
            "incorrect": 0,
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "f1_score": 0.0,
            "true_positives": 0,
            "false_positives": 0,
            "false_negatives": 0,
            "confusion_matrix": {},
        }

    matrix = defaultdict(Counter)
    correct = 0
    fp = 0
    fn = 0
    total = 0
    for expected, predicted in pairs:
        total += 1
        expected_label = "__MISSING_EXPECTATION__" if expected is None else str(expected)
        predicted_label = "__MISSING_PREDICTION__" if predicted is None else str(predicted)
        matrix[expected_label][predicted_label] += 1
        if expected is not None and predicted is not None and expected == predicted:
            correct += 1
        else:
            if predicted is not None:
                fp += 1
            if expected is not None:
                fn += 1
    for predicted in extras:
        total += 1
        fp += 1
        matrix["__UNEXPECTED__"][str(predicted)] += 1

    precision = _safe_divide(correct, correct + fp)
    recall = _safe_divide(correct, correct + fn)
    f1 = _safe_divide(2 * precision * recall, precision + recall)
    return {
        "status": "evaluated",
        "evaluated_examples": len(pairs),
        "total_evaluated": len(pairs),
        "predictions_included": total,
        "correct": correct,
        "incorrect": total - correct,
        "accuracy": _safe_divide(correct, total),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "f1_score": f1,
        "true_positives": correct,
        "false_positives": fp,
        "false_negatives": fn,
        "confusion_matrix": {key: dict(val) for key, val in matrix.items()},
    }


# ---------------------------------------------------------------------------
# Data Loading and Normalization
# ---------------------------------------------------------------------------

def _load_dataset(dataset=None):
    """Load ground truth dataset from data/evaluation/ground_truth.json or fallback."""
    if dataset is not None:
        return dataset
    if GROUND_TRUTH_PATH.exists():
        with open(GROUND_TRUTH_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    try:
        from backend.evaluation_corpus import CASES
        return CASES
    except ImportError:
        return []


def _extract_case_info(case):
    """Normalize fields across different dataset schema variants."""
    cid = case.get("id") or case.get("case_id", "UNKNOWN")
    text = case.get("input_text", "")
    category = case.get("category")
    split = case.get("split", "heldout")

    exp = case.get("expected")
    if isinstance(exp, dict):
        abbrs = exp.get("abbreviations") or case.get("expected_abbreviations") or []
        meds = exp.get("medications") or case.get("expected_medications") or []
        specialty = exp.get("specialty") or case.get("expected_specialty")
        negation = exp.get("negation") if "negation" in exp else case.get("expected_negation")
        ocr_img = exp.get("ocr_image_path") or exp.get("ocr_image") or case.get("ocr_image_path") or case.get("ocr_image")
        ocr_ref = exp.get("ocr_reference_text") or case.get("ocr_reference_text")
    else:
        abbrs = case.get("expected_abbreviations") or []
        meds = case.get("expected_medications") or []
        specialty = case.get("expected_specialty")
        negation = case.get("expected_negation")
        ocr_img = case.get("ocr_image_path") or case.get("ocr_image")
        ocr_ref = case.get("ocr_reference_text")

    return {
        "id": cid,
        "input_text": text,
        "category": category,
        "split": split,
        "expected_abbreviations": abbrs,
        "expected_medications": meds,
        "expected_specialty": specialty,
        "expected_negation": negation,
        "ocr_image": ocr_img,
        "ocr_reference_text": ocr_ref,
        "raw": case,
    }


def _match_medication(expected_med, pred_meds, used_indices):
    """Find the best matching predicted medication by drug or generic name."""
    exp_name = expected_med.get("drug_name") or expected_med.get("medicine_name", "")
    for idx, pred in enumerate(pred_meds):
        if idx in used_indices:
            continue
        p_name = pred.get("drug_name", "")
        p_gen = pred.get("generic_name", "")
        if _fuzzy_match(p_name, exp_name) or _fuzzy_match(p_gen, exp_name):
            used_indices.add(idx)
            return pred
    return None


# ---------------------------------------------------------------------------
# Main Evaluation Function
# ---------------------------------------------------------------------------

def run_evaluation(interpreter, ocr_service=None, split="heldout", dataset=None):
    """Run full SynapRx evaluation across 11 key components.
    
    Evaluates:
      1. abbreviation_recognition
      2. full_form_identification
      3. contextual_disambiguation
      4. clinical_status
      5. negation_detection
      6. prescription_extraction
      7. medicine_dose_association
      8. route_frequency_extraction
      9. food_timing_extraction
      10. ocr_accuracy
      11. specialty_detection

    Returns dict with metrics for each component and an overall summary.
    """
    raw_dataset = _load_dataset(dataset)
    all_normalized = [_extract_case_info(c) for c in raw_dataset]
    cases = [c for c in all_normalized if c["split"] == split]

    # Partition OCR vs Text cases
    ocr_cases = [c for c in cases if c["ocr_image"]]
    text_cases = [c for c in cases if not c["ocr_image"]]

    # Check whether the dataset has explicit category partitions
    has_categories = any(c["category"] for c in cases)

    # Component data collectors
    comp_data = {
        "abbreviation_recognition": {"tp": 0, "fp": 0, "fn": 0, "total": 0, "failed": [], "cm": None},
        "full_form_identification": {"tp": 0, "fp": 0, "fn": 0, "total": 0, "failed": [], "cm": None},
        "contextual_disambiguation": {"tp": 0, "fp": 0, "fn": 0, "total": 0, "failed": [], "preds": [], "gts": []},
        "clinical_status": {"tp": 0, "fp": 0, "fn": 0, "total": 0, "failed": [], "preds": [], "gts": []},
        "negation_detection": {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "total": 0, "failed": [], "cm": None},
        "prescription_extraction": {"tp": 0, "fp": 0, "fn": 0, "total": 0, "failed": [], "cm": None},
        "medicine_dose_association": {"tp": 0, "fp": 0, "fn": 0, "total": 0, "failed": [], "cm": None},
        "route_frequency_extraction": {"tp": 0, "fp": 0, "fn": 0, "total": 0, "failed": [], "cm": None},
        "food_timing_extraction": {"tp": 0, "fp": 0, "fn": 0, "total": 0, "failed": [], "preds": [], "gts": []},
        "ocr_accuracy": {"tp": 0, "fp": 0, "fn": 0, "total": 0, "failed": [], "cm": None, "char_err": 0, "char_tot": 0, "word_err": 0, "word_tot": 0, "rows": []},
        "specialty_detection": {"tp": 0, "fp": 0, "fn": 0, "total": 0, "failed": [], "cm": None},
    }

    all_error_categories = Counter()
    text_cases_exact = 0

    # -----------------------------------------------------------------------
    # 10. OCR Accuracy Evaluation
    # -----------------------------------------------------------------------
    comp_ocr = comp_data["ocr_accuracy"]
    if ocr_service is not None and ocr_cases:
        for case in ocr_cases:
            cid = case["id"]
            img_rel = case["ocr_image"]
            ref_text = case["ocr_reference_text"] or ""
            img_path = ROOT / img_rel
            if img_path.exists():
                ocr_res = ocr_service.process_image(str(img_path))
                pred_text = ocr_res.get("full_text", "") if ocr_res and ocr_res.get("success") else ""
                ref_norm = _normalize(ref_text)
                pred_norm = _normalize(pred_text)

                cdist = _levenshtein_distance(ref_norm, pred_norm)
                ctot = len(ref_norm)
                rw = ref_norm.split()
                pw = pred_norm.split()
                wdist = _levenshtein_distance(rw, pw)
                wtot = len(rw)

                cer = _safe_divide(cdist, ctot)
                wer = _safe_divide(wdist, wtot)

                comp_ocr["total"] += 1
                comp_ocr["char_err"] += cdist
                comp_ocr["char_tot"] += ctot
                comp_ocr["word_err"] += wdist
                comp_ocr["word_tot"] += wtot

                comp_ocr["rows"].append({
                    "case_id": cid,
                    "image": img_rel,
                    "status": "Measured",
                    "reference_text": ref_text,
                    "predicted_text": pred_text,
                    "reference_characters": ctot,
                    "character_errors": cdist,
                    "cer": cer,
                    "wer": wer,
                    "ocr_success": bool(ocr_res.get("success")),
                })
                if cdist > 0:
                    err_type = "ocr_character_error"
                    all_error_categories[err_type] += 1
                    comp_ocr["failed"].append({
                        "id": cid,
                        "input_text": img_rel,
                        "expected": ref_text[:80] + "...",
                        "actual": pred_text[:80] + "...",
                        "error_type": err_type,
                    })

    # Cache interpretation results per text case
    interp_cache = {}
    for case in text_cases:
        text = case["input_text"]
        if interpreter:
            res = interpreter.interpret(text)
        else:
            res = {"success": False}
        interp_cache[case["id"]] = res if isinstance(res, dict) and res.get("success") else {
            "success": False,
            "abbreviations": [],
            "medications": [],
            "specialty": {},
        }

    # -----------------------------------------------------------------------
    # 1. Abbreviation Recognition
    # -----------------------------------------------------------------------
    comp_rec = comp_data["abbreviation_recognition"]
    rec_cases = [
        c for c in text_cases
        if not has_categories or c["category"] in {"abbreviation_recognition", "unknown_abbreviation", "edge_cases"}
    ]
    for case in rec_cases:
        cid = case["id"]
        text = case["input_text"]
        exp_abbrs = case["expected_abbreviations"]
        if not exp_abbrs and not has_categories:
            continue
        comp_rec["total"] += len(exp_abbrs)
        pred_abbrs = interp_cache[cid].get("abbreviations", []) or []
        pred_tokens = [_normalize(a.get("token")) for a in pred_abbrs]

        for ea in exp_abbrs:
            tok = _normalize(ea.get("token"))
            if tok in pred_tokens:
                comp_rec["tp"] += 1
                pred_tokens.remove(tok)
            else:
                comp_rec["fn"] += 1
                err_type = "missing_abbreviation"
                all_error_categories[err_type] += 1
                comp_rec["failed"].append({
                    "id": cid,
                    "input_text": text,
                    "expected": ea.get("token"),
                    "actual": None,
                    "error_type": err_type,
                })

        for extra in pred_tokens:
            comp_rec["fp"] += 1
            err_type = "spurious_abbreviation"
            all_error_categories[err_type] += 1
            comp_rec["failed"].append({
                "id": cid,
                "input_text": text,
                "expected": None,
                "actual": extra,
                "error_type": err_type,
            })

    # -----------------------------------------------------------------------
    # 2. Full-Form Identification
    # -----------------------------------------------------------------------
    comp_ff = comp_data["full_form_identification"]
    ff_cases = [
        c for c in text_cases
        if not has_categories or c["category"] in {
            "abbreviation_recognition",
            "abbreviation_disambiguation",
            "clinical_status",
            "edge_cases",
        }
    ]
    for case in ff_cases:
        cid = case["id"]
        text = case["input_text"]
        pred_abbrs = interp_cache[cid].get("abbreviations", []) or []
        for ea in case["expected_abbreviations"]:
            exp_full = ea.get("full_form") or ea.get("expected_full_form")
            if not exp_full:
                continue
            comp_ff["total"] += 1
            tok = _normalize(ea.get("token"))
            pred = next((p for p in pred_abbrs if _normalize(p.get("token")) == tok), None)
            pred_meaning = pred.get("meaning") if pred else None
            if pred and _fuzzy_match(pred_meaning, exp_full):
                comp_ff["tp"] += 1
            else:
                comp_ff["fn"] += 1
                if pred:
                    comp_ff["fp"] += 1
                err_type = "incorrect_full_form" if pred else "missing_prediction"
                all_error_categories[err_type] += 1
                comp_ff["failed"].append({
                    "id": cid,
                    "input_text": text,
                    "expected": exp_full,
                    "actual": pred_meaning,
                    "error_type": err_type,
                })

    # -----------------------------------------------------------------------
    # 3. Contextual Disambiguation
    # -----------------------------------------------------------------------
    comp_dis = comp_data["contextual_disambiguation"]
    dis_cases = [
        c for c in text_cases
        if (has_categories and c["category"] == "abbreviation_disambiguation")
        or any(
            ea.get("contextual") or ea.get("ambiguous") or ea.get("is_disambiguation")
            for ea in c["expected_abbreviations"]
        )
    ]
    for case in dis_cases:
        cid = case["id"]
        text = case["input_text"]
        pred_abbrs = interp_cache[cid].get("abbreviations", []) or []
        for ea in case["expected_abbreviations"]:
            is_disambig = (
                (has_categories and case["category"] == "abbreviation_disambiguation")
                or ea.get("contextual")
                or ea.get("ambiguous")
                or ea.get("is_disambiguation")
            )
            if not is_disambig:
                continue
            exp_meaning = (
                ea.get("expected_contextual_meaning")
                or ea.get("full_form")
                or ea.get("expected_full_form")
            )
            if not exp_meaning:
                continue
            comp_dis["total"] += 1
            tok = _normalize(ea.get("token"))
            pred = next((p for p in pred_abbrs if _normalize(p.get("token")) == tok), None)
            pred_meaning = pred.get("meaning") if pred else None
            comp_dis["gts"].append(exp_meaning)
            comp_dis["preds"].append(pred_meaning if pred_meaning else "(Missing)")

            if pred and (
                _fuzzy_match(pred_meaning, exp_meaning)
                or _normalize(pred_meaning) == _normalize(exp_meaning)
            ):
                comp_dis["tp"] += 1
            else:
                comp_dis["fn"] += 1
                if pred:
                    comp_dis["fp"] += 1
                err_type = "disambiguation_error" if pred else "missing_prediction"
                all_error_categories[err_type] += 1
                comp_dis["failed"].append({
                    "id": cid,
                    "input_text": text,
                    "expected": exp_meaning,
                    "actual": pred_meaning,
                    "error_type": err_type,
                })

    # -----------------------------------------------------------------------
    # 4. Clinical Status
    # -----------------------------------------------------------------------
    comp_cs = comp_data["clinical_status"]
    cs_cases = [
        c for c in text_cases
        if (c["category"] == "clinical_status" if has_categories else any(
            ea.get("clinical_status") or ea.get("expected_status")
            for ea in c["expected_abbreviations"]
        ))
    ]
    for case in cs_cases:
        cid = case["id"]
        text = case["input_text"]
        pred_abbrs = interp_cache[cid].get("abbreviations", []) or []
        for ea in case["expected_abbreviations"]:
            exp_status = ea.get("clinical_status") or ea.get("expected_status")
            if not exp_status:
                continue
            comp_cs["total"] += 1
            tok = _normalize(ea.get("token"))
            pred = next((p for p in pred_abbrs if _normalize(p.get("token")) == tok), None)
            p_status = pred.get("clinical_status") if pred else None
            comp_cs["gts"].append(exp_status)
            comp_cs["preds"].append(p_status if p_status else "(Missing)")

            if pred and _normalize(p_status) == _normalize(exp_status):
                comp_cs["tp"] += 1
            else:
                comp_cs["fn"] += 1
                if pred:
                    comp_cs["fp"] += 1
                err_type = "status_mismatch" if pred else "missing_prediction"
                all_error_categories[err_type] += 1
                comp_cs["failed"].append({
                    "id": cid,
                    "input_text": text,
                    "expected": exp_status,
                    "actual": p_status,
                    "error_type": err_type,
                })

    # -----------------------------------------------------------------------
    # 5. Negation Detection
    # -----------------------------------------------------------------------
    comp_neg = comp_data["negation_detection"]
    neg_cases = [
        c for c in text_cases
        if (c["category"] == "clinical_negation" if has_categories else (
            c["expected_negation"] is not None
            or any("expected_negation" in ea or "negated" in ea for ea in c["expected_abbreviations"])
        ))
    ]
    for case in neg_cases:
        cid = case["id"]
        text = case["input_text"]
        pred_abbrs = interp_cache[cid].get("abbreviations", []) or []

        # Determine expected negation value
        if case["expected_negation"] is not None:
            exp_neg = bool(case["expected_negation"])
        elif case["expected_abbreviations"]:
            ea = case["expected_abbreviations"][0]
            exp_neg = bool(ea.get("expected_negation") if "expected_negation" in ea else ea.get("negated", False))
        else:
            exp_neg = False

        comp_neg["total"] += 1
        # Target token if known
        tok = _normalize(case["expected_abbreviations"][0].get("token")) if case["expected_abbreviations"] else None
        pred = next((p for p in pred_abbrs if _normalize(p.get("token")) == tok), None) if tok else (pred_abbrs[0] if pred_abbrs else None)

        if pred is None:
            if exp_neg:
                comp_neg["fn"] += 1
            else:
                comp_neg["fp"] += 1
            err_type = "missing_prediction"
            all_error_categories[err_type] += 1
            comp_neg["failed"].append({
                "id": cid,
                "input_text": text,
                "expected": f"negated={exp_neg}",
                "actual": None,
                "error_type": err_type,
            })
        else:
            p_neg = bool(pred.get("negated", False))
            if exp_neg and p_neg:
                comp_neg["tp"] += 1
            elif not exp_neg and not p_neg:
                comp_neg["tn"] += 1
            elif not exp_neg and p_neg:
                comp_neg["fp"] += 1
                err_type = "false_positive_negation"
                all_error_categories[err_type] += 1
                comp_neg["failed"].append({
                    "id": cid,
                    "input_text": text,
                    "expected": f"negated={exp_neg}",
                    "actual": f"negated={p_neg}",
                    "error_type": err_type,
                })
            else:
                comp_neg["fn"] += 1
                err_type = "false_negative_negation"
                all_error_categories[err_type] += 1
                comp_neg["failed"].append({
                    "id": cid,
                    "input_text": text,
                    "expected": f"negated={exp_neg}",
                    "actual": f"negated={p_neg}",
                    "error_type": err_type,
                })

    # -----------------------------------------------------------------------
    # 6. Prescription Extraction
    # -----------------------------------------------------------------------
    comp_rx = comp_data["prescription_extraction"]
    rx_cases = [
        c for c in text_cases
        if not has_categories or c["category"] in {"prescription_parsing", "edge_cases"}
    ]
    for case in rx_cases:
        cid = case["id"]
        text = case["input_text"]
        exp_meds = case["expected_medications"]
        if not exp_meds and not has_categories:
            continue
        pred_meds = interp_cache[cid].get("medications", []) or []
        used_indices = set()

        for em in exp_meds:
            comp_rx["total"] += 1
            exp_drug = em.get("drug_name") or em.get("medicine_name", "")
            exp_dose = em.get("dosage_strength") or em.get("dose", "")
            exp_form = em.get("form", "")

            pm = _match_medication(em, pred_meds, used_indices)
            if pm:
                p_drug = pm.get("drug_name", "")
                p_dose = pm.get("dosage_strength", "")
                p_form = pm.get("form", "")

                drug_ok = _fuzzy_match(p_drug, exp_drug) or _fuzzy_match(pm.get("generic_name"), exp_drug)
                dose_ok = (
                    _fuzzy_match(p_dose, exp_dose)
                    or (
                        _normalize(exp_dose) in {"unspecified", "not specified"}
                        and _normalize(p_dose) in {"unspecified", "not specified"}
                    )
                )
                form_ok = (
                    not exp_form
                    or _fuzzy_match(p_form, exp_form)
                    or (
                        _normalize(exp_form) in {"dosage form not specified", "unspecified"}
                        and _normalize(p_form) in {"dosage form not specified", "unspecified"}
                    )
                )

                if drug_ok and dose_ok and form_ok:
                    comp_rx["tp"] += 1
                else:
                    comp_rx["fn"] += 1
                    comp_rx["fp"] += 1
                    err_type = "prescription_mismatch"
                    all_error_categories[err_type] += 1
                    comp_rx["failed"].append({
                        "id": cid,
                        "input_text": text,
                        "expected": f"{exp_drug} | {exp_dose} | {exp_form}",
                        "actual": f"{p_drug} | {p_dose} | {p_form}",
                        "error_type": err_type,
                    })
            else:
                comp_rx["fn"] += 1
                err_type = "missing_medication"
                all_error_categories[err_type] += 1
                comp_rx["failed"].append({
                    "id": cid,
                    "input_text": text,
                    "expected": f"{exp_drug} | {exp_dose} | {exp_form}",
                    "actual": None,
                    "error_type": err_type,
                })

        # Spurious predicted medications
        for idx, extra_m in enumerate(pred_meds):
            if idx not in used_indices:
                comp_rx["fp"] += 1
                err_type = "spurious_medication"
                all_error_categories[err_type] += 1
                comp_rx["failed"].append({
                    "id": cid,
                    "input_text": text,
                    "expected": None,
                    "actual": extra_m.get("drug_name"),
                    "error_type": err_type,
                })

    # -----------------------------------------------------------------------
    # 7. Medicine-Dose Association
    # -----------------------------------------------------------------------
    comp_dose = comp_data["medicine_dose_association"]
    dose_cases = [
        c for c in text_cases
        if not has_categories or c["category"] in {"medicine_extraction", "prescription_parsing", "edge_cases"}
    ]
    for case in dose_cases:
        cid = case["id"]
        text = case["input_text"]
        exp_meds = case["expected_medications"]
        if not exp_meds and not has_categories:
            continue
        pred_meds = interp_cache[cid].get("medications", []) or []
        used_indices = set()

        for em in exp_meds:
            comp_dose["total"] += 1
            exp_drug = em.get("drug_name") or em.get("medicine_name", "")
            exp_dose = em.get("dosage_strength") or em.get("dose", "")

            pm = _match_medication(em, pred_meds, used_indices)
            if pm:
                p_dose = pm.get("dosage_strength", "")
                dose_ok = (
                    _fuzzy_match(p_dose, exp_dose)
                    or (
                        _normalize(exp_dose) in {"unspecified", "not specified"}
                        and _normalize(p_dose) in {"unspecified", "not specified"}
                    )
                )
                if dose_ok:
                    comp_dose["tp"] += 1
                else:
                    comp_dose["fn"] += 1
                    comp_dose["fp"] += 1
                    err_type = "dose_mismatch"
                    all_error_categories[err_type] += 1
                    comp_dose["failed"].append({
                        "id": cid,
                        "input_text": text,
                        "expected": f"{exp_drug}: {exp_dose}",
                        "actual": f"{pm.get('drug_name')}: {p_dose}",
                        "error_type": err_type,
                    })
            else:
                comp_dose["fn"] += 1
                err_type = "missing_medication"
                all_error_categories[err_type] += 1
                comp_dose["failed"].append({
                    "id": cid,
                    "input_text": text,
                    "expected": f"{exp_drug}: {exp_dose}",
                    "actual": None,
                    "error_type": err_type,
                })

    # -----------------------------------------------------------------------
    # 8. Route & Frequency Extraction
    # -----------------------------------------------------------------------
    comp_rf = comp_data["route_frequency_extraction"]
    rf_cases = [
        c for c in text_cases
        if not has_categories or c["category"] in {"route_extraction", "prescription_parsing", "edge_cases"}
    ]
    for case in rf_cases:
        cid = case["id"]
        text = case["input_text"]
        pred_meds = interp_cache[cid].get("medications", []) or []
        used_indices = set()

        for em in case["expected_medications"]:
            exp_freq = em.get("frequency_code") or em.get("frequency", "")
            exp_route = em.get("route_code") or em.get("route", "")
            if not exp_freq and not exp_route:
                continue
            comp_rf["total"] += 1
            pm = _match_medication(em, pred_meds, used_indices)
            if pm:
                p_freq = pm.get("frequency_code", "")
                p_route = pm.get("route_code", "")
                freq_ok = (
                    not exp_freq
                    or _normalize(p_freq) == _normalize(exp_freq)
                    or (
                        _normalize(exp_freq) in {"unspecified", "not specified"}
                        and _normalize(p_freq) in {"unspecified", "not specified"}
                    )
                )
                route_ok = (
                    not exp_route
                    or _normalize(p_route) == _normalize(exp_route)
                    or (
                        _normalize(exp_route) in {"unspecified", "not specified"}
                        and _normalize(p_route) in {"unspecified", "not specified"}
                    )
                )
                if freq_ok and route_ok:
                    comp_rf["tp"] += 1
                else:
                    comp_rf["fn"] += 1
                    comp_rf["fp"] += 1
                    err_type = "route_frequency_mismatch"
                    all_error_categories[err_type] += 1
                    comp_rf["failed"].append({
                        "id": cid,
                        "input_text": text,
                        "expected": f"freq={exp_freq}, route={exp_route}",
                        "actual": f"freq={p_freq}, route={p_route}",
                        "error_type": err_type,
                    })
            else:
                comp_rf["fn"] += 1
                err_type = "missing_medication"
                all_error_categories[err_type] += 1
                comp_rf["failed"].append({
                    "id": cid,
                    "input_text": text,
                    "expected": f"freq={exp_freq}, route={exp_route}",
                    "actual": None,
                    "error_type": err_type,
                })

    # -----------------------------------------------------------------------
    # 9. Food Timing Extraction
    # -----------------------------------------------------------------------
    comp_food = comp_data["food_timing_extraction"]
    food_cases = [
        c for c in text_cases
        if not has_categories or c["category"] in {"food_timing", "prescription_parsing", "edge_cases"}
    ]
    for case in food_cases:
        cid = case["id"]
        text = case["input_text"]
        pred_meds = interp_cache[cid].get("medications", []) or []
        used_indices = set()

        for em in case["expected_medications"]:
            exp_food = em.get("food_timing_code") or em.get("food_timing", "")
            if not exp_food:
                continue
            comp_food["total"] += 1
            pm = _match_medication(em, pred_meds, used_indices)
            p_food = pm.get("food_timing_code") if pm else None
            comp_food["gts"].append(exp_food)
            comp_food["preds"].append(p_food if p_food else "(Missing)")

            food_ok = pm and (
                _normalize(p_food) == _normalize(exp_food)
                or (
                    _normalize(exp_food) in {"unspecified", "not specified"}
                    and _normalize(p_food) in {"unspecified", "not specified"}
                )
            )
            if food_ok:
                comp_food["tp"] += 1
            else:
                comp_food["fn"] += 1
                if pm:
                    comp_food["fp"] += 1
                err_type = "food_timing_mismatch" if pm else "missing_medication"
                all_error_categories[err_type] += 1
                comp_food["failed"].append({
                    "id": cid,
                    "input_text": text,
                    "expected": exp_food,
                    "actual": p_food,
                    "error_type": err_type,
                })

    # -----------------------------------------------------------------------
    # 11. Specialty Detection
    # -----------------------------------------------------------------------
    comp_spec = comp_data["specialty_detection"]
    spec_cases = [
        c for c in text_cases
        if (c["category"] == "specialty_detection" if has_categories else c["expected_specialty"] is not None)
    ]
    for case in spec_cases:
        cid = case["id"]
        text = case["input_text"]
        exp_spec = case["expected_specialty"]
        if not exp_spec:
            continue
        comp_spec["total"] += 1
        res = interp_cache[cid]
        p_spec = res.get("specialty", {}).get("primary") if res.get("specialty") else None

        if p_spec and _normalize(p_spec) == _normalize(exp_spec):
            comp_spec["tp"] += 1
        else:
            comp_spec["fn"] += 1
            if p_spec:
                comp_spec["fp"] += 1
            err_type = "specialty_mismatch" if p_spec else "missing_prediction"
            all_error_categories[err_type] += 1
            comp_spec["failed"].append({
                "id": cid,
                "input_text": text,
                "expected": exp_spec,
                "actual": p_spec,
                "error_type": err_type,
            })

    # Exact match for full text cases (abbreviation + medication accuracy)
    for case in text_cases:
        cid = case["id"]
        res = interp_cache[cid]
        pred_abbrs = res.get("abbreviations", []) or []
        pred_meds = res.get("medications", []) or []
        exp_abbrs = case["expected_abbreviations"]
        exp_meds = case["expected_medications"]

        p_toks = sorted([_normalize(a.get("token")) for a in pred_abbrs])
        e_toks = sorted([_normalize(a.get("token")) for a in exp_abbrs])
        p_mds = sorted([_normalize(m.get("drug_name")) for m in pred_meds])
        e_mds = sorted([_normalize(m.get("drug_name") or m.get("medicine_name")) for m in exp_meds])
        if p_toks == e_toks and p_mds == e_mds:
            text_cases_exact += 1

    # -----------------------------------------------------------------------
    # Assemble Metrics for all 11 Components
    # -----------------------------------------------------------------------
    metrics = {}
    evaluated_accuracies = []
    total_correct = 0
    total_incorrect = 0

    for comp_name in COMPONENT_NAMES:
        data = comp_data[comp_name]
        total = data["total"]

        if total == 0 and data["tp"] == 0 and data["fp"] == 0 and data["fn"] == 0:
            metrics[comp_name] = {
                "status": "not_evaluated",
                "reason": "No examples in dataset",
            }
            continue

        if comp_name == "negation_detection":
            tp = data["tp"]
            fp = data["fp"]
            fn = data["fn"]
            tn = data["tn"]
            prec = _safe_divide(tp, tp + fp)
            rec = _safe_divide(tp, tp + fn)
            f1 = _safe_divide(2 * prec * rec, prec + rec)
            acc = _safe_divide(tp + tn, total)
            cm = None
            corr = tp + tn
            incorr = fp + fn
        elif comp_name == "ocr_accuracy":
            ctot = data["char_tot"]
            cerr = data["char_err"]
            wtot = data["word_tot"]
            werr = data["word_err"]
            cer = _safe_divide(cerr, ctot)
            wer = _safe_divide(werr, wtot)
            acc = max(0.0, round(1.0 - cer, 4))
            tp = max(0, ctot - cerr)
            fp = cerr
            fn = cerr
            prec = _safe_divide(tp, ctot)
            rec = prec
            f1 = prec
            cm = None
            corr = tp
            incorr = cerr
        else:
            tp = data["tp"]
            fp = data["fp"]
            fn = data["fn"]
            m = _compute_metrics(tp, fp, fn, total=total)
            acc = m["accuracy"]
            prec = m["precision"]
            rec = m["recall"]
            f1 = m["f1_score"]
            if "gts" in data:
                cm = _build_confusion_matrix(data["preds"], data["gts"])
            else:
                cm = None
            corr = tp
            incorr = fp + fn

        comp_result = {
            "status": "evaluated",
            "total_evaluated": total,
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1_score": f1,
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "failed_examples": data["failed"],
            "confusion_matrix": cm,
            # Backward-compatibility aliases
            "evaluated_examples": total,
            "correct": corr,
            "incorrect": incorr,
            "f1": f1,
        }
        if comp_name == "ocr_accuracy":
            comp_result["cer"] = cer
            comp_result["wer"] = wer
            comp_result["character_errors"] = cerr
            comp_result["reference_characters"] = ctot
            comp_result["word_errors"] = werr
            comp_result["reference_words"] = wtot
        if comp_name == "prescription_extraction":
            comp_result["exact_match_accuracy"] = acc

        metrics[comp_name] = comp_result
        evaluated_accuracies.append((comp_name, acc))
        total_correct += corr
        total_incorrect += incorr

    # Aliases for frontend / legacy test compatibility
    if "contextual_disambiguation" in metrics:
        metrics["ambiguity_handling"] = metrics["contextual_disambiguation"]
    if "clinical_status" in metrics:
        metrics["clinical_status_classification"] = metrics["clinical_status"]
    if "ocr_accuracy" in metrics:
        metrics["ocr_character_error_rate"] = metrics["ocr_accuracy"]

    # -----------------------------------------------------------------------
    # Overall Summary
    # -----------------------------------------------------------------------
    if evaluated_accuracies:
        avg_acc = round(sum(a for _, a in evaluated_accuracies) / len(evaluated_accuracies), 4)
        strongest = max(evaluated_accuracies, key=lambda x: x[1])[0]
        weakest = min(evaluated_accuracies, key=lambda x: x[1])[0]
    else:
        avg_acc = 0.0
        strongest = None
        weakest = None

    common_errors = [
        {"error_type": err, "count": count}
        for err, count in all_error_categories.most_common()
    ]

    summary = {
        "total_metrics_calculated": len(evaluated_accuracies),
        "average_accuracy": avg_acc,
        "strongest_component": strongest,
        "weakest_component": weakest,
        "total_correct": total_correct,
        "total_incorrect": total_incorrect,
        "common_error_categories": common_errors,
    }

    ambiguous_total = comp_data["contextual_disambiguation"]["total"]
    ambiguous_tp = comp_data["contextual_disambiguation"]["tp"]

    report = {
        "summary": summary,
        "overall_summary": summary,
        "metrics": metrics,
        "dataset": {
            "name": "SynapRx Ground Truth Evaluation Corpus",
            "split": split,
            "total_cases_in_split": len(cases),
            "text_cases": len(text_cases),
            "ocr_cases": len(ocr_cases),
            "development_cases": sum(c["split"] == "development" for c in all_normalized),
            "heldout_cases": sum(c["split"] == "heldout" for c in all_normalized),
            "ground_truth_status": "Manually verified against independent clinical terminology references",
        },
        "overall_text_exact_match": {
            "status": "Measured" if text_cases else "Not Evaluated",
            "evaluated_examples": len(text_cases),
            "correct": text_cases_exact,
            "incorrect": len(text_cases) - text_cases_exact,
            "accuracy": _safe_divide(text_cases_exact, len(text_cases)),
        },
        "ambiguous_case_summary": {
            "status": "Measured" if ambiguous_total else "Not Evaluated",
            "evaluated_examples": ambiguous_total,
            "correct_clarification_requests": ambiguous_tp,
            "incorrect_or_unresolved": ambiguous_total - ambiguous_tp,
            "correct": ambiguous_tp,
            "incorrect": ambiguous_total - ambiguous_tp,
            "accuracy": _safe_divide(ambiguous_tp, ambiguous_total),
        },
        "ocr_cases": comp_data["ocr_accuracy"].get("rows", []),
        "failed_examples": [f for d in comp_data.values() for f in d.get("failed", [])][:200],
        "common_error_categories": common_errors,
    }

    # Direct top-level access to the 11 component results
    for k, v in metrics.items():
        report[k] = v

    return report


# ---------------------------------------------------------------------------
# CSV Export Function
# ---------------------------------------------------------------------------

def evaluation_csv(report):
    """Serialize evaluation report into a tabular CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "record_type",
        "case_id",
        "split",
        "component",
        "expected",
        "actual",
        "correct",
        "accuracy",
        "precision",
        "recall",
        "f1_score",
    ])

    split = report.get("dataset", {}).get("split", report.get("split", ""))

    # Summary record
    summary = report.get("summary", {})
    if summary:
        writer.writerow([
            "summary",
            "",
            split,
            "overall",
            "",
            "",
            summary.get("total_correct", ""),
            summary.get("average_accuracy", ""),
            "",
            "",
            "",
        ])

    # Component metric records
    for comp_name, metric in report.get("metrics", {}).items():
        if not isinstance(metric, dict) or metric.get("status") != "evaluated":
            continue
        writer.writerow([
            "metric",
            "",
            split,
            comp_name,
            "",
            "",
            metric.get("true_positives", metric.get("correct", "")),
            metric.get("accuracy", ""),
            metric.get("precision", ""),
            metric.get("recall", ""),
            metric.get("f1_score", metric.get("f1", "")),
        ])

    # Failed example records
    for failure in report.get("failed_examples", []):
        writer.writerow([
            "failure",
            failure.get("id", failure.get("case_id", "")),
            split,
            failure.get("error_type", ""),
            str(failure.get("expected", "")),
            str(failure.get("actual", "")),
            False,
            "",
            "",
            "",
            "",
        ])

    # OCR records
    for ocr in report.get("ocr_cases", []):
        writer.writerow([
            "ocr",
            ocr.get("case_id", ""),
            split,
            "ocr_accuracy",
            ocr.get("reference_text", ""),
            ocr.get("predicted_text", ""),
            ocr.get("character_errors", 1) == 0,
            ocr.get("cer", ""),
            "",
            "",
            "",
        ])

    return output.getvalue()


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    """Run CLI evaluation and output summary json."""
    from backend.ocr_service import MedicalOcrService
    from backend.prescription_parser import PrescriptionInterpreter

    report = run_evaluation(PrescriptionInterpreter(), MedicalOcrService(), split="heldout")
    print(json.dumps({
        "summary": report["summary"],
        "dataset": report["dataset"],
        "metrics": {
            k: {
                "status": v.get("status"),
                "total_evaluated": v.get("total_evaluated"),
                "accuracy": v.get("accuracy"),
                "precision": v.get("precision"),
                "recall": v.get("recall"),
                "f1_score": v.get("f1_score"),
            }
            for k, v in report["metrics"].items()
            if isinstance(v, dict) and k in COMPONENT_NAMES
        },
        "common_error_categories": report["common_error_categories"][:5],
    }, indent=2))


if __name__ == "__main__":
    main()
