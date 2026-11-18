"""
OCR Service for Medical Prescription & Report Interpretation.
Uses Windows.Media.Ocr (built-in Windows Runtime OCR engine)
with PIL image preprocessing, orientation normalization, and PDF support via PyMuPDF.
"""

import os
import json
import subprocess
import tempfile
from PIL import Image, ImageEnhance, ImageOps

class MedicalOcrService:
    def __init__(self):
        self.script_path = os.path.join(os.path.dirname(__file__), "win_ocr_runner.ps1")
        self._ensure_runner_script()

    def _ensure_runner_script(self):
        script_content = r'''param(
    [Parameter(Mandatory=$true)][string]$ImagePath
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[void][Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
[void][Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics, ContentType = WindowsRuntime]
[void][Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
[void][Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime]

function AwaitAction($asyncOp, $targetType) {
    $asTaskMethods = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { 
        $_.Name -eq 'AsTask' -and $_.IsGenericMethodDefinition 
    }
    $genMethod = $asTaskMethods[0].MakeGenericMethod($targetType)
    $task = $genMethod.Invoke($null, @($asyncOp))
    $task.Wait()
    return $task.Result
}

try {
    $fullPath = [System.IO.Path]::GetFullPath($ImagePath)
    $fileOp = [Windows.Storage.StorageFile]::GetFileFromPathAsync($fullPath)
    $file = AwaitAction $fileOp ([Windows.Storage.StorageFile])

    $streamOp = $file.OpenAsync([Windows.Storage.FileAccessMode]::Read)
    $stream = AwaitAction $streamOp ([Windows.Storage.Streams.IRandomAccessStream])

    $decoderOp = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)
    $decoder = AwaitAction $decoderOp ([Windows.Graphics.Imaging.BitmapDecoder])

    $bitmapOp = $decoder.GetSoftwareBitmapAsync()
    $bitmap = AwaitAction $bitmapOp ([Windows.Graphics.Imaging.SoftwareBitmap])

    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
    if (-not $engine) {
        $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new("en-US"))
    }

    $ocrOp = $engine.RecognizeAsync($bitmap)
    $result = AwaitAction $ocrOp ([Windows.Media.Ocr.OcrResult])

    $lines = @()
    if ($result.Lines) {
        foreach ($line in $result.Lines) {
            $lines += $line.Text
        }
    }

    $output = @{
        Success = $true
        FullText = $result.Text
        Lines = $lines
        LineCount = $lines.Count
        TextAngle = $result.TextAngle
    }
    $output | ConvertTo-Json -Compress
} catch {
    $errOutput = @{
        Success = $false
        Error = $_.Exception.Message
        FullText = ""
        Lines = @()
    }
    $errOutput | ConvertTo-Json -Compress
}
'''
        os.makedirs(os.path.dirname(self.script_path), exist_ok=True)
        with open(self.script_path, "w", encoding="utf-8") as f:
            f.write(script_content)

    def _run_single_ocr(self, image_path):
        """Run OCR on a single prepared image path."""
        try:
            cmd = [
                "powershell",
                "-ExecutionPolicy", "Bypass",
                "-File", self.script_path,
                "-ImagePath", os.path.abspath(image_path)
            ]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=25)
            if proc.returncode == 0 and proc.stdout.strip():
                # Extract JSON from output
                out = proc.stdout.strip()
                # Find outermost JSON object
                start = out.find("{")
                end = out.rfind("}")
                if start != -1 and end != -1:
                    data = json.loads(out[start:end+1])
                    return data
            return {"Success": False, "Error": proc.stderr or "Empty OCR output", "FullText": "", "Lines": []}
        except Exception as e:
            return {"Success": False, "Error": str(e), "FullText": "", "Lines": []}

    def process_image(self, input_path):
        """
        Preprocess image (contrast enhancement, auto-orientations 0/90/180/270)
        and extract best recognized text.
        """
        if not os.path.exists(input_path):
            return {"success": False, "error": f"File not found: {input_path}"}

        # Handle PDF
        if input_path.lower().endswith(".pdf"):
            return self._process_pdf(input_path)

        try:
            with Image.open(input_path) as img:
                # Convert to RGB
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                
                # Check 4 orientations to pick highest text yield
                best_res = {"FullText": "", "Lines": [], "Success": False}
                best_len = 0
                best_rot = 0

                with tempfile.TemporaryDirectory() as tmpdir:
                    for angle in [0, 90, 270, 180]:
                        rotated = img if angle == 0 else img.rotate(angle, expand=True)
                        
                        # Enhance contrast slightly for prescription readability
                        enhancer = ImageEnhance.Contrast(rotated)
                        enhanced = enhancer.enhance(1.4)
                        
                        tmp_file = os.path.join(tmpdir, f"test_{angle}.png")
                        enhanced.save(tmp_file, "PNG")

                        res = self._run_single_ocr(tmp_file)
                        text_len = len(res.get("FullText", "").strip())
                        if text_len > best_len:
                            best_len = text_len
                            best_res = res
                            best_rot = angle
                            # If we found substantial text (>50 chars), good enough
                            if text_len > 120:
                                break

                raw_full = best_res.get("FullText", "").strip()
                lines_list = best_res.get("Lines", [])
                if lines_list and "\n" not in raw_full:
                    cleaned_text = "\n".join(lines_list)
                else:
                    cleaned_text = raw_full

                return {
                    "success": True,
                    "full_text": cleaned_text,
                    "lines": lines_list,
                    "detected_rotation": best_rot,
                    "engine": "Windows Native OCR (English)",
                    "character_count": len(cleaned_text)
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _process_pdf(self, pdf_path):
        """Extract text from PDF, rendering pages if needed."""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_path)
            extracted_text = []
            for i, page in enumerate(doc):
                text = page.get_text()
                if text.strip():
                    extracted_text.append(text.strip())
                else:
                    # Render page as image and run OCR
                    pix = page.get_pixmap(dpi=200)
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                        pix.save(tmp.name)
                        tmp_name = tmp.name
                    res = self._run_single_ocr(tmp_name)
                    if os.path.exists(tmp_name):
                        os.remove(tmp_name)
                    if res.get("FullText"):
                        extracted_text.append(res["FullText"])
            
            combined = "\n\n".join(extracted_text)
            return {
                "success": True,
                "full_text": combined,
                "lines": [l.strip() for l in combined.splitlines() if l.strip()],
                "engine": "PyMuPDF + Windows Native OCR",
                "page_count": len(doc)
            }
        except Exception as e:
            return {"success": False, "error": f"PDF processing error: {str(e)}"}

if __name__ == "__main__":
    ocr = MedicalOcrService()
    test_img = r"c:\Users\2415j\Downloads\WhatsApp Image 2026-11-16 at 6.46.21 PM.jpeg"
    print("Testing OCR service on WhatsApp image (auto-rotation detection):")
    res = ocr.process_image(test_img)
    print("Success:", res.get("success"))
    print("Rotation detected:", res.get("detected_rotation"))
    print("Full text:", res.get("full_text"))
    print("Lines:", res.get("lines"))
