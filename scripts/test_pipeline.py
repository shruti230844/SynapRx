from backend.ocr_service import MedicalOcrService
from backend.prescription_parser import PrescriptionInterpreter

ocr = MedicalOcrService()
parser = PrescriptionInterpreter()

for s_path in ['samples/sample1_cardio_diabetic.png', 'samples/sample2_pulmonology_infection.png', 'samples/sample3_neurology_ms_clinic.png']:
    print(f"\n==================== TESTING {s_path} ====================")
    res = ocr.process_image(s_path)
    analysis = parser.interpret(res['full_text'])
    print("Specialty:", analysis['specialty'])
    print("Medications:", [f"{m['drug_name']} ({m['dosage_strength']}, {m['food_timing_badge']})" for m in analysis['medications']])
    print("Key Abbreviations:")
    for a in analysis['abbreviations']:
        if a['token'] in ['CAD', 'T2DM', 'HTN', 'MS', 'PE', 'CAP', 'AC', 'PC', 'TID', 'QHS', 'PRN', 'SOS', 'BD', 'OD']:
            print(f"  * {a['token']} -> {a['meaning']} ({a.get('confidence', '')}%) [{a.get('source', '')[:35]}]")
