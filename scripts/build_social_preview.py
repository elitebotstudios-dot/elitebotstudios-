#!/usr/bin/env python3
"""Regenerate assets/social-preview.png (1200×630) from the brand mark.

Social cards are the one place the full logo appears at a large size, so the
master artwork is composited rather than redrawn. Run after changing the logo:

    python3 scripts/build_social_preview.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
W, H = 1200, 630
GOLD = (216, 182, 106)
WHITE = (244, 246, 248)
MUTED = (157, 170, 184)
BG = (9, 12, 17)


def font(name, size):
    root = '/usr/share/fonts/truetype/dejavu'
    return ImageFont.truetype(f'{root}/{name}', size)


def main():
    card = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(card)

    # quiet blueprint grid
    for x in range(40, W, 40):
        d.line((x, 0, x, H), fill=(15, 20, 27), width=1)
    for y in range(30, H, 40):
        d.line((0, y, W, y), fill=(15, 20, 27), width=1)

    # warm panel glow behind the mark
    mark = Image.open(ASSETS / 'logo-mark.webp').convert('RGBA')
    mark.thumbnail((430, 430), Image.LANCZOS)
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for r in range(360, 0, -6):
        a = int(16 * (1 - r / 360))
        gd.ellipse((150 + 215 - r, 300 - r, 150 + 215 + r, 300 + r), fill=(216, 182, 106, a))
    card = Image.alpha_composite(card.convert('RGBA'), glow).convert('RGB')
    card.paste(mark, (150, 300 - mark.height // 2), mark)
    d = ImageDraw.Draw(card)

    mono = font('DejaVuSansMono.ttf', 17)
    bold = font('DejaVuSans-Bold.ttf', 60)
    body = font('DejaVuSans.ttf', 22)
    small = font('DejaVuSansMono.ttf', 15)

    x = 620
    d.text((x, 176), 'ELITE BOT STUDIOS', font=mono, fill=WHITE)
    d.line((x, 214, x + 120, 214), fill=(60, 54, 40), width=2)
    d.rectangle((x, 213, x + 40, 215), fill=GOLD)

    d.text((x, 246), 'Power. Control.', font=bold, fill=WHITE)
    d.text((x, 312), 'Intelligence.', font=bold, fill=GOLD)
    d.text((x, 404), 'Embedded systems  ·  Power electronics', font=body, fill=MUTED)
    d.text((x, 436), 'Intelligent hardware  ·  Documented design', font=body, fill=MUTED)

    d.line((72, 528, W - 72, 528), fill=(38, 46, 54), width=1)
    d.text((72, 556), 'MUHAMMAD SHAHZAIB ABBAS  /  NUST · PAKISTAN', font=small, fill=(183, 192, 202))
    d.text((W - 72, 556), 'ELITEBOTSTUDIOS.ME', font=small, fill=GOLD, anchor='ra')

    card.save(ASSETS / 'social-preview.png', quality=94, optimize=True)
    print('social-preview.png', card.size, (ASSETS / 'social-preview.png').stat().st_size, 'bytes')


if __name__ == '__main__':
    main()
