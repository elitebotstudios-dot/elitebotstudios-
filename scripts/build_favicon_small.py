#!/usr/bin/env python3
"""Build a legible small-size favicon from the brand monogram.

The master artwork is a metallic plate with a brushed-gold "EB" and fine
circuit traces. At 16 px that detail collapses into an indistinct gold shape,
so the 16 and 32 px icons use a simplified, high-contrast cut of the same
monogram: the same two letters, flat gold, no plate, no traces, no bevel.

The letters are drawn at 8x and reduced with a Lanczos filter, which keeps the
stems and counters crisp instead of smearing them the way a direct downscale of
the detailed artwork does.

    python3 scripts/build_favicon_small.py

Outputs (assets/):
    favicon-16x16.png    transparent, simplified monogram
    favicon-32x32.png    transparent, simplified monogram

Every other size keeps the detailed artwork: logo-mark.webp in the header and
the opaque 180/192/512 px tiles, where the full emblem has room to read.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
FONT_CANDIDATES = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
]
GOLD = (232, 200, 126, 255)          # lighter end of the brand gold, for contrast
MASTER = 512                          # supersampled working size


def load_font(size):
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    raise SystemExit('No suitable bold font found; install fonts-dejavu.')


def build_master():
    """Draw "EB" tightly into a square transparent canvas."""
    font = load_font(int(MASTER * 0.72))
    im = Image.new('RGBA', (MASTER, MASTER), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    left, top, right, bottom = draw.textbbox((0, 0), 'EB', font=font)
    draw.text(((MASTER - (right - left)) / 2 - left,
               (MASTER - (bottom - top)) / 2 - top), 'EB', font=font, fill=GOLD)
    box = im.split()[3].getbbox()
    im = im.crop(box)
    side = max(im.size)
    square = Image.new('RGBA', (side, side), (0, 0, 0, 0))
    square.paste(im, ((side - im.width) // 2, (side - im.height) // 2))
    return square


def main():
    master = build_master()
    for px in (16, 32):
        icon = master.resize((px, px), Image.LANCZOS)
        out = ASSETS / ('favicon-%dx%d.png' % (px, px))
        icon.save(out, optimize=True)
        print('wrote %s (%d bytes)' % (out.relative_to(ROOT), out.stat().st_size))


if __name__ == '__main__':
    main()
