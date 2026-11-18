import unittest

from backend.prescription_parser import PrescriptionInterpreter


TEST_PRESCRIPTION = (
    "Patient with HTN, T2DM, GERD, and elevated LDL is prescribed "
    "pantoprazole 40 mg PO OD AC (once daily before breakfast), "
    "metformin 500 mg PO BD PC (twice daily after breakfast and dinner), "
    "amoxicillin 500 mg PO TID PC (three times daily after meals), "
    "aspirin 81 mg PO OD PC after lunch, "
    "atorvastatin 20 mg PO QHS (at bedtime), and paracetamol 500 mg PO PRN for pain; "
    "follow up in OPD and review BP, HbA1c, and CBC. QXZ"
)


class PrescriptionInterpreterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.interpreter = PrescriptionInterpreter()

    def test_current_prescription_matches_each_instruction_to_its_medicine(self):
        result = self.interpreter.interpret(TEST_PRESCRIPTION)
        abbreviations = {item["token"]: item for item in result["abbreviations"]}
        required = {"PO", "OD", "BD", "TID", "QHS", "PRN", "AC", "PC", "LDL", "OPD", "BP", "HBA1C", "CBC", "MG", "QXZ"}
        self.assertTrue(required.issubset(abbreviations))
        self.assertTrue(abbreviations["QXZ"]["clarification_required"])

        medications = result["medications"]
        self.assertEqual(len(medications), 6)
        self.assertEqual([medication["frequency_code"] for medication in medications], ["OD", "BD", "TID", "OD", "QHS", "PRN"])
        self.assertEqual([medication["route_code"] for medication in medications], ["PO"] * 6)
        self.assertEqual(medications[0]["food_timing_instruction"], "Take before breakfast.")
        self.assertEqual(medications[1]["food_timing_instruction"], "Take after breakfast and dinner.")
        self.assertEqual(medications[2]["food_timing_instruction"], "Take after meals.")
        self.assertEqual(medications[3]["food_timing_instruction"], "Take after lunch.")
        self.assertEqual(medications[4]["food_timing_instruction"], "Take at bedtime.")
        self.assertNotIn("ai_interpretation", result)
        self.assertFalse(hasattr(self.interpreter, "ai"))

    def test_repeated_ambiguous_abbreviation_uses_each_occurrence_context(self):
        text = (
            "Cardiology: MS with mitral valve thickening and echocardiogram. "
            + "routine follow-up note; no additional findings. " * 5
            + "Neurology: MS with demyelinating lesions on MRI brain."
        )
        results = self.interpreter.interpret(text)["abbreviations"]
        ms_entries = [item for item in results if item["token"] == "MS"]

        self.assertEqual(len(ms_entries), 1)
        self.assertEqual(ms_entries[0]["occurrences"], 2)
        self.assertEqual(
            [item["meaning"] for item in ms_entries[0]["occurrence_details"]],
            ["Mitral Stenosis", "Multiple Sclerosis"],
        )

    def test_slash_form_route_is_recognized(self):
        results = self.interpreter.interpret("Insulin 10 units SC/SubQ twice daily.")["abbreviations"]
        route = next(item for item in results if item["token"] == "SC/SUBQ")
        self.assertEqual(route["meaning"], "Injected into fatty tissue under skin (e.g. insulin)")

    def test_explicit_negation_marks_abbreviation_and_removes_diagnosis(self):
        result = self.interpreter.interpret("HTN ruled out after normal blood pressure review.")
        htn = next(item for item in result["abbreviations"] if item["token"] == "HTN")
        self.assertTrue(htn["negated"])
        diagnosis = next(item for item in result["diagnoses"] if item["abbreviation"] == "HTN")
        self.assertEqual(diagnosis["clinical_status"], "Ruled Out / Not Evident")

    def test_reference_disagreement_is_reported(self):
        class ConflictingCasi:
            abbr_senses = {"MS": {"synthetic sense": 1}}

            def load(self):
                return True

            def disambiguate(self, abbreviation, text, focus_snippet=None):
                return {
                    "predicted_sense": "Unrelated CASI candidate",
                    "confidence": 52.0,
                    "matched_context_keywords": ["synthetic clue"],
                    "alternative_senses": [],
                    "casi_total_references": 1,
                    "data_source": "CASI test fixture",
                }

        interpreter = PrescriptionInterpreter(casi_engine=ConflictingCasi(), custom_kb=self.interpreter.kb)
        result = interpreter.interpret("MRI brain shows demyelinating lesions; MS noted.")
        ms = next(item for item in result["abbreviations"] if item["token"] == "MS")
        self.assertTrue(ms["model_comparison"]["disagreement"])
        self.assertEqual(ms["model_comparison"]["status"], "disagreement")

    def test_uppercase_prescription_words_are_not_flagged_as_unknown(self):
        results = self.interpreter.interpret("PATIENT TAKE TABLET ONCE DAILY BEFORE BREAKFAST WITH FOOD.")["abbreviations"]
        self.assertEqual(results, [])

    def test_six_expected_clinical_and_prescription_cases(self):
        cases = [
            "Patient denies SOB. ECG shows AF.",
            "No evidence of acute MI. EF is normal.",
            "History of HTN and AF. LVH noted on echocardiography.",
            "RBS elevated. HbA1c is elevated.",
            "Tab. Pantoprazole 40 mg PO OD AC.",
            "OD right eye examination advised.",
        ]
        results = [self.interpreter.interpret(text) for text in cases]

        first = {item["token"]: item for item in results[0]["abbreviations"]}
        self.assertEqual(first["SOB"]["meaning"], "Shortness of Breath")
        self.assertEqual(first["SOB"]["clinical_status"], "Negative / Denied")
        self.assertEqual(first["AF"]["meaning"], "Atrial Fibrillation")
        self.assertEqual(first["AF"]["clinical_status"], "Positive / Confirmed Finding")
        self.assertFalse(first["ECG"]["negated"])

        second = {item["token"]: item for item in results[1]["abbreviations"]}
        self.assertEqual(second["MI"]["meaning"], "Myocardial Infarction")
        self.assertEqual(second["MI"]["clinical_status"], "Ruled Out / Not Evident")
        self.assertEqual(second["EF"]["meaning"], "Ejection Fraction")
        self.assertEqual(second["EF"]["clinical_status"], "Normal Finding")

        third = {item["token"]: item for item in results[2]["abbreviations"]}
        self.assertEqual(third["HTN"]["clinical_status"], "Past History")
        self.assertEqual(third["AF"]["clinical_status"], "Past History")
        self.assertEqual(third["LVH"]["meaning"], "Left Ventricular Hypertrophy")
        self.assertEqual(third["LVH"]["clinical_status"], "Positive / Confirmed Finding")

        fourth = {item["token"]: item for item in results[3]["abbreviations"]}
        self.assertEqual(fourth["RBS"]["meaning"], "Random Blood Sugar")
        self.assertEqual(fourth["RBS"]["clinical_status"], "Positive Finding / Elevated")
        self.assertTrue(fourth["RBS"]["matched_keywords"])
        self.assertEqual(fourth["HBA1C"]["clinical_status"], "Positive Finding / Elevated")
        self.assertTrue(fourth["HBA1C"]["matched_keywords"])

        medication = results[4]["medications"][0]
        self.assertEqual(medication["drug_name"], "Pantoprazole")
        self.assertEqual(medication["dosage_strength"], "40 mg")
        self.assertEqual(medication["route_code"], "PO")
        self.assertEqual(medication["frequency_code"], "OD")
        self.assertEqual(medication["food_timing_code"], "AC")
        self.assertEqual(medication["food_timing_instruction"], "Take 30 to 60 minutes before food, unless the prescription specifies otherwise.")

        eye_od = results[5]["abbreviations"][0]
        self.assertEqual(eye_od["meaning"], "Right Eye (Oculus Dexter)")
        self.assertFalse(eye_od["alternative_senses"])

    def test_clause_scoped_negation_does_not_leak_across_findings(self):
        result = self.interpreter.interpret("Patient denies SOB but ECG shows AF.")
        abbreviations = {item["token"]: item for item in result["abbreviations"]}
        self.assertEqual(abbreviations["SOB"]["clinical_status"], "Negative / Denied")
        self.assertEqual(abbreviations["AF"]["clinical_status"], "Positive / Confirmed Finding")

    def test_suspected_condition_and_unrecognized_abbreviation_are_flagged(self):
        result = self.interpreter.interpret("Possible pneumonia; QXZ noted.")
        abbreviations = {item["token"]: item for item in result["abbreviations"]}
        self.assertEqual(abbreviations["PNEUMONIA"]["clinical_status"], "Suspected / Uncertain")
        self.assertTrue(abbreviations["QXZ"]["clarification_required"])
        self.assertEqual(abbreviations["QXZ"]["meaning"], "Unrecognized abbreviation")

    def test_ambiguous_od_requests_context(self):
        result = self.interpreter.interpret("OD")
        od = result["abbreviations"][0]
        self.assertEqual(od["meaning"], "Ambiguous abbreviation")
        self.assertTrue(od["clarification_required"])
        self.assertEqual({item["sense"] for item in od["alternative_senses"]}, {"Once daily", "Right Eye (Oculus Dexter)"})

    def test_medicine_name_resolves_od_even_without_dose_or_form(self):
        result = self.interpreter.interpret("Amlodipine OD")
        od = next(item for item in result["abbreviations"] if item["token"] == "OD")
        self.assertEqual(od["meaning"], "Once daily")
        self.assertFalse(od["alternative_senses"])

    def test_repeated_token_is_one_row_with_occurrence_statuses(self):
        result = self.interpreter.interpret("History of AF. ECG now shows AF.")
        af_entries = [item for item in result["abbreviations"] if item["token"] == "AF"]
        self.assertEqual(len(af_entries), 1)
        self.assertEqual(af_entries[0]["occurrences"], 2)
        self.assertEqual(
            [item["clinical_status"] for item in af_entries[0]["occurrence_details"]],
            ["Past History", "Positive / Confirmed Finding"],
        )
        summary = " ".join(result["patient_summary"])
        self.assertEqual(summary.count("AF ("), 1)
        self.assertIn("Past History", summary)
        self.assertIn("Positive / Confirmed Finding", summary)

    def test_context_disambiguates_ac_joint_from_food_code(self):
        result = self.interpreter.interpret("AC joint pain after exercise.")
        ac = next(item for item in result["abbreviations"] if item["token"] == "AC")
        self.assertEqual(ac["meaning"], "Acromioclavicular")

    def test_multiple_medicine_instructions_remain_associated(self):
        result = self.interpreter.interpret(
            "Pantoprazole 40 mg PO OD AC before breakfast; "
            "Metformin 500 mg PO BD PC after dinner."
        )
        medications = result["medications"]
        self.assertEqual(len(medications), 2)
        self.assertEqual(medications[0]["drug_name"], "Pantoprazole")
        self.assertEqual(medications[0]["food_timing_instruction"], "Take before breakfast.")
        self.assertEqual(medications[1]["drug_name"], "Metformin")
        self.assertEqual(medications[1]["food_timing_instruction"], "Take after dinner.")
        self.assertTrue(all("additional_instructions" in medication for medication in medications))

    def test_reviewed_cbc_does_not_inherit_neighboring_elevated_status(self):
        result = self.interpreter.interpret("CBC reviewed. HbA1c elevated. LDL elevated.")
        abbreviations = {item["token"]: item for item in result["abbreviations"]}
        self.assertEqual(abbreviations["CBC"]["clinical_status"], "Reviewed / Mentioned")
        self.assertEqual(abbreviations["HBA1C"]["clinical_status"], "Positive Finding / Elevated")
        self.assertEqual(abbreviations["LDL"]["clinical_status"], "Positive Finding / Elevated")
        self.assertNotIn("elevated", abbreviations["CBC"]["matched_keywords"])

    def test_history_heading_applies_to_coordinated_conditions(self):
        result = self.interpreter.interpret("History: HTN, T2DM, GERD, and CAD.")
        abbreviations = {item["token"]: item for item in result["abbreviations"]}
        for token in ["HTN", "T2DM", "GERD", "CAD"]:
            self.assertEqual(abbreviations[token]["clinical_status"], "Past History")
        diagnoses = {item["abbreviation"]: item for item in result["diagnoses"]}
        for token in ["HTN", "T2DM", "GERD", "CAD"]:
            self.assertEqual(diagnoses[token]["clinical_status"], "Past History")

    def test_repeated_bp_retains_finding_and_monitoring_statuses(self):
        result = self.interpreter.interpret("Current BP is elevated. Monitor BP regularly.")
        bp = next(item for item in result["abbreviations"] if item["token"] == "BP")
        self.assertEqual(bp["occurrences"], 2)
        self.assertEqual(
            [occurrence["clinical_status"] for occurrence in bp["occurrence_details"]],
            ["Positive Finding / Elevated", "Monitoring Instruction"],
        )

    def test_medicines_keep_different_routes_doses_and_frequencies(self):
        result = self.interpreter.interpret(
            "Pantoprazole 40 mg PO OD AC before breakfast; "
            "Salbutamol 100 mcg Inh Q6H."
        )
        medications = result["medications"]
        self.assertEqual(len(medications), 2)
        self.assertEqual(
            [(item["drug_name"], item["dosage_strength"], item["route_code"], item["frequency_code"], item["food_timing_code"]) for item in medications],
            [
                ("Pantoprazole", "40 mg", "PO", "OD", "AC"),
                ("Salbutamol (Albuterol)", "100 mcg", "INH", "Q6H", "Unspecified"),
            ],
        )


if __name__ == "__main__":
    unittest.main()