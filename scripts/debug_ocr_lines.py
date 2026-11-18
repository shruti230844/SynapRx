from backend.ocr_service import MedicalOcrService
ocr = MedicalOcrService()
res = ocr.process_image('samples/sample1_cardio_diabetic.png')
print("All OCR lines:")
for idx, l in enumerate(res['lines']):
    print(f"{idx}: {repr(l)}")
