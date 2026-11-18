"""
Generate and copy all prescription photos and scans directly into the user's Downloads folder.
Includes both realistic camera photos and clean clinical scans.
"""

from PIL import Image, ImageDraw, ImageFilter
import os
import math

downloads_dir = r"C:\Users\2415j\Downloads"
samples_dir = r"samples"

# Ensure output directory
os.makedirs(downloads_dir, exist_ok=True)

samples = [
    {
        "src": os.path.join(samples_dir, "sample1_cardio_diabetic.png"),
        "scan_name": "1_Cardio_Prescription_Scan.png",
        "photo_name": "1_Cardio_Prescription_Camera_Photo.jpg",
        "desk_color": (232, 219, 197),
        "angle": -2.2
    },
    {
        "src": os.path.join(samples_dir, "sample2_pulmonology_infection.png"),
        "scan_name": "2_Pulmonology_Prescription_Scan.png",
        "photo_name": "2_Pulmonology_Prescription_Camera_Photo.jpg",
        "desk_color": (224, 226, 228), # Clinic gray desk
        "angle": 1.8
    },
    {
        "src": os.path.join(samples_dir, "sample3_neurology_ms_clinic.png"),
        "scan_name": "3_Neurology_MS_Prescription_Scan.png",
        "photo_name": "3_Neurology_MS_Prescription_Camera_Photo.jpg",
        "desk_color": (218, 205, 185), # Wooden desk
        "angle": -1.5
    }
]

saved_files = []

for item in samples:
    base_img = Image.open(item["src"])
    
    # 1. Save pristine scan version
    scan_dest = os.path.join(downloads_dir, item["scan_name"])
    base_img.save(scan_dest, "PNG")
    saved_files.append(scan_dest)
    
    # 2. Render realistic smartphone camera photo on a desk
    desk_w, desk_h = 1600, 2000
    desk = Image.new("RGB", (desk_w, desk_h), color=item["desk_color"])
    desk_draw = ImageDraw.Draw(desk)
    
    # Add subtle desk gradient / shadow
    base_rgb = item["desk_color"]
    for y in range(desk_h):
        shift = int(10 * math.sin(y / 50.0))
        desk_draw.line([(0, y), (desk_w, y)], fill=(
            max(0, min(255, base_rgb[0] + shift)),
            max(0, min(255, base_rgb[1] + shift)),
            max(0, min(255, base_rgb[2] + shift))
        ))
        
    rx_w, rx_h = 1120, 1490
    rx_resized = base_img.resize((rx_w, rx_h), Image.Resampling.LANCZOS)
    
    # Realistic soft paper drop shadow
    shadow = Image.new("RGBA", (rx_w + 60, rx_h + 60), color=(0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle([(20, 20), (rx_w + 40, rx_h + 40)], radius=15, fill=(0, 0, 0, 75))
    shadow = shadow.filter(ImageFilter.GaussianBlur(16))
    
    angle = item["angle"]
    rotated_shadow = shadow.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    rotated_paper = rx_resized.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    
    paste_x = (desk_w - rotated_paper.width) // 2
    paste_y = (desk_h - rotated_paper.height) // 2
    
    desk.paste(rotated_shadow, (paste_x - 12, paste_y + 14), rotated_shadow)
    desk.paste(rotated_paper, (paste_x, paste_y))
    
    photo_dest = os.path.join(downloads_dir, item["photo_name"])
    desk.save(photo_dest, "JPEG", quality=93)
    saved_files.append(photo_dest)

print("Saved all prescription files to Downloads:")
for f in saved_files:
    size_kb = os.path.getsize(f) / 1024
    print(f"  * {os.path.basename(f)} ({size_kb:.1f} KB)")
