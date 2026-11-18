"""
Generate realistic prescription and clinical report sample images for testing OCR and AI interpretation.
"""

from PIL import Image, ImageDraw, ImageFont
import os

os.makedirs("samples", exist_ok=True)

def draw_prescription(filename, title, doctor, subtitle, patient, date, diagnosis, rx_items, notes):
    # Standard A5/A4 aspect ratio image
    width, height = 1200, 1600
    img = Image.new("RGB", (width, height), color="#FCFDFF")
    draw = ImageDraw.Draw(img)

    # Decorative header banner
    draw.rectangle([(0, 0), (width, 140)], fill="#1E3A8A") # Navy blue
    draw.rectangle([(0, 140), (width, 148)], fill="#3B82F6") # Light blue accent

    # Clinic Header Text
    try:
        font_head = ImageFont.truetype("arialbd.ttf", 36)
        font_sub = ImageFont.truetype("arial.ttf", 20)
        font_bold = ImageFont.truetype("arialbd.ttf", 24)
        font_regular = ImageFont.truetype("arial.ttf", 22)
        font_small = ImageFont.truetype("arial.ttf", 18)
        font_rx = ImageFont.truetype("georgiab.ttf", 46)
        font_hand = ImageFont.truetype("timesbd.ttf", 26)
    except:
        font_head = font_sub = font_bold = font_regular = font_small = font_rx = font_hand = ImageFont.load_default()

    draw.text((50, 30), title, fill="#FFFFFF", font=font_head)
    draw.text((50, 78), doctor, fill="#E0E7FF", font=font_sub)
    draw.text((50, 106), subtitle, fill="#93C5FD", font=font_small)

    # Patient Details Strip
    draw.rectangle([(40, 170), (width - 40, 240)], fill="#F1F5F9", outline="#CBD5E1", width=2)
    draw.text((60, 185), f"PATIENT: {patient}", fill="#0F172A", font=font_bold)
    draw.text((60, 212), f"CLINICAL DIAGNOSIS / INDICATION: {diagnosis}", fill="#334155", font=font_regular)
    draw.text((width - 320, 185), f"DATE: {date}", fill="#0F172A", font=font_bold)
    draw.text((width - 320, 212), "OPD REG: #MED-2026-9481", fill="#64748B", font=font_small)

    # Rx Symbol
    draw.text((60, 260), "℞", fill="#1E3A8A", font=font_rx)
    draw.line([(60, 320), (width - 60, 320)], fill="#E2E8F0", width=2)

    # Rx Items Table
    y = 350
    for idx, item in enumerate(rx_items, 1):
        # Card container for each medicine
        box_y1 = y
        box_y2 = y + 105
        draw.rectangle([(60, box_y1), (width - 60, box_y2)], fill="#FFFFFF", outline="#E2E8F0", width=1)
        
        # Medicine number and name
        draw.text((80, y + 12), f"{idx}. {item['name']}", fill="#0F172A", font=font_bold)
        
        # Dosage & Sig line
        sig_str = f"Sig: {item['sig']}  |  Frequency: {item['freq']}  |  Timing: {item['timing']}"
        draw.text((105, y + 44), sig_str, fill="#1D4ED8", font=font_hand)
        
        # Duration & Indication
        meta_str = f"Duration: {item['duration']}   (Indication: {item['for']})"
        draw.text((105, y + 74), meta_str, fill="#475569", font=font_small)
        
        y += 125

    # Clinical Notes & Ambiguous Medical Acronyms Section
    y += 20
    draw.rectangle([(60, y), (width - 60, y + 170)], fill="#FEF3C7", outline="#F59E0B", width=2)
    draw.text((80, y + 15), "CLINICAL FINDINGS & INVESTIGATION SUMMARY:", fill="#92400E", font=font_bold)
    
    note_lines = notes.split("\n")
    ny = y + 50
    for nline in note_lines:
        draw.text((80, ny), nline, fill="#78350F", font=font_regular)
        ny += 30

    # Safety Notice & Signature Footer
    draw.line([(60, height - 170), (width - 60, height - 170)], fill="#CBD5E1", width=2)
    draw.text((60, height - 150), "Important: Take medications strictly as scheduled. Do not substitute without physician authorization.", fill="#64748B", font=font_small)
    draw.text((60, height - 125), "Emergency Contact: 24/7 Helpline: 1800-MED-CARE | Next Review: After 4 weeks", fill="#64748B", font=font_small)

    # Doctor signature placeholder
    draw.text((width - 320, height - 150), doctor.split(",")[0], fill="#1E3A8A", font=font_hand)
    draw.text((width - 320, height - 115), "Authorized Medical Practitioner", fill="#94A3B8", font=font_small)

    img.save(filename, "PNG", quality=95)
    print(f"Saved {filename}")

