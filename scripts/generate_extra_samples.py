import os
from PIL import Image, ImageDraw, ImageFont

def make_presc(filename, title, doctor, subtitle, patient, date, diagnosis, rx_items, notes):
    width, height = 1200, 1600
    img = Image.new('RGB', (width, height), color='#FCFDFF')
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (width, 140)], fill='#1E3A8A')
    draw.rectangle([(0, 140), (width, 148)], fill='#3B82F6')
    try:
        font_head = ImageFont.truetype('arialbd.ttf', 36)
        font_sub = ImageFont.truetype('arial.ttf', 20)
        font_bold = ImageFont.truetype('arialbd.ttf', 24)
        font_regular = ImageFont.truetype('arial.ttf', 22)
        font_small = ImageFont.truetype('arial.ttf', 18)
        font_rx = ImageFont.truetype('georgiab.ttf', 46)
    except Exception:
        font_head = font_sub = font_bold = font_regular = font_small = font_rx = ImageFont.load_default()

    draw.text((50, 30), title, fill='#FFFFFF', font=font_head)
    draw.text((50, 78), doctor, fill='#E0E7FF', font=font_sub)
    draw.text((50, 106), subtitle, fill='#93C5FD', font=font_small)

    draw.rectangle([(40, 170), (width - 40, 240)], fill='#F1F5F9', outline='#CBD5E1', width=2)
    draw.text((60, 185), f'PATIENT: {patient}', fill='#0F172A', font=font_bold)
    draw.text((60, 212), f'CLINICAL DIAGNOSIS / INDICATION: {diagnosis}', fill='#334155', font=font_regular)
    draw.text((width - 320, 185), f'DATE: {date}', fill='#0F172A', font=font_bold)
    draw.text((width - 320, 212), 'OPD REG: #MED-2026-9481', fill='#64748B', font=font_small)

    draw.text((60, 260), '℞', fill='#1E3A8A', font=font_rx)
    draw.line([(60, 320), (width - 60, 320)], fill='#E2E8F0', width=2)

    y = 350
    for idx, item in enumerate(rx_items, 1):
        draw.rectangle([(50, y), (width - 50, y + 105)], fill='#FFFFFF', outline='#E2E8F0', width=1)
        name = item['name']
        sig = item['sig']
        freq = item['freq']
        timing = item['timing']
        dur = item['duration']
        ind = item['for']
        draw.text((70, y + 12), f'{idx}. {name}', fill='#1E293B', font=font_bold)
        draw.text((70, y + 44), f'Sig: {sig} | Frequency: {freq} | Timing: {timing}', fill='#475569', font=font_regular)
        draw.text((70, y + 74), f'Duration: {dur} (Indication: {ind})', fill='#0369A1', font=font_small)
        y += 120

    y += 20
    draw.rectangle([(40, y), (width - 40, y + 150)], fill='#F8FAFC', outline='#CBD5E1', width=1)
    draw.text((60, y + 15), 'CLINICAL FINDINGS & INVESTIGATION SUMMARY:', fill='#0F172A', font=font_bold)
    lines = notes.split('\n')
    for l_idx, line in enumerate(lines):
        draw.text((60, y + 50 + l_idx * 30), line, fill='#334155', font=font_regular)

    img.save(filename)
    print('Saved', filename)

if __name__ == '__main__':
    make_presc(
        'samples/sample4_rheumatology_clinic.png',
        'ST. JUDE ARTHRITIS & RHEUMATOLOGY CENTER',
        'Dr. Victoria Vance, MD, FACR',
        'Senior Consultant Rheumatologist | Reg. #61984',
        'Mrs. Brenda Miller, 49 Yrs / Female',
        '16-Nov-2026',
        'Rheumatoid Arthritis (RA), Osteopenia, Chronic Joint Pain',
        [
            {'name': 'Tab Methotrexate 15 mg', 'sig': '1 tab QWK', 'freq': 'Once weekly', 'timing': 'Take on Friday with dinner', 'duration': '12 weeks', 'for': 'Disease-modifying antirheumatic therapy'},
            {'name': 'Tab Folic Acid 5 mg', 'sig': '1 tab OD', 'freq': 'Once daily', 'timing': 'Morning after breakfast (skip on Friday)', 'duration': '12 weeks', 'for': 'Methotrexate toxicity prevention'},
            {'name': 'Tab Hydroxychloroquine 200 mg', 'sig': '1 tab BD PC', 'freq': 'Twice daily', 'timing': 'After meals', 'duration': '12 weeks', 'for': 'Synovial inflammation control'},
            {'name': 'Tab Calcium + Vitamin D3 500 mg', 'sig': '1 tab OD CC', 'freq': 'Once daily', 'timing': 'With lunch', 'duration': '12 weeks', 'for': 'Bone density preservation'}
        ],
        '1. Joint exam: Symmetric bilateral wrist and MCP synovitis; DAS28 score 4.2.\n2. RF positive, anti-CCP positive; RA confirmed on serology.\n3. Baseline LFT and CBC reviewed; monitor blood counts monthly.'
    )

    make_presc(
        'samples/sample5_gastroenterology_clinic.png',
        'DIGESTIVE HEALTH SPECIALISTS CLINIC',
        'Dr. Michael Brooks, MD, FACG',
        'Consultant Gastroenterologist & Hepatologist | Reg. #45210',
        'Mr. David Kumar, 52 Yrs / Male',
        '17-Nov-2026',
        'Gastroesophageal Reflux Disease (GERD), Peptic Ulcer Disease (PUD)',
        [
            {'name': 'Tab Pantoprazole 40 mg', 'sig': '1 tab OD AC', 'freq': 'Once daily', 'timing': '30 mins Before Breakfast', 'duration': '30 days', 'for': 'Gastric acid suppression'},
            {'name': 'Syr Sucralfate 10 ml', 'sig': '10 ml QID AC', 'freq': 'Four times a day', 'timing': '1 hour Before meals and at bedtime', 'duration': '14 days', 'for': 'Mucosal cytoprotection'},
            {'name': 'Tab Domperidone 10 mg', 'sig': '1 tab TID AC', 'freq': 'Three times a day', 'timing': '15 mins Before meals', 'duration': '14 days', 'for': 'Upper GI motility support'},
            {'name': 'Syr Antacid 15 ml', 'sig': '15 ml SOS PC', 'freq': 'As needed', 'timing': 'After meals for acute heartburn', 'duration': '14 days', 'for': 'Acid reflux symptom relief'}
        ],
        '1. Upper GI Endoscopy: Grade B reflux esophagitis; antral gastritis noted.\n2. H. pylori rapid urease test negative; PUD healing confirmed.\n3. Strict dietary modifications advised: avoid spicy food, caffeine, and late dinners.'
    )
