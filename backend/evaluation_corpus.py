"""Independent, reference-authored SynapRx evaluation corpus.

Expected labels are written from terminology references and explicit case text;
they are never obtained from PrescriptionInterpreter or CasiEngine.
"""

REFERENCES = {
    "SOB": ("Shortness of Breath", "Merck Manual Consumer Version: Shortness of Breath (Dyspnea)"),
    "AF": ("Atrial Fibrillation", "American Heart Association: Atrial Fibrillation"),
    "LVH": ("Left Ventricular Hypertrophy", "Mayo Clinic: Left Ventricular Hypertrophy"),
    "EF": ("Ejection Fraction", "American Heart Association: Ejection Fraction"),
    "MI": ("Myocardial Infarction", "NHLBI: Heart Attack"),
    "RBS": ("Random Blood Sugar", "MedlinePlus: Blood Glucose Test"),
    "HBA1C": ("Hemoglobin A1c", "MedlinePlus: Hemoglobin A1C Test"),
    "CBC": ("Complete Blood Count", "MedlinePlus: Complete Blood Count"),
    "LDL": ("Low-density lipoprotein", "MedlinePlus: Cholesterol Levels"),
    "BP": ("Blood Pressure", "American Heart Association: Understanding Blood Pressure Readings"),
    "HTN": ("Hypertension (High Blood Pressure)", "ACC/AHA Blood Pressure Guideline"),
    "T2DM": ("Type 2 Diabetes Mellitus", "American Diabetes Association: Standards of Care"),
    "GERD": ("Gastroesophageal Reflux Disease", "NIDDK: Acid Reflux (GER & GERD)"),
    "CAD": ("Coronary Artery Disease", "American Heart Association: Coronary Artery Disease"),
    "CAP": ("Community-Acquired Pneumonia", "ATS/IDSA: Community-Acquired Pneumonia Guideline"),
    "PNEUMONIA": ("Pneumonia", "NHLBI: Pneumonia"),
    "MS": ("Multiple Sclerosis", "National Multiple Sclerosis Society / AAN"),
    "PE": ("Pulmonary Embolism", "European Society of Cardiology: Pulmonary Embolism"),
    "ECG": ("Electrocardiogram", "Mayo Clinic: Electrocardiogram"),
    "CXR": ("Chest X-ray", "RadiologyInfo.org: Chest X-ray"),
    "MRI": ("Magnetic Resonance Imaging", "RadiologyInfo.org: MRI"),
    "OPD": ("Outpatient Department", "NHS: Outpatient appointments"),
    "PO": ("By mouth (orally)", "BNF: Prescription route abbreviations"),
    "IV": ("Intravenous", "BNF: Prescription route abbreviations"),
    "INH": ("Inhalation", "BNF: Prescription route abbreviations"),
    "OD": ("Once daily", "BNF: Prescription frequency abbreviations"),
    "BD": ("Twice a day", "BNF: Prescription frequency abbreviations"),
    "TID": ("Three times a day", "USP/BNF: Prescription frequency abbreviations"),
    "QID": ("Four times a day", "USP/BNF: Prescription frequency abbreviations"),
    "Q6H": ("Every 6 hours", "Clinical Pharmacy Standards: Interval dosing"),
    "QHS": ("Every night at bedtime", "ISMP/USP: Bedtime abbreviations"),
    "PRN": ("As needed", "Joint Commission: Medication Management Standards"),
    "AC": ("Before meals / On an empty stomach", "FDA/BNF: Ante cibum"),
    "PC": ("After meals / Following food", "FDA/BNF: Post cibum"),
    "CC": ("With food / With meals", "FDA: Cum cibo"),
    "MG": ("Milligram", "NIST: SI Units"),
    "MCG": ("Microgram", "NIST: SI Units"),
    "IU": ("International Unit", "USP: Units of biological activity"),
    "QXZ": (None, "No matching term in the local reference set; intentionally unknown"),
}


