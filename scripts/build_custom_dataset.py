"""
Build and compile the Expanded Custom Medical Dataset.
Includes:
- Disease abbreviations & multi-specialty meanings
- Prescription sig codes & food-timing instructions (AC, PC, CC, etc.)
- Medicine terminology & counseling pearls
- ISMP error-prone abbreviation safety alerts
- Cross-specialty ambiguous abbreviation inventory
"""

import json
import os

os.makedirs(r"data/custom_dataset", exist_ok=True)

# 1. Disease Abbreviations Dataset
disease_abbreviations = [
    {
        "abbreviation": "T2DM",
        "full_name": "Type 2 Diabetes Mellitus",
        "specialty": "Endocrinology",
        "icd10_hint": "E11",
        "plain_english": "A chronic metabolic condition where the body resists or doesn't produce enough insulin, leading to high blood sugar levels.",
        "key_context_keywords": ["glucose", "insulin", "hba1c", "metformin", "fasting", "ppbg", "pancreas", "polyuria", "polydipsia", "retinopathy", "nephropathy"],
        "verified_source": "American Diabetes Association (ADA 2024 Standards of Care) / WHO ICD-11",
        "safety_considerations": "Requires regular monitoring of HbA1c, kidney function, and foot health. Risk of hypoglycemia if taking insulin or sulfonylureas."
    },
    {
        "abbreviation": "T1DM",
        "full_name": "Type 1 Diabetes Mellitus",
        "specialty": "Endocrinology",
        "icd10_hint": "E10",
        "plain_english": "An autoimmune disorder where the immune system destroys insulin-producing beta cells in the pancreas, requiring lifelong daily insulin therapy.",
        "key_context_keywords": ["insulin", "autoimmune", "dka", "ketones", "c-peptide", "basal", "bolus", "hypoglycemia"],
        "verified_source": "American Diabetes Association (ADA) / NIH MedlinePlus",
        "safety_considerations": "High risk of Diabetic Ketoacidosis (DKA) and hypoglycemia. Never stop insulin therapy without urgent specialist consultation."
    },
    {
        "abbreviation": "HTN",
        "full_name": "Hypertension (High Blood Pressure)",
        "specialty": "Cardiology",
        "icd10_hint": "I10",
        "plain_english": "Long-term high pressure in the blood vessels, forcing the heart to pump harder and increasing risk of heart attack and stroke.",
        "key_context_keywords": ["bp", "systolic", "diastolic", "mmhg", "amlodipine", "telmisartan", "ace-i", "arb", "cardiovascular", "sphygmomanometer"],
        "verified_source": "ACC/AHA 2023 Blood Pressure Practice Guidelines",
        "safety_considerations": "Target BP is typically < 130/80 mmHg. Abrupt discontinuation of antihypertensives can cause dangerous rebound hypertension."
    },
    {
        "abbreviation": "CAD",
        "full_name": "Coronary Artery Disease",
        "specialty": "Cardiology",
        "icd10_hint": "I25.1",
        "plain_english": "Narrowing or blockage of coronary arteries that supply blood to heart muscle, usually caused by plaque buildup (atherosclerosis).",
        "key_context_keywords": ["angina", "stent", "cabg", "chest pain", "atherosclerosis", "statin", "troponin", "aspirin", "ischemia", "coronary angiogram"],
        "verified_source": "American Heart Association (AHA) / ACC",
        "safety_considerations": "Any sudden onset of crushing chest pain radiating to the left arm or jaw is a medical emergency requiring immediate ER care."
    },
    {
        "abbreviation": "COPD",
        "full_name": "Chronic Obstructive Pulmonary Disease",
        "specialty": "Pulmonology",
        "icd10_hint": "J44.9",
        "plain_english": "A progressive inflammatory lung condition causing obstructed airflow, shortness of breath, chronic cough, and sputum production (includes emphysema and chronic bronchitis).",
        "key_context_keywords": ["fev1", "fvc", "spirometry", "inhaler", "smoking", "dyspnea", "wheezing", "exacerbation", "bronchodilator", "tiotropium", "oxygen"],
        "verified_source": "Global Initiative for Chronic Obstructive Lung Disease (GOLD 2024)",
        "safety_considerations": "High risk of acute exacerbations triggered by viral or bacterial infections. Patients require annual influenza and pneumococcal vaccination."
    },
    {
        "abbreviation": "CKD",
        "full_name": "Chronic Kidney Disease",
        "specialty": "Nephrology",
        "icd10_hint": "N18",
        "plain_english": "Longstanding, gradual loss of kidney function over months or years, measured by reduced estimated glomerular filtration rate (eGFR).",
        "key_context_keywords": ["egfr", "creatinine", "bun", "proteinuria", "albuminuria", "dialysis", "nephropathy", "potassium", "uremia"],
        "verified_source": "KDIGO (Kidney Disease: Improving Global Outcomes) 2024 Guidelines",
        "safety_considerations": "Doses of renally cleared medications must be adjusted based on eGFR. Avoid nephrotoxic drugs like NSAIDs (ibuprofen, diclofenac)."
    },
    {
        "abbreviation": "GERD",
        "full_name": "Gastroesophageal Reflux Disease",
        "specialty": "Gastroenterology",
        "icd10_hint": "K21.9",
        "plain_english": "A digestive disorder where stomach acid repeatedly flows back up into the tube connecting your mouth and stomach (esophagus), causing heartburn and acid regurgitation.",
        "key_context_keywords": ["heartburn", "acid", "reflux", "ppi", "pantoprazole", "omeprazole", "dysphagia", "endoscopy", "esophagitis", "antacid"],
        "verified_source": "American College of Gastroenterology (ACG) Guidelines",
        "safety_considerations": "PPIs are most effective when taken 30-60 minutes before the first meal of the day (AC). Alarm symptoms (difficulty swallowing, bleeding) require urgent endoscopy."
    },
    {
        "abbreviation": "DVT",
        "full_name": "Deep Vein Thrombosis",
        "specialty": "Hematology / Vascular",
        "icd10_hint": "I82.40",
        "plain_english": "A blood clot that forms in a deep vein, usually in the legs or pelvis, causing swelling, pain, warmth, and erythema.",
        "key_context_keywords": ["clot", "doppler", "ultrasound", "calf", "swelling", "d-dimer", "anticoagulation", "heparin", "warfarin", "eliquis", "thrombus"],
        "verified_source": "American Society of Hematology (ASH) / CHEST Guidelines",
        "safety_considerations": "Risk of embolization to the lungs causing life-threatening Pulmonary Embolism (PE). Monitor for sudden shortness of breath or chest pain."
    },
    {
        "abbreviation": "PE",
        "full_name": "Pulmonary Embolism",
        "specialty": "Pulmonology / Cardiology",
        "icd10_hint": "I26.9",
        "plain_english": "A blockage in one of the pulmonary arteries in the lungs, typically caused by a blood clot traveling from the deep leg veins.",
        "key_context_keywords": ["cta chest", "d-dimer", "dyspnea", "pleuritic chest pain", "hypoxia", "tachycardia", "wells score", "ventilation perfusion"],
        "verified_source": "European Society of Cardiology (ESC) / CHEST Guidelines",
        "safety_considerations": "Critical medical emergency. Note: 'PE' can also mean 'Physical Examination' or 'Pleural Effusion' depending on context."
    },
    {
        "abbreviation": "AFIB",
        "full_name": "Atrial Fibrillation",
        "specialty": "Cardiology",
        "icd10_hint": "I48.91",
        "plain_english": "An irregular and often very rapid heart rhythm (arrhythmia) originating in the upper heart chambers (atria) that can lead to blood clots, stroke, and heart failure.",
        "key_context_keywords": ["arrhythmia", "ecg", "irregularly irregular", "cha2ds2-vasc", "rate control", "rhythm control", "anticoagulant", "palpitations", "beta blocker"],
        "verified_source": "AHA/ACC/ACCP/HRS 2023 Guideline for Management of Atrial Fibrillation",
        "safety_considerations": "High risk of thromboembolic stroke. Most patients require anticoagulation unless contraindications exist."
    },
    {
        "abbreviation": "CHF",
        "full_name": "Congestive Heart Failure",
        "specialty": "Cardiology",
        "icd10_hint": "I50.9",
        "plain_english": "A chronic condition where the heart doesn't pump blood as well as it should, leading to fluid buildup in the lungs, legs, and tissues.",
        "key_context_keywords": ["ejection fraction", "bnp", "nt-probnp", "edema", "furosemide", "orthopnea", "pnd", "lasix", "sacubitril", "cardiomegaly"],
        "verified_source": "ACC/AHA/HFSA Heart Failure Guidelines",
        "safety_considerations": "Patients should monitor daily body weight and fluid intake. Sudden weight gain (> 2-3 lbs in a day) signals worsening fluid overload."
    },
    {
        "abbreviation": "RA",
        "full_name": "Rheumatoid Arthritis",
        "specialty": "Rheumatology",
        "icd10_hint": "M06.9",
        "plain_english": "A chronic autoimmune inflammatory disease causing symmetric joint inflammation, swelling, stiffness (worse in morning), and potential joint deformity.",
        "key_context_keywords": ["joints", "morning stiffness", "synovitis", "rf", "anti-ccp", "methotrexate", "dmards", "biologics", "symmetric polyarthritis"],
        "verified_source": "American College of Rheumatology (ACR) Guidelines",
        "safety_considerations": "Note: 'RA' can also refer to 'Right Atrium' or 'Refractory Anemia' in cardiology/hematology contexts."
    },
    {
        "abbreviation": "SLE",
        "full_name": "Systemic Lupus Erythematosus",
        "specialty": "Rheumatology",
        "icd10_hint": "M32.9",
        "plain_english": "A chronic autoimmune disease where the body's immune system attacks its own tissues and organs (skin, joints, kidneys, brain, blood vessels).",
        "key_context_keywords": ["ana", "anti-dsdna", "malar rash", "lupus nephritis", "photosensitivity", "hydroxychloroquine", "complement", "flares"],
        "verified_source": "ACR/EULAR Classification Criteria for SLE",
        "safety_considerations": "Hydroxychloroquine is foundational; annual ophthalmologic eye exams required to monitor for retinal toxicity."
    },
    {
        "abbreviation": "CVA",
        "full_name": "Cerebrovascular Accident (Stroke)",
        "specialty": "Neurology",
        "icd10_hint": "I63.9",
        "plain_english": "Interruption of blood supply to a part of the brain (ischemic or hemorrhagic), depriving brain tissue of oxygen and nutrients and causing focal neurological deficits.",
        "key_context_keywords": ["infarct", "ischemic", "hemorrhagic", "ct head", "mri brain", "nihss", "tpa", "hemiparesis", "aphasia", "facial droop"],
        "verified_source": "AHA/ASA Stroke Guidelines",
        "safety_considerations": "Acute CVA is a time-critical emergency ('Time is Brain'). In physical exams, 'CVA' can also mean 'Costovertebral Angle' (kidney punch tenderness)."
    },
    {
        "abbreviation": "TIA",
        "full_name": "Transient Ischemic Attack",
        "specialty": "Neurology",
        "icd10_hint": "G45.9",
        "plain_english": "A brief episode of neurological dysfunction caused by temporary focal cerebral ischemia without permanent acute tissue infarction ('mini-stroke').",
        "key_context_keywords": ["transient", "neurological", "amaurosis fugax", "abcd2 score", "carotid doppler", "antiplatelet", "mri dwi negative"],
        "verified_source": "AHA/ASA TIA Management Guidelines",
        "safety_considerations": "High risk of subsequent completed stroke within 48-90 days; requires urgent vascular and cardiac evaluation."
    },
    {
        "abbreviation": "BPH",
        "full_name": "Benign Prostatic Hyperplasia",
        "specialty": "Urology",
        "icd10_hint": "N40.1",
        "plain_english": "Non-cancerous enlargement of the prostate gland in men that squeezes the urethra, causing urinary hesitancy, weak stream, nocturia, and urgency.",
        "key_context_keywords": ["prostate", "psa", "tamsulosin", "finasteride", "luts", "nocturia", "urinary frequency", "ipss"],
        "verified_source": "American Urological Association (AUA) Guidelines",
        "safety_considerations": "Alpha-1 blockers (e.g., tamsulosin) should be taken after the same meal each day (PC) to reduce orthostatic hypotension."
    },
    {
        "abbreviation": "UTI",
        "full_name": "Urinary Tract Infection",
        "specialty": "Urology / Infectious Disease",
        "icd10_hint": "N39.0",
        "plain_english": "An infection in any part of the urinary system (kidneys, bladder, urethra), most commonly caused by bacteria such as Escherichia coli.",
        "key_context_keywords": ["dysuria", "urinalysis", "urine culture", "nitrofurantoin", "e. coli", "pyuria", "leukocyte esterase", "nitrites"],
        "verified_source": "Infectious Diseases Society of America (IDSA) Guidelines",
        "safety_considerations": "Complete the full antibiotic course even if symptoms improve quickly, to prevent recurrence and antimicrobial resistance."
    },
    {
        "abbreviation": "PCOS",
        "full_name": "Polycystic Ovary Syndrome",
        "specialty": "Endocrinology / Gynecology",
        "icd10_hint": "E28.2",
        "plain_english": "A hormonal disorder causing enlarged ovaries with small cysts, irregular menstrual periods, elevated androgen levels, and insulin resistance.",
        "key_context_keywords": ["oligomenorrhea", "hirsutism", "insulin resistance", "rotterdam criteria", "lh/fsh", "metformin", "oral contraceptives"],
        "verified_source": "Rotterdam Consensus / Endocrine Society Clinical Guidelines",
        "safety_considerations": "Associated with increased long-term risk of type 2 diabetes, metabolic syndrome, and endometrial hyperplasia."
    },
    {
        "abbreviation": "MDD",
        "full_name": "Major Depressive Disorder",
        "specialty": "Psychiatry",
        "icd10_hint": "F32.9",
        "plain_english": "A mood disorder that causes persistent feelings of sadness, emptiness, loss of interest, fatigue, sleep disruption, and difficulty functioning.",
        "key_context_keywords": ["depression", "anhedonia", "phq-9", "ssri", "sertraline", "escitalopram", "psychotherapy", "suicidal ideation"],
        "verified_source": "American Psychiatric Association (APA) DSM-5-TR",
        "safety_considerations": "Antidepressants carry a black-box warning for increased suicidal thoughts in adolescents and young adults during the first weeks of therapy."
    },
    {
        "abbreviation": "GAD",
        "full_name": "Generalized Anxiety Disorder",
        "specialty": "Psychiatry",
        "icd10_hint": "F41.1",
        "plain_english": "Severe, ongoing anxiety and excessive worry that interferes with daily activities and is disproportionate to actual events.",
        "key_context_keywords": ["anxiety", "worry", "gad-7", "restlessness", "muscle tension", "ssri", "buspirone", "benzodiazepines"],
        "verified_source": "APA DSM-5-TR / NICE Guidelines",
        "safety_considerations": "Benzodiazepines should be limited to short-term acute use due to risk of dependence and cognitive impairment."
    },
    {
        "abbreviation": "IBD",
        "full_name": "Inflammatory Bowel Disease",
        "specialty": "Gastroenterology",
        "icd10_hint": "K52.9",
        "plain_english": "An umbrella term for chronic inflammation of tissues in digestive tract, primarily comprising Ulcerative Colitis (UC) and Crohn's Disease (CD).",
        "key_context_keywords": ["crohn", "ulcerative colitis", "colonoscopy", "calprotectin", "mesalamine", "biologics", "bloody diarrhea", "cramping"],
        "verified_source": "American Gastroenterological Association (AGA) / ECCO",
        "safety_considerations": "Different from IBS (Irritable Bowel Syndrome), which is non-inflammatory and does not cause intestinal wall ulcers."
    },
    {
        "abbreviation": "PUD",
        "full_name": "Peptic Ulcer Disease",
        "specialty": "Gastroenterology",
        "icd10_hint": "K27.9",
        "plain_english": "Sores that develop on the inside lining of stomach (gastric ulcer) and upper portion of small intestine (duodenal ulcer), often caused by H. pylori or NSAID use.",
        "key_context_keywords": ["h. pylori", "epigastric pain", "melena", "endoscopy", "nsaids", "ppi", "pantoprazole", "mucosal ulceration"],
        "verified_source": "ACG Clinical Guideline on Treatment of Helicobacter pylori Infection",
        "safety_considerations": "NSAIDs must be stopped or co-prescribed with a gastroprotective PPI. Monitor for black tarry stools (melena) signaling hemorrhage."
    },
    {
        "abbreviation": "CAP",
        "full_name": "Community-Acquired Pneumonia",
        "specialty": "Pulmonology / Infectious Disease",
        "icd10_hint": "J18.9",
        "plain_english": "Pneumonia contracted outside of healthcare facilities, causing inflammation of the lung alveoli with fever, productive cough, and infiltrate on chest imaging.",
        "key_context_keywords": ["cxr infiltrate", "sputum", "curb-65", "fever", "cough", "azithromycin", "amoxicillin", "ceftriaxone", "crackles"],
        "verified_source": "ATS/IDSA Guidelines for Management of CAP",
        "safety_considerations": "Assess severity using CURB-65 or PSI scores to determine whether outpatient or inpatient hospitalization is indicated."
    },
    {
        "abbreviation": "AKI",
        "full_name": "Acute Kidney Injury",
        "specialty": "Nephrology",
        "icd10_hint": "N17.9",
        "plain_english": "A sudden episode of kidney failure or kidney damage that happens within a few hours or days, causing waste products to build up in blood.",
        "key_context_keywords": ["creatinine jump", "oliguria", "anuria", "kdigo staging", "dehydration", "prerenal", "intrinsic", "postrenal"],
        "verified_source": "KDIGO Clinical Practice Guideline for AKI",
        "safety_considerations": "Identify and treat underlying causes (volume depletion, nephrotoxic drugs, urinary obstruction). Discontinue ACE-i/ARBs temporarily."
    },
    {
        "abbreviation": "PAD",
        "full_name": "Peripheral Artery Disease",
        "specialty": "Vascular Surgery / Cardiology",
        "icd10_hint": "I73.9",
        "plain_english": "A common circulatory problem in which narrowed arteries reduce blood flow to the limbs, causing leg pain when walking (claudication).",
        "key_context_keywords": ["claudication", "abi", "ankle-brachial index", "arterial doppler", "gangrene", "cilostazol", "statin", "atherosclerosis"],
        "verified_source": "AHA/ACC Guideline on Peripheral Artery Disease",
        "safety_considerations": "Diagnosed via Ankle-Brachial Index (ABI < 0.9). Aggressive cardiovascular risk factor management is essential."
    }
]

