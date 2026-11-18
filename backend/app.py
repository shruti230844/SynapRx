"""
Flask Application Backend for Medical Abbreviation & Prescription Interpretation System.
Provides RESTful endpoints for OCR extraction, CASI disambiguation,
Custom Medical KB lookup, medication scheduling, and frontend serving.
"""

import os
import tempfile
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename

from backend.casi_engine import CasiEngine
from backend.custom_kb import CustomMedicalKB
from backend.prescription_parser import PrescriptionInterpreter
from backend.ocr_service import MedicalOcrService

app = Flask(__name__, static_folder="../frontend", static_url_path="")
CORS(app)

# Initialize engines
casi_engine = CasiEngine()
casi_engine.load()

custom_kb = CustomMedicalKB()
custom_kb.load()

interpreter = PrescriptionInterpreter(casi_engine=casi_engine, custom_kb=custom_kb)
ocr_service = MedicalOcrService()
evaluation_cache = {}

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "pdf"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# --- API Endpoints ---

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "casi_loaded": casi_engine.is_loaded,
        "custom_kb_loaded": custom_kb.is_loaded,
        "casi_unique_abbrs": len(casi_engine.abbr_senses),
        "custom_diseases": len(custom_kb.diseases),
        "custom_medicines": len(custom_kb.medicines),
        "version": "1.0.0"
    })

@app.route("/api/ocr", methods=["POST"])
def ocr_endpoint():
    """Handle image or PDF upload and perform OCR extraction."""
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded in 'file' field"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"success": False, "error": "Invalid file type. Allowed: PNG, JPG, JPEG, WEBP, PDF"}), 400

    filename = secure_filename(file.filename)
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        ocr_result = ocr_service.process_image(tmp_path)
        return jsonify(ocr_result)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except:
                pass

@app.route("/api/interpret", methods=["POST"])
def interpret_endpoint():
    """Perform full AI medical interpretation on clinical / prescription text."""
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    
    if not text.strip():
        return jsonify({"success": False, "error": "Input text cannot be empty."}), 400

    result = interpreter.interpret(text)
    return jsonify(result)

def get_evaluation_report(split):
    if split not in {"development", "heldout"}:
        raise ValueError("split must be 'development' or 'heldout'")
    if split not in evaluation_cache:
        from backend.evaluation import run_evaluation
        evaluation_cache[split] = run_evaluation(interpreter, ocr_service, split=split)
    return evaluation_cache[split]

@app.route("/api/evaluation", methods=["GET"])
def evaluation_endpoint():
    split = request.args.get("split", "heldout")
    try:
        return jsonify(get_evaluation_report(split))
    except ValueError as error:
        return jsonify({"success": False, "error": str(error)}), 400

@app.route("/api/evaluation/export", methods=["GET"])
def evaluation_export_endpoint():
    split = request.args.get("split", "heldout")
    export_format = request.args.get("format", "json").lower()
    try:
        report = get_evaluation_report(split)
    except ValueError as error:
        return jsonify({"success": False, "error": str(error)}), 400
    if export_format == "csv":
        from backend.evaluation import evaluation_csv
        return Response(
            evaluation_csv(report),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename=synaprx-evaluation-{split}.csv"},
        )
    if export_format != "json":
        return jsonify({"success": False, "error": "format must be 'json' or 'csv'"}), 400
    return Response(
        jsonify(report).get_data(as_text=True),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename=synaprx-evaluation-{split}.json"},
    )

@app.route("/api/disambiguate", methods=["POST"])
def disambiguate_single():
    """Disambiguate a single abbreviation given a specific context sentence."""
    data = request.get_json(silent=True) or {}
    abbr = data.get("abbr", "").strip().upper()
    context = data.get("context", "").strip()

    if not abbr:
        return jsonify({"success": False, "error": "Missing 'abbr' parameter."}), 400

    # Specialty detection
    spec_info = custom_kb.detect_specialty(context) if context else {"primary": "General Medicine"}

    # 1. Check CASI
    casi_res = casi_engine.disambiguate(abbr, context) if abbr in casi_engine.abbr_senses else None

    # 2. Check Custom multi-specialty
    custom_res = custom_kb.disambiguate_custom(abbr, context, spec_info["primary"])

    # 3. Check disease / sig codes
    disease_entry = custom_kb.lookup_disease(abbr)
    sig_freq = custom_kb.lookup_sig_frequency(abbr)
    food_timing = custom_kb.lookup_food_timing(abbr)

    return jsonify({
        "success": True,
        "abbreviation": abbr,
        "context": context,
        "detected_specialty": spec_info,
        "casi_benchmark": casi_res,
        "custom_medical_kb": custom_res,
        "disease_entry": disease_entry,
        "sig_code": sig_freq,
        "food_timing": food_timing
    })

@app.route("/api/casi/stats", methods=["GET"])
def casi_stats():
    """Return summary statistics of the CASI benchmark dataset."""
    stats = casi_engine.get_statistics()
    return jsonify(stats)