def _abbr(token, status="Mentioned / Uncertain", meaning=None, ambiguous=False, unknown=False):
    full_form, reference = REFERENCES[token]
    alternatives = []
    if ambiguous or unknown:
        full_form = None
        meaning = "Unrecognized abbreviation" if unknown else "Clarification required"
        if ambiguous:
            alternatives = {
                "AF": ["Atrial Fibrillation", "Afebrile (informal shorthand)"],
                "MI": ["Myocardial Infarction", "Mitral Insufficiency"],
                "OD": ["Once daily", "Right Eye (Oculus Dexter)"],
            }.get(token, [])
    else:
        full_form = meaning or full_form
        meaning = full_form or "Unrecognized abbreviation"
    return {
        "token": token,
        "expected_full_form": full_form,
        "expected_status": status,
        "expected_contextual_meaning": meaning,
        "contextual": token in {"SOB", "AF", "LVH", "EF", "MI", "RBS", "MS", "PE", "OD", "AC", "PC", "CAP"},
        "ambiguous": ambiguous,
        "unknown": unknown,
        "possible_meanings": alternatives,
        "expected_negation": status in {"Negative / Denied", "Ruled Out / Not Evident"},
        "reference": reference,
    }


def _med(name, dose, route, frequency, food_timing, additional=None):
    return {"medicine_name": name, "dose": dose, "route": route, "frequency": frequency,
            "food_timing": food_timing, "additional_instructions": additional or []}


def _case(case_id, split, text, abbreviations=(), medications=(), ocr_image=None, ocr_reference=None):
    return {
        "case_id": case_id,
        "split": split,
        "input_text": text,
        "expected_abbreviations": list(abbreviations),
        "expected_medications": list(medications),
        "ocr_image": ocr_image,
        "ocr_reference_text": ocr_reference,
        "manual_verification": {
            "status": "manually reviewed",
            "basis": "Expected labels were independently authored and checked against the named terminology source and the case text.",
            "clinician_adjudicated": False,
        },
    }


def _rx(case_id, text, tokens, medicine):
    return _case(case_id, "heldout", text, [_abbr(token) for token in tokens], [medicine])


CASES = [
    # Development split (20): overlaps focused rule-development tests by design.
    _case("DEV-001", "development", "CBC reviewed. HbA1c elevated. LDL elevated.", [_abbr("CBC", "Reviewed / Mentioned"), _abbr("HBA1C", "Positive Finding / Elevated"), _abbr("LDL", "Positive Finding / Elevated")]),
    _case("DEV-002", "development", "History: HTN, T2DM, GERD, and CAD.", [_abbr("HTN", "Past History"), _abbr("T2DM", "Past History"), _abbr("GERD", "Past History"), _abbr("CAD", "Past History")]),
    _case("DEV-003", "development", "Current BP is elevated. Monitor BP regularly.", [_abbr("BP", "Positive Finding / Elevated"), _abbr("BP", "Monitoring Instruction")]),
    _case("DEV-004", "development", "Patient denies SOB. ECG shows AF.", [_abbr("SOB", "Negative / Denied"), _abbr("ECG"), _abbr("AF", "Positive / Confirmed Finding")]),
    _case("DEV-005", "development", "No evidence of acute MI. EF is normal.", [_abbr("MI", "Ruled Out / Not Evident"), _abbr("EF", "Normal Finding")]),
    _case("DEV-006", "development", "Possible pneumonia; QXZ noted.", [_abbr("PNEUMONIA", "Suspected / Uncertain"), _abbr("QXZ", unknown=True)]),
    _case("DEV-007", "development", "Tab. Pantoprazole 40 mg PO OD AC before breakfast.", [_abbr(x) for x in ["MG", "PO", "OD", "AC"]], [_med("Pantoprazole", "40 mg", "PO", "OD", "AC")]),
    _case("DEV-008", "development", "OD right eye examination advised.", [_abbr("OD", meaning="Right Eye (Oculus Dexter)")]),
    _case("DEV-009", "development", "AC joint pain after exercise.", [_abbr("AC", meaning="Acromioclavicular")]),
    _case("DEV-010", "development", "Amlodipine OD.", [_abbr("OD")], [_med("Amlodipine", "Dose not specified", "Not specified", "OD", "Not specified")]),
    _case("DEV-011", "development", "AF.", [_abbr("AF", ambiguous=True)]),
    _case("DEV-012", "development", "Patient reports SOB after walking uphill.", [_abbr("SOB", "Positive / Confirmed Finding")]),
    _case("DEV-013", "development", "RBS is normal today.", [_abbr("RBS", "Normal Finding")]),
    _case("DEV-014", "development", "HTN ruled out after review.", [_abbr("HTN", "Ruled Out / Not Evident")]),
    _case("DEV-015", "development", "History of AF. Electrocardiogram now shows AF.", [_abbr("AF", "Past History"), _abbr("AF", "Positive / Confirmed Finding")]),
    _case("DEV-016", "development", "RBS reviewed after glucose testing.", [_abbr("RBS", "Reviewed / Mentioned")]),
    _case("DEV-017", "development", "No evidence of CAD, but GERD is present.", [_abbr("CAD", "Ruled Out / Not Evident"), _abbr("GERD", "Positive / Confirmed Finding")]),
    _case("DEV-018", "development", "History of HTN; denies SOB.", [_abbr("HTN", "Past History"), _abbr("SOB", "Negative / Denied")]),
    _case("DEV-019", "development", "Pantoprazole 40 mg PO OD AC before breakfast; Metformin 500 mg PO BD PC after dinner.", [_abbr(x) for x in ["MG", "PO", "OD", "AC", "BD", "PC"]], [_med("Pantoprazole", "40 mg", "PO", "OD", "AC"), _med("Metformin", "500 mg", "PO", "BD", "PC")]),
    _case("DEV-020", "development", "Possible AF on rhythm tracing; no evidence of acute MI.", [_abbr("AF", "Suspected / Uncertain"), _abbr("MI", "Ruled Out / Not Evident")]),
]