# 2. Multi-Specialty Ambiguous Abbreviations Inventory
ambiguous_abbreviations = [
    {
        "abbreviation": "MS",
        "senses": [
            {
                "sense": "Mitral Stenosis",
                "specialty": "Cardiology",
                "definition": "Narrowing of the mitral valve orifice obstructing blood flow from left atrium to left ventricle.",
                "context_keywords": ["valve", "murmur", "rheumatic", "diastolic", "opening snap", "atrial fibrillation", "echocardiogram", "cardiac", "heart"],
                "typical_prescriptions": ["furosemide", "digoxin", "warfarin", "metoprolol"],
                "verified_source": "AHA/ACC Valvular Heart Disease Guidelines"
            },
            {
                "sense": "Multiple Sclerosis",
                "specialty": "Neurology",
                "definition": "Immune-mediated demyelinating disease of the central nervous system.",
                "context_keywords": ["demyelinating", "mri brain", "plaques", "oligoclonal bands", "relapse", "flare", "paresthesia", "optic neuritis", "spasticity"],
                "typical_prescriptions": ["interferon beta", "glatiramer", "methylprednisolone", "ocrelizumab", "baclofen"],
                "verified_source": "National Multiple Sclerosis Society / AAN Guidelines"
            },
            {
                "sense": "Morphine Sulfate",
                "specialty": "Pharmacology / Palliative Care",
                "definition": "Potent opioid analgesic used for severe acute or chronic pain.",
                "context_keywords": ["mg", "iv", "sc", "pain", "breakthrough pain", "dose", "analgesia", "opioid", "titration"],
                "typical_prescriptions": ["morphine sulfate 10mg PO Q4H PRN pain"],
                "verified_source": "FDA Prescribing Information / ISMP High-Risk List"
            },
            {
                "sense": "Mental Status",
                "specialty": "Psychiatry / General Medicine",
                "definition": "Clinical assessment of a patient's cognitive, emotional, and behavioral functioning.",
                "context_keywords": ["exam", "alert", "oriented", "confused", "lethargic", "intact", "baseline", "altered", "encephalopathy"],
                "typical_prescriptions": [],
                "verified_source": "DSM-5-TR Clinical Examination Guidelines"
            },
            {
                "sense": "Musculoskeletal",
                "specialty": "Orthopedics / Physical Examination",
                "definition": "Relating to the muscular and skeletal systems together.",
                "context_keywords": ["exam", "joints", "range of motion", "rom", "tenderness", "swelling", "extremities", "bony"],
                "typical_prescriptions": ["nsaid", "paracetamol", "physiotherapy"],
                "verified_source": "Physical Diagnosis Guidelines"
            }
        ],
        "ismp_warning": "CRITICAL ISMP ALERT: 'MS' is on the ISMP Do Not Use list because 'MS' can be misinterpreted as Morphine Sulfate or Magnesium Sulfate, leading to fatal overdoses. Never abbreviate drug names."
    },
    {
        "abbreviation": "AC",
        "senses": [
            {
                "sense": "Ante Cibum (Before Meals)",
                "specialty": "Prescription Shorthand / Pharmacology",
                "definition": "Instruction indicating that a medication must be taken prior to food consumption (empty stomach).",
                "context_keywords": ["tab", "cap", "mg", "empty stomach", "meals", "breakfast", "before food", "pantoprazole", "omeprazole", "levothyroxine"],
                "typical_prescriptions": ["tab pantoprazole 40mg 1 tab AC breakfast"],
                "verified_source": "British National Formulary (BNF) / Latin Medical Terminology"
            },
            {
                "sense": "Acromioclavicular",
                "specialty": "Orthopedics / Anatomy",
                "definition": "Pertaining to the joint formed by the junction of the acromion of the scapula and the clavicle.",
                "context_keywords": ["joint", "shoulder", "clavicle", "separation", "ligament", "sprain", "x-ray", "orthopedic"],
                "typical_prescriptions": ["sling", "nsaid", "ice"],
                "verified_source": "American Academy of Orthopaedic Surgeons (AAOS)"
            },
            {
                "sense": "Adriamycin + Cyclophosphamide",
                "specialty": "Oncology",
                "definition": "Common chemotherapy regimen combination used primarily in breast cancer treatment.",
                "context_keywords": ["chemotherapy", "breast cancer", "doxorubicin", "cyclophosphamide", "oncology", "cycle", "infusion", "neutropenia"],
                "typical_prescriptions": ["ondansetron", "filgrastim", "doxorubicin"],
                "verified_source": "NCCN (National Comprehensive Cancer Network) Guidelines"
            },
            {
                "sense": "Assist-Control",
                "specialty": "Critical Care / Pulmonology",
                "definition": "A mechanical ventilation mode where the ventilator delivers a preset tidal volume with every breath.",
                "context_keywords": ["ventilator", "mechanical ventilation", "tidal volume", "peep", "fio2", "icu", "respiratory rate"],
                "typical_prescriptions": ["propofol", "fentanyl"],
                "verified_source": "American Thoracic Society (ATS) Mechanical Ventilation Guidelines"
            }
        ],
        "ismp_warning": "In medication orders, ensure AC is clearly documented as 'before meals' to prevent dosing errors."
    },
    {
        "abbreviation": "PC",
        "senses": [
            {
                "sense": "Post Cibum (After Meals)",
                "specialty": "Prescription Shorthand / Pharmacology",
                "definition": "Instruction indicating that a medication must be administered after meals or with food.",
                "context_keywords": ["tab", "cap", "after food", "after meals", "food", "metformin", "aspirin", "ibuprofen", "full stomach"],
                "typical_prescriptions": ["tab metformin 500mg BD PC"],
                "verified_source": "British National Formulary (BNF) / Latin Sig Codes"
            },
            {
                "sense": "Pressure Support / Pressure Control",
                "specialty": "Critical Care / Pulmonology",
                "definition": "A mode of mechanical ventilation delivering breaths at a set inspiratory pressure.",
                "context_keywords": ["ventilator", "icu", "mode", "peep", "inspiratory pressure", "intubated"],
                "typical_prescriptions": [],
                "verified_source": "ATS Critical Care Guidelines"
            },
            {
                "sense": "Packed Cells",
                "specialty": "Hematology / Transfusion Medicine",
                "definition": "Concentrated red blood cells prepared from whole blood for transfusion.",
                "context_keywords": ["transfusion", "units", "hemoglobin", "prbc", "crossmatch", "blood bank"],
                "typical_prescriptions": ["transfuse 2 units PC over 4 hours"],
                "verified_source": "AABB Transfusion Standards"
            }
        ]
    },
    {
        "abbreviation": "PE",
        "senses": [
            {
                "sense": "Pulmonary Embolism",
                "specialty": "Pulmonology / Emergency Medicine",
                "definition": "Life-threatening occlusion of pulmonary arterial bed by a thrombus.",
                "context_keywords": ["cta", "d-dimer", "shortness of breath", "pleuritic chest pain", "wells score", "anticoagulation", "hypoxia"],
                "typical_prescriptions": ["enoxaparin", "heparin", "apixaban"],
                "verified_source": "CHEST / ESC Guidelines"
            },
            {
                "sense": "Physical Examination",
                "specialty": "General Clinical Medicine",
                "definition": "Systematic evaluation of the objective bodily findings of a patient.",
                "context_keywords": ["heent", "cvs", "rs", "abdomen", "cns", "vitals", "inspection", "palpation", "auscultation"],
                "typical_prescriptions": [],
                "verified_source": "Bates' Guide to Physical Examination"
            },
            {
                "sense": "Pleural Effusion",
                "specialty": "Pulmonology",
                "definition": "Abnormal accumulation of fluid in the pleural space between parietal and visceral pleura.",
                "context_keywords": ["thoracentesis", "blunting of costophrenic angle", "exudative", "transudative", "light criteria", "fluid"],
                "typical_prescriptions": ["furosemide", "antibiotics"],
                "verified_source": "British Thoracic Society (BTS) Pleural Disease Guidelines"
            }
        ]
    },
    {
        "abbreviation": "CVA",
        "senses": [
            {
                "sense": "Cerebrovascular Accident (Stroke)",
                "specialty": "Neurology / Emergency Medicine",
                "definition": "Sudden focal neurological impairment resulting from infarction or hemorrhage in brain tissue.",
                "context_keywords": ["infarct", "stroke", "nihss", "tpa", "hemiparesis", "aphasia", "mri brain", "ct head", "neurology"],
                "typical_prescriptions": ["aspirin", "clopidogrel", "atorvastatin"],
                "verified_source": "AHA/ASA Stroke Guidelines"
            },
            {
                "sense": "Costovertebral Angle (Tenderness)",
                "specialty": "Nephrology / Physical Examination",
                "definition": "The acute angle formed on either side of the back between the twelfth rib and the vertebral column; tenderness indicates kidney infection (pyelonephritis).",
                "context_keywords": ["flank pain", "tenderness", "pyelonephritis", "punch", "kidney", "urinalysis", "cva tenderness"],
                "typical_prescriptions": ["ceftriaxone", "ciprofloxacin"],
                "verified_source": "Bates' Guide to Physical Examination"
            }
        ]
    },
    {
        "abbreviation": "RA",
        "senses": [
            {
                "sense": "Rheumatoid Arthritis",
                "specialty": "Rheumatology",
                "definition": "Chronic inflammatory autoimmune joint disease.",
                "context_keywords": ["morning stiffness", "synovitis", "rf", "anti-ccp", "methotrexate", "dmards", "biologics", "hand joints", "mcp"],
                "typical_prescriptions": ["methotrexate 15mg weekly", "folic acid", "hydroxychloroquine"],
                "verified_source": "American College of Rheumatology (ACR)"
            },
            {
                "sense": "Right Atrium",
                "specialty": "Cardiology / Anatomy",
                "definition": "The right upper chamber of the heart receiving deoxygenated blood from the vena cavae.",
                "context_keywords": ["echocardiogram", "enlargement", "right ventricle", "tricuspid", "central venous", "cardiac"],
                "typical_prescriptions": [],
                "verified_source": "ASE Echocardiography Nomenclature"
            },
            {
                "sense": "Refractory Anemia",
                "specialty": "Hematology / Oncology",
                "definition": "A subtype of myelodysplastic syndrome (MDS) characterized by persistent anemia unresponsive to iron or vitamin therapy.",
                "context_keywords": ["myelodysplastic", "mds", "bone marrow", "blasts", "ringed sideroblasts", "cytopenia"],
                "typical_prescriptions": ["erythropoietin", "blood transfusion"],
                "verified_source": "WHO Classification of Tumours of Haematopoietic and Lymphoid Tissues"
            }
        ]
    },
    {
        "abbreviation": "PT",
        "senses": [
            {
                "sense": "Prothrombin Time",
                "specialty": "Hematology / Laboratory",
                "definition": "Blood test measuring how quickly blood forms a clot in the extrinsic coagulation pathway, reported as INR.",
                "context_keywords": ["inr", "coagulation", "warfarin", "anticoagulation", "bleeding", "clotting", "seconds", "plasma"],
                "typical_prescriptions": ["warfarin"],
                "verified_source": "CLSI Coagulation Testing Standards"
            },
            {
                "sense": "Physical Therapy",
                "specialty": "Rehabilitation Medicine",
                "definition": "Treatment to restore movement, function, and relieve pain using physical methods.",
                "context_keywords": ["exercises", "mobility", "rehab", "gait training", "strengthening", "ambulation", "post-op"],
                "typical_prescriptions": [],
                "verified_source": "APTA (American Physical Therapy Association)"
            },
            {
                "sense": "Patient",
                "specialty": "General Clinical Documentation",
                "definition": "Abbreviation for patient in progress notes.",
                "context_keywords": ["pt is a", "pt presented", "pt states", "pt denies", "pt tolerating"],
                "typical_prescriptions": [],
                "verified_source": "Standard Medical Documentation"
            }
        ]
    },
    {
        "abbreviation": "CA",
        "senses": [
            {
                "sense": "Cancer / Carcinoma",
                "specialty": "Oncology",
                "definition": "Malignant neoplasm of epithelial origin.",
                "context_keywords": ["biopsy", "malignancy", "metastasis", "chemotherapy", "radiation", "tumor", "staging", "oncologist"],
                "typical_prescriptions": ["chemotherapy", "tamoxifen", "palliative"],
                "verified_source": "NCCN Oncology Terminology"
            },
            {
                "sense": "Calcium",
                "specialty": "Endocrinology / Laboratory",
                "definition": "Essential divalent cation and electrolyte measured in serum chemistry.",
                "context_keywords": ["mg/dl", "ionized", "albumin", "corrected calcium", "parathyroid", "pth", "hypercalcemia", "hypocalcemia"],
                "typical_prescriptions": ["calcium carbonate", "calcitriol"],
                "verified_source": "Endocrine Society Clinical Guidelines"
            },
            {
                "sense": "Coronary Artery",
                "specialty": "Cardiology / Anatomy",
                "definition": "Arteries supplying oxygenated blood to the myocardium.",
                "context_keywords": ["cad", "angiogram", "stenosis", "bypass", "left anterior descending", "circumflex"],
                "typical_prescriptions": [],
                "verified_source": "ACC/AHA Terminology"
            }
        ]
    },
    {
        "abbreviation": "DC",
        "senses": [
            {
                "sense": "Discharge",
                "specialty": "Hospital Administration / Inpatient Care",
                "definition": "The formal release of a hospitalized patient to home or step-down facility.",
                "context_keywords": ["summary", "home", "hospital course", "follow-up", "stable", "vitals", "discharge medications"],
                "typical_prescriptions": [],
                "verified_source": "Hospital Clinical Documentation Guidelines"
            },
            {
                "sense": "Discontinue",
                "specialty": "Pharmacology / Nursing Orders",
                "definition": "Order to stop administration of a medication, treatment, or catheter.",
                "context_keywords": ["stop", "order", "antibiotics", "medication", "foley", "d/c iv fluids"],
                "typical_prescriptions": [],
                "verified_source": "ISMP Safe Medication Order Guidelines"
            }
        ],
        "ismp_warning": "ISMP Alert: 'D/C' is an error-prone abbreviation. It can be confused between 'discharge' (patient going home) and 'discontinue' (stopping a medication). Always write out the full word."
    },
    {
        "abbreviation": "ER",
        "senses": [
            {
                "sense": "Emergency Room / Emergency Department",
                "specialty": "Emergency Medicine",
                "definition": "Hospital department specializing in emergency care.",
                "context_keywords": ["presented to", "admitted from", "trauma", "triage", "acuity", "stat"],
                "typical_prescriptions": [],
                "verified_source": "ACEP Emergency Terminology"
            },
            {
                "sense": "Extended Release",
                "specialty": "Pharmaceutics / Formulation",
                "definition": "Dosage form modified to release the active drug over a prolonged time period.",
                "context_keywords": ["tablet", "capsule", "24hr", "daily", "once daily", "do not crush", "formulation"],
                "typical_prescriptions": ["metformin er", "bupropion er", "venlafaxine er"],
                "verified_source": "USP Modified-Release Terminology"
            },
            {
                "sense": "Estrogen Receptor",
                "specialty": "Oncology / Pathology",
                "definition": "Nuclear hormone receptor tested in breast cancer biopsies (ER-positive vs ER-negative).",
                "context_keywords": ["er positive", "pr positive", "her2", "immunohistochemistry", "tamoxifen", "aromatase inhibitor"],
                "typical_prescriptions": ["anastrozole", "tamoxifen"],
                "verified_source": "ASCO/CAP Breast Cancer Biomarker Guidelines"
            }
        ]
    }
]