@app.route("/api/casi/abbreviations", methods=["GET"])
def casi_abbreviations():
    """Return all abbreviations present in CASI with their sense counts."""
    items = []
    for abbr in sorted(casi_engine.abbr_senses.keys()):
        senses = casi_engine.abbr_senses[abbr]
        top_sense = senses.most_common(1)[0]
        items.append({
            "abbreviation": abbr,
            "senses_count": len(senses),
            "total_occurrences": sum(senses.values()),
            "predominant_sense": top_sense[0],
            "predominant_percentage": round((top_sense[1] / sum(senses.values())) * 100, 1)
        })
    return jsonify({
        "total_abbreviations": len(items),
        "abbreviations": items
    })

@app.route("/api/casi/detail/<abbr>", methods=["GET"])
def casi_detail(abbr):
    """Return detailed sense distributions and sample contexts from CASI."""
    detail = casi_engine.get_abbreviation_detail(abbr)
    if not detail:
        return jsonify({"success": False, "error": f"Abbreviation '{abbr}' not found in CASI dataset."}), 404
    return jsonify({"success": True, "data": detail})

@app.route("/api/custom/summary", methods=["GET"])
def custom_summary():
    """Summary of the expanded custom medical dataset."""
    return jsonify({
        "diseases_count": len(custom_kb.diseases),
        "multispecialty_abbreviations": len(custom_kb.multispecialty_abbrs),
        "sig_frequencies_count": len(custom_kb.sig_frequencies),
        "food_timings_count": len(custom_kb.food_timings),
        "medicines_count": len(set(m["generic_name"] for m in custom_kb.medicines.values())),
        "ismp_error_prone_count": len(custom_kb.ismp_warnings),
        "sources": [
            "World Health Organization (WHO ICD-11 & Essential Medicines)",
            "U.S. FDA CDER Prescribing Guidelines & DailyMed",
            "British National Formulary (BNF) Sig Codes & Latin Abbreviations",
            "Institute for Safe Medication Practices (ISMP 2024 List of Error-Prone Abbreviations)",
            "American Heart Association / ACC Guidelines",
            "American Diabetes Association (ADA 2024 Standards of Care)"
        ]
    })

@app.route("/api/custom/all", methods=["GET"])
def custom_all():
    """Return full custom dataset records."""
    return jsonify({
        "diseases": custom_kb.diseases,
        "multispecialty_abbreviations": list(custom_kb.multispecialty_abbrs.values()),
        "sig_frequencies": list(custom_kb.sig_frequencies.values()),
        "food_timings": list(custom_kb.food_timings.values()),
        "routes": list(custom_kb.routes.values()),
        "ismp_warnings": custom_kb.ismp_warnings
    })