# Fifty manually authored held-out terminology/status cases, five per new target term plus existing terms.
_heldout_term_specs = [
    ("SOB", [
        ("Breathlessness appeared during stair climbing; the note records SOB.", "Positive / Confirmed Finding"),
        ("The patient denies shortness of breath (SOB) while resting.", "Negative / Denied"),
        ("Possible SOB during exertion; cause is not established.", "Suspected / Uncertain"),
        ("No signs of SOB at rest.", "Ruled Out / Not Evident"),
        ("Past history includes episodes of SOB during exercise.", "Past History"),
    ]),
    ("AF", [
        ("Irregular rhythm on electrocardiogram is documented as AF.", "Positive / Confirmed Finding"),
        ("The history of atrial fibrillation (AF) is documented in the chart.", "Past History"),
        ("Possible AF on the rhythm strip; confirmation is pending.", "Suspected / Uncertain"),
        ("AF was ruled out on the electrocardiogram.", "Ruled Out / Not Evident"),
        ("AF noted with palpitations and an irregular heartbeat.", "Positive / Confirmed Finding"),
    ]),
    ("LVH", [
        ("Echocardiography reports LVH.", "Positive / Confirmed Finding"),
        ("History of LVH is listed in the cardiology record.", "Past History"),
        ("No evidence of LVH on the heart ultrasound.", "Ruled Out / Not Evident"),
        ("Possible LVH based on electrocardiogram findings.", "Suspected / Uncertain"),
        ("LVH.", "Mentioned / Uncertain"),
    ]),
    ("EF", [
        ("Echocardiogram measured EF at 60 percent.", "Positive / Confirmed Finding"),
        ("EF is normal on the cardiac ultrasound.", "Normal Finding"),
        ("Reduced EF is documented in the heart failure report.", "Reduced / Low Finding"),
        ("Ejection fraction (EF) was measured during imaging.", "Mentioned / Uncertain"),
        ("EF.", "Mentioned / Uncertain"),
    ]),
    ("MI", [
        ("Troponin and electrocardiogram confirm acute MI.", "Positive / Confirmed Finding"),
        ("History of MI is recorded in the chart.", "Past History"),
        ("Possible MI with chest discomfort; workup is pending.", "Suspected / Uncertain"),
        ("MI ruled out after serial testing.", "Ruled Out / Not Evident"),
        ("MI. OD. AF.", "Ambiguous"),
    ]),
    ("RBS", [
        ("Random blood sugar (RBS) is elevated after lunch.", "Positive Finding / Elevated"),
        ("RBS normal on repeat testing.", "Normal Finding"),
        ("Random glucose (RBS) checked during the visit.", "Reviewed / Mentioned"),
        ("Repeat RBS tomorrow for monitoring.", "Monitoring Instruction"),
        ("RBS elevated during today's diabetes check.", "Positive Finding / Elevated"),
    ]),
    ("HTN", [("Blood pressure history includes HTN.", "Past History"), ("No evidence of HTN after evaluation.", "Ruled Out / Not Evident")]),
    ("T2DM", [("History of T2DM with regular glucose monitoring.", "Past History"), ("T2DM is confirmed in the assessment.", "Positive / Confirmed Finding")]),
    ("CAD", [("CAD noted after coronary imaging.", "Positive / Confirmed Finding"), ("Past history of CAD and prior stent placement.", "Past History")]),
    ("GERD", [("GERD symptoms are present after meals.", "Positive / Confirmed Finding")]),
    ("CAP", [("Possible CAP based on cough and fever.", "Suspected / Uncertain")]),
    ("MS", [("MRI brain shows demyelinating lesions in MS.", "Multiple Sclerosis"), ("Echocardiography shows a thickened mitral valve with MS.", "Mitral Stenosis")]),
    ("PE", [("CTA chest confirms pulmonary embolism (PE).", "Pulmonary Embolism"), ("PE: physical examination shows normal heart, lungs, abdomen, and extremities.", "Physical Examination")]),
    ("HBA1C", [("HbA1c reviewed during diabetes follow-up.", "Reviewed / Mentioned"), ("HbA1c elevated after three months of monitoring.", "Positive Finding / Elevated")]),
    ("CBC", [("CBC reviewed by the clinician.", "Reviewed / Mentioned"), ("CBC normal on today's laboratory report.", "Normal Finding")]),
    ("LDL", [("LDL elevated on the lipid panel.", "Positive Finding / Elevated"), ("LDL normal at follow-up.", "Normal Finding")]),
    ("BP", [("Blood pressure (BP) checked today.", "Reviewed / Mentioned"), ("Monitor BP at home and record every reading.", "Monitoring Instruction")]),
]

