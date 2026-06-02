"""Build OG share card: use the user-provided base image, swap the bottom bar text."""
from PIL import Image, ImageDraw, ImageFont
import os, urllib.request

SRC = "assets/og-base.jpg"
OUT = "assets/og-image-v4.jpg"

YELLOW = (255, 207, 58)
BLACK = (4, 4, 10)

img = Image.open(SRC).convert("RGB")
W, H = img.size  # 1200 x 630

# The yellow bar in the base image runs along the bottom.
# Detect its top edge by scanning columns from bottom-up for the dominant yellow row.
px = img.load()

def is_yellow(rgb):
    r, g, b = rgb
    # loose match: high red+green, low-ish blue, R near G
    return r > 180 and g > 130 and b < 140 and abs(r - g) < 90 and r > b + 40

# Sample at the far left edge of the bar (x=40-90) where there's no text
sample_xs = list(range(40, 90, 5))
yellow_rows = []
for y in range(H):
    yellow_count = sum(1 for x in sample_xs if is_yellow(px[x, y]))
    if yellow_count > len(sample_xs) * 0.5:
        yellow_rows.append(y)

if not yellow_rows:
    raise RuntimeError("could not detect yellow bar")

# Take the longest contiguous run (the bar)
runs = []
cur = [yellow_rows[0]]
for y in yellow_rows[1:]:
    if y == cur[-1] + 1:
        cur.append(y)
    else:
        runs.append(cur)
        cur = [y]
runs.append(cur)
run = max(runs, key=len)
bar_top, bar_bottom = run[0], run[-1]

print(f"Yellow bar detected: y={bar_top} to y={bar_bottom} (height={bar_bottom-bar_top+1})")

# Repaint the bar solid yellow (covers old text)
draw = ImageDraw.Draw(img)
draw.rectangle((0, bar_top, W, bar_bottom), fill=YELLOW)

# --- Load Bungee font ---
os.makedirs("/home/user/workspace/.fonts", exist_ok=True)
font_url = "https://github.com/google/fonts/raw/main/ofl/bungee/Bungee-Regular.ttf"
font_path = "/home/user/workspace/.fonts/Bungee-Regular.ttf"
if not os.path.exists(font_path):
    urllib.request.urlretrieve(font_url, font_path)

text = "A TRANSMISSION FROM DEEP SPACE."
bar_h = bar_bottom - bar_top + 1
# fit text to bar width with side padding
side_pad = 60
target_w = W - 2 * side_pad

size = bar_h
font = None
while size > 20:
    f = ImageFont.truetype(font_path, size)
    bbox = draw.textbbox((0, 0), text, font=f)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    if tw <= target_w and th <= bar_h * 0.72:
        font = f
        break
    size -= 1

bbox = draw.textbbox((0, 0), text, font=font)
tw = bbox[2] - bbox[0]
th = bbox[3] - bbox[1]
tx = (W - tw) // 2 - bbox[0]
ty = bar_top + (bar_h - th) // 2 - bbox[1]
draw.text((tx, ty), text, fill=BLACK, font=font)

img.save(OUT, "JPEG", quality=90, optimize=True)
print(f"Wrote {OUT} ({os.path.getsize(OUT)} bytes) — font size {size}")
