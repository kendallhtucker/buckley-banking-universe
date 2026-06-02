"""Build OG share card: real storyboard photo, centered in a broadcast frame.
No AI image manipulation — pure overlay with Pillow."""
from PIL import Image, ImageDraw, ImageFont
import os, urllib.request

W, H = 1200, 630
BAR_H = 110

YELLOW = (255, 207, 58)
CYAN = (103, 232, 255)
MAGENTA = (255, 62, 196)
BLACK = (4, 4, 10)

SRC = "assets/andy-nebula.jpg"
OUT = "assets/og-image-v3.jpg"

# Photo area = full width above the bar, with some inset padding
PAD = 36
photo_zone_w = W - 2 * PAD
photo_zone_h = H - BAR_H - 2 * PAD

# Load photo and fit (contain, no crop) inside the photo zone
img = Image.open(SRC).convert("RGB")
src_w, src_h = img.size
src_ratio = src_w / src_h
zone_ratio = photo_zone_w / photo_zone_h

if src_ratio > zone_ratio:
    # photo wider than zone -> fit to width
    new_w = photo_zone_w
    new_h = int(new_w / src_ratio)
else:
    # photo taller than zone -> fit to height
    new_h = photo_zone_h
    new_w = int(new_h * src_ratio)

img = img.resize((new_w, new_h), Image.LANCZOS)

# --- Build canvas (deep blue-black bg) ---
canvas = Image.new("RGB", (W, H), BLACK)

# Center the photo horizontally; align top of photo to top of photo zone
photo_x = (W - new_w) // 2
photo_y = PAD
canvas.paste(img, (photo_x, photo_y))

# --- Yellow bottom bar ---
canvas.paste(Image.new("RGB", (W, BAR_H), YELLOW), (0, H - BAR_H))

draw = ImageDraw.Draw(canvas)

# --- Fonts ---
os.makedirs("/home/user/workspace/.fonts", exist_ok=True)
for url, name in [
    ("https://github.com/google/fonts/raw/main/ofl/bungee/Bungee-Regular.ttf", "Bungee-Regular.ttf"),
    ("https://github.com/google/fonts/raw/main/ofl/vt323/VT323-Regular.ttf", "VT323-Regular.ttf"),
]:
    path = f"/home/user/workspace/.fonts/{name}"
    if not os.path.exists(path):
        try:
            urllib.request.urlretrieve(url, path)
        except Exception as e:
            print("font dl failed:", name, e)

def find_font(names, size):
    paths = ["/home/user/workspace/.fonts", "/usr/share/fonts", "/usr/local/share/fonts"]
    for base in paths:
        if not os.path.isdir(base): continue
        for root, _, files in os.walk(base):
            for f in files:
                if any(n.lower() in f.lower() for n in names):
                    try:
                        return ImageFont.truetype(os.path.join(root, f), size)
                    except Exception:
                        pass
    return None

# --- Tagline (auto-fit) ---
text = "A TRANSMISSION FROM DEEP SPACE"
size = 78
bungee = None
while size > 30:
    f = find_font(["Bungee-Regular", "Bungee"], size) or find_font(["DejaVuSans-Bold"], int(size*0.9))
    bbox = draw.textbbox((0,0), text, font=f)
    if bbox[2] - bbox[0] <= W - 100:
        bungee = f
        break
    size -= 2

bbox = draw.textbbox((0, 0), text, font=bungee)
tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
tx = (W - tw) // 2
ty = H - BAR_H + (BAR_H - th) // 2 - bbox[1]
draw.text((tx, ty), text, fill=BLACK, font=bungee)

# --- Cyan outer thin frame ---
def rect_outline(draw, box, color, width):
    x0, y0, x1, y1 = box
    for i in range(width):
        draw.rectangle((x0+i, y0+i, x1-i, y1-i), outline=color)

rect_outline(draw, (10, 10, W-11, H-11), CYAN, 2)

# --- L-shaped corner ticks ---
tick_len = 56
tick_w = 5
pad = 26

def corner(x, y, dx, dy):
    # horizontal segment
    hx0 = x if dx > 0 else x - tick_len + tick_w
    hx1 = hx0 + tick_len
    draw.rectangle((hx0, y, hx1, y + tick_w), fill=CYAN)
    # vertical segment
    vy0 = y if dy > 0 else y - tick_len + tick_w
    vy1 = vy0 + tick_len
    draw.rectangle((x, vy0, x + tick_w, vy1), fill=CYAN)

corner(pad, pad, 1, 1)                                # TL
corner(W - pad - tick_w, pad, -1, 1)                  # TR
# Bottom ticks anchor to top of yellow bar
by = H - BAR_H + 10
corner(pad, by, 1, -1)                                # BL pointing up-right
corner(W - pad - tick_w, by, -1, -1)                  # BR pointing up-left

# --- REC dot + CH 03 (top-left) ---
rx, ry = 64, 64
draw.ellipse((rx, ry, rx + 22, ry + 22), fill=MAGENTA)
vt = find_font(["VT323-Regular", "VT323"], 44) or find_font(["DejaVuSansMono"], 34)
draw.text((rx + 36, ry - 8), "REC", fill=CYAN, font=vt)
draw.text((rx, ry + 30), "CH 03", fill=CYAN, font=vt)

# --- Subtle scanlines over the whole canvas ---
overlay = Image.new("RGBA", (W, H), (0,0,0,0))
od = ImageDraw.Draw(overlay)
for y in range(0, H - BAR_H, 3):
    od.line((0, y, W, y), fill=(0, 0, 0, 26))
canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")

canvas.save(OUT, "JPEG", quality=88, optimize=True)
print(f"Wrote {OUT} ({os.path.getsize(OUT)} bytes)")