# 3. Prescription Sig Codes & Instructions
prescription_sig_codes = {
    "frequencies": [
        {
            "code": "OD",
            "latin": "Omni die",
            "english": "Once daily",
            "timing_details": "Take once every 24 hours at approximately the same time each day.",
            "schedule_slots": ["morning"],
            "ismp_status": "Acceptable in UK/Commonwealth; in USA, ISMP recommends writing 'daily' to avoid confusion with 'OS' (left eye) or 'OD' (right eye).",
            "verified_source": "British National Formulary (BNF) / Latin Sig Codes"
        },
        {
            "code": "QD",
            "latin": "Quaque die",
            "english": "Every day / Once daily",
            "timing_details": "Take once daily.",
            "schedule_slots": ["morning"],
            "ismp_status": "PROHIBITED on ISMP and Joint Commission Do Not Use lists. Often misread as QID (four times daily). Always write 'daily'.",
            "verified_source": "The Joint Commission Official Do Not Use List / ISMP"
        },
        {
            "code": "BD",
            "latin": "Bis in die",
            "english": "Twice a day",
            "timing_details": "Take twice daily, approximately 12 hours apart (typically morning and evening).",
            "schedule_slots": ["morning", "evening"],
            "ismp_status": "Standard international abbreviation. Ensure clear spacing.",
            "verified_source": "British National Formulary (BNF)"
        },
        {
            "code": "BID",
            "latin": "Bis in die",
            "english": "Twice a day",
            "timing_details": "Take two times a day, approximately 10 to 12 hours apart (e.g. 8 AM and 8 PM).",
            "schedule_slots": ["morning", "evening"],
            "ismp_status": "Widely accepted in US practice.",
            "verified_source": "USP Pharmacopeia / FDA Sig Codes"
        },
        {
            "code": "TID",
            "latin": "Ter in die",
            "english": "Three times a day",
            "timing_details": "Take three times daily during waking hours, roughly 6 to 8 hours apart (e.g. morning, afternoon, evening).",
            "schedule_slots": ["morning", "afternoon", "evening"],
            "ismp_status": "Standard prescription abbreviation.",
            "verified_source": "USP Pharmacopeia / BNF"
        },
        {
            "code": "TDS",
            "latin": "Ter die sumendum",
            "english": "Three times a day to be taken",
            "timing_details": "Take three times daily (morning, midday, night).",
            "schedule_slots": ["morning", "afternoon", "evening"],
            "ismp_status": "Commonly used in UK, Commonwealth, and India.",
            "verified_source": "British National Formulary (BNF)"
        },
        {
            "code": "QID",
            "latin": "Quater in die",
            "english": "Four times a day",
            "timing_details": "Take four times daily, spaced evenly throughout the day (approximately every 4 to 6 hours while awake).",
            "schedule_slots": ["morning", "afternoon", "evening", "bedtime"],
            "ismp_status": "Standard. Ensure not confused with QD.",
            "verified_source": "USP Pharmacopeia / BNF"
        },
        {
            "code": "QDS",
            "latin": "Quater die sumendum",
            "english": "Four times a day to be taken",
            "timing_details": "Take four times daily.",
            "schedule_slots": ["morning", "afternoon", "evening", "bedtime"],
            "ismp_status": "Commonwealth equivalent of QID.",
            "verified_source": "British National Formulary (BNF)"
        },
        {
            "code": "Q4H",
            "latin": "Quaque 4 hora",
            "english": "Every 4 hours",
            "timing_details": "Take around the clock every 4 hours (e.g. 6 times per 24 hours).",
            "schedule_slots": ["custom_interval_4h"],
            "ismp_status": "Standard interval designation.",
            "verified_source": "Clinical Pharmacy Standards"
        },
        {
            "code": "Q6H",
            "latin": "Quaque 6 hora",
            "english": "Every 6 hours",
            "timing_details": "Take around the clock every 6 hours (e.g. 4 times per 24 hours).",
            "schedule_slots": ["morning", "afternoon", "evening", "bedtime"],
            "ismp_status": "Standard interval designation.",
            "verified_source": "Clinical Pharmacy Standards"
        },
        {
            "code": "Q8H",
            "latin": "Quaque 8 hora",
            "english": "Every 8 hours",
            "timing_details": "Take every 8 hours (e.g. 3 times per 24 hours, evenly spaced).",
            "schedule_slots": ["morning", "afternoon", "evening"],
            "ismp_status": "Standard interval designation.",
            "verified_source": "Clinical Pharmacy Standards"
        },
        {
            "code": "Q12H",
            "latin": "Quaque 12 hora",
            "english": "Every 12 hours",
            "timing_details": "Take every 12 hours (e.g. 8:00 AM and 8:00 PM).",
            "schedule_slots": ["morning", "evening"],
            "ismp_status": "Standard interval designation.",
            "verified_source": "Clinical Pharmacy Standards"
        },
        {
            "code": "QHS",
            "latin": "Quaque hora somni",
            "english": "Every night at bedtime",
            "timing_details": "Take once nightly right before going to sleep.",
            "schedule_slots": ["bedtime"],
            "ismp_status": "ISMP cautions against 'qhs' as 'hs' can mean half-strength. Recommended to write 'at bedtime'.",
            "verified_source": "ISMP / USP"
        },
        {
            "code": "HS",
            "latin": "Hora somni",
            "english": "At bedtime",
            "timing_details": "Take at sleep time.",
            "schedule_slots": ["bedtime"],
            "ismp_status": "Write 'at bedtime' to avoid mistaking for 'half strength'.",
            "verified_source": "Joint Commission / ISMP"
        },
        {
            "code": "PRN",
            "latin": "Pro re nata",
            "english": "As needed / As circumstances require",
            "timing_details": "Take only when required for specified symptom (e.g. pain, fever, nausea). Respect the minimum interval specified (e.g. 'PRN pain Q6H max 3 tabs/day').",
            "schedule_slots": ["as_needed"],
            "ismp_status": "Must always be paired with a clinical indication (e.g. PRN pain, PRN fever) and maximum daily limit.",
            "verified_source": "Joint Commission Medication Management Standards"
        },
        {
            "code": "SOS",
            "latin": "Si opus sit",
            "english": "If necessary / In case of emergency",
            "timing_details": "Take a single dose if needed. In Commonwealth/Indian prescriptions, often used identically to PRN (e.g. Tab Paracetamol SOS).",
            "schedule_slots": ["as_needed"],
            "ismp_status": "Specify maximum frequency and indication.",
            "verified_source": "British / Indian Pharmacopeial Practice"
        },
        {
            "code": "STAT",
            "latin": "Statim",
            "english": "Immediately / At once",
            "timing_details": "Administer right away as a single emergency or loading dose.",
            "schedule_slots": ["immediate"],
            "ismp_status": "Reserved for urgent clinical necessity.",
            "verified_source": "Critical Care / Nursing Standards"
        }
    ],
    "food_timings": [
        {
            "code": "AC",
            "latin": "Ante cibum",
            "english": "Before meals / On an empty stomach",
            "instruction": "Take 30 to 60 minutes before eating food or drinking anything other than water.",
            "clinical_rationale": "Prevents food from blocking drug absorption or, for proton pump inhibitors, allows the drug to block acid pumps before they are activated by a meal.",
            "common_examples": ["Pantoprazole", "Omeprazole", "Levothyroxine", "Alendronate", "Sucralfate"],
            "verified_source": "FDA Prescribing Information / BNF"
        },
        {
            "code": "PC",
            "latin": "Post cibum",
            "english": "After meals / Following food",
            "instruction": "Take immediately or within 30 minutes after completing a meal.",
            "clinical_rationale": "Food buffers gastric mucosa against irritation/ulcers (NSAIDs), or enhances drug absorption, or reduces gastrointestinal upset/nausea.",
            "common_examples": ["Aspirin", "Ibuprofen", "Diclofenac", "Metformin", "Iron supplements (if GI upset occurs)", "Spironolactone"],
            "verified_source": "FDA Prescribing Information / BNF"
        },
        {
            "code": "CC",
            "latin": "Cum cibo",
            "english": "With food / With meals",
            "instruction": "Take midway through your meal or with the first few bites of food.",
            "clinical_rationale": "Ensures direct mixing with food to maximize absorption of fat-soluble agents or reduce direct mucosal contact.",
            "common_examples": ["Acarbose (with first bite)", "Pancreatic enzymes (Creon)", "Ritonavir", "Atorvastatin (can take with or without food)"],
            "verified_source": "FDA Prescribing Information"
        },
        {
            "code": "Empty Stomach",
            "latin": "Ventriculo vacuo",
            "english": "On an empty stomach",
            "instruction": "Take at least 1 hour before eating or 2 hours after your last meal, with a full glass of plain water.",
            "clinical_rationale": "Food components (such as dietary calcium, proteins, or fats) severely bind or degrade the active compound.",
            "common_examples": ["Levothyroxine", "Ampicillin", "Bisphosphonates", "Captopril"],
            "verified_source": "USP Patient Counseling Information"
        }
    ],
    "routes": [
        {"code": "PO", "latin": "Per os", "english": "By mouth (orally)"},
        {"code": "IV", "latin": "Intravenous", "english": "Directly into a vein"},
        {"code": "IM", "latin": "Intramuscular", "english": "Injected into muscle tissue"},
        {"code": "SC / SubQ", "latin": "Subcutaneous", "english": "Injected into fatty tissue under skin (e.g. insulin)"},
        {"code": "SL", "latin": "Sublingual", "english": "Dissolved under the tongue (e.g. nitroglycerin)"},
        {"code": "Top", "latin": "Topical", "english": "Applied directly to affected skin"},
        {"code": "Inh", "latin": "Inhalation", "english": "Inhaled through the mouth into lungs"},
        {"code": "Neb", "latin": "Nebulization", "english": "Inhaled as a fine mist via nebulizer machine"},
        {"code": "PR", "latin": "Per rectum", "english": "Administered into rectum (suppository or enema)"},
        {"code": "PV", "latin": "Per vaginam", "english": "Administered into vagina"},
        {"code": "Ophth", "latin": "Ophthalmic", "english": "Instilled into the eyes (eye drops/ointment)"},
        {"code": "Otic", "latin": "Auris", "english": "Instilled into ear canal (ear drops)"}
    ]
}

