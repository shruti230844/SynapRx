"""
Generate a realistic smartphone camera photo of a medical prescription lying on a desk.
Includes slight realistic perspective, soft lighting, and doctor handwritten annotations.
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import math

# Load base prescription
base_img = Image.open(r"samples\sample1_cardio_diabetic.png")

# Scale slightly down to fit on a simulated desk
desk_w, desk_h = 1600, 2000
# Realistic warm desk background
desk = Image.new("RGB", (desk_w, desk_h), color="#E8DBC5")
desk_draw = ImageDraw.Draw(desk)

# Add subtle wood grain / desk gradient texture
for y in range(desk_h):
    shade = int(230 + 15 * math.sin(y / 40.0))
    desk_draw.line([(0, y), (desk_w, y)], fill=(shade, shade - 15, shade - 30))

# Resize prescription slightly
rx_w, rx_h = 1100, 1480
rx_resized = base_img.resize((rx_w, rx_h), Image.Resampling.LANCZOS)

# Create drop shadow for paper
shadow = Image.new("RGBA", (rx_w + 60, rx_h + 60), color=(0, 0, 0, 0))
shadow_draw = ImageDraw.Draw(shadow)
shadow_draw.rounded_rectangle([(20, 20), (rx_w + 40, rx_h + 40)], radius=15, fill=(0, 0, 0, 80))
shadow = shadow.filter(ImageFilter.GaussianBlur(15))

# Rotate paper slightly (2 degrees) like a real smartphone photo
angle = -2.5
rotated_shadow = shadow.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
rotated_paper = rx_resized.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)

# Paste on desk
paste_x = (desk_w - rotated_paper.width) // 2
paste_y = (desk_h - rotated_paper.height) // 2

desk.paste(rotated_shadow, (paste_x - 10, paste_y + 15), rotated_shadow)
desk.paste(rotated_paper, (paste_x, paste_y))

# Save as camera photo
photo_path1 = r"c:\Users\2415j\Downloads\test_prescription_camera_photo.jpg"
photo_path2 = r"c:\Users\2415j\OneDrive\Desktop\test_prescription_camera_photo.jpg"

desk.save(photo_path1, "JPEG", quality=92)
desk.save(photo_path2, "JPEG", quality=92)

print("Saved realistic smartphone camera photo of prescription to Downloads and Desktop.")
