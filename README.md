# SynapRx: AI Medical Abbreviation & Prescription Interpretation System

SynapRx is a responsive, context-aware clinical abbreviation disambiguation and prescription interpretation system. It is designed to assist healthcare professionals, clinical coders, pharmacy staff, and patients in understanding complex medical shorthand, Latin prescription sig codes, medication administration timings, and disease abbreviations.

---

## 🌟 Key Features

1. **Context-Aware Abbreviation Disambiguation (CASI Benchmark Model)**
   - Powered by the **Clinical Abbreviation Sense Inventory (CASI)** dataset (37,500 clinical note contexts across 75 ambiguous abbreviations, Moon et al., University of Minnesota).
   - Solves multi-sense ambiguity where identical acronyms mean completely different things across clinical specialties:
     - **MS**: *Mitral Stenosis* (Cardiology) vs. *Multiple Sclerosis* (Neurology) vs. *Morphine Sulfate* (Analgesia/Pain) vs. *Mental Status* (Cognitive Exam).
     - **PE**: *Pulmonary Embolism* (Emergency/Chest) vs. *Physical Examination* (General Clinic) vs. *Pleural Effusion* (Pulmonology).
     - **AC**: *Ante Cibum / Before Meals* (Prescription Timing) vs. *Acromioclavicular Joint* (Orthopedics) vs. *Adriamycin-Cyclophosphamide* (Oncology).
     - **CVA**: *Cerebrovascular Accident / Stroke* (Neurology) vs. *Costovertebral Angle Tenderness* (Nephrology).
     - **RA**: *Rheumatoid Arthritis* (Rheumatology) vs. *Right Atrium* (Cardiology).
     - **PT**: *Prothrombin Time* (Hematology/Lab) vs. *Physical Therapy* (Rehab) vs. *Patient*.
     - **DC**: *Discharge* (Inpatient) vs. *Discontinue* (Orders).
   - Computes Bayesian context likelihood and TF-IDF cosine similarity against CASI clinical sentence centroids to extract trigger words and provide confidence ratings.

2. **Expanded Custom Medical Knowledge Base (Kept Separate from CASI)**
   - Maintained in `data/custom_dataset/` strictly separate from the original CASI dataset (`data/casi_reference/`).
   - Comprises 5 verified modules:
     - `disease_abbreviations.json`: 25+ major chronic conditions mapped with ICD-10 codes, clinical keywords, and patient explanations.
     - `abbreviation_senses_multispecialty.json`: Multi-specialty sense definitions with typical prescriptions and context triggers.
     - `prescription_sig_codes.json`: Complete Latin prescription shorthand (OD, BD, TID, QID, Q4H, QHS, PRN, SOS, STAT).
     - `medicine_terminology.json`: Commonly prescribed medications with brand/generic mappings, indications, drug classes, and counseling pearls.
     - `ismp_error_prone_abbreviations.json`: Institute for Safe Medication Practices (ISMP) official warnings on hazardous abbreviations (U, QD, QOD, trailing zeros, missing leading zeros).

3. **Food Timing Administration Rules (AC, PC, CC, Empty Stomach)**
   - **Ante Cibum (AC) - Before Meals**: Detailed instructions for taking medications 30-60 minutes before food with clinical rationale (e.g. Proton Pump Inhibitors like Pantoprazole/Omeprazole, Levothyroxine).
   - **Post Cibum (PC) - After Meals**: Instructions for taking medications immediately after food to buffer gastric mucosa against ulceration (Aspirin, NSAIDs) or prevent GI distress (Metformin, Augmentin).
   - **Cum Cibo (CC) - With Food**: Direct mixing with food for fat-soluble agents.
   - **Hora Somni (HS) - Bedtime**: Nighttime dosing for statins and neuropathic medications.

4. **Prescription Image OCR Pipeline**
   - Built-in native Windows OCR engine (`Windows.Media.Ocr.OcrEngine`) with automated multi-angle rotation detection (0°, 90°, 180°, 270°), contrast enhancement, and noise reduction.
   - Handles camera photos, document scans, PNG, JPG, JPEG, and PDF documents.
   - Extracted text review box allows instant user editing and verification prior to AI interpretation.