@app.route("/api/samples", methods=["GET"])
def get_samples():
    """List pre-configured sample prescriptions for instant testing."""
    samples = [
        {
            "id": "sample1",
            "title": "Cardio-Diabetic Consultation (CAD, T2DM, HTN)",
            "specialty": "Cardiology & Diabetology",
            "image_url": "/samples/sample1_cardio_diabetic.png",
            "description": "58-year-old male with CAD, Type 2 Diabetes, and Hypertension. Demonstrates context-aware disambiguation of MS (Mitral Stenosis vs Multiple Sclerosis) and food timing (AC vs PC vs QHS).",
            "text": """METRO HEART & METABOLIC CARE CENTER
Dr. Sarah Mitchell, MD, FACC
Senior Consultant Interventional Cardiologist & Diabetologist | Reg. #74921
PATIENT: Mr. Robert Sterling, 58 Yrs / Male
DATE: 12-Nov-2026
CLINICAL DIAGNOSIS / INDICATION: CAD (Status Post PTCA), T2DM, Essential HTN, Dyslipidemia

℞
1. Tab Pantoprazole 40 mg
Sig: 1 tab OD AC (Ante Cibum) | Frequency: Once daily | Timing: 30 mins Before Breakfast
Duration: 30 days (Indication: Acid peptic prophylaxis)

2. Tab Metformin HCl 500 mg
Sig: 1 tab BD PC (Post Cibum) | Frequency: Twice daily | Timing: Immediately After Meals
Duration: 30 days (Indication: Glycemic control in T2DM)

3. Tab Atorvastatin 20 mg
Sig: 1 tab QHS (Hora Somni) | Frequency: Once daily | Timing: At Bedtime
Duration: 30 days (Indication: Lipid lowering & plaque stabilization)

4. Tab Amlodipine 5 mg
Sig: 1 tab OD (Omni Die) | Frequency: Once daily | Timing: Morning After Food
Duration: 30 days (Indication: Blood pressure management)

5. Tab Aspirin (Ecosprin) 75 mg
Sig: 1 tab OD PC | Frequency: Once daily | Timing: After Lunch
Duration: 30 days (Indication: Antiplatelet therapy)

CLINICAL FINDINGS & INVESTIGATION SUMMARY:
1. 2D Echo report: Mild LA dilation, EF 52%. Mitral valve leaflets normal; MS ruled out.
2. ECG: Normal sinus rhythm, rate 74/min. No acute ST-T ischemic changes.
3. Patient advised strict diabetic diet, low sodium intake, and regular BP/SMBG monitoring."""
        },
        {
            "id": "sample2",
            "title": "Pulmonology & Acute Infection (CAP, Asthma)",
            "specialty": "Pulmonology & Infectious Disease",
            "image_url": "/samples/sample2_pulmonology_infection.png",
            "description": "42-year-old female with Community-Acquired Pneumonia and asthma exacerbation. Demonstrates PE (Pulmonary Embolism vs Physical Exam), PRN, SOS, and antibiotic food instructions.",
            "text": """APEX PULMONARY & CRITICAL CARE CLINIC
Dr. Rajesh Patel, MD, FCCP
Consultant Pulmonologist & Sleep Specialist | Reg. #58319
PATIENT: Ms. Emily Watson, 42 Yrs / Female
DATE: 14-Nov-2026
CLINICAL DIAGNOSIS / INDICATION: Community Acquired Pneumonia (CAP), Bronchial Asthma Exacerbation

℞
1. Tab Augmentin 625 mg (Amoxicillin + Clav)
Sig: 1 tab TID PC | Frequency: Three times a day | Timing: After Meals
Duration: 7 days (Indication: Bacterial respiratory infection)

2. Inhaler Salbutamol 100 mcg (Ventolin)
Sig: 2 puffs QID PRN | Frequency: Four times a day / As needed | Timing: When breathless or wheezing
Duration: 14 days (Indication: Acute bronchospasm rescue)

3. Tab Paracetamol (Dolo) 650 mg
Sig: 1 tab SOS / PRN | Frequency: As needed (max 3 tabs/day) | Timing: After food for fever > 100°F or bodyache
Duration: 5 days (Indication: Fever & myalgia relief)

4. Syr Ambroxol + Guaiphenesin 10 ml
Sig: 10 ml TID PC | Frequency: Three times a day | Timing: After Food with warm water
Duration: 7 days (Indication: Productive cough & mucolysis)

CLINICAL FINDINGS & INVESTIGATION SUMMARY:
1. CXR PA view shows right lower zone patchy consolidation. No pleural effusion.
2. CTA Chest performed in ER: Pulmonary Embolism (PE) ruled out.
3. Spirometry: FEV1/FVC ratio 0.68, reversible with bronchodilator. Steam inhalation TID."""
        },
        {
            "id": "sample3",
            "title": "Neurology Clinic (Multiple Sclerosis, Neuropathic Pain)",
            "specialty": "Neurology & Neuroimmunology",
            "image_url": "/samples/sample3_neurology_ms_clinic.png",
            "description": "36-year-old female in MS follow-up. Demonstrates context-aware disambiguation of MS to Multiple Sclerosis, alongside bedtime dosing (QHS) and spasticity management.",
            "text": """UNIVERSITY NEUROSCIENCE INSTITUTE
Dr. Anthony Rossi, MD, FAAN
Professor & Chief of Clinical Neuroimmunology | Reg. #88102
PATIENT: Mrs. Laura Chen, 36 Yrs / Female
DATE: 15-Nov-2026
CLINICAL DIAGNOSIS / INDICATION: Relapsing-Remitting Multiple Sclerosis (MS), Neuropathic Dysesthesia

℞
1. Cap Pregabalin 75 mg
Sig: 1 cap QHS | Frequency: Once daily at bedtime | Timing: 30 mins before sleep
Duration: 30 days (Indication: Neuropathic pain & paresthesias)

2. Tab Baclofen 10 mg
Sig: 1 tab BD PC | Frequency: Twice daily | Timing: After Morning & Evening meals
Duration: 30 days (Indication: Lower extremity spasticity)

3. Cap Vitamin D3 60,000 IU
Sig: 1 cap QWK (Once Weekly) | Frequency: Once weekly | Timing: With fatty meal on Sundays
Duration: 8 weeks (Indication: Hypovitaminosis D in MS)

4. Tab Methylprednisolone 4 mg
Sig: Tapering schedule as directed | Frequency: As per written plan | Timing: Morning after breakfast with milk
Duration: 10 days (Indication: Post-relapse maintenance)

CLINICAL FINDINGS & INVESTIGATION SUMMARY:
1. MS Clinic Follow-up: EDSS score stable at 2.0. Patient reports reduced sensory tingling.
2. Recent 3T MRI Brain & Cervical Spine: Stable demyelinating lesions without active Gd-enhancement.
3. Mental Status (MS) exam: Intact cognition, MoCA score 29/30. Continue physiotherapy."""
        }
    ]
    return jsonify(samples)

@app.route("/samples/<path:filename>")
def serve_sample_image(filename):
    """Serve sample prescription images from the samples directory."""
    samples_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "samples"))
    return send_from_directory(samples_dir, filename)

@app.route("/")
def index():
    """Serve single-page frontend app."""
    return send_from_directory(app.static_folder, "index.html")

@app.route("/evaluation")
def evaluation_page():
    return send_from_directory(app.static_folder, "evaluation.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
