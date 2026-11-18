import unittest

from backend.evaluation import _classification_metrics, _levenshtein_distance, run_evaluation
from backend.evaluation_corpus import CASES


class EvaluationTests(unittest.TestCase):
    def test_ground_truth_has_separate_development_and_heldout_splits(self):
        self.assertEqual(len(CASES), 100)
        self.assertEqual(sum(item["split"] == "development" for item in CASES), 20)
        self.assertEqual(sum(item["split"] == "heldout" for item in CASES), 80)
        self.assertEqual(sum(bool(item["ocr_image"]) for item in CASES), 3)
        self.assertTrue(all(item["manual_verification"]["status"] == "manually reviewed" for item in CASES))

    def test_missing_and_spurious_predictions_are_not_correct(self):
        metric = _classification_metrics(
            [("AF", "AF"), ("MI", None), ("OD", "Right Eye")],
            extras=["QXZ"],
        )
        self.assertEqual(metric["true_positives"], 1)
        self.assertEqual(metric["false_positives"], 2)
        self.assertEqual(metric["false_negatives"], 2)
        self.assertEqual(metric["accuracy"], 0.25)
        self.assertIn("MI", metric["confusion_matrix"])

    def test_empty_predictions_fail_expected_occurrences(self):
        class EmptyInterpreter:
            def interpret(self, text):
                return {"success": True, "abbreviations": [], "medications": []}

        dataset = [{
            "case_id": "TEST-001",
            "split": "heldout",
            "input_text": "ECG shows AF.",
            "expected_abbreviations": [{
                "token": "AF",
                "expected_full_form": "Atrial Fibrillation",
                "expected_status": "Positive / Confirmed Finding",
                "expected_contextual_meaning": "Atrial Fibrillation",
                "contextual": True,
                "ambiguous": False,
                "expected_negation": False,
            }],
            "expected_medications": [],
            "ocr_image": None,
            "ocr_reference_text": None,
            "manual_verification": {"status": "manually reviewed"},
        }]
        report = run_evaluation(EmptyInterpreter(), None, split="heldout", dataset=dataset)
        self.assertEqual(report["metrics"]["abbreviation_recognition"]["false_negatives"], 1)
        self.assertEqual(report["metrics"]["full_form_identification"]["accuracy"], 0.0)
        self.assertEqual(report["metrics"]["ambiguity_handling"]["evaluated_examples"], 1)
        self.assertEqual(report["overall_text_exact_match"]["correct"], 0)

    def test_character_error_distance(self):
        self.assertEqual(_levenshtein_distance("kitten", "sitting"), 3)


if __name__ == "__main__":
    unittest.main()
