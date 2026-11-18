"""
Comprehensive verification test for data/evaluation/ground_truth.json.
Validates all requirements from the prompt.
"""

import json
import os
import unittest

class TestGroundTruthEvaluationDataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = os.path.join("data", "evaluation", "ground_truth.json")
        cls.assertTrue(os.path.exists(path), f"File does not exist: {path}")
        with open(path, "r", encoding="utf-8") as f:
            cls.data = json.load(f)

    def test_total_count(self):
        self.assertGreaterEqual(len(self.data), 120, "Dataset must have at least 120 examples.")
        print(f"Total examples: {len(self.data)}")

    def test_split_counts(self):
        dev = [x for x in self.data if x.get("split") == "development"]
        heldout = [x for x in self.data if x.get("split") == "heldout"]
        self.assertEqual(len(dev), 40, f"Development split must be 40 examples, got {len(dev)}")
        self.assertGreaterEqual(len(heldout), 80, f"Heldout split must be 80+ examples, got {len(heldout)}")
        print(f"Splits -> Development: {len(dev)}, Heldout: {len(heldout)}")

    def test_schema_conformance(self):
        ids = set()
        for idx, item in enumerate(self.data):
            self.assertIn("id", item, f"Missing 'id' at index {idx}")
            self.assertIn("split", item, f"Missing 'split' at index {idx}")
            self.assertIn("category", item, f"Missing 'category' at index {idx}")
            self.assertIn("input_text", item, f"Missing 'input_text' at index {idx}")
            self.assertIn("expected", item, f"Missing 'expected' at index {idx}")
            self.assertIn("notes", item, f"Missing 'notes' at index {idx}")

            # Check uniqueness of ID
            self.assertNotIn(item["id"], ids, f"Duplicate ID: {item['id']}")
            ids.add(item["id"])

            expected = item["expected"]
            self.assertIn("abbreviations", expected)
            self.assertIsInstance(expected["abbreviations"], list)
            self.assertIn("medications", expected)
            self.assertIsInstance(expected["medications"], list)
            self.assertIn("specialty", expected)
            self.assertIsInstance(expected["specialty"], str)
            self.assertIn("negation", expected)
            self.assertIsInstance(expected["negation"], bool)

            for abbr in expected["abbreviations"]:
                self.assertIn("token", abbr)
                self.assertIn("full_form", abbr)
                self.assertIn("category", abbr)
                self.assertIn("clinical_status", abbr)

    def test_category_counts(self):
        expected_min_counts = {
            "abbreviation_recognition": 15,
            "abbreviation_disambiguation": 15,
            "clinical_negation": 12,
            "clinical_status": 10,
            "prescription_parsing": 15,
            "food_timing": 10,
            "medicine_extraction": 10,
            "route_extraction": 5,
            "unknown_abbreviation": 5,
            "specialty_detection": 5,
            "ocr_reference": 5,
            "edge_cases": 8
        }
        category_counts = {}
        for item in self.data:
            cat = item["category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1

        for cat, min_count in expected_min_counts.items():
            actual = category_counts.get(cat, 0)
            self.assertGreaterEqual(actual, min_count, f"Category '{cat}' count {actual} < minimum {min_count}")
            print(f"Category '{cat}': {actual} (min: {min_count})")

    def test_abbreviation_recognition_tokens(self):
        req_tokens = ["CAD", "T2DM", "HTN", "COPD", "CHF", "CVA", "DVT", "PE", "CKD", "GERD", "CAP", "TIA", "SLE", "DKA"]
        found_tokens = set()
        for item in self.data:
            if item["category"] == "abbreviation_recognition":
                for abbr in item["expected"]["abbreviations"]:
                    found_tokens.add(abbr["token"])
        for token in req_tokens:
            self.assertIn(token, found_tokens, f"Required abbreviation '{token}' missing from abbreviation_recognition")

    def test_abbreviation_disambiguation_meanings(self):
        disam_items = [x for x in self.data if x["category"] == "abbreviation_disambiguation"]
        meanings = {}
        for item in disam_items:
            for abbr in item["expected"]["abbreviations"]:
                meanings.setdefault(abbr["token"], []).append((item["expected"]["specialty"], abbr["full_form"]))

        # Verify MS disambiguation
        ms_meanings = [m[1] for m in meanings.get("MS", [])]
        self.assertTrue(any("Mitral Stenosis" in m for m in ms_meanings), "MS cardiac Mitral Stenosis missing")
        self.assertTrue(any("Multiple Sclerosis" in m for m in ms_meanings), "MS neuro Multiple Sclerosis missing")
        self.assertTrue(any("Morphine Sulfate" in m for m in ms_meanings), "MS pain Morphine Sulfate missing")

        # Verify PE disambiguation
        pe_meanings = [m[1] for m in meanings.get("PE", [])]
        self.assertTrue(any("Pulmonary Embolism" in m for m in pe_meanings), "PE pulm Pulmonary Embolism missing")
        self.assertTrue(any("Physical Examination" in m for m in pe_meanings), "PE general Physical Examination missing")

        # Verify RA disambiguation
        ra_meanings = [m[1] for m in meanings.get("RA", [])]
        self.assertTrue(any("Rheumatoid Arthritis" in m for m in ra_meanings), "RA rheum Rheumatoid Arthritis missing")
        self.assertTrue(any("Right Atrium" in m for m in ra_meanings), "RA cardiac Right Atrium missing")

        # Verify PT disambiguation
        pt_meanings = [m[1] for m in meanings.get("PT", [])]
        self.assertTrue(any("Physical Therapy" in m for m in pt_meanings), "PT rehab Physical Therapy missing")
        self.assertTrue(any("Prothrombin Time" in m for m in pt_meanings), "PT lab Prothrombin Time missing")

        # Verify AC prescription disambiguation
        ac_meanings = [m[1] for m in meanings.get("AC", [])]
        self.assertTrue(any("Before Meals" in m or "Ante Cibum" in m for m in ac_meanings), "AC prescription Before Meals missing")

        # Verify DC disambiguation
        dc_meanings = [m[1] for m in meanings.get("DC", [])]
        self.assertTrue(any("Discharge" in m for m in dc_meanings), "DC discharge missing")
        self.assertTrue(any("Discontinue" in m for m in dc_meanings), "DC discontinue missing")

    def test_clinical_negation_cases(self):
        neg_items = [x for x in self.data if x["category"] == "clinical_negation"]
        texts = [x["input_text"] for x in neg_items]
        
        expected_phrases = [
            ("No evidence of CAD", "Ruled Out"),
            ("PE ruled out", "Ruled Out"),
            ("Negative for RA", "Negative"),
            ("Denies HTN", "Negative"),
            ("Without CHF", "Negative"),
            ("History of T2DM", "Past History"),
            ("Suspected PE", "Suspected"),
            ("Possible DVT", "Suspected"),
            ("Normal ECG", "Normal"),
            ("Confirmed CAD", "Positive"),
            ("Monitor LDL", "Monitoring"),
            ("LDL elevated", "Elevated"),
        ]

        for phrase, status_substr in expected_phrases:
            matching = [item for item in neg_items if phrase.lower() in item["input_text"].lower()]
            self.assertTrue(len(matching) > 0, f"Missing negation phrase: '{phrase}'")
            status = matching[0]["expected"]["abbreviations"][0]["clinical_status"]
            self.assertIn(status_substr.lower(), status.lower(), f"Phrase '{phrase}' expected status containing '{status_substr}', got '{status}'")

    def test_prescription_parsing_fields_and_forms(self):
        rx_items = [x for x in self.data if x["category"] == "prescription_parsing"]
        forms = set()
        freqs = set()
        for item in rx_items:
            for med in item["expected"]["medications"]:
                self.assertIn("drug_name", med)
                self.assertIn("dosage_strength", med)
                self.assertIn("frequency_code", med)
                self.assertIn("food_timing_code", med)
                self.assertIn("form", med)
                forms.add(med["form"])
                freqs.add(med["frequency_code"])

        # Check Tab, Cap, Syr, Inhaler, Inj
        for f in ["Tab", "Cap", "Syr", "Inhaler", "Inj"]:
            self.assertIn(f, forms, f"Prescription form '{f}' missing from prescription_parsing")

        # Check OD, BD, TDS, QID, PRN, SOS
        for fq in ["OD", "BD", "TDS", "QID", "PRN", "SOS"]:
            self.assertIn(fq, freqs, f"Prescription frequency '{fq}' missing from prescription_parsing")

    def test_food_timing_codes(self):
        ft_items = [x for x in self.data if x["category"] == "food_timing"]
        codes = set()
        for item in ft_items:
            for med in item["expected"]["medications"]:
                codes.add(med["food_timing_code"])
        for c in ["AC", "PC", "CC", "HS"]:
            self.assertIn(c, codes, f"Food timing code '{c}' missing from food_timing category")

    def test_medicine_extraction_brand_names(self):
        med_items = [x for x in self.data if x["category"] == "medicine_extraction"]
        drugs = [item["expected"]["medications"][0]["drug_name"] for item in med_items]
        self.assertTrue(any("Aspirin" in d for d in drugs), "Ecosprin -> Aspirin mapping missing")
        self.assertTrue(any("Paracetamol" in d for d in drugs), "Dolo -> Paracetamol mapping missing")
        self.assertTrue(any("Salbutamol" in d for d in drugs), "Ventolin -> Salbutamol mapping missing")

    def test_route_extraction_routes(self):
        route_items = [x for x in self.data if x["category"] == "route_extraction"]
        routes = [item["expected"]["medications"][0].get("route_code") for item in route_items]
        for r in ["PO", "IV", "IM", "SC", "INH"]:
            self.assertTrue(any(r in (rt or "") for rt in routes), f"Route '{r}' missing from route_extraction")

    def test_unknown_abbreviations(self):
        unk_items = [x for x in self.data if x["category"] == "unknown_abbreviation"]
        tokens = [item["expected"]["abbreviations"][0]["token"] for item in unk_items]
        self.assertIn("XYZQ", tokens, "'XYZQ' missing from unknown_abbreviation")
        self.assertIn("BRKN", tokens, "'BRKN' missing from unknown_abbreviation")
        for item in unk_items:
            abbr = item["expected"]["abbreviations"][0]
            self.assertIsNone(abbr["full_form"], f"Unknown abbreviation {abbr['token']} should have full_form=None")

    def test_specialty_detection_specialties(self):
        spec_items = [x for x in self.data if x["category"] == "specialty_detection"]
        specs = [item["expected"]["specialty"] for item in spec_items]
        self.assertIn("Cardiology", specs, "Cardiology missing from specialty_detection")
        self.assertIn("Neurology", specs, "Neurology missing from specialty_detection")
        self.assertIn("Pulmonology", specs, "Pulmonology missing from specialty_detection")

    def test_ocr_reference_files_and_text(self):
        ocr_items = [x for x in self.data if x["category"] == "ocr_reference"]
        self.assertGreaterEqual(len(ocr_items), 5, "Must have at least 5 ocr_reference items")
        for item in ocr_items:
            img_path = item.get("ocr_image_path") or item["expected"].get("ocr_image_path")
            self.assertIsNotNone(img_path, f"Missing ocr_image_path in item {item['id']}")
            self.assertTrue(os.path.exists(img_path), f"Image file not found on disk: {img_path}")
            ref_text = item.get("ocr_reference_text") or item["expected"].get("ocr_reference_text")
            self.assertIsNotNone(ref_text, f"Missing ocr_reference_text in item {item['id']}")
            self.assertGreater(len(ref_text), 20, f"ocr_reference_text too short in item {item['id']}")

    def test_edge_cases(self):
        edge_items = [x for x in self.data if x["category"] == "edge_cases"]
        texts = [x["input_text"] for x in edge_items]
        # lowercase "ac", "bd", "tds"
        self.assertTrue(any("ac" in t.lower() and t.islower() for t in texts), "Lowercase 'ac' edge case missing")
        self.assertTrue(any("bd" in t.lower() and t.islower() for t in texts), "Lowercase 'bd' edge case missing")
        self.assertTrue(any("tds" in t.lower() and t.islower() for t in texts), "Lowercase 'tds' edge case missing")
        # CARDIAC
        cardiac_item = [x for x in edge_items if "CARDIAC" in x["input_text"]]
        self.assertTrue(len(cardiac_item) > 0, "CARDIAC edge case missing")
        self.assertEqual(len(cardiac_item[0]["expected"]["abbreviations"]), 0, "CARDIAC should not extract AC")
        # short input
        self.assertTrue(any(t in ["CAD", "HTN"] for t in texts), "Very short input edge case missing")

if __name__ == "__main__":
    unittest.main()
