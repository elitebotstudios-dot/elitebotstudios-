#!/usr/bin/env python3
"""Build the brand asset set from the master logo artwork.

Source: the owner-supplied master image (RGB on pure black). This script
removes the outer background with a border flood fill, trims the mark, and
writes every size the site and manifest reference. Run it whenever the master
artwork changes:

    python3 scripts/build_brand_assets.py path/to/master.png

Outputs (assets/):
    logo-mark.webp          transparent mark, 512px tall, for the header
    favicon-32x32.png       transparent, cropped to the monogram
    favicon-16x16.png       transparent, cropped to the monogram
    apple-touch-icon.png    180px opaque tile (iOS does not support alpha)
    logo-192.png            192px opaque tile (manifest)
    logo-512.png            512px opaque tile (manifest, schema logo)
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
TILE_BG = (8, 11, 16, 255)          # --bg
MAGIC = (255, 0, 255)


def cut_background(im):
    """Remove near-black pixels connected to the border, keep interior darks."""
    work = im.convert('RGB').copy()
    w, h = work.size
    for seed in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        ImageDraw.floodfill(work, seed, MAGIC, thresh=24)
    px = work.load()
    alpha = Image.new('L', (w, h), 255)
    ap = alpha.load()
    for y in range(h):
        for x in range(w):
            if px[x, y] == MAGIC:
                ap[x, y] = 0
    # Erode one pixel further so anti-aliased halo does not survive on dark pages.
    eroded = alpha.filter(ImageFilter.MinFilter(3))
    out = im.convert('RGBA')
    out.putalpha(eroded)
    return out


def trim(im, margin=0):
    box = im.split()[3].getbbox()
    l, t, r, b = box
    return im.crop((max(0, l - margin), max(0, t - margin),
                    min(im.width, r + margin), min(im.height, b + margin)))


def gold_crop(im, pad=10):
    """Crop to the golden monogram so small favicons stay legible."""
    px = im.load()
    w, h = im.size
    xs, ys = [], []
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            r, g, b, a = px[x, y]
            if a > 200 and r > 140 and g > 100 and b < 120:
                xs.append(x)
                ys.append(y)
    if not xs:
        return im
    box = (max(0, min(xs) - pad), max(0, min(ys) - pad),
           min(w, max(xs) + pad), min(h, max(ys) + pad))
    return im.crop(box)


def square(im, size, background=None):
    """Fit the mark into a square, optionally on an opaque tile."""
    canvas = Image.new('RGBA', (size, size), background or (0, 0, 0, 0))
    scale = min(size / im.width, size / im.height)
    w, h = max(1, round(im.width * scale)), max(1, round(im.height * scale))
    resized = im.resize((w, h), Image.LANCZOS)
    canvas.alpha_composite(resized, ((size - w) // 2, (size - h) // 2))
    return canvas


def main():
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/home/user/uploads/image-1.png')
    if not source.exists():
        sys.exit('master artwork not found: %s' % source)
    master = Image.open(source).convert('RGBA')
    cut = trim(cut_background(master))

    # Header mark: transparent, bounded so the header stays light.
    header = cut.copy()
    header.thumbnail((512, 512), Image.LANCZOS)
    header.save(ASSETS / 'logo-mark.webp', 'WEBP', quality=92, method=6)

    # Favicons: crop to the monogram so the letters read at 16–32 px.
    mono = gold_crop(cut)
    square(mono, 32).save(ASSETS / 'favicon-32x32.png', optimize=True)
    square(mono, 16).save(ASSETS / 'favicon-16x16.png', optimize=True)

    # Opaque tiles for platforms that do not rely on transparency.
    square(cut, 180, TILE_BG).convert('RGB').save(ASSETS / 'apple-touch-icon.png', optimize=True)
    square(cut, 192, TILE_BG).convert('RGB').save(ASSETS / 'logo-192.png', optimize=True)
    square(cut, 512, TILE_BG).convert('RGB').save(ASSETS / 'logo-512.png', optimize=True)

    for name in ('logo-mark.webp', 'favicon-32x32.png', 'favicon-16x16.png',
                 'apple-touch-icon.png', 'logo-192.png', 'logo-512.png'):
        path = ASSETS / name
        print('%-24s %6d bytes  %s' % (name, path.stat().st_size, Image.open(path).size))


if __name__ == '__main__':
    main()