_holdout_number = 21
for _token, _cases in _heldout_term_specs:
    for _text, _status_or_meaning in _cases:
        if _token == "MI" and _text == "MI. OD. AF.":
            _expected = _abbr("MI", ambiguous=True)
            _extra = [_abbr("OD", ambiguous=True), _abbr("AF", ambiguous=True)]
        elif _token == "MI" and _status_or_meaning == "Ambiguous":
            _expected = _abbr("MI", ambiguous=True)
            _extra = []
        elif _token in {"MS", "PE"}:
            _expected = _abbr(_token, meaning=_status_or_meaning)
            _extra = []
        else:
            _expected = _abbr(_token, _status_or_meaning)
            _extra = []
        CASES.append(_case(f"HOLD-{_holdout_number:03}", "heldout", _text, [_expected] + _extra))
        _holdout_number += 1

# Twenty held-out prescription orders with field-level, medicine-specific labels.
_prescriptions = [
    ("Pantoprazole 40 mg PO OD AC before breakfast.", ["MG", "PO", "OD", "AC"], _med("Pantoprazole", "40 mg", "PO", "OD", "AC")),
    ("Omeprazole 20 mg PO OD AC before breakfast.", ["MG", "PO", "OD", "AC"], _med("Omeprazole", "20 mg", "PO", "OD", "AC")),
    ("Levothyroxine 50 mcg PO OD AC before breakfast.", ["MCG", "PO", "OD", "AC"], _med("Levothyroxine", "50 mcg", "PO", "OD", "AC")),
    ("Metformin 500 mg PO BD PC after breakfast.", ["MG", "PO", "BD", "PC"], _med("Metformin", "500 mg", "PO", "BD", "PC")),
    ("Metformin 1000 mg PO BD PC after dinner.", ["MG", "PO", "BD", "PC"], _med("Metformin", "1000 mg", "PO", "BD", "PC")),
    ("Augmentin 625 mg PO TID PC after meals.", ["MG", "PO", "TID", "PC"], _med("Amoxicillin and Clavulanate Potassium", "625 mg", "PO", "TID", "PC")),
    ("Paracetamol 500 mg PO PRN for pain.", ["MG", "PO", "PRN"], _med("Paracetamol (Acetaminophen)", "500 mg", "PO", "PRN", "Unspecified", ["PRN for pain"])),
    ("Aspirin 81 mg PO OD PC after lunch.", ["MG", "PO", "OD", "PC"], _med("Aspirin (Acetylsalicylic Acid)", "81 mg", "PO", "OD", "PC")),
    ("Atorvastatin 20 mg PO QHS at bedtime.", ["MG", "PO", "QHS"], _med("Atorvastatin", "20 mg", "PO", "QHS", "HS")),
    ("Amlodipine 5 mg PO OD.", ["MG", "PO", "OD"], _med("Amlodipine", "5 mg", "PO", "OD", "Unspecified")),
    ("Salbutamol 100 mcg Inh Q6H.", ["MCG", "INH", "Q6H"], _med("Salbutamol (Albuterol)", "100 mcg", "INH", "Q6H", "Unspecified")),
    ("Pregabalin 75 mg PO QHS at bedtime.", ["MG", "PO", "QHS"], _med("Pregabalin", "75 mg", "PO", "QHS", "HS")),
    ("Baclofen 10 mg PO BD PC after breakfast and dinner.", ["MG", "PO", "BD", "PC"], _med("Baclofen", "10 mg", "PO", "BD", "PC")),
    ("Methylprednisolone 4 mg PO OD PC after breakfast.", ["MG", "PO", "OD", "PC"], _med("Methylprednisolone", "4 mg", "PO", "OD", "PC")),
    ("Pantoprazole 20 mg PO OD AC, 30 minutes before food.", ["MG", "PO", "OD", "AC"], _med("Pantoprazole", "20 mg", "PO", "OD", "AC")),
    ("Aspirin 75 mg PO OD PC after food.", ["MG", "PO", "OD", "PC"], _med("Aspirin (Acetylsalicylic Acid)", "75 mg", "PO", "OD", "PC")),
    ("Salbutamol 2 puffs Inh QID PRN for wheezing.", ["INH", "QID", "PRN"], _med("Salbutamol (Albuterol)", "2 puffs", "INH", "QID", "Unspecified", ["PRN for wheezing"])),
    ("Tab Diclofenac 50 mg PO BD PC after meals.", ["MG", "PO", "BD", "PC"], _med("Diclofenac", "50 mg", "PO", "BD", "PC")),
    ("Tab Vitamin D3 1000 IU PO OD CC with food.", ["IU", "PO", "OD", "CC"], _med("Vitamin D3", "1000 IU", "PO", "OD", "CC")),
    ("Inj Ceftriaxone 1 g IV OD.", ["IV", "OD"], _med("Ceftriaxone", "1 g", "IV", "OD", "Unspecified")),
]
for _text, _tokens, _expected_medication in _prescriptions:
    _expected_abbreviations = [_abbr(token) for token in _tokens]
    if _expected_medication["dose"]:
        unit = "MCG" if "mcg" in _expected_medication["dose"].lower() else "MG" if "mg" in _expected_medication["dose"].lower() else "ML" if "ml" in _expected_medication["dose"].lower() else "IU" if "iu" in _expected_medication["dose"].lower() else None
        if unit and unit not in _tokens:
            _expected_abbreviations.append(_abbr(unit))
    CASES.append(_case(f"HOLD-{_holdout_number:03}", "heldout", _text, _expected_abbreviations, [_expected_medication]))
    _holdout_number += 1