# 4. Medicine Terminology Database
medicine_terminology = [
    {
        "generic_name": "Metformin",
        "brand_names": ["Glucophage", "Glycomet", "Riomet", "Fortamet"],
        "drug_class": "Biguanide Antidiabetic Agent",
        "primary_indications": "Type 2 Diabetes Mellitus (first-line therapy), Polycystic Ovary Syndrome (PCOS).",
        "typical_dosages": "500 mg, 850 mg, 1000 mg tablets; 500 mg, 750 mg, 1000 mg Extended Release (ER)",
        "food_instructions": "Take POST CIBUM (PC - with or immediately after meals).",
        "food_rationale": "Taking with or after food minimizes common gastrointestinal side effects such as nausea, abdominal cramps, and diarrhea.",
        "common_specialty": "Endocrinology / General Internal Medicine",
        "patient_counseling": "Swallow extended-release tablets whole; do not crush or chew. Temporarily hold before contrast dye procedures or major surgery due to rare risk of lactic acidosis. Avoid excessive alcohol.",
        "verified_source": "FDA DailyMed / ADA Standards of Medical Care in Diabetes"
    },
    {
        "generic_name": "Pantoprazole",
        "brand_names": ["Protonix", "Pantocid", "Pan 40", "Pantodac"],
        "drug_class": "Proton Pump Inhibitor (PPI)",
        "primary_indications": "Gastroesophageal Reflux Disease (GERD), Peptic Ulcer Disease, Erosive Esophagitis, Zollinger-Ellison Syndrome.",
        "typical_dosages": "20 mg, 40 mg delayed-release tablets; 40 mg IV vial",
        "food_instructions": "Take ANTE CIBUM (AC - 30 to 60 minutes before breakfast / first meal).",
        "food_rationale": "PPIs work best when the gastric parietal cell proton pumps are actively stimulated by food ingestion. Taking it 30-60 mins beforehand ensures the drug is present when pumps activate.",
        "common_specialty": "Gastroenterology / Internal Medicine",
        "patient_counseling": "Do not chew, crush, or split delayed-release tablets. Long-term use (> 1 year) may slightly reduce absorption of vitamin B12, magnesium, and calcium.",
        "verified_source": "FDA DailyMed / American College of Gastroenterology (ACG)"
    },
    {
        "generic_name": "Atorvastatin",
        "brand_names": ["Lipitor", "Atorva", "Storvas", "Lipicure"],
        "drug_class": "HMG-CoA Reductase Inhibitor (Statin)",
        "primary_indications": "Hypercholesterolemia, Primary and Secondary Prevention of Cardiovascular Disease (CAD, stroke, heart attack).",
        "typical_dosages": "10 mg, 20 mg, 40 mg, 80 mg film-coated tablets",
        "food_instructions": "Take once daily, with or without food. Frequently prescribed at bedtime (QHS) or with the evening meal.",
        "food_rationale": "Can be taken anytime, but liver cholesterol synthesis peaks overnight, so evening or bedtime dosing is customary.",
        "common_specialty": "Cardiology / Internal Medicine",
        "patient_counseling": "Promptly report unexplained muscle pain, tenderness, or weakness (rare myopathy/rhabdomyolysis). Avoid consuming large quantities of grapefruit juice (> 1 liter/day) as it elevates drug levels.",
        "verified_source": "ACC/AHA Cholesterol Guidelines / FDA DailyMed"
    },
    {
        "generic_name": "Amlodipine",
        "brand_names": ["Norvasc", "Amlong", "Amlopres", "Stamlo"],
        "drug_class": "Dihydropyridine Calcium Channel Blocker (CCB)",
        "primary_indications": "Hypertension (High Blood Pressure), Chronic Stable Angina, Vasospastic (Prinzmetal's) Angina.",
        "typical_dosages": "2.5 mg, 5 mg, 10 mg tablets",
        "food_instructions": "Take once daily (OD), with or without food, at the same time every day.",
        "food_rationale": "Food does not affect amlodipine bioavailability. Consistency in timing maintains steady 24-hour blood pressure control.",
        "common_specialty": "Cardiology / Internal Medicine",
        "patient_counseling": "May cause peripheral edema (swelling of ankles or lower legs) or dizziness when standing up quickly. Do not discontinue abruptly.",
        "verified_source": "AHA/ACC Hypertension Guidelines / FDA DailyMed"
    },
    {
        "generic_name": "Amoxicillin and Clavulanate Potassium",
        "brand_names": ["Augmentin", "Moxikind-CV", "Clavam", "Amoclav"],
        "drug_class": "Penicillin-class Antibiotic + Beta-lactamase Inhibitor",
        "primary_indications": "Bacterial respiratory tract infections (sinusitis, community-acquired pneumonia), Otitis media, Skin and soft tissue infections, Animal bites, Recurrent UTIs.",
        "typical_dosages": "375 mg, 625 mg, 1000 mg tablets; 228.5 mg/5ml, 457 mg/5ml pediatric oral suspension",
        "food_instructions": "Take POST CIBUM (PC - at the start of a meal or immediately after eating).",
        "food_rationale": "Administering with food optimizes absorption of clavulanate potassium and significantly reduces gastrointestinal intolerance and nausea.",
        "common_specialty": "Infectious Disease / General Practice / Pediatrics",
        "patient_counseling": "Complete the full prescribed duration (e.g. 5 to 7 days) even if symptoms resolve completely. Confirm absence of penicillin allergy. Report severe watery diarrhea.",
        "verified_source": "IDSA Guidelines / FDA DailyMed"
    },
    {
        "generic_name": "Aspirin (Acetylsalicylic Acid)",
        "brand_names": ["Ecosprin", "Bayer Aspirin", "Disprin", "Empirin"],
        "drug_class": "Antiplatelet Agent / Nonsteroidal Anti-inflammatory Drug (NSAID)",
        "primary_indications": "Secondary prevention of cardiovascular events in established CAD, stroke/TIA prevention, Acute coronary syndrome.",
        "typical_dosages": "75 mg, 81 mg (low-dose cardioprotective 'baby aspirin'), 150 mg, 325 mg (analgesic/anti-inflammatory)",
        "food_instructions": "Take POST CIBUM (PC - immediately after a meal or with a glass of milk/water).",
        "food_rationale": "Aspirin directly irritates gastric lining and inhibits protective prostaglandins; taking after food buffers the stomach against erosions and ulcers.",
        "common_specialty": "Cardiology / Neurology",
        "patient_counseling": "Do not take with other NSAIDs without medical guidance. Watch for symptoms of GI bleeding (black tarry stools, coffee-ground vomitus).",
        "verified_source": "USPSTF / ACC/AHA Prevention Guidelines"
    },
    {
        "generic_name": "Salbutamol (Albuterol)",
        "brand_names": ["Ventolin", "Asthalin", "ProAir", "Proventil"],
        "drug_class": "Short-Acting Beta-2 Adrenergic Agonist (SABA) Bronchodilator",
        "primary_indications": "Acute bronchospasm in Asthma, COPD, and Exercise-Induced Bronchospasm.",
        "typical_dosages": "100 mcg/puff Metered Dose Inhaler (MDI); 2.5 mg/3ml nebulizer solution; 2 mg, 4 mg oral tablets",
        "food_instructions": "Inhalation: Independent of food. Rinse mouth with water after use if combined with a corticosteroid.",
        "food_rationale": "Inhaled directly into airway; no gastrointestinal absorption required for lung bronchodilation.",
        "common_specialty": "Pulmonology / Emergency Medicine / Pediatrics",
        "patient_counseling": "Use as a 'rescue' inhaler for sudden shortness of breath or wheezing (1-2 puffs every 4-6 hours PRN). May cause transient tremor, palpitations, or tachycardia.",
        "verified_source": "Global Initiative for Asthma (GINA 2024) / FDA DailyMed"
    },
    {
        "generic_name": "Levothyroxine",
        "brand_names": ["Synthroid", "Thyronorm", "Eltroxin", "Levoxyl"],
        "drug_class": "Synthetic Thyroid Hormone (T4)",
        "primary_indications": "Hypothyroidism (Hashimoto's, post-thyroidectomy), Pituitary TSH suppression in thyroid cancer.",
        "typical_dosages": "25 mcg, 50 mcg, 75 mcg, 88 mcg, 100 mcg, 112 mcg, 125 mcg, 150 mcg tablets",
        "food_instructions": "Take ANTE CIBUM (AC - strictly on an empty stomach 30 to 60 minutes before breakfast with a full glass of plain water).",
        "food_rationale": "Dietary calcium, soy, coffee, iron, and fiber severely impair gastrointestinal absorption of levothyroxine, causing subtherapeutic hormone levels.",
        "common_specialty": "Endocrinology / General Medicine",
        "patient_counseling": "Do not take iron, calcium supplements, or antacids within 4 hours of levothyroxine. Regular TSH monitoring required every 6 to 12 weeks during dose titration.",
        "verified_source": "American Thyroid Association (ATA) Guidelines / FDA DailyMed"
    },
    {
        "generic_name": "Pregabalin",
        "brand_names": ["Lyrica", "Pregeb", "Pregalin", "Nervin"],
        "drug_class": "Gabapentinoid / Alpha-2-delta Ligand",
        "primary_indications": "Diabetic Peripheral Neuropathic Pain, Post-herpetic Neuralgia, Fibromyalgia, Neuropathic pain in spinal cord injury, Adjunctive therapy for focal seizures.",
        "typical_dosages": "50 mg, 75 mg, 150 mg, 300 mg capsules",
        "food_instructions": "Take with or without food. Commonly prescribed at bedtime (QHS) initially to minimize daytime drowsiness.",
        "food_rationale": "Absorption rate is slightly decreased with food, but overall extent of absorption is not clinically altered.",
        "common_specialty": "Neurology / Pain Management / Rheumatology",
        "patient_counseling": "Causes dizziness, somnolence, and peripheral edema. Avoid alcohol. Do not discontinue suddenly due to risk of withdrawal symptoms and rebound seizures.",
        "verified_source": "AAN Neuropathic Pain Guidelines / FDA DailyMed"
    },
    {
        "generic_name": "Telmisartan",
        "brand_names": ["Micardis", "Telma", "Telmikind", "Creser"],
        "drug_class": "Angiotensin II Receptor Blocker (ARB)",
        "primary_indications": "Hypertension, Cardiovascular risk reduction in patients unable to take ACE inhibitors, Diabetic nephropathy.",
        "typical_dosages": "20 mg, 40 mg, 80 mg tablets",
        "food_instructions": "Take once daily (OD), with or without food, at the same time each day.",
        "food_rationale": "Bioavailability is slightly reduced with food, but clinical blood pressure lowering efficacy remains consistent.",
        "common_specialty": "Cardiology / Nephrology",
        "patient_counseling": "Contraindicated in pregnancy (teratogenic / fetal toxicity). Monitor serum potassium and creatinine periodically.",
        "verified_source": "ACC/AHA Guidelines / FDA DailyMed"
    },
    {
        "generic_name": "Paracetamol (Acetaminophen)",
        "brand_names": ["Dolo 650", "Calpol", "Tylenol", "Panadol", "Crocin"],
        "drug_class": "Analgesic and Antipyretic",
        "primary_indications": "Mild to moderate pain (headache, arthralgia, toothache), fever reduction.",
        "typical_dosages": "325 mg, 500 mg, 650 mg tablets; 120 mg/5ml, 250 mg/5ml syrups; 1000 mg IV infusion",
        "food_instructions": "Can be taken with or without food. Taking with food or a glass of water is gentle on the stomach.",
        "food_rationale": "Does not irritate the stomach lining unlike NSAIDs (aspirin, ibuprofen).",
        "common_specialty": "General Medicine / Pediatrics / Emergency",
        "patient_counseling": "Do not exceed maximum daily limit (3000 to 4000 mg in 24 hours for healthy adults) to prevent acute hepatotoxicity (liver failure). Check all combination cold/cough products for hidden acetaminophen.",
        "verified_source": "FDA Acetaminophen Dosing Guidelines / WHO Essential Medicines"
    },
    {
        "generic_name": "Omeprazole",
        "brand_names": ["Prilosec", "Omez", "Losec", "Ocid"],
        "drug_class": "Proton Pump Inhibitor (PPI)",
        "primary_indications": "Duodenal and Gastric Ulcers, GERD, H. pylori eradication (as part of triple therapy).",
        "typical_dosages": "10 mg, 20 mg, 40 mg delayed-release capsules",
        "food_instructions": "Take ANTE CIBUM (AC - 30 to 60 minutes before a meal, preferably breakfast).",
        "food_rationale": "Acid pumps must be inhibited prior to food-stimulated activation.",
        "common_specialty": "Gastroenterology / General Medicine",
        "patient_counseling": "Swallow capsules whole with water; do not crush or chew pellets inside the capsule.",
        "verified_source": "FDA DailyMed / ACG Guidelines"
    }
]

