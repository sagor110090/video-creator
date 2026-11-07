"""Draw the AI Video Creator app icon (1024x1024 PNG) and build AppIcon.icns with iconutil.

Run: desktop/.venv/bin/python desktop/packaging/make_icon.py
"""
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

S = 1024
OUT = Path(__file__).resolve().parents[1] / "assets"


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def gradient(size, c1, c2, c3):
    """Diagonal 3-stop gradient: c1 top-left -> c2 middle -> c3 bottom-right."""
    w, h = size
    g = Image.new("RGB", size)
    px = g.load()
    for y in range(h):
        for x in range(w):
            t = (x / w * 0.55 + y / h * 0.45)
            px[x, y] = lerp(c1, c2, t / 0.5) if t < 0.5 else lerp(c2, c3, (t - 0.5) / 0.5)
    return g


def rounded_mask(size, box, radius, scale=4):
    big = Image.new("L", (size[0] * scale, size[1] * scale), 0)
    ImageDraw.Draw(big).rounded_rectangle([v * scale for v in box], radius * scale, fill=255)
    return big.resize(size, Image.LANCZOS)


def draw():
    icon = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    tile = (100, 100, 924, 924)                       # macOS icon grid: 824px tile, soft shadow
    shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((100, 118, 924, 942), 185, fill=(4, 8, 30, 150))
    icon.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(22)))

    grad = gradient((S, S), (37, 99, 235), (67, 56, 202), (147, 51, 234)).convert("RGBA")
    # soft light from the top-left
    glow = Image.new("L", (S, S), 0)
    ImageDraw.Draw(glow).ellipse((-120, -160, 640, 560), fill=110)
    grad = Image.composite(Image.new("RGBA", (S, S), (255, 255, 255, 255)), grad,
                           glow.filter(ImageFilter.GaussianBlur(120)).point(lambda v: v // 3))
    mask = rounded_mask((S, S), tile, 185)
    tile_img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    tile_img.paste(grad, (0, 0), mask)
    icon.alpha_composite(tile_img)

    # inner rim highlight
    rim = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(rim).rounded_rectangle((104, 104, 920, 920), 182, outline=(255, 255, 255, 70), width=4)
    icon.alpha_composite(rim)

    sc = 4
    fg = Image.new("RGBA", (S * sc, S * sc), (0, 0, 0, 0))
    d = ImageDraw.Draw(fg)
    # play button: a properly rounded triangle (inset triangle + round-joined outline)
    cx, cy = 430 * sc, 512 * sc
    h, rad = 205 * sc, 46 * sc                       # half-height of the triangle, corner radius
    inset = [(cx - h * 0.62 + rad, cy - h + rad * 1.7), (cx - h * 0.62 + rad, cy + h - rad * 1.7),
             (cx + h * 1.0 - rad * 1.6, cy)]
    d.polygon(inset, fill=(255, 255, 255, 255))
    for i in range(3):
        a, b = inset[i], inset[(i + 1) % 3]
        d.line([a, b], fill=(255, 255, 255, 255), width=int(rad * 2))
    for x, y in inset:
        d.ellipse((x - rad, y - rad, x + rad, y + rad), fill=(255, 255, 255, 255))
    # voice wave bars to the right of the play button
    bars = [(688, 88), (748, 158), (808, 104)]
    for x, hh in bars:
        d.rounded_rectangle(((x - 18) * sc, (cy / sc - hh) * sc, (x + 18) * sc, (cy / sc + hh) * sc),
                            18 * sc, fill=(255, 255, 255, 215))
    # AI sparkle, top-right
    sx, sy, R = 760 * sc, 250 * sc, 86 * sc
    star = []
    for i in range(8):
        a = math.pi / 4 * i - math.pi / 2
        rr = R if i % 2 == 0 else R * 0.28
        star.append((sx + rr * math.cos(a), sy + rr * math.sin(a)))
    d.polygon(star, fill=(253, 224, 71, 255))
    d.ellipse((sx - 12 * sc, sy - 12 * sc, sx + 12 * sc, sy + 12 * sc), fill=(255, 255, 255, 255))
    fg = fg.resize((S, S), Image.LANCZOS)
    # soft drop shadow under the white shapes
    sh = Image.new("RGBA", (S, S), (10, 10, 60, 0))
    sh.putalpha(fg.getchannel("A").point(lambda v: v * 0.45).filter(ImageFilter.GaussianBlur(14)))
    sh = ImageChops.offset(sh, 0, 10)
    icon.alpha_composite(sh)
    icon.alpha_composite(fg)
    return icon


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    png = OUT / "app_icon.png"
    img = draw()
    img.save(png)
    iconset = Path(tempfile.mkdtemp()) / "AppIcon.iconset"
    iconset.mkdir()
    for size in (16, 32, 128, 256, 512):
        img.resize((size, size), Image.LANCZOS).save(iconset / f"icon_{size}x{size}.png")
        img.resize((size * 2, size * 2), Image.LANCZOS).save(iconset / f"icon_{size}x{size}@2x.png")
    subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(OUT / "AppIcon.icns")], check=True)
    shutil.rmtree(iconset.parent)
    print("wrote", png, "and", OUT / "AppIcon.icns")


if __name__ == "__main__":
    sys.exit(main())