_mixed_cases = [
    ("No evidence of CAD; history of HTN.", [_abbr("CAD", "Ruled Out / Not Evident"), _abbr("HTN", "Past History")]),
    ("Possible MI but electrocardiogram shows AF.", [_abbr("MI", "Suspected / Uncertain"), _abbr("AF", "Positive / Confirmed Finding")]),
    ("Current BP elevated; monitor BP every morning.", [_abbr("BP", "Positive Finding / Elevated"), _abbr("BP", "Monitoring Instruction")]),
    ("History of HTN. Possible T2DM.", [_abbr("HTN", "Past History"), _abbr("T2DM", "Suspected / Uncertain")]),
    ("AC joint pain; Pantoprazole 40 mg PO OD AC before breakfast.", [_abbr("AC", meaning="Acromioclavicular"), _abbr("MG"), _abbr("PO"), _abbr("OD"), _abbr("AC", meaning="Before meals / On an empty stomach")]),
    ("OD right eye; Pantoprazole 40 mg PO OD AC.", [_abbr("OD", meaning="Right Eye (Oculus Dexter)"), _abbr("MG"), _abbr("PO"), _abbr("OD"), _abbr("AC")]),
    ("Possible CAP with SOB; no evidence of PE. QXZ noted.", [_abbr("CAP", "Suspected / Uncertain"), _abbr("SOB", "Positive / Confirmed Finding"), _abbr("PE", "Ruled Out / Not Evident"), _abbr("QXZ", unknown=True)]),
]
for _text, _expected in _mixed_cases:
    _medications = []
    if "Pantoprazole" in _text:
        _medications = [_med("Pantoprazole", "40 mg", "PO", "OD", "AC")]
    CASES.append(_case(f"HOLD-{_holdout_number:03}", "heldout", _text, _expected, _medications))
    _holdout_number += 1