# 5. ISMP Error-Prone Abbreviations & High-Risk Shorthand
ismp_error_prone = [
    {
        "abbreviation": "U, u",
        "intended_meaning": "Unit",
        "misinterpretation": "Mistaken as '0' (zero), the number '4' (four), or 'cc'. E.g. '10 U' read as '100' or '104', causing fatal 10-fold insulin overdoses.",
        "safe_practice": "Write 'unit' or 'units' fully in all circumstances.",
        "source": "ISMP List of Error-Prone Abbreviations / The Joint Commission Do Not Use List"
    },
    {
        "abbreviation": "IU",
        "intended_meaning": "International Unit",
        "misinterpretation": "Mistaken as 'IV' (intravenous) or the number '10' (ten).",
        "safe_practice": "Write 'international unit' or 'units'.",
        "source": "ISMP List of Error-Prone Abbreviations / The Joint Commission"
    },
    {
        "abbreviation": "Q.D., QD, q.d., qd",
        "intended_meaning": "Every day / Once daily",
        "misinterpretation": "Mistaken for 'QID' (four times daily) or 'QOD' (every other day).",
        "safe_practice": "Write 'daily' or 'once daily'.",
        "source": "ISMP List of Error-Prone Abbreviations / The Joint Commission"
    },
    {
        "abbreviation": "Q.O.D., QOD, q.o.d., qod",
        "intended_meaning": "Every other day",
        "misinterpretation": "Mistaken for 'QD' (daily) or 'QID' (four times daily). Period after 'Q' can be seen as 'I'.",
        "safe_practice": "Write 'every other day'.",
        "source": "ISMP List of Error-Prone Abbreviations / The Joint Commission"
    },
    {
        "abbreviation": "Trailing Zero (X.0 mg)",
        "intended_meaning": "e.g., 5.0 mg meant as 5 mg",
        "misinterpretation": "The decimal point is easily overlooked, resulting in a 10-fold overdose (50 mg instead of 5 mg).",
        "safe_practice": "NEVER use a trailing zero for whole numbers. Write '5 mg', never '5.0 mg'.",
        "source": "ISMP / Joint Commission Official Standards"
    },
    {
        "abbreviation": "Lack of Leading Zero (.X mg)",
        "intended_meaning": "e.g., .5 mg meant as 0.5 mg",
        "misinterpretation": "Decimal point overlooked; read as 5 mg (10-fold overdose).",
        "safe_practice": "ALWAYS use a leading zero before a decimal point. Write '0.5 mg', never '.5 mg'.",
        "source": "ISMP / Joint Commission Official Standards"
    },
    {
        "abbreviation": "MS, MSO4, MgSO4",
        "intended_meaning": "Morphine Sulfate or Magnesium Sulfate",
        "misinterpretation": "Confused for one another. Patients receiving morphine instead of magnesium sulfate or vice versa, causing lethal respiratory depression.",
        "safe_practice": "Write 'morphine sulfate' or 'magnesium sulfate' out completely. Never abbreviate drug names.",
        "source": "ISMP / Joint Commission Do Not Use List"
    },
    {
        "abbreviation": "μg",
        "intended_meaning": "Microgram",
        "misinterpretation": "Mistaken for 'mg' (milligram), resulting in a 1,000-fold overdose.",
        "safe_practice": "Write 'mcg' or 'micrograms'.",
        "source": "ISMP / FDA Standards"
    },
    {
        "abbreviation": "cc",
        "intended_meaning": "Cubic centimeter",
        "misinterpretation": "Mistaken for 'u' (units) or '00'.",
        "safe_practice": "Use 'mL' (milliliter).",
        "source": "ISMP List of Error-Prone Abbreviations"
    },
    {
        "abbreviation": "D/C",
        "intended_meaning": "Discharge or Discontinue",
        "misinterpretation": "Premature discontinuation of medications meant to be continued upon discharge, or continued medications meant to be stopped.",
        "safe_practice": "Write 'discharge' or 'discontinue'.",
        "source": "ISMP List of Error-Prone Abbreviations"
    }
]

# Write all files
with open(r"data/custom_dataset/disease_abbreviations.json", "w", encoding="utf-8") as f:
    json.dump(disease_abbreviations, f, indent=2)

with open(r"data/custom_dataset/abbreviation_senses_multispecialty.json", "w", encoding="utf-8") as f:
    json.dump(ambiguous_abbreviations, f, indent=2)

with open(r"data/custom_dataset/prescription_sig_codes.json", "w", encoding="utf-8") as f:
    json.dump(prescription_sig_codes, f, indent=2)

with open(r"data/custom_dataset/medicine_terminology.json", "w", encoding="utf-8") as f:
    json.dump(medicine_terminology, f, indent=2)

with open(r"data/custom_dataset/ismp_error_prone_abbreviations.json", "w", encoding="utf-8") as f:
    json.dump(ismp_error_prone, f, indent=2)

print("Successfully compiled and saved all 5 custom dataset modules into data/custom_dataset/")