# Prescription 1: Cardio-Diabetic Prescription
draw_prescription(
    "samples/sample1_cardio_diabetic.png",
    "METRO HEART & METABOLIC CARE CENTER",
    "Dr. Sarah Mitchell, MD, FACC",
    "Senior Consultant Interventional Cardiologist & Diabetologist | Reg. #74921",
    "Mr. Robert Sterling, 58 Yrs / Male",
    "12-Nov-2026",
    "CAD (Status Post PTCA), T2DM, Essential HTN, Dyslipidemia",
    [
        {"name": "Tab Pantoprazole 40 mg", "sig": "1 tab OD AC (Ante Cibum)", "freq": "Once daily", "timing": "30 mins Before Breakfast", "duration": "30 days", "for": "Acid peptic prophylaxis"},
        {"name": "Tab Metformin HCl 500 mg", "sig": "1 tab BD PC (Post Cibum)", "freq": "Twice daily", "timing": "Immediately After Meals", "duration": "30 days", "for": "Glycemic control in T2DM"},
        {"name": "Tab Atorvastatin 20 mg", "sig": "1 tab QHS (Hora Somni)", "freq": "Once daily", "timing": "At Bedtime", "duration": "30 days", "for": "Lipid lowering & plaque stabilization"},
        {"name": "Tab Amlodipine 5 mg", "sig": "1 tab OD (Omni Die)", "freq": "Once daily", "timing": "Morning After Food", "duration": "30 days", "for": "Blood pressure management"},
        {"name": "Tab Aspirin (Ecosprin) 75 mg", "sig": "1 tab OD PC", "freq": "Once daily", "timing": "After Lunch", "duration": "30 days", "for": "Antiplatelet therapy"}
    ],
    "1. 2D Echo report: Mild LA dilation, EF 52%. Mitral valve leaflets normal; MS ruled out.\n2. ECG: Normal sinus rhythm, rate 74/min. No acute ST-T ischemic changes.\n3. Patient advised strict diabetic diet, low sodium intake, and regular BP/SMBG monitoring."
)

# Prescription 2: Respiratory & Acute Infection Prescription
draw_prescription(
    "samples/sample2_pulmonology_infection.png",
    "APEX PULMONARY & CRITICAL CARE CLINIC",
    "Dr. Rajesh Patel, MD, FCCP",
    "Consultant Pulmonologist & Sleep Specialist | Reg. #58319",
    "Ms. Emily Watson, 42 Yrs / Female",
    "14-Nov-2026",
    "Community Acquired Pneumonia (CAP), Bronchial Asthma Exacerbation",
    [
        {"name": "Tab Augmentin 625 mg (Amoxicillin + Clav)", "sig": "1 tab TID PC", "freq": "Three times a day", "timing": "After Meals", "duration": "7 days", "for": "Bacterial respiratory infection"},
        {"name": "Inhaler Salbutamol 100 mcg (Ventolin)", "sig": "2 puffs QID PRN", "freq": "Four times a day / As needed", "timing": "When breathless or wheezing", "duration": "14 days", "for": "Acute bronchospasm rescue"},
        {"name": "Tab Paracetamol (Dolo) 650 mg", "sig": "1 tab SOS / PRN", "freq": "As needed (max 3 tabs/day)", "timing": "After food for fever > 100°F or bodyache", "duration": "5 days", "for": "Fever & myalgia relief"},
        {"name": "Syr Ambroxol + Guaiphenesin 10 ml", "sig": "10 ml TID PC", "freq": "Three times a day", "timing": "After Food with warm water", "duration": "7 days", "for": "Productive cough & mucolysis"}
    ],
    "1. CXR PA view shows right lower zone patchy consolidation. No pleural effusion.\n2. CTA Chest performed in ER: Pulmonary Embolism (PE) ruled out.\n3. Spirometry: FEV1/FVC ratio 0.68, reversible with bronchodilator. Steam inhalation TID."
)

# Prescription 3: Neurology Clinic Note with Multiple Sclerosis
draw_prescription(
    "samples/sample3_neurology_ms_clinic.png",
    "UNIVERSITY NEUROSCIENCE INSTITUTE",
    "Dr. Anthony Rossi, MD, FAAN",
    "Professor & Chief of Clinical Neuroimmunology | Reg. #88102",
    "Mrs. Laura Chen, 36 Yrs / Female",
    "15-Nov-2026",
    "Relapsing-Remitting Multiple Sclerosis (MS), Neuropathic Dysesthesia",
    [
        {"name": "Cap Pregabalin 75 mg", "sig": "1 cap QHS", "freq": "Once daily at bedtime", "timing": "30 mins before sleep", "duration": "30 days", "for": "Neuropathic pain & paresthesias"},
        {"name": "Tab Baclofen 10 mg", "sig": "1 tab BD PC", "freq": "Twice daily", "timing": "After Morning & Evening meals", "duration": "30 days", "for": "Lower extremity spasticity"},
        {"name": "Cap Vitamin D3 60,000 IU", "sig": "1 cap QWK (Once Weekly)", "freq": "Once weekly", "timing": "With fatty meal on Sundays", "duration": "8 weeks", "for": "Hypovitaminosis D in MS"},
        {"name": "Tab Methylprednisolone 4 mg", "sig": "Tapering schedule as directed", "freq": "As per written plan", "timing": "Morning after breakfast with milk", "duration": "10 days", "for": "Post-relapse maintenance"}
    ],
    "1. MS Clinic Follow-up: EDSS score stable at 2.0. Patient reports reduced sensory tingling.\n2. Recent 3T MRI Brain & Cervical Spine: Stable demyelinating lesions without active Gd-enhancement.\n3. Mental Status (MS) exam: Intact cognition, MoCA score 29/30. Continue physiotherapy."
)

print("Sample prescriptions generated successfully.")