5. **Chronological 24-Hour Daily Medication Schedule**
   - Automatically maps prescribed medications into structured patient routine slots:
     - **Morning (07:00 AM - 09:00 AM)** (Prioritizes AC before breakfast, followed by PC after breakfast)
     - **Afternoon (12:30 PM - 02:00 PM)** (Lunch PC)
     - **Evening (07:00 PM - 08:30 PM)** (Dinner PC)
     - **Bedtime (09:30 PM - 10:30 PM)** (QHS overnight medications)
     - **As-Needed / Emergency (PRN / SOS)** (Symptom-based relief medications)

6. **Patient Safety Guardrails & Non-Diagnostic Disclaimer**
   - Prominently warns users and highlights ISMP error-prone abbreviations.
   - Explicit disclaimer that the tool is informational and must **not** be used for disease diagnosis or autonomous dosage adjustments.

---

## 📁 Project Directory Structure

```
prj4/
├── backend/
│   ├── app.py                      # Flask REST API and static frontend server
│   ├── casi_engine.py              # Statistical context-aware disambiguation model (37.5k CASI records)
│   ├── custom_kb.py                # Expanded Custom Medical Knowledge Base & ISMP engine
│   ├── prescription_parser.py      # Medication, food timing, schedule, and patient summary parser
│   ├── ocr_service.py              # Windows native OCR runner with 4-way rotation detection
│   └── win_ocr_runner.ps1          # WinRT Windows.Media.Ocr PowerShell execution bridge
├── data/
│   ├── casi_reference/             # PRIMARY REFERENCE DATASET (Original CASI corpus)
│   │   └── AnonymizedClinicalAbbreviationsAndAcronymsDataSet.txt  (15.98 MB, 37,500 clinical contexts)
│   └── custom_dataset/             # EXPANDED CUSTOM DATASET (Kept completely separate)
│       ├── abbreviation_senses_multispecialty.json
│       ├── disease_abbreviations.json
│       ├── ismp_error_prone_abbreviations.json
│       ├── medicine_terminology.json
│       └── prescription_sig_codes.json
├── frontend/
│   ├── index.html                  # Responsive clinical UI with Tailwind CSS & Lucide icons
│   ├── app.js                      # Client-side state, OCR handlers, and interactive explorer
│   └── styles.css                  # Custom clinical badges, timeline cards, and layout styles
├── samples/
│   ├── sample1_cardio_diabetic.png # Realistic digitized prescription (CAD, T2DM, MS as Mitral Stenosis)
│   ├── sample2_pulmonology_infection.png # Realistic prescription (CAP, Asthma, PE as Pulmonary Embolism)
│   └── sample3_neurology_ms_clinic.png   # Realistic prescription (MS as Multiple Sclerosis, Pregabalin)
├── scripts/
│   ├── build_custom_dataset.py     # Script compiling the custom verified datasets
│   ├── generate_sample_prescriptions.py # Pillow script rendering high-res test prescriptions
│   └── test_pipeline.py            # Automated test suite for OCR, parsing, and disambiguation
└── README.md
```

---

## 🚀 Running the Application

### Prerequisites
- Python 3.10+ (tested with Python 3.11.9)
- Windows 10 or Windows 11 (for built-in `Windows.Media.Ocr.OcrEngine`)

### Start Server
```powershell
# Set python path to current workspace
$env:PYTHONPATH="."
python backend\app.py
```

Open your web browser and navigate to:
```
http://127.0.0.1:5000/
```

---

## 🔬 Verified Data Sources
- **CASI Corpus**: Moon et al., University of Minnesota NLP Group & National Library of Medicine (NLM).
- **WHO**: Model List of Essential Medicines & International Classification of Diseases (ICD-11).
- **FDA CDER**: Center for Drug Evaluation and Research Prescribing Guidelines & DailyMed.
- **BNF**: British National Formulary Latin Sig Codes & Prescription Standards.
- **ISMP**: Institute for Safe Medication Practices 2024 List of Error-Prone Abbreviations, Symbols, and Dose Designations.
- **Joint Commission**: Official "Do Not Use" List.
