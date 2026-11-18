"""
Script to generate data/evaluation/ground_truth.json for SynapRx.
Contains 130 clinically accurate test examples split into development (40) and heldout (90).
"""

import os
import json

def build_dataset():
    examples = []
    current_id = 1

    def add_case(split, category, input_text, abbreviations, medications, specialty, negation, notes, ocr_image_path=None, ocr_reference_text=None):
        nonlocal current_id
        case_id = f"EVAL_{current_id:03d}"
        current_id += 1
        
        expected = {
            "abbreviations": abbreviations,
            "medications": medications,
            "specialty": specialty,
            "negation": negation,
        }
        if ocr_image_path is not None:
            expected["ocr_image_path"] = ocr_image_path
        if ocr_reference_text is not None:
            expected["ocr_reference_text"] = ocr_reference_text

        item = {
            "id": case_id,
            "split": split,
            "category": category,
            "input_text": input_text,
            "expected": expected,
            "notes": notes
        }
        if ocr_image_path is not None:
            item["ocr_image_path"] = ocr_image_path
        if ocr_reference_text is not None:
            item["ocr_reference_text"] = ocr_reference_text

        examples.append(item)

    # =========================================================================
    # CATEGORY 1: abbreviation_recognition (16 examples: 5 dev, 11 heldout)
    # Required tokens: CAD, T2DM, HTN, COPD, CHF, CVA, DVT, PE, CKD, GERD, CAP, TIA, SLE, DKA (+ AFIB, BPH)
    # =========================================================================

    add_case(
        split="development",
        category="abbreviation_recognition",
        input_text="Patient diagnosed with CAD after cardiac catheterization.",
        abbreviations=[{"token": "CAD", "full_form": "Coronary Artery Disease", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Cardiology",
        negation=False,
        notes="Recognition of CAD in standard cardiology diagnosis context."
    )
    add_case(
        split="development",
        category="abbreviation_recognition",
        input_text="Poor glycemic control in a patient with longstanding T2DM.",
        abbreviations=[{"token": "T2DM", "full_form": "Type 2 Diabetes Mellitus", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Endocrinology / Diabetology",
        negation=False,
        notes="Recognition of T2DM in endocrinology context."
    )
    add_case(
        split="development",
        category="abbreviation_recognition",
        input_text="Patient has essential HTN managed with calcium channel blockers.",
        abbreviations=[{"token": "HTN", "full_form": "Hypertension (High Blood Pressure)", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Cardiology",
        negation=False,
        notes="Recognition of HTN in hypertension management context."
    )
    add_case(
        split="development",
        category="abbreviation_recognition",
        input_text="Spirometry demonstrates severe airflow limitation consistent with COPD.",
        abbreviations=[{"token": "COPD", "full_form": "Chronic Obstructive Pulmonary Disease", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Pulmonology",
        negation=False,
        notes="Recognition of COPD with obstructive spirometry context."
    )
    add_case(
        split="development",
        category="abbreviation_recognition",
        input_text="Echocardiogram reveals reduced ejection fraction and signs of CHF.",
        abbreviations=[{"token": "CHF", "full_form": "Congestive Heart Failure", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Cardiology",
        negation=False,
        notes="Recognition of CHF in heart failure presentation."
    )
    add_case(
        split="heldout",
        category="abbreviation_recognition",
        input_text="Patient admitted to acute stroke unit following an ischemic CVA.",
        abbreviations=[{"token": "CVA", "full_form": "Cerebrovascular Accident (Stroke)", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Neurology",
        negation=False,
        notes="Recognition of CVA in acute stroke context."
    )
    add_case(
        split="heldout",
        category="abbreviation_recognition",
        input_text="Compression ultrasonography confirmed acute proximal DVT in the left femoral vein.",
        abbreviations=[{"token": "DVT", "full_form": "Deep Vein Thrombosis", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Cardiology",
        negation=False,
        notes="Recognition of DVT confirmed on venous ultrasound."
    )
    add_case(
        split="heldout",
        category="abbreviation_recognition",
        input_text="CTA chest revealed acute bilateral segmental PE.",
        abbreviations=[{"token": "PE", "full_form": "Pulmonary Embolism", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Pulmonology",
        negation=False,
        notes="Recognition of PE on thoracic computed tomography angiogram."
    )
    add_case(
        split="heldout",
        category="abbreviation_recognition",
        input_text="Elevated serum creatinine and persistent albuminuria indicating stage 3 CKD.",
        abbreviations=[{"token": "CKD", "full_form": "Chronic Kidney Disease", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Nephrology",
        negation=False,
        notes="Recognition of CKD with renal impairment markers."
    )
    add_case(
        split="heldout",
        category="abbreviation_recognition",
        input_text="Endoscopy reveals reflux esophagitis consistent with chronic GERD.",
        abbreviations=[{"token": "GERD", "full_form": "Gastroesophageal Reflux Disease", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Gastroenterology",
        negation=False,
        notes="Recognition of GERD confirmed by endoscopic findings."
    )
    add_case(
        split="heldout",
        category="abbreviation_recognition",
        input_text="Chest radiograph showed right lower lobe consolidation consistent with CAP.",
        abbreviations=[{"token": "CAP", "full_form": "Community-Acquired Pneumonia", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Pulmonology",
        negation=False,
        notes="Recognition of CAP with classic radiographic consolidation."
    )
    add_case(
        split="heldout",
        category="abbreviation_recognition",
        input_text="Transient right-sided weakness lasting 20 minutes suspicious for acute TIA.",
        abbreviations=[{"token": "TIA", "full_form": "Transient Ischemic Attack", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Neurology",
        negation=False,
        notes="Recognition of TIA in transient neurological deficit."
    )
    add_case(
        split="heldout",
        category="abbreviation_recognition",
        input_text="Positive ANA and anti-dsDNA titers confirmed systemic diagnosis of SLE.",
        abbreviations=[{"token": "SLE", "full_form": "Systemic Lupus Erythematosus", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Rheumatology",
        negation=False,
        notes="Recognition of SLE supported by autoimmune serology."
    )
    add_case(
        split="heldout",
        category="abbreviation_recognition",
        input_text="Arterial blood gas showed metabolic acidosis and ketonemia in acute DKA.",
        abbreviations=[{"token": "DKA", "full_form": "Diabetic Ketoacidosis", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Endocrinology / Diabetology",
        negation=False,
        notes="Recognition of DKA with severe acid-base disturbance."
    )
    add_case(
        split="heldout",
        category="abbreviation_recognition",
        input_text="12-lead ECG demonstrates irregularly irregular rhythm confirming AFIB.",
        abbreviations=[{"token": "AFIB", "full_form": "Atrial Fibrillation", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Cardiology",
        negation=False,
        notes="Recognition of AFIB on electrocardiographic rhythm strip."
    )
    add_case(
        split="heldout",
        category="abbreviation_recognition",
        input_text="Urologic evaluation reveals significant bladder outlet obstruction secondary to BPH.",
        abbreviations=[{"token": "BPH", "full_form": "Benign Prostatic Hyperplasia", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="General Medicine",
        negation=False,
        notes="Recognition of BPH in urological symptom presentation."
    )

    # =========================================================================
    # CATEGORY 2: abbreviation_disambiguation (16 examples: 5 dev, 11 heldout)
    # Required: MS cardiac, MS neuro, MS pain, PE pulm, PE general, RA rheum,
    #           RA cardiac, PT rehab, PT lab, AC prescription, DC discharge, DC discontinue
    # Extras: AC joint, PC prescription, CA oncology, CA cardiology
    # =========================================================================

    add_case(
        split="development",
        category="abbreviation_disambiguation",
        input_text="Echocardiogram reveals severe rheumatic MS with a thickened mitral valve and diastolic murmur.",
        abbreviations=[{"token": "MS", "full_form": "Mitral Stenosis", "category": "Cardiology", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Cardiology",
        negation=False,
        notes="Disambiguation: MS in cardiac valvular context resolves to Mitral Stenosis."
    )
    add_case(
        split="development",
        category="abbreviation_disambiguation",
        input_text="Brain MRI demonstrates periventricular demyelinating plaques characteristic of MS.",
        abbreviations=[{"token": "MS", "full_form": "Multiple Sclerosis", "category": "Neurology", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Neurology",
        negation=False,
        notes="Disambiguation: MS in neuro demyelinating context resolves to Multiple Sclerosis."
    )
    add_case(
        split="development",
        category="abbreviation_disambiguation",
        input_text="Administer MS 10mg IV STAT for acute severe breakthrough cancer pain.",
        abbreviations=[{"token": "MS", "full_form": "Morphine Sulfate", "category": "Pharmacology / Palliative Care", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="General Medicine",
        negation=False,
        notes="Disambiguation: MS with dosage and IV route resolves to Morphine Sulfate."
    )
    add_case(
        split="development",
        category="abbreviation_disambiguation",
        input_text="CTA chest confirms acute segmental PE with right heart strain.",
        abbreviations=[{"token": "PE", "full_form": "Pulmonary Embolism", "category": "Pulmonology", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Pulmonology",
        negation=False,
        notes="Disambiguation: PE in chest imaging context resolves to Pulmonary Embolism."
    )
    add_case(
        split="development",
        category="abbreviation_disambiguation",
        input_text="General PE: alert, oriented, clear breath sounds, abdomen soft and non-tender.",
        abbreviations=[{"token": "PE", "full_form": "Physical Examination", "category": "General Medicine", "clinical_status": "Normal Finding"}],
        medications=[],
        specialty="General Medicine",
        negation=False,
        notes="Disambiguation: PE heading prior to clinical signs resolves to Physical Examination."
    )
    add_case(
        split="heldout",
        category="abbreviation_disambiguation",
        input_text="Patient presents with symmetrical MCP synovitis and positive RF confirming RA.",
        abbreviations=[{"token": "RA", "full_form": "Rheumatoid Arthritis", "category": "Rheumatology", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Rheumatology",
        negation=False,
        notes="Disambiguation: RA with synovitis and RF resolves to Rheumatoid Arthritis."
    )
    add_case(
        split="heldout",
        category="abbreviation_disambiguation",
        input_text="Echocardiography shows severe enlargement of the RA and tricuspid regurgitation.",
        abbreviations=[{"token": "RA", "full_form": "Right Atrium", "category": "Cardiology", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Cardiology",
        negation=False,
        notes="Disambiguation: RA in cardiac chamber imaging resolves to Right Atrium."
    )
    add_case(
        split="heldout",
        category="abbreviation_disambiguation",
        input_text="Referred for outpatient PT 3 times weekly for stroke gait rehabilitation.",
        abbreviations=[{"token": "PT", "full_form": "Physical Therapy", "category": "Rehabilitation / Physical Medicine", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="General Medicine",
        negation=False,
        notes="Disambiguation: PT in rehabilitation context resolves to Physical Therapy."
    )
    add_case(
        split="heldout",
        category="abbreviation_disambiguation",
        input_text="Coagulation monitoring reveals an elevated PT of 24.5 seconds on warfarin.",
        abbreviations=[{"token": "PT", "full_form": "Prothrombin Time", "category": "Laboratory / Hematology", "clinical_status": "Positive Finding / Elevated"}],
        medications=[],
        specialty="General Medicine",
        negation=False,
        notes="Disambiguation: PT in coagulation lab panel resolves to Prothrombin Time."
    )
    add_case(
        split="heldout",
        category="abbreviation_disambiguation",
        input_text="Tab Pantoprazole 40mg OD AC taken 30 minutes before breakfast.",
        abbreviations=[{"token": "AC", "full_form": "Ante Cibum (Before Meals)", "category": "Prescription Shorthand", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[{"drug_name": "Pantoprazole", "dosage_strength": "40mg", "frequency_code": "OD", "food_timing_code": "AC", "form": "Tab"}],
        specialty="Gastroenterology",
        negation=False,
        notes="Disambiguation: AC in prescription frequency resolves to Before Meals (Ante Cibum)."
    )
    add_case(
        split="heldout",
        category="abbreviation_disambiguation",
        input_text="Patient is clinically stable, afebrile, and authorized for DC to home tomorrow morning.",
        abbreviations=[{"token": "DC", "full_form": "Discharge", "category": "Administrative / Care Plan", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="General Medicine",
        negation=False,
        notes="Disambiguation: DC regarding leaving hospital resolves to Discharge."
    )
    add_case(
        split="heldout",
        category="abbreviation_disambiguation",
        input_text="Due to acute elevation in serum creatinine, DC metformin immediately.",
        abbreviations=[{"token": "DC", "full_form": "Discontinue", "category": "Medication Order", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Nephrology",
        negation=False,
        notes="Disambiguation: DC applied to an active drug order resolves to Discontinue."
    )
    add_case(
        split="heldout",
        category="abbreviation_disambiguation",
        input_text="Tenderness and joint space widening localized to the left AC joint after trauma.",
        abbreviations=[{"token": "AC", "full_form": "Acromioclavicular", "category": "Orthopedics / Anatomy", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="General Medicine",
        negation=False,
        notes="Disambiguation: AC joint anatomical reference resolves to Acromioclavicular."
    )
    add_case(
        split="heldout",
        category="abbreviation_disambiguation",
        input_text="Tab Metformin 500mg PO BD PC taken immediately following morning and evening meals.",
        abbreviations=[{"token": "PC", "full_form": "Post Cibum (After Meals)", "category": "Prescription Shorthand", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[{"drug_name": "Metformin", "dosage_strength": "500mg", "frequency_code": "BD", "food_timing_code": "PC", "form": "Tab"}],
        specialty="Endocrinology / Diabetology",
        negation=False,
        notes="Disambiguation: PC in prescription context resolves to After Meals (Post Cibum)."
    )
    add_case(
        split="heldout",
        category="abbreviation_disambiguation",
        input_text="Biopsy confirmed metastatic colon CA with secondary hepatic metastases.",
        abbreviations=[{"token": "CA", "full_form": "Cancer / Carcinoma", "category": "Oncology", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Gastroenterology",
        negation=False,
        notes="Disambiguation: CA in biopsy/metastasis context resolves to Cancer / Carcinoma."
    )
    add_case(
        split="heldout",
        category="abbreviation_disambiguation",
        input_text="Coronary angiography demonstrated high-grade stenosis of the left main CA.",
        abbreviations=[{"token": "CA", "full_form": "Coronary Artery", "category": "Cardiology", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Cardiology",
        negation=False,
        notes="Disambiguation: CA in angiography context resolves to Coronary Artery."
    )

    # =========================================================================
    # CATEGORY 3: clinical_negation (13 examples: 4 dev, 9 heldout)
    # Required: "No evidence of CAD", "PE ruled out", "Negative for RA", "Denies HTN",
    #           "Without CHF", "History of T2DM", "Suspected PE", "Possible DVT",
    #           "Normal ECG", "Confirmed CAD", "Monitor LDL", "LDL elevated", (+ "No signs of COPD")
    # =========================================================================

    add_case(
        split="development",
        category="clinical_negation",
        input_text="Coronary catheterization showed patent vessels with no evidence of CAD.",
        abbreviations=[{"token": "CAD", "full_form": "Coronary Artery Disease", "category": "Disease / Diagnosis", "clinical_status": "Ruled Out / Not Evident"}],
        medications=[],
        specialty="Cardiology",
        negation=True,
        notes="'No evidence of CAD' indicates disease has been definitively ruled out."
    )
    add_case(
        split="development",
        category="clinical_negation",
        input_text="D-dimer within normal limits and acute PE ruled out on contrast CTA.",
        abbreviations=[{"token": "PE", "full_form": "Pulmonary Embolism", "category": "Disease / Diagnosis", "clinical_status": "Ruled Out / Not Evident"}],
        medications=[],
        specialty="Pulmonology",
        negation=True,
        notes="'PE ruled out' classifies status as Ruled Out / Not Evident."
    )
    add_case(
        split="development",
        category="clinical_negation",
        input_text="Autoimmune panel and rheumatoid factor were negative for RA.",
        abbreviations=[{"token": "RA", "full_form": "Rheumatoid Arthritis", "category": "Disease / Diagnosis", "clinical_status": "Negative / Denied"}],
        medications=[],
        specialty="Rheumatology",
        negation=True,
        notes="'Negative for RA' represents laboratory negation."
    )
    add_case(
        split="development",
        category="clinical_negation",
        input_text="Patient has normal blood pressure readings and denies HTN during intake.",
        abbreviations=[{"token": "HTN", "full_form": "Hypertension (High Blood Pressure)", "category": "Disease / Diagnosis", "clinical_status": "Negative / Denied"}],
        medications=[],
        specialty="Cardiology",
        negation=True,
        notes="'Denies HTN' represents patient-reported symptom/condition negation."
    )
    add_case(
        split="heldout",
        category="clinical_negation",
        input_text="Transthoracic echocardiogram demonstrates normal ventricular function without CHF.",
        abbreviations=[{"token": "CHF", "full_form": "Congestive Heart Failure", "category": "Disease / Diagnosis", "clinical_status": "Negative / Denied"}],
        medications=[],
        specialty="Cardiology",
        negation=True,
        notes="'Without CHF' demonstrates absence of heart failure signs."
    )
    add_case(
        split="heldout",
        category="clinical_negation",
        input_text="Chart review confirms a 10-year past medical history of T2DM on oral therapy.",
        abbreviations=[{"token": "T2DM", "full_form": "Type 2 Diabetes Mellitus", "category": "Disease / Diagnosis", "clinical_status": "Past History"}],
        medications=[],
        specialty="Endocrinology / Diabetology",
        negation=False,
        notes="'History of T2DM' classifies condition status as Past History."
    )
    add_case(
        split="heldout",
        category="clinical_negation",
        input_text="Patient presents with acute pleurisy and hypoxemia with suspected PE.",
        abbreviations=[{"token": "PE", "full_form": "Pulmonary Embolism", "category": "Disease / Diagnosis", "clinical_status": "Suspected / Uncertain"}],
        medications=[],
        specialty="Pulmonology",
        negation=False,
        notes="'Suspected PE' indicates diagnostic uncertainty awaiting confirmation."
    )
    add_case(
        split="heldout",
        category="clinical_negation",
        input_text="Unilateral right lower extremity edema and tenderness raise concern for possible DVT.",
        abbreviations=[{"token": "DVT", "full_form": "Deep Vein Thrombosis", "category": "Disease / Diagnosis", "clinical_status": "Suspected / Uncertain"}],
        medications=[],
        specialty="Cardiology",
        negation=False,
        notes="'Possible DVT' classifies status as Suspected / Uncertain."
    )
    add_case(
        split="heldout",
        category="clinical_negation",
        input_text="Cardiovascular evaluation reveals normal heart sounds and a completely normal ECG.",
        abbreviations=[{"token": "ECG", "full_form": "Electrocardiogram", "category": "Investigation / Cardiology", "clinical_status": "Normal Finding"}],
        medications=[],
        specialty="Cardiology",
        negation=False,
        notes="'Normal ECG' classifies status as Normal Finding."
    )
    add_case(
        split="heldout",
        category="clinical_negation",
        input_text="Selective coronary angiography demonstrated multivessel occlusions and confirmed CAD.",
        abbreviations=[{"token": "CAD", "full_form": "Coronary Artery Disease", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Cardiology",
        negation=False,
        notes="'Confirmed CAD' explicitly confirms condition diagnosis."
    )
    add_case(
        split="heldout",
        category="clinical_negation",
        input_text="Initiate high-intensity statin therapy and monitor LDL at next outpatient follow-up.",
        abbreviations=[{"token": "LDL", "full_form": "Low-density lipoprotein", "category": "Investigation / Lipid Panel", "clinical_status": "Monitoring Instruction"}],
        medications=[],
        specialty="Cardiology",
        negation=False,
        notes="'Monitor LDL' classifies as a future monitoring instruction."
    )
    add_case(
        split="heldout",
        category="clinical_negation",
        input_text="Fasting lipid profile demonstrates LDL elevated at 178 mg/dL.",
        abbreviations=[{"token": "LDL", "full_form": "Low-density lipoprotein", "category": "Investigation / Lipid Panel", "clinical_status": "Positive Finding / Elevated"}],
        medications=[],
        specialty="Cardiology",
        negation=False,
        notes="'LDL elevated' classifies finding as Positive Finding / Elevated."
    )
    add_case(
        split="heldout",
        category="clinical_negation",
        input_text="Patient has clear lung sounds bilaterally with no signs of COPD.",
        abbreviations=[{"token": "COPD", "full_form": "Chronic Obstructive Pulmonary Disease", "category": "Disease / Diagnosis", "clinical_status": "Ruled Out / Not Evident"}],
        medications=[],
        specialty="Pulmonology",
        negation=True,
        notes="'No signs of COPD' classifies status as Ruled Out / Not Evident."
    )

    # =========================================================================
    # CATEGORY 4: clinical_status (12 examples: 4 dev, 8 heldout)
    # Demonstrating comprehensive variety of clinical status values
    # =========================================================================

    add_case(
        split="development",
        category="clinical_status",
        input_text="Transthoracic echocardiogram demonstrates severe dilated cardiomyopathy and CHF.",
        abbreviations=[{"token": "CHF", "full_form": "Congestive Heart Failure", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Cardiology",
        negation=False,
        notes="Clinical status: Positive / Confirmed Finding."
    )
    add_case(
        split="development",
        category="clinical_status",
        input_text="Patient explicitly denies SOB during brisk walking or exertion.",
        abbreviations=[{"token": "SOB", "full_form": "Shortness of Breath", "category": "Symptom", "clinical_status": "Negative / Denied"}],
        medications=[],
        specialty="Pulmonology",
        negation=True,
        notes="Clinical status: Negative / Denied."
    )
    add_case(
        split="development",
        category="clinical_status",
        input_text="Diffusion-weighted MRI brain is negative; acute CVA ruled out.",
        abbreviations=[{"token": "CVA", "full_form": "Cerebrovascular Accident (Stroke)", "category": "Disease / Diagnosis", "clinical_status": "Ruled Out / Not Evident"}],
        medications=[],
        specialty="Neurology",
        negation=True,
        notes="Clinical status: Ruled Out / Not Evident."
    )
    add_case(
        split="development",
        category="clinical_status",
        input_text="Focal crackles in right lower lobe raise suspicion of probable CAP.",
        abbreviations=[{"token": "CAP", "full_form": "Community-Acquired Pneumonia", "category": "Disease / Diagnosis", "clinical_status": "Suspected / Uncertain"}],
        medications=[],
        specialty="Pulmonology",
        negation=False,
        notes="Clinical status: Suspected / Uncertain."
    )
    add_case(
        split="heldout",
        category="clinical_status",
        input_text="Patient has a documented past medical history of acute MI in 2021.",
        abbreviations=[{"token": "MI", "full_form": "Myocardial Infarction", "category": "Disease / Diagnosis", "clinical_status": "Past History"}],
        medications=[],
        specialty="Cardiology",
        negation=False,
        notes="Clinical status: Past History."
    )
    add_case(
        split="heldout",
        category="clinical_status",
        input_text="Posteroanterior view confirms completely normal CXR without infiltrates or effusion.",
        abbreviations=[{"token": "CXR", "full_form": "Chest X-ray", "category": "Investigation / Imaging", "clinical_status": "Normal Finding"}],
        medications=[],
        specialty="Pulmonology",
        negation=False,
        notes="Clinical status: Normal Finding."
    )
    add_case(
        split="heldout",
        category="clinical_status",
        input_text="Follow-up glycemic testing reveals HbA1c elevated at 9.2 percent.",
        abbreviations=[{"token": "HBA1C", "full_form": "Hemoglobin A1c", "category": "Investigation / Diabetes Monitoring", "clinical_status": "Positive Finding / Elevated"}],
        medications=[],
        specialty="Endocrinology / Diabetology",
        negation=False,
        notes="Clinical status: Positive Finding / Elevated."
    )
    add_case(
        split="heldout",
        category="clinical_status",
        input_text="Patient instructed to monitor BP daily and record morning and evening values.",
        abbreviations=[{"token": "BP", "full_form": "Blood Pressure", "category": "Clinical Measurement", "clinical_status": "Monitoring Instruction"}],
        medications=[],
        specialty="Cardiology",
        negation=False,
        notes="Clinical status: Monitoring Instruction."
    )
    add_case(
        split="heldout",
        category="clinical_status",
        input_text="Routine outpatient CBC reviewed with the attending physician today.",
        abbreviations=[{"token": "CBC", "full_form": "Complete Blood Count", "category": "Investigation / Laboratory Test", "clinical_status": "Reviewed / Mentioned"}],
        medications=[],
        specialty="General Medicine",
        negation=False,
        notes="Clinical status: Reviewed / Mentioned."
    )
    add_case(
        split="heldout",
        category="clinical_status",
        input_text="Echocardiography shows severely reduced EF of 32 percent.",
        abbreviations=[{"token": "EF", "full_form": "Ejection Fraction", "category": "Clinical Measurement", "clinical_status": "Reduced / Low Finding"}],
        medications=[],
        specialty="Cardiology",
        negation=False,
        notes="Clinical status: Reduced / Low Finding."
    )
    add_case(
        split="heldout",
        category="clinical_status",
        input_text="Outpatient transfer summary lists CKD among previous clinical notes.",
        abbreviations=[{"token": "CKD", "full_form": "Chronic Kidney Disease", "category": "Disease / Diagnosis", "clinical_status": "Mentioned / Uncertain"}],
        medications=[],
        specialty="Nephrology",
        negation=False,
        notes="Clinical status: Mentioned / Uncertain."
    )
    add_case(
        split="heldout",
        category="clinical_status",
        input_text="Emergency blood glucose reveals fingerstick RBS elevated at 295 mg/dL.",
        abbreviations=[{"token": "RBS", "full_form": "Random Blood Sugar", "category": "Investigation / Diabetes Monitoring", "clinical_status": "Positive Finding / Elevated"}],
        medications=[],
        specialty="Endocrinology / Diabetology",
        negation=False,
        notes="Clinical status: Positive Finding / Elevated."
    )

    # =========================================================================
    # CATEGORY 5: prescription_parsing (16 examples: 5 dev, 11 heldout)
    # Required: Tab/Cap/Syr/Inhaler/Inj + OD/BD/TDS/QID/PRN/SOS
    # Fields: drug_name, dosage_strength, frequency_code, food_timing_code, form
    # =========================================================================

    add_case(
        split="development",
        category="prescription_parsing",
        input_text="Tab Pantoprazole 40mg OD AC",
        abbreviations=[],
        medications=[{"drug_name": "Pantoprazole", "dosage_strength": "40mg", "frequency_code": "OD", "food_timing_code": "AC", "form": "Tab"}],
        specialty="Gastroenterology",
        negation=False,
        notes="Prescription parsing: Tablet formulation with OD frequency and AC food timing."
    )
    add_case(
        split="development",
        category="prescription_parsing",
        input_text="Tab Metformin 500mg BD PC",
        abbreviations=[],
        medications=[{"drug_name": "Metformin", "dosage_strength": "500mg", "frequency_code": "BD", "food_timing_code": "PC", "form": "Tab"}],
        specialty="Endocrinology / Diabetology",
        negation=False,
        notes="Prescription parsing: Tablet formulation with BD frequency and PC food timing."
    )
    add_case(
        split="development",
        category="prescription_parsing",
        input_text="Tab Augmentin 625mg TDS PC",
        abbreviations=[],
        medications=[{"drug_name": "Amoxicillin and Clavulanate Potassium", "dosage_strength": "625mg", "frequency_code": "TDS", "food_timing_code": "PC", "form": "Tab"}],
        specialty="Infectious Disease",
        negation=False,
        notes="Prescription parsing: Tablet antibiotic with TDS frequency and PC timing."
    )
    add_case(
        split="development",
        category="prescription_parsing",
        input_text="Tab Paracetamol 500mg QID PRN",
        abbreviations=[],
        medications=[{"drug_name": "Paracetamol (Acetaminophen)", "dosage_strength": "500mg", "frequency_code": "QID", "food_timing_code": "Unspecified", "form": "Tab"}],
        specialty="General Medicine",
        negation=False,
        notes="Prescription parsing: Tablet with QID PRN instruction."
    )
    add_case(
        split="development",
        category="prescription_parsing",
        input_text="Tab Paracetamol 650mg PRN",
        abbreviations=[],
        medications=[{"drug_name": "Paracetamol (Acetaminophen)", "dosage_strength": "650mg", "frequency_code": "PRN", "food_timing_code": "Unspecified", "form": "Tab"}],
        specialty="General Medicine",
        negation=False,
        notes="Prescription parsing: Tablet analgesic with PRN frequency."
    )
    add_case(
        split="heldout",
        category="prescription_parsing",
        input_text="Tab Paracetamol 650mg SOS",
        abbreviations=[],
        medications=[{"drug_name": "Paracetamol (Acetaminophen)", "dosage_strength": "650mg", "frequency_code": "SOS", "food_timing_code": "Unspecified", "form": "Tab"}],
        specialty="General Medicine",
        negation=False,
        notes="Prescription parsing: Tablet analgesic with SOS frequency code."
    )
    add_case(
        split="heldout",
        category="prescription_parsing",
        input_text="Cap Omeprazole 20mg OD AC",
        abbreviations=[],
        medications=[{"drug_name": "Omeprazole", "dosage_strength": "20mg", "frequency_code": "OD", "food_timing_code": "AC", "form": "Cap"}],
        specialty="Gastroenterology",
        negation=False,
        notes="Prescription parsing: Capsule PPI formulation with OD frequency and AC timing."
    )
    add_case(
        split="heldout",
        category="prescription_parsing",
        input_text="Cap Pregabalin 75mg BD PC",
        abbreviations=[],
        medications=[{"drug_name": "Pregabalin", "dosage_strength": "75mg", "frequency_code": "BD", "food_timing_code": "PC", "form": "Cap"}],
        specialty="Neurology",
        negation=False,
        notes="Prescription parsing: Capsule anticonvulsant with BD frequency and PC timing."
    )
    add_case(
        split="heldout",
        category="prescription_parsing",
        input_text="Cap Pregabalin 75mg HS",
        abbreviations=[],
        medications=[{"drug_name": "Pregabalin", "dosage_strength": "75mg", "frequency_code": "HS", "food_timing_code": "HS", "form": "Cap"}],
        specialty="Neurology",
        negation=False,
        notes="Prescription parsing: Capsule with bedtime HS frequency and timing."
    )
    add_case(
        split="heldout",
        category="prescription_parsing",
        input_text="Syr Ambroxol 10ml TDS PC",
        abbreviations=[],
        medications=[{"drug_name": "Ambroxol", "dosage_strength": "10ml", "frequency_code": "TDS", "food_timing_code": "PC", "form": "Syr"}],
        specialty="Pulmonology",
        negation=False,
        notes="Prescription parsing: Syrup formulation with TDS frequency and PC timing."
    )
    add_case(
        split="heldout",
        category="prescription_parsing",
        input_text="Syr Paracetamol 5ml BD PRN",
        abbreviations=[],
        medications=[{"drug_name": "Paracetamol (Acetaminophen)", "dosage_strength": "5ml", "frequency_code": "BD", "food_timing_code": "Unspecified", "form": "Syr"}],
        specialty="General Medicine",
        negation=False,
        notes="Prescription parsing: Pediatric syrup formulation with BD PRN frequency."
    )
    add_case(
        split="heldout",
        category="prescription_parsing",
        input_text="Inhaler Salbutamol 100mcg QID PRN",
        abbreviations=[],
        medications=[{"drug_name": "Salbutamol (Albuterol)", "dosage_strength": "100mcg", "frequency_code": "QID", "food_timing_code": "Unspecified", "form": "Inhaler"}],
        specialty="Pulmonology",
        negation=False,
        notes="Prescription parsing: Inhaler bronchodilator with QID PRN frequency."
    )
    add_case(
        split="heldout",
        category="prescription_parsing",
        input_text="Inhaler Salbutamol 2 puffs PRN SOS",
        abbreviations=[],
        medications=[{"drug_name": "Salbutamol (Albuterol)", "dosage_strength": "2 puffs", "frequency_code": "PRN", "food_timing_code": "Unspecified", "form": "Inhaler"}],
        specialty="Pulmonology",
        negation=False,
        notes="Prescription parsing: Inhaler dosage with puff unit and PRN/SOS frequency."
    )
    add_case(
        split="heldout",
        category="prescription_parsing",
        input_text="Inj Ceftriaxone 1g OD IV",
        abbreviations=[],
        medications=[{"drug_name": "Ceftriaxone", "dosage_strength": "1g", "frequency_code": "OD", "food_timing_code": "Unspecified", "form": "Inj"}],
        specialty="Infectious Disease",
        negation=False,
        notes="Prescription parsing: Injectable antibiotic with OD frequency and IV route."
    )
    add_case(
        split="heldout",
        category="prescription_parsing",
        input_text="Inj Morphine 5mg STAT IV",
        abbreviations=[],
        medications=[{"drug_name": "Morphine", "dosage_strength": "5mg", "frequency_code": "STAT", "food_timing_code": "Unspecified", "form": "Inj"}],
        specialty="General Medicine",
        negation=False,
        notes="Prescription parsing: Injectable opioid with STAT immediate frequency."
    )
    add_case(
        split="heldout",
        category="prescription_parsing",
        input_text="Tab Baclofen 10mg BD PC",
        abbreviations=[],
        medications=[{"drug_name": "Baclofen", "dosage_strength": "10mg", "frequency_code": "BD", "food_timing_code": "PC", "form": "Tab"}],
        specialty="Neurology",
        negation=False,
        notes="Prescription parsing: Muscle relaxant tablet with BD frequency and PC timing."
    )

    # =========================================================================
    # CATEGORY 6: food_timing (12 examples: 4 dev, 8 heldout)
    # Required: AC/PC/CC/HS codes and natural language equivalents
    # =========================================================================

    add_case(
        split="development",
        category="food_timing",
        input_text="Tab Pantoprazole 40mg OD AC",
        abbreviations=[],
        medications=[{"drug_name": "Pantoprazole", "dosage_strength": "40mg", "frequency_code": "OD", "food_timing_code": "AC", "form": "Tab"}],
        specialty="Gastroenterology",
        negation=False,
        notes="Food timing code AC (Ante Cibum / Before meals)."
    )
    add_case(
        split="development",
        category="food_timing",
        input_text="Tab Metformin 500mg BD PC",
        abbreviations=[],
        medications=[{"drug_name": "Metformin", "dosage_strength": "500mg", "frequency_code": "BD", "food_timing_code": "PC", "form": "Tab"}],
        specialty="Endocrinology / Diabetology",
        negation=False,
        notes="Food timing code PC (Post Cibum / After meals)."
    )
    add_case(
        split="development",
        category="food_timing",
        input_text="Tab Atorvastatin 20mg HS",
        abbreviations=[],
        medications=[{"drug_name": "Atorvastatin", "dosage_strength": "20mg", "frequency_code": "HS", "food_timing_code": "HS", "form": "Tab"}],
        specialty="Cardiology",
        negation=False,
        notes="Food timing code HS (Hora Somni / At bedtime)."
    )
    add_case(
        split="development",
        category="food_timing",
        input_text="Take Pantoprazole 40mg before breakfast.",
        abbreviations=[],
        medications=[{"drug_name": "Pantoprazole", "dosage_strength": "40mg", "frequency_code": "OD", "food_timing_code": "AC", "form": "Oral"}],
        specialty="Gastroenterology",
        negation=False,
        notes="Natural language food timing: 'before breakfast' maps to AC."
    )
    add_case(
        split="heldout",
        category="food_timing",
        input_text="Take Metformin 500mg after meals.",
        abbreviations=[],
        medications=[{"drug_name": "Metformin", "dosage_strength": "500mg", "frequency_code": "BD", "food_timing_code": "PC", "form": "Oral"}],
        specialty="Endocrinology / Diabetology",
        negation=False,
        notes="Natural language food timing: 'after meals' maps to PC."
    )
    add_case(
        split="heldout",
        category="food_timing",
        input_text="Take Vitamin D3 1000 IU with food.",
        abbreviations=[],
        medications=[{"drug_name": "Vitamin D3", "dosage_strength": "1000 IU", "frequency_code": "OD", "food_timing_code": "CC", "form": "Oral"}],
        specialty="General Medicine",
        negation=False,
        notes="Natural language food timing: 'with food' maps to CC."
    )
    add_case(
        split="heldout",
        category="food_timing",
        input_text="Take Pregabalin 75mg at bedtime.",
        abbreviations=[],
        medications=[{"drug_name": "Pregabalin", "dosage_strength": "75mg", "frequency_code": "HS", "food_timing_code": "HS", "form": "Oral"}],
        specialty="Neurology",
        negation=False,
        notes="Natural language food timing: 'at bedtime' maps to HS."
    )
    add_case(
        split="heldout",
        category="food_timing",
        input_text="Tab Levothyroxine 50mcg OD empty stomach",
        abbreviations=[],
        medications=[{"drug_name": "Levothyroxine", "dosage_strength": "50mcg", "frequency_code": "OD", "food_timing_code": "AC", "form": "Tab"}],
        specialty="Endocrinology / Diabetology",
        negation=False,
        notes="Natural language food timing: 'empty stomach' maps to AC."
    )
    add_case(
        split="heldout",
        category="food_timing",
        input_text="Tab Aspirin 75mg OD after lunch",
        abbreviations=[],
        medications=[{"drug_name": "Aspirin (Acetylsalicylic Acid)", "dosage_strength": "75mg", "frequency_code": "OD", "food_timing_code": "PC", "form": "Tab"}],
        specialty="Cardiology",
        negation=False,
        notes="Natural language food timing: 'after lunch' maps to PC."
    )
    add_case(
        split="heldout",
        category="food_timing",
        input_text="Tab Calcium Carbonate 500mg with meals",
        abbreviations=[],
        medications=[{"drug_name": "Calcium Carbonate", "dosage_strength": "500mg", "frequency_code": "OD", "food_timing_code": "CC", "form": "Tab"}],
        specialty="General Medicine",
        negation=False,
        notes="Natural language food timing: 'with meals' maps to CC."
    )
    add_case(
        split="heldout",
        category="food_timing",
        input_text="Tab Omeprazole 20mg OD 30 minutes before food",
        abbreviations=[],
        medications=[{"drug_name": "Omeprazole", "dosage_strength": "20mg", "frequency_code": "OD", "food_timing_code": "AC", "form": "Tab"}],
        specialty="Gastroenterology",
        negation=False,
        notes="Natural language food timing: '30 minutes before food' maps to AC."
    )
    add_case(
        split="heldout",
        category="food_timing",
        input_text="Tab Diclofenac 50mg BD PC",
        abbreviations=[],
        medications=[{"drug_name": "Diclofenac", "dosage_strength": "50mg", "frequency_code": "BD", "food_timing_code": "PC", "form": "Tab"}],
        specialty="General Medicine",
        negation=False,
        notes="Food timing code PC with NSAID formulation."
    )

    # =========================================================================
    # CATEGORY 7: medicine_extraction (12 examples: 4 dev, 8 heldout)
    # Required: Drug+dose+form with brand names: Ecosprin->Aspirin, Dolo->Paracetamol, Ventolin->Salbutamol
    # =========================================================================

    add_case(
        split="development",
        category="medicine_extraction",
        input_text="Tab Ecosprin 75mg OD",
        abbreviations=[],
        medications=[{"drug_name": "Aspirin (Acetylsalicylic Acid)", "dosage_strength": "75mg", "frequency_code": "OD", "food_timing_code": "Unspecified", "form": "Tab"}],
        specialty="Cardiology",
        negation=False,
        notes="Brand name resolution: Ecosprin resolves to generic Aspirin."
    )
    add_case(
        split="development",
        category="medicine_extraction",
        input_text="Tab Dolo 650mg SOS",
        abbreviations=[],
        medications=[{"drug_name": "Paracetamol (Acetaminophen)", "dosage_strength": "650mg", "frequency_code": "SOS", "food_timing_code": "Unspecified", "form": "Tab"}],
        specialty="General Medicine",
        negation=False,
        notes="Brand name resolution: Dolo resolves to generic Paracetamol."
    )
    add_case(
        split="development",
        category="medicine_extraction",
        input_text="Inhaler Ventolin 100mcg PRN",
        abbreviations=[],
        medications=[{"drug_name": "Salbutamol (Albuterol)", "dosage_strength": "100mcg", "frequency_code": "PRN", "food_timing_code": "Unspecified", "form": "Inhaler"}],
        specialty="Pulmonology",
        negation=False,
        notes="Brand name resolution: Ventolin resolves to generic Salbutamol."
    )
    add_case(
        split="development",
        category="medicine_extraction",
        input_text="Tab Glucophage 500mg BD",
        abbreviations=[],
        medications=[{"drug_name": "Metformin", "dosage_strength": "500mg", "frequency_code": "BD", "food_timing_code": "Unspecified", "form": "Tab"}],
        specialty="Endocrinology / Diabetology",
        negation=False,
        notes="Brand name resolution: Glucophage resolves to generic Metformin."
    )
    add_case(
        split="heldout",
        category="medicine_extraction",
        input_text="Cap Lipitor 20mg HS",
        abbreviations=[],
        medications=[{"drug_name": "Atorvastatin", "dosage_strength": "20mg", "frequency_code": "HS", "food_timing_code": "HS", "form": "Cap"}],
        specialty="Cardiology",
        negation=False,
        notes="Brand name resolution: Lipitor resolves to generic Atorvastatin."
    )
    add_case(
        split="heldout",
        category="medicine_extraction",
        input_text="Tab Norvasc 5mg OD",
        abbreviations=[],
        medications=[{"drug_name": "Amlodipine", "dosage_strength": "5mg", "frequency_code": "OD", "food_timing_code": "Unspecified", "form": "Tab"}],
        specialty="Cardiology",
        negation=False,
        notes="Brand name resolution: Norvasc resolves to generic Amlodipine."
    )
    add_case(
        split="heldout",
        category="medicine_extraction",
        input_text="Tab Augmentin 625mg TDS",
        abbreviations=[],
        medications=[{"drug_name": "Amoxicillin and Clavulanate Potassium", "dosage_strength": "625mg", "frequency_code": "TDS", "food_timing_code": "Unspecified", "form": "Tab"}],
        specialty="Infectious Disease",
        negation=False,
        notes="Brand name resolution: Augmentin resolves to generic Amoxicillin + Clavulanate."
    )
    add_case(
        split="heldout",
        category="medicine_extraction",
        input_text="Cap Lyrica 75mg QHS",
        abbreviations=[],
        medications=[{"drug_name": "Pregabalin", "dosage_strength": "75mg", "frequency_code": "QHS", "food_timing_code": "HS", "form": "Cap"}],
        specialty="Neurology",
        negation=False,
        notes="Brand name resolution: Lyrica resolves to generic Pregabalin."
    )
    add_case(
        split="heldout",
        category="medicine_extraction",
        input_text="Tab Calpol 500mg PRN",
        abbreviations=[],
        medications=[{"drug_name": "Paracetamol (Acetaminophen)", "dosage_strength": "500mg", "frequency_code": "PRN", "food_timing_code": "Unspecified", "form": "Tab"}],
        specialty="General Medicine",
        negation=False,
        notes="Brand name resolution: Calpol resolves to generic Paracetamol."
    )
    add_case(
        split="heldout",
        category="medicine_extraction",
        input_text="Tab Synthroid 50mcg OD",
        abbreviations=[],
        medications=[{"drug_name": "Levothyroxine", "dosage_strength": "50mcg", "frequency_code": "OD", "food_timing_code": "Unspecified", "form": "Tab"}],
        specialty="Endocrinology / Diabetology",
        negation=False,
        notes="Brand name resolution: Synthroid resolves to generic Levothyroxine."
    )
    add_case(
        split="heldout",
        category="medicine_extraction",
        input_text="Tab Pan 40 OD",
        abbreviations=[],
        medications=[{"drug_name": "Pantoprazole", "dosage_strength": "40mg", "frequency_code": "OD", "food_timing_code": "Unspecified", "form": "Tab"}],
        specialty="Gastroenterology",
        negation=False,
        notes="Brand name resolution: Pan 40 resolves to generic Pantoprazole."
    )
    add_case(
        split="heldout",
        category="medicine_extraction",
        input_text="Tab Asthalin 2mg TDS",
        abbreviations=[],
        medications=[{"drug_name": "Salbutamol (Albuterol)", "dosage_strength": "2mg", "frequency_code": "TDS", "food_timing_code": "Unspecified", "form": "Tab"}],
        specialty="Pulmonology",
        negation=False,
        notes="Brand name resolution: Asthalin resolves to generic Salbutamol."
    )

    # =========================================================================
    # CATEGORY 8: route_extraction (6 examples: 2 dev, 4 heldout)
    # Required routes: PO, IV, IM, SC, INH
    # =========================================================================

    add_case(
        split="development",
        category="route_extraction",
        input_text="Tab Metformin 500mg PO BD",
        abbreviations=[],
        medications=[{"drug_name": "Metformin", "dosage_strength": "500mg", "frequency_code": "BD", "food_timing_code": "Unspecified", "form": "Tab", "route_code": "PO"}],
        specialty="Endocrinology / Diabetology",
        negation=False,
        notes="Route extraction: Oral administration route (PO)."
    )
    add_case(
        split="development",
        category="route_extraction",
        input_text="Inj Ceftriaxone 1g IV OD",
        abbreviations=[],
        medications=[{"drug_name": "Ceftriaxone", "dosage_strength": "1g", "frequency_code": "OD", "food_timing_code": "Unspecified", "form": "Inj", "route_code": "IV"}],
        specialty="Infectious Disease",
        negation=False,
        notes="Route extraction: Intravenous administration route (IV)."
    )
    add_case(
        split="heldout",
        category="route_extraction",
        input_text="Inj Diclofenac 75mg IM STAT",
        abbreviations=[],
        medications=[{"drug_name": "Diclofenac", "dosage_strength": "75mg", "frequency_code": "STAT", "food_timing_code": "Unspecified", "form": "Inj", "route_code": "IM"}],
        specialty="General Medicine",
        negation=False,
        notes="Route extraction: Intramuscular administration route (IM)."
    )
    add_case(
        split="heldout",
        category="route_extraction",
        input_text="Inj Insulin Glargine 10 units SC QHS",
        abbreviations=[],
        medications=[{"drug_name": "Insulin Glargine", "dosage_strength": "10 units", "frequency_code": "QHS", "food_timing_code": "HS", "form": "Inj", "route_code": "SC"}],
        specialty="Endocrinology / Diabetology",
        negation=False,
        notes="Route extraction: Subcutaneous administration route (SC)."
    )
    add_case(
        split="heldout",
        category="route_extraction",
        input_text="Salbutamol 100mcg INH QID",
        abbreviations=[],
        medications=[{"drug_name": "Salbutamol (Albuterol)", "dosage_strength": "100mcg", "frequency_code": "QID", "food_timing_code": "Unspecified", "form": "Inhaler", "route_code": "INH"}],
        specialty="Pulmonology",
        negation=False,
        notes="Route extraction: Inhalation administration route (INH)."
    )
    add_case(
        split="heldout",
        category="route_extraction",
        input_text="Paracetamol 1g IV or PO PRN",
        abbreviations=[],
        medications=[{"drug_name": "Paracetamol (Acetaminophen)", "dosage_strength": "1g", "frequency_code": "PRN", "food_timing_code": "Unspecified", "form": "Dosage form not specified", "route_code": "IV / PO"}],
        specialty="General Medicine",
        negation=False,
        notes="Route extraction: Dual permissible route extraction (IV or PO)."
    )

    # =========================================================================
    # CATEGORY 9: unknown_abbreviation (6 examples: 2 dev, 4 heldout)
    # Required: Fictional abbreviations: "XYZQ", "BRKN" -> unrecognized
    # =========================================================================

    add_case(
        split="development",
        category="unknown_abbreviation",
        input_text="Patient presents with persistent fever and unexplained XYZQ.",
        abbreviations=[{"token": "XYZQ", "full_form": None, "category": "Unknown / Unrecognized", "clinical_status": "Mentioned / Uncertain"}],
        medications=[],
        specialty="General Medicine",
        negation=False,
        notes="Unknown abbreviation handling: 'XYZQ' should remain unrecognized."
    )
    add_case(
        split="development",
        category="unknown_abbreviation",
        input_text="Clinical assessment noted atypical BRKN during joint examination.",
        abbreviations=[{"token": "BRKN", "full_form": None, "category": "Unknown / Unrecognized", "clinical_status": "Mentioned / Uncertain"}],
        medications=[],
        specialty="General Medicine",
        negation=False,
        notes="Unknown abbreviation handling: 'BRKN' should remain unrecognized."
    )
    add_case(
        split="heldout",
        category="unknown_abbreviation",
        input_text="Diagnostic workup ordered for unresolved QXZ findings.",
        abbreviations=[{"token": "QXZ", "full_form": None, "category": "Unknown / Unrecognized", "clinical_status": "Mentioned / Uncertain"}],
        medications=[],
        specialty="General Medicine",
        negation=False,
        notes="Unknown abbreviation handling: 'QXZ' should remain unrecognized."
    )
    add_case(
        split="heldout",
        category="unknown_abbreviation",
        input_text="Laboratory report flagged an unrecognized marker PLKJ.",
        abbreviations=[{"token": "PLKJ", "full_form": None, "category": "Unknown / Unrecognized", "clinical_status": "Mentioned / Uncertain"}],
        medications=[],
        specialty="General Medicine",
        negation=False,
        notes="Unknown abbreviation handling: 'PLKJ' should remain unrecognized."
    )
    add_case(
        split="heldout",
        category="unknown_abbreviation",
        input_text="Cardiology consult requested for suspect ZYTT phenomenon.",
        abbreviations=[{"token": "ZYTT", "full_form": None, "category": "Unknown / Unrecognized", "clinical_status": "Mentioned / Uncertain"}],
        medications=[],
        specialty="Cardiology",
        negation=False,
        notes="Unknown abbreviation handling: 'ZYTT' should remain unrecognized."
    )
    add_case(
        split="heldout",
        category="unknown_abbreviation",
        input_text="Follow-up note mentions ambiguous WXVR notation in chart.",
        abbreviations=[{"token": "WXVR", "full_form": None, "category": "Unknown / Unrecognized", "clinical_status": "Mentioned / Uncertain"}],
        medications=[],
        specialty="General Medicine",
        negation=False,
        notes="Unknown abbreviation handling: 'WXVR' should remain unrecognized."
    )

    # =========================================================================
    # CATEGORY 10: specialty_detection (6 examples: 2 dev, 4 heldout)
    # Required: Cardio text->Cardiology, Neuro->Neurology, Pulm->Pulmonology
    # Extras: Gastro, Nephro, Rheum
    # =========================================================================

    add_case(
        split="development",
        category="specialty_detection",
        input_text="Patient with CAD and essential HTN underwent coronary stent placement and 2D echo.",
        abbreviations=[
            {"token": "CAD", "full_form": "Coronary Artery Disease", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"},
            {"token": "HTN", "full_form": "Hypertension (High Blood Pressure)", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"}
        ],
        medications=[],
        specialty="Cardiology",
        negation=False,
        notes="Clinical specialty detection: Cardiology based on CAD, stent, and echo context."
    )
    add_case(
        split="development",
        category="specialty_detection",
        input_text="Brain MRI demonstrates demyelinating lesions and relapsing MS flare with paresthesia.",
        abbreviations=[{"token": "MS", "full_form": "Multiple Sclerosis", "category": "Neurology", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Neurology",
        negation=False,
        notes="Clinical specialty detection: Neurology based on brain MRI, demyelination, and MS."
    )
    add_case(
        split="heldout",
        category="specialty_detection",
        input_text="Patient with COPD and acute wheezing requires bronchodilator inhalers and CXR review.",
        abbreviations=[
            {"token": "COPD", "full_form": "Chronic Obstructive Pulmonary Disease", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"},
            {"token": "CXR", "full_form": "Chest X-ray", "category": "Investigation / Imaging", "clinical_status": "Reviewed / Mentioned"}
        ],
        medications=[],
        specialty="Pulmonology",
        negation=False,
        notes="Clinical specialty detection: Pulmonology based on COPD, wheezing, inhaler, and CXR."
    )
    add_case(
        split="heldout",
        category="specialty_detection",
        input_text="Chronic GERD with acid reflux, heartburn, and severe epigastric burning after meals.",
        abbreviations=[{"token": "GERD", "full_form": "Gastroesophageal Reflux Disease", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Gastroenterology",
        negation=False,
        notes="Clinical specialty detection: Gastroenterology based on GERD, acid reflux, heartburn."
    )
    add_case(
        split="heldout",
        category="specialty_detection",
        input_text="Evaluation of CKD stage 4 with rising serum creatinine, low GFR, and proteinuria.",
        abbreviations=[{"token": "CKD", "full_form": "Chronic Kidney Disease", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Nephrology",
        negation=False,
        notes="Clinical specialty detection: Nephrology based on CKD, creatinine, GFR, and proteinuria."
    )
    add_case(
        split="heldout",
        category="specialty_detection",
        input_text="Morning stiffness exceeding one hour with bilateral wrist synovitis in active RA.",
        abbreviations=[{"token": "RA", "full_form": "Rheumatoid Arthritis", "category": "Rheumatology", "clinical_status": "Positive / Confirmed Finding"}],
        medications=[],
        specialty="Rheumatology",
        negation=False,
        notes="Clinical specialty detection: Rheumatology based on morning stiffness, synovitis, and RA."
    )

    # =========================================================================
    # CATEGORY 11: ocr_reference (5 examples: 1 dev, 4 heldout)
    # Required: Set ocr_image_path to files in samples/, set ocr_reference_text
    # =========================================================================

    ocr_sample1_text = (
        "METRO HEART & METABOLIC CARE CENTER\n"
        "Dr. Sarah Mitchell, MD, FACC\n"
        "Senior Consultant Interventional Cardiologist & Diabetologist | Reg. #74921\n"
        "PATIENT: Mr. Robert Sterling, 58 Yrs / Male\n"
        "DATE: 12-Nov-2026\n"
        "OPD REG: #MED-2026-9481\n"
        "CLINICAL DIAGNOSIS / INDICATION: CAD (Status Post PTCA), T2DM, Essential HTN, Dyslipidemia\n"
        "1. Tab Pantoprazole 40 mg\n"
        "Sig: 1 tab OD AC (Ante Cibum) | Frequency: Once daily | Timing: 30 mins Before Breakfast\n"
        "Duration: 30 days (Indication: Acid peptic prophylaxis)\n"
        "2. Tab Metformin HCl 500 mg\n"
        "Sig: 1 tab BD PC (Post Cibum) | Frequency: Twice daily | Timing: Immediately After Meals\n"
        "Duration: 30 days (Indication: Glycemic control in T2DM)\n"
        "3. Tab Atorvastatin 20 mg\n"
        "Sig: 1 tab QHS (Hora Somni) | Frequency: Once daily | Timing: At Bedtime\n"
        "Duration: 30 days (Indication: Lipid lowering & plaque stabilization)\n"
        "4. Tab Amlodipine 5 mg\n"
        "Sig: 1 tab OD (Omni Die) | Frequency: Once daily | Timing: Morning After Food\n"
        "Duration: 30 days (Indication: Blood pressure management)\n"
        "5. Tab Aspirin (Ecosprin) 75 mg\n"
        "Sig: 1 tab OD PC | Frequency: Once daily | Timing: After Lunch\n"
        "Duration: 30 days (Indication: Antiplatelet therapy)\n"
        "CLINICAL FINDINGS & INVESTIGATION SUMMARY:\n"
        "1. 2D Echo report: Mild LA dilation, EF 52%. Mitral valve leaflets normal; MS ruled out.\n"
        "2. ECG: Normal sinus rhythm, rate 74/min. No acute ST-T ischemic changes.\n"
        "3. Patient advised strict diabetic diet, low sodium intake, and regular BP/SMBG monitoring.\n"
        "Important: Take medications strictly as scheduled. Do not substitute without physician authorization.\n"
        "Emergency Contact: 24/7 Helpline: 1800-MED-CARE | Next Review: After 4 weeks\n"
        "Dr. Sarah Mitchell\n"
        "Authorized Medical Practitioner"
    )

    ocr_sample2_text = (
        "APEX PULMONARY & CRITICAL CARE CLINIC\n"
        "Dr. Rajesh Patel, MD, FCCP\n"
        "Consultant Pulmonologist & Sleep Specialist | Reg. #58319\n"
        "PATIENT: Ms. Emily Watson, 42 Yrs / Female\n"
        "DATE: 14-Nov-2026\n"
        "OPD REG: #MED-2026-9481\n"
        "CLINICAL DIAGNOSIS / INDICATION: Community Acquired Pneumonia (CAP), Bronchial Asthma Exacerbation\n"
        "1. Tab Augmentin 625 mg (Amoxicillin + Clav)\n"
        "Sig: 1 tab TID PC | Frequency: Three times a day | Timing: After Meals\n"
        "Duration: 7 days (Indication: Bacterial respiratory infection)\n"
        "2. Inhaler Salbutamol 100 mcg (Ventolin)\n"
        "Sig: 2 puffs QID PRN | Frequency: Four times a day / As needed | Timing: When breathless or wheezing\n"
        "Duration: 14 days (Indication: Acute bronchospasm rescue)\n"
        "3. Tab Paracetamol (Dolo) 650 mg\n"
        "Sig: 1 tab SOS / PRN | Frequency: As needed (max 3 tabs/day) | Timing: After food for fever > 100°F or bodyache\n"
        "Duration: 5 days (Indication: Fever & myalgia relief)\n"
        "4. Syr Ambroxol + Guaiphenesin 10 ml\n"
        "Sig: 10 ml TID PC | Frequency: Three times a day | Timing: After Food with warm water\n"
        "Duration: 7 days (Indication: Productive cough & mucolysis)\n"
        "CLINICAL FINDINGS & INVESTIGATION SUMMARY:\n"
        "1. CXR PA view shows right lower zone patchy consolidation. No pleural effusion.\n"
        "2. CTA Chest performed in ER: Pulmonary Embolism (PE) ruled out.\n"
        "3. Spirometry: FEV1/FVC ratio 0.68, reversible with bronchodilator. Steam inhalation TID.\n"
        "Important: Take medications strictly as scheduled. Do not substitute without physician authorization.\n"
        "Emergency Contact: 24/7 Helpline: 1800-MED-CARE | Next Review: After 4 weeks\n"
        "Dr. Rajesh Patel\n"
        "Authorized Medical Practitioner"
    )

    ocr_sample3_text = (
        "UNIVERSITY NEUROSCIENCE INSTITUTE\n"
        "Dr. Anthony Rossi, MD, FAAN\n"
        "Professor & Chief of Clinical Neuroimmunology | Reg. #88102\n"
        "PATIENT: Mrs. Laura Chen, 36 Yrs / Female\n"
        "DATE: 15-Nov-2026\n"
        "OPD REG: #MED-2026-9481\n"
        "CLINICAL DIAGNOSIS / INDICATION: Relapsing-Remitting Multiple Sclerosis (MS), Neuropathic Dysesthesia\n"
        "1. Cap Pregabalin 75 mg\n"
        "Sig: 1 cap QHS | Frequency: Once daily at bedtime | Timing: 30 mins before sleep\n"
        "Duration: 30 days (Indication: Neuropathic pain & paresthesias)\n"
        "2. Tab Baclofen 10 mg\n"
        "Sig: 1 tab BD PC | Frequency: Twice daily | Timing: After Morning & Evening meals\n"
        "Duration: 30 days (Indication: Lower extremity spasticity)\n"
        "3. Cap Vitamin D3 60,000 IU\n"
        "Sig: 1 cap QWK (Once Weekly) | Frequency: Once weekly | Timing: With fatty meal on Sundays\n"
        "Duration: 8 weeks (Indication: Hypovitaminosis D in MS)\n"
        "4. Tab Methylprednisolone 4 mg\n"
        "Sig: Tapering schedule as directed | Frequency: As per written plan | Timing: Morning after breakfast with milk\n"
        "Duration: 10 days (Indication: Post-relapse maintenance)\n"
        "CLINICAL FINDINGS & INVESTIGATION SUMMARY:\n"
        "1. MS Clinic Follow-up: EDSS score stable at 2.0. Patient reports reduced sensory tingling.\n"
        "2. Recent 3T MRI Brain & Cervical Spine: Stable demyelinating lesions without active Gd-enhancement.\n"
        "3. Mental Status (MS) exam: Intact cognition, MoCA score 29/30. Continue physiotherapy.\n"
        "Important: Take medications strictly as scheduled. Do not substitute without physician authorization.\n"
        "Emergency Contact: 24/7 Helpline: 1800-MED-CARE | Next Review: After 4 weeks\n"
        "Dr. Anthony Rossi\n"
        "Authorized Medical Practitioner"
    )

    ocr_sample4_text = (
        "ST. JUDE ARTHRITIS & RHEUMATOLOGY CENTER\n"
        "Dr. Victoria Vance, MD, FACR\n"
        "Senior Consultant Rheumatologist | Reg. #61984\n"
        "PATIENT: Mrs. Brenda Miller, 49 Yrs / Female\n"
        "DATE: 16-Nov-2026\n"
        "OPD REG: #MED-2026-9481\n"
        "CLINICAL DIAGNOSIS / INDICATION: Rheumatoid Arthritis (RA), Osteopenia, Chronic Joint Pain\n"
        "1. Tab Methotrexate 15 mg\n"
        "Sig: 1 tab QWK | Frequency: Once weekly | Timing: Take on Friday with dinner\n"
        "Duration: 12 weeks (Indication: Disease-modifying antirheumatic therapy)\n"
        "2. Tab Folic Acid 5 mg\n"
        "Sig: 1 tab OD | Frequency: Once daily | Timing: Morning after breakfast (skip on Friday)\n"
        "Duration: 12 weeks (Indication: Methotrexate toxicity prevention)\n"
        "3. Tab Hydroxychloroquine 200 mg\n"
        "Sig: 1 tab BD PC | Frequency: Twice daily | Timing: After meals\n"
        "Duration: 12 weeks (Indication: Synovial inflammation control)\n"
        "4. Tab Calcium + Vitamin D3 500 mg\n"
        "Sig: 1 tab OD CC | Frequency: Once daily | Timing: With lunch\n"
        "Duration: 12 weeks (Indication: Bone density preservation)\n"
        "CLINICAL FINDINGS & INVESTIGATION SUMMARY:\n"
        "1. Joint exam: Symmetric bilateral wrist and MCP synovitis; DAS28 score 4.2.\n"
        "2. RF positive, anti-CCP positive; RA confirmed on serology.\n"
        "3. Baseline LFT and CBC reviewed; monitor blood counts monthly."
    )

    ocr_sample5_text = (
        "DIGESTIVE HEALTH SPECIALISTS CLINIC\n"
        "Dr. Michael Brooks, MD, FACG\n"
        "Consultant Gastroenterologist & Hepatologist | Reg. #45210\n"
        "PATIENT: Mr. David Kumar, 52 Yrs / Male\n"
        "DATE: 17-Nov-2026\n"
        "OPD REG: #MED-2026-9481\n"
        "CLINICAL DIAGNOSIS / INDICATION: Gastroesophageal Reflux Disease (GERD), Peptic Ulcer Disease (PUD)\n"
        "1. Tab Pantoprazole 40 mg\n"
        "Sig: 1 tab OD AC | Frequency: Once daily | Timing: 30 mins Before Breakfast\n"
        "Duration: 30 days (Indication: Gastric acid suppression)\n"
        "2. Syr Sucralfate 10 ml\n"
        "Sig: 10 ml QID AC | Frequency: Four times a day | Timing: 1 hour Before meals and at bedtime\n"
        "Duration: 14 days (Indication: Mucosal cytoprotection)\n"
        "3. Tab Domperidone 10 mg\n"
        "Sig: 1 tab TID AC | Frequency: Three times a day | Timing: 15 mins Before meals\n"
        "Duration: 14 days (Indication: Upper GI motility support)\n"
        "4. Syr Antacid 15 ml\n"
        "Sig: 15 ml SOS PC | Frequency: As needed | Timing: After meals for acute heartburn\n"
        "Duration: 14 days (Indication: Acid reflux symptom relief)\n"
        "CLINICAL FINDINGS & INVESTIGATION SUMMARY:\n"
        "1. Upper GI Endoscopy: Grade B reflux esophagitis; antral gastritis noted.\n"
        "2. H. pylori rapid urease test negative; PUD healing confirmed.\n"
        "3. Strict dietary modifications advised: avoid spicy food, caffeine, and late dinners."
    )

    add_case(
        split="development",
        category="ocr_reference",
        input_text="",
        abbreviations=[
            {"token": "CAD", "full_form": "Coronary Artery Disease", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"},
            {"token": "T2DM", "full_form": "Type 2 Diabetes Mellitus", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"},
            {"token": "HTN", "full_form": "Hypertension (High Blood Pressure)", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"}
        ],
        medications=[
            {"drug_name": "Pantoprazole", "dosage_strength": "40 mg", "frequency_code": "OD", "food_timing_code": "AC", "form": "Tab"},
            {"drug_name": "Metformin", "dosage_strength": "500 mg", "frequency_code": "BD", "food_timing_code": "PC", "form": "Tab"},
            {"drug_name": "Atorvastatin", "dosage_strength": "20 mg", "frequency_code": "QHS", "food_timing_code": "HS", "form": "Tab"},
            {"drug_name": "Amlodipine", "dosage_strength": "5 mg", "frequency_code": "OD", "food_timing_code": "Unspecified", "form": "Tab"},
            {"drug_name": "Aspirin (Acetylsalicylic Acid)", "dosage_strength": "75 mg", "frequency_code": "OD", "food_timing_code": "PC", "form": "Tab"}
        ],
        specialty="Cardiology",
        negation=False,
        notes="OCR reference case 1: Metro Heart & Metabolic Care Center prescription note.",
        ocr_image_path="samples/sample1_cardio_diabetic.png",
        ocr_reference_text=ocr_sample1_text
    )
    add_case(
        split="heldout",
        category="ocr_reference",
        input_text="",
        abbreviations=[
            {"token": "CAP", "full_form": "Community-Acquired Pneumonia", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"},
            {"token": "PE", "full_form": "Pulmonary Embolism", "category": "Disease / Diagnosis", "clinical_status": "Ruled Out / Not Evident"}
        ],
        medications=[
            {"drug_name": "Amoxicillin and Clavulanate Potassium", "dosage_strength": "625 mg", "frequency_code": "TID", "food_timing_code": "PC", "form": "Tab"},
            {"drug_name": "Salbutamol (Albuterol)", "dosage_strength": "100 mcg", "frequency_code": "QID", "food_timing_code": "Unspecified", "form": "Inhaler"},
            {"drug_name": "Paracetamol (Acetaminophen)", "dosage_strength": "650 mg", "frequency_code": "SOS", "food_timing_code": "Unspecified", "form": "Tab"},
            {"drug_name": "Ambroxol", "dosage_strength": "10 ml", "frequency_code": "TID", "food_timing_code": "PC", "form": "Syr"}
        ],
        specialty="Pulmonology",
        negation=False,
        notes="OCR reference case 2: Apex Pulmonary & Critical Care Clinic prescription note.",
        ocr_image_path="samples/sample2_pulmonology_infection.png",
        ocr_reference_text=ocr_sample2_text
    )
    add_case(
        split="heldout",
        category="ocr_reference",
        input_text="",
        abbreviations=[
            {"token": "MS", "full_form": "Multiple Sclerosis", "category": "Neurology", "clinical_status": "Positive / Confirmed Finding"}
        ],
        medications=[
            {"drug_name": "Pregabalin", "dosage_strength": "75 mg", "frequency_code": "QHS", "food_timing_code": "HS", "form": "Cap"},
            {"drug_name": "Baclofen", "dosage_strength": "10 mg", "frequency_code": "BD", "food_timing_code": "PC", "form": "Tab"},
            {"drug_name": "Vitamin D3", "dosage_strength": "60,000 IU", "frequency_code": "QWK", "food_timing_code": "CC", "form": "Cap"},
            {"drug_name": "Methylprednisolone", "dosage_strength": "4 mg", "frequency_code": "As prescribed", "food_timing_code": "PC", "form": "Tab"}
        ],
        specialty="Neurology",
        negation=False,
        notes="OCR reference case 3: University Neuroscience Institute MS clinic prescription note.",
        ocr_image_path="samples/sample3_neurology_ms_clinic.png",
        ocr_reference_text=ocr_sample3_text
    )
    add_case(
        split="heldout",
        category="ocr_reference",
        input_text="",
        abbreviations=[
            {"token": "RA", "full_form": "Rheumatoid Arthritis", "category": "Rheumatology", "clinical_status": "Positive / Confirmed Finding"}
        ],
        medications=[
            {"drug_name": "Methotrexate", "dosage_strength": "15 mg", "frequency_code": "QWK", "food_timing_code": "CC", "form": "Tab"},
            {"drug_name": "Folic Acid", "dosage_strength": "5 mg", "frequency_code": "OD", "food_timing_code": "PC", "form": "Tab"},
            {"drug_name": "Hydroxychloroquine", "dosage_strength": "200 mg", "frequency_code": "BD", "food_timing_code": "PC", "form": "Tab"},
            {"drug_name": "Calcium + Vitamin D3", "dosage_strength": "500 mg", "frequency_code": "OD", "food_timing_code": "CC", "form": "Tab"}
        ],
        specialty="Rheumatology",
        negation=False,
        notes="OCR reference case 4: St. Jude Arthritis & Rheumatology Center prescription note.",
        ocr_image_path="samples/sample4_rheumatology_clinic.png",
        ocr_reference_text=ocr_sample4_text
    )
    add_case(
        split="heldout",
        category="ocr_reference",
        input_text="",
        abbreviations=[
            {"token": "GERD", "full_form": "Gastroesophageal Reflux Disease", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"},
            {"token": "PUD", "full_form": "Peptic Ulcer Disease", "category": "Disease / Diagnosis", "clinical_status": "Positive / Confirmed Finding"}
        ],
        medications=[
            {"drug_name": "Pantoprazole", "dosage_strength": "40 mg", "frequency_code": "OD", "food_timing_code": "AC", "form": "Tab"},
            {"drug_name": "Sucralfate", "dosage_strength": "10 ml", "frequency_code": "QID", "food_timing_code": "AC", "form": "Syr"},
            {"drug_name": "Domperidone", "dosage_strength": "10 mg", "frequency_code": "TID", "food_timing_code": "AC", "form": "Tab"},
            {"drug_name": "Antacid", "dosage_strength": "15 ml", "frequency_code": "SOS", "food_timing_code": "PC", "form": "Syr"}
        ],
        specialty="Gastroenterology",
        negation=False,
        notes="OCR reference case 5: Digestive Health Specialists Clinic prescription note.",
        ocr_image_path="samples/sample5_gastroenterology_clinic.png",
        ocr_reference_text=ocr_sample5_text
    )

    # =========================================================================
    # CATEGORY 12: edge_cases (10 examples: 2 dev, 8 heldout)
    # Required: lowercase "ac","bd","tds"; abbreviation inside word (CARDIAC should not extract AC);
    #           multiple abbreviations; very short input; numbers that look like abbreviations
    # =========================================================================

    add_case(
        split="development",
        category="edge_cases",
        input_text="take pantoprazole 40mg od ac before breakfast",
        abbreviations=[
            {"token": "OD", "full_form": "Once daily", "category": "Prescription Frequency", "clinical_status": "Positive / Confirmed Finding"},
            {"token": "AC", "full_form": "Ante Cibum (Before Meals)", "category": "Prescription Shorthand", "clinical_status": "Positive / Confirmed Finding"}
        ],
        medications=[{"drug_name": "Pantoprazole", "dosage_strength": "40mg", "frequency_code": "OD", "food_timing_code": "AC", "form": "Oral"}],
        specialty="Gastroenterology",
        negation=False,
        notes="Edge case: Lowercase 'ac' and 'od' must be recognized despite lower casing."
    )
    add_case(
        split="development",
        category="edge_cases",
        input_text="Patient admitted for urgent CARDIAC catheterization.",
        abbreviations=[],
        medications=[],
        specialty="Cardiology",
        negation=False,
        notes="Edge case: CARDIAC contains substring 'AC' but must NOT extract 'AC' as an abbreviation."
    )
    add_case(
        split="heldout",
        category="edge_cases",
        input_text="take metformin 500mg bd pc after meals",
        abbreviations=[
            {"token": "BD", "full_form": "Twice a day", "category": "Prescription Frequency", "clinical_status": "Positive / Confirmed Finding"},
            {"token": "PC", "full_form": "Post Cibum (After Meals)", "category": "Prescription Shorthand", "clinical_status": "Positive / Confirmed Finding"}
        ],
        medications=[{"drug_name": "Metformin", "dosage_strength": "500mg", "frequency_code": "BD", "food_timing_code": "PC", "form": "Oral"}],
        specialty="Endocrinology / Diabetology",
        negation=False,
        notes="Edge case: Lowercase 'bd' and 'pc' must be recognized correctly."
    )
    add_case(
        split="heldout",
        category="edge_cases",
        input_text="amoxicillin 500mg tds pc for 7 days",
        abbreviations=[
            {"token": "TDS", "full_form": "Three times a day", "category": "Prescription Frequency", "clinical_status": "Positive / Confirmed Finding"},
            {"token": "PC", "full_form": "Post Cibum (After Meals)", "category": "Prescription Shorthand", "clinical_status": "Positive / Confirmed Finding"}
        ],
        medications=[{"drug_name": "Amoxicillin and Clavulanate Potassium", "dosage_strength": "500mg", "frequency_code": "TDS", "food_timing_code": "PC", "form": "Oral"}],
        specialty="Infectious Disease",
        negation=False,
        notes="Edge case: Lowercase 'tds' and 'pc' must be parsed without error."
    )
    add_case(
        split="heldout",
        category="edge_cases",
        input_text="DIABETES education and insulin initiation completed.",
        abbreviations=[],
        medications=[],
        specialty="Endocrinology / Diabetology",
        negation=False,
        notes="Edge case: DIABETES contains substring 'ET' or 'BE', which must not be extracted."
    )
    add_case(
        split="heldout",
        category="edge_cases",
        input_text="CHEST tightness with exertion evaluated in ED.",
        abbreviations=[],
        medications=[],
        specialty="Cardiology",
        negation=False,
        notes="Edge case: Word CHEST must not extract spurious abbreviations."
    )
    add_case(
        split="heldout",
        category="edge_cases",
        input_text="Complex past medical history: CAD, HTN, T2DM, and GERD.",
        abbreviations=[
            {"token": "CAD", "full_form": "Coronary Artery Disease", "category": "Disease / Diagnosis", "clinical_status": "Past History"},
            {"token": "HTN", "full_form": "Hypertension (High Blood Pressure)", "category": "Disease / Diagnosis", "clinical_status": "Past History"},
            {"token": "T2DM", "full_form": "Type 2 Diabetes Mellitus", "category": "Disease / Diagnosis", "clinical_status": "Past History"},
            {"token": "GERD", "full_form": "Gastroesophageal Reflux Disease", "category": "Disease / Diagnosis", "clinical_status": "Past History"}
        ],
        medications=[],
        specialty="General Medicine",
        negation=False,
        notes="Edge case: Comma-separated multiple adjacent medical abbreviations in a single clause."
    )
    add_case(
        split="heldout",
        category="edge_cases",
        input_text="CAD",
        abbreviations=[{"token": "CAD", "full_form": "Coronary Artery Disease", "category": "Disease / Diagnosis", "clinical_status": "Mentioned / Uncertain"}],
        medications=[],
        specialty="Cardiology",
        negation=False,
        notes="Edge case: Very short input consisting of a single isolated abbreviation token."
    )
    add_case(
        split="heldout",
        category="edge_cases",
        input_text="HTN",
        abbreviations=[{"token": "HTN", "full_form": "Hypertension (High Blood Pressure)", "category": "Disease / Diagnosis", "clinical_status": "Mentioned / Uncertain"}],
        medications=[],
        specialty="Cardiology",
        negation=False,
        notes="Edge case: Very short input consisting of a single abbreviation token 'HTN'."
    )
    add_case(
        split="heldout",
        category="edge_cases",
        input_text="Vitals: BP 120/80 mmHg, SpO2 98% on room air, COVID-19 negative.",
        abbreviations=[{"token": "BP", "full_form": "Blood Pressure", "category": "Clinical Measurement", "clinical_status": "Reviewed / Mentioned"}],
        medications=[],
        specialty="General Medicine",
        negation=False,
        notes="Edge case: Numbers, ratios (120/80), percentages (98%), and hyphens must not create spurious abbreviations."
    )

    return examples

if __name__ == "__main__":
    out_dir = os.path.join("data", "evaluation")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "ground_truth.json")

    dataset = build_dataset()
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated {len(dataset)} examples at {out_path}")