_ocr_references = [
    ("samples/sample1_cardio_diabetic.png", "METRO HEART & METABOLIC CARE CENTER\nDr. Sarah Mitchell, MD, FACC\nSenior Consultant Interventional Cardiologist & Diabetologist | Reg. #74921\nPATIENT: Mr. Robert Sterling, 58 Yrs / Male\nDATE: 12-Nov-2026\nOPD REG: #MED-2026-9481\nCLINICAL DIAGNOSIS / INDICATION: CAD (Status Post PTCA), T2DM, Essential HTN, Dyslipidemia\n1. Tab Pantoprazole 40 mg\nSig: 1 tab OD AC (Ante Cibum) | Frequency: Once daily | Timing: 30 mins Before Breakfast\nDuration: 30 days (Indication: Acid peptic prophylaxis)\n2. Tab Metformin HCl 500 mg\nSig: 1 tab BD PC (Post Cibum) | Frequency: Twice daily | Timing: Immediately After Meals\nDuration: 30 days (Indication: Glycemic control in T2DM)\n3. Tab Atorvastatin 20 mg\nSig: 1 tab QHS (Hora Somni) | Frequency: Once daily | Timing: At Bedtime\nDuration: 30 days (Indication: Lipid lowering & plaque stabilization)\n4. Tab Amlodipine 5 mg\nSig: 1 tab OD (Omni Die) | Frequency: Once daily | Timing: Morning After Food\nDuration: 30 days (Indication: Blood pressure management)\n5. Tab Aspirin (Ecosprin) 75 mg\nSig: 1 tab OD PC | Frequency: Once daily | Timing: After Lunch\nDuration: 30 days (Indication: Antiplatelet therapy)\nCLINICAL FINDINGS & INVESTIGATION SUMMARY:\n1. 2D Echo report: Mild LA dilation, EF 52%. Mitral valve leaflets normal; MS ruled out.\n2. ECG: Normal sinus rhythm, rate 74/min. No acute ST-T ischemic changes.\n3. Patient advised strict diabetic diet, low sodium intake, and regular BP/SMBG monitoring.\nImportant: Take medications strictly as scheduled. Do not substitute without physician authorization.\nEmergency Contact: 24/7 Helpline: 1800-MED-CARE | Next Review: After 4 weeks\nDr. Sarah Mitchell\nAuthorized Medical Practitioner"),
    ("samples/sample2_pulmonology_infection.png", "APEX PULMONARY & CRITICAL CARE CLINIC\nDr. Rajesh Patel, MD, FCCP\nConsultant Pulmonologist & Sleep Specialist | Reg. #58319\nPATIENT: Ms. Emily Watson, 42 Yrs / Female\nDATE: 14-Nov-2026\nOPD REG: #MED-2026-9481\nCLINICAL DIAGNOSIS / INDICATION: Community Acquired Pneumonia (CAP), Bronchial Asthma Exacerbation\n1. Tab Augmentin 625 mg (Amoxicillin + Clav)\nSig: 1 tab TID PC | Frequency: Three times a day | Timing: After Meals\nDuration: 7 days (Indication: Bacterial respiratory infection)\n2. Inhaler Salbutamol 100 mcg (Ventolin)\nSig: 2 puffs QID PRN | Frequency: Four times a day / As needed | Timing: When breathless or wheezing\nDuration: 14 days (Indication: Acute bronchospasm rescue)\n3. Tab Paracetamol (Dolo) 650 mg\nSig: 1 tab SOS / PRN | Frequency: As needed (max 3 tabs/day) | Timing: After food for fever > 100Â°F or bodyache\nDuration: 5 days (Indication: Fever & myalgia relief)\n4. Syr Ambroxol + Guaiphenesin 10 ml\nSig: 10 ml TID PC | Frequency: Three times a day | Timing: After Food with warm water\nDuration: 7 days (Indication: Productive cough & mucolysis)\nCLINICAL FINDINGS & INVESTIGATION SUMMARY:\n1. CXR PA view shows right lower zone patchy consolidation. No pleural effusion.\n2. CTA Chest performed in ER: Pulmonary Embolism (PE) ruled out.\n3. Spirometry: FEV1/FVC ratio 0.68, reversible with bronchodilator. Steam inhalation TID.\nImportant: Take medications strictly as scheduled. Do not substitute without physician authorization.\nEmergency Contact: 24/7 Helpline: 1800-MED-CARE | Next Review: After 4 weeks\nDr. Rajesh Patel\nAuthorized Medical Practitioner"),
    ("samples/sample3_neurology_ms_clinic.png", "UNIVERSITY NEUROSCIENCE INSTITUTE\nDr. Anthony Rossi, MD, FAAN\nProfessor & Chief of Clinical Neuroimmunology | Reg. #88102\nPATIENT: Mrs. Laura Chen, 36 Yrs / Female\nDATE: 15-Nov-2026\nOPD REG: #MED-2026-9481\nCLINICAL DIAGNOSIS / INDICATION: Relapsing-Remitting Multiple Sclerosis (MS), Neuropathic Dysesthesia\n1. Cap Pregabalin 75 mg\nSig: 1 cap QHS | Frequency: Once daily at bedtime | Timing: 30 mins before sleep\nDuration: 30 days (Indication: Neuropathic pain & paresthesias)\n2. Tab Baclofen 10 mg\nSig: 1 tab BD PC | Frequency: Twice daily | Timing: After Morning & Evening meals\nDuration: 30 days (Indication: Lower extremity spasticity)\n3. Cap Vitamin D3 60,000 IU\nSig: 1 cap QWK (Once Weekly) | Frequency: Once weekly | Timing: With fatty meal on Sundays\nDuration: 8 weeks (Indication: Hypovitaminosis D in MS)\n4. Tab Methylprednisolone 4 mg\nSig: Tapering schedule as directed | Frequency: As per written plan | Timing: Morning after breakfast with milk\nDuration: 10 days (Indication: Post-relapse maintenance)\nCLINICAL FINDINGS & INVESTIGATION SUMMARY:\n1. MS Clinic Follow-up: EDSS score stable at 2.0. Patient reports reduced sensory tingling.\n2. Recent 3T MRI Brain & Cervical Spine: Stable demyelinating lesions without active Gd-enhancement.\n3. Mental Status (MS) exam: Intact cognition, MoCA score 29/30. Continue physiotherapy.\nImportant: Take medications strictly as scheduled. Do not substitute without physician authorization.\nEmergency Contact: 24/7 Helpline: 1800-MED-CARE | Next Review: After 4 weeks\nDr. Anthony Rossi\nAuthorized Medical Practitioner"),
]
for _image, _transcription in _ocr_references:
    CASES.append(_case(f"OCR-{_holdout_number:03}", "heldout", "", ocr_image=_image, ocr_reference=_transcription))
    _holdout_number += 1

if len(CASES) != 100 or _holdout_number != 101:
    raise RuntimeError(f"Evaluation ground truth must contain exactly 100 cases, got {len(CASES)}")
if sum(item["split"] == "development" for item in CASES) != 20:
    raise RuntimeError("Development split must contain 20 cases")
if sum(item["split"] == "heldout" for item in CASES) != 80:
    raise RuntimeError("Held-out split must contain 80 cases")

