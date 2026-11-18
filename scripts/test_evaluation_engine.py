import unittest
import json
from pathlib import Path

from backend.evaluation import (
    _levenshtein_distance,
    _safe_divide,
    _compute_metrics,
    _build_confusion_matrix,
    _normalize,
    _fuzzy_match,
    run_evaluation,
    evaluation_csv,
)

class EvaluationEngineTests(unittest.TestCase):
    def test_helper_levenshtein_distance(self):
        self.assertEqual(_levenshtein_distance("kitten", "sitting"), 3)
        self.assertEqual(_levenshtein_distance("", "test"), 4)
        self.assertEqual(_levenshtein_distance("same", "same"), 0)
        # Token-level distance
        self.assertEqual(_levenshtein_distance(["a", "b", "c"], ["a", "c"]), 1)

    def test_helper_safe_divide(self):
        self.assertEqual(_safe_divide(10, 0), 0.0)
        self.assertEqual(_safe_divide(1, 2), 0.5)
        self.assertEqual(_safe_divide(0, 5), 0.0)

    def test_helper_compute_metrics(self):
        m = _compute_metrics(tp=8, fp=2, fn=2)
        self.assertEqual(m["precision"], 0.8)
        self.assertEqual(m["recall"], 0.8)
        self.assertEqual(m["f1_score"], 0.8)
        self.assertEqual(m["accuracy"], _safe_divide(8, 12))

    def test_helper_build_confusion_matrix(self):
        preds = ["Cardiology", "Neurology", "Cardiology"]
        gts = ["Cardiology", "Cardiology", "Neurology"]
        cm = _build_confusion_matrix(preds, gts)
        self.assertIn("labels", cm)
        self.assertIn("matrix", cm)
        self.assertEqual(cm["labels"], ["Cardiology", "Neurology"])
        self.assertEqual(len(cm["matrix"]), 2)
        self.assertEqual(len(cm["matrix"][0]), 2)
        # gt=Cardiology: 1 pred Cardio, 1 pred Neuro -> row 0: [1, 1]
        self.assertEqual(cm["matrix"][0], [1, 1])
        # gt=Neurology: 1 pred Cardio, 0 pred Neuro -> row 1: [1, 0]
        self.assertEqual(cm["matrix"][1], [1, 0])

    def test_helper_normalize(self):
        self.assertEqual(_normalize("  CAD   "), "cad")
        self.assertEqual(_normalize(None), "")
        self.assertEqual(_normalize("Word  with   spaces"), "word with spaces")

    def test_helper_fuzzy_match(self):
        self.assertTrue(_fuzzy_match("Pantoprazole 40mg", "Pantoprazole"))
        self.assertTrue(_fuzzy_match("Pantoprazole", "Pantoprazole 40mg"))
        self.assertTrue(_fuzzy_match("Coronary Artery Disease", "coronary artery disease"))
        self.assertFalse(_fuzzy_match("CAD", "Hypertension"))
        self.assertFalse(_fuzzy_match(None, "CAD"))
        self.assertFalse(_fuzzy_match("CAD", None))

    def test_all_11_components_structure_and_edge_cases(self):
        class MockInterpreter:
            def interpret(self, text):
                return {
                    "success": True,
                    "specialty": {"primary": "Cardiology"},
                    "abbreviations": [
                        {
                            "token": "CAD",
                            "meaning": "Coronary Artery Disease",
                            "clinical_status": "Past History",
                            "negated": False,
                        }
                    ],
                    "medications": [
                        {
                            "drug_name": "Amlodipine",
                            "dosage_strength": "5 mg",
                            "form": "Oral",
                            "frequency_code": "OD",
                            "route_code": "PO",
                            "food_timing_code": "PC",
                        }
                    ],
                }

        dataset = [
            {
                "case_id": "CASE-1",
                "split": "heldout",
                "input_text": "History of CAD. Tab Amlodipine 5 mg PO OD PC.",
                "expected_specialty": "Cardiology",
                "expected_abbreviations": [
                    {
                        "token": "CAD",
                        "expected_full_form": "Coronary Artery Disease",
                        "expected_status": "Past History",
                        "expected_contextual_meaning": "Coronary Artery Disease",
                        "contextual": True,
                        "ambiguous": False,
                        "expected_negation": False,
                    }
                ],
                "expected_medications": [
                    {
                        "drug_name": "Amlodipine",
                        "dosage_strength": "5 mg",
                        "form": "Oral",
                        "frequency_code": "OD",
                        "route_code": "PO",
                        "food_timing_code": "PC",
                    }
                ],
            }
        ]

        report = run_evaluation(MockInterpreter(), None, split="heldout", dataset=dataset)

        # 11 components
        expected_components = [
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

        for comp in expected_components:
            self.assertIn(comp, report["metrics"], f"Missing component: {comp}")
            res = report["metrics"][comp]
            self.assertIn("status", res)
            if res["status"] == "evaluated":
                self.assertIn("total_evaluated", res)
                self.assertIn("accuracy", res)
                self.assertIn("precision", res)
                self.assertIn("recall", res)
                self.assertIn("f1_score", res)
                self.assertIn("true_positives", res)
                self.assertIn("false_positives", res)
                self.assertIn("false_negatives", res)
                self.assertIn("failed_examples", res)
                self.assertIn("confusion_matrix", res)
            else:
                self.assertEqual(res["status"], "not_evaluated")
                self.assertIn("reason", res)

        # Check contextual_disambiguation, clinical_status, food_timing have confusion matrix
        for comp in ["contextual_disambiguation", "clinical_status", "food_timing_extraction"]:
            cm = report["metrics"][comp]["confusion_matrix"]
            self.assertIsNotNone(cm, f"{comp} should have a confusion matrix")
            self.assertIn("labels", cm)
            self.assertIn("matrix", cm)

        # Check overall summary
        summary = report["summary"]
        self.assertIn("total_metrics_calculated", summary)
        self.assertIn("average_accuracy", summary)
        self.assertIn("strongest_component", summary)
        self.assertIn("weakest_component", summary)
        self.assertIn("total_correct", summary)
        self.assertIn("total_incorrect", summary)
        self.assertIn("common_error_categories", summary)

        # Check CSV export
        csv_str = evaluation_csv(report)
        self.assertIsInstance(csv_str, str)
        self.assertIn("record_type,case_id,split,component", csv_str)
        self.assertIn("abbreviation_recognition", csv_str)

    def test_never_treat_missing_predictions_as_correct(self):
        class EmptyInterpreter:
            def interpret(self, text):
                return {"success": True, "abbreviations": [], "medications": []}

        dataset = [
            {
                "case_id": "EMPTY-1",
                "split": "heldout",
                "input_text": "History of CAD. Tab Amlodipine 5 mg PO OD PC.",
                "expected_specialty": "Cardiology",
                "expected_abbreviations": [
                    {
                        "token": "CAD",
                        "expected_full_form": "Coronary Artery Disease",
                        "expected_status": "Past History",
                        "expected_contextual_meaning": "Coronary Artery Disease",
                        "contextual": True,
                        "ambiguous": False,
                        "expected_negation": True,
                    }
                ],
                "expected_medications": [
                    {
                        "drug_name": "Amlodipine",
                        "dosage_strength": "5 mg",
                        "form": "Oral",
                        "frequency_code": "OD",
                        "route_code": "PO",
                        "food_timing_code": "PC",
                    }
                ],
            }
        ]

        report = run_evaluation(EmptyInterpreter(), None, split="heldout", dataset=dataset)
        self.assertEqual(report["metrics"]["abbreviation_recognition"]["accuracy"], 0.0)
        self.assertEqual(report["metrics"]["abbreviation_recognition"]["false_negatives"], 1)
        self.assertEqual(report["metrics"]["full_form_identification"]["accuracy"], 0.0)
        self.assertEqual(report["metrics"]["prescription_extraction"]["accuracy"], 0.0)
        self.assertEqual(report["metrics"]["specialty_detection"]["accuracy"], 0.0)
        self.assertEqual(report["metrics"]["medicine_dose_association"]["accuracy"], 0.0)

    def test_empty_dataset_component_status(self):
        class EmptyInterpreter:
            def interpret(self, text):
                return {"success": True}

        # Dataset with no medications and no abbreviations
        dataset = [
            {
                "case_id": "NONE-1",
                "split": "heldout",
                "input_text": "Unremarkable.",
            }
        ]
        report = run_evaluation(EmptyInterpreter(), None, split="heldout", dataset=dataset)
        self.assertEqual(report["metrics"]["prescription_extraction"]["status"], "not_evaluated")
        self.assertEqual(report["metrics"]["prescription_extraction"]["reason"], "No examples in dataset")

if __name__ == "__main__":
    unittest.main()
