#!/usr/bin/env python3
"""
Cuatro chord diagram generator — matches micuatro.com style.

Usage:
    python3 make_chord_diagram.py "G7"  g7.jpg  --fret 2313 --finger 2314
    python3 make_chord_diagram.py "Bb"  bb.jpg  --fret 5343 --finger 3121 --barre 3333
    python3 make_chord_diagram.py "Bø"  bm7b5.jpg --fret 2333
    python3 make_chord_diagram.py "C"   c.jpg   --fret 0003 --nfrets 6

Arguments
---------
chord_name   Display label shown at top of diagram (e.g. "G7", "Bø", "Bb")
output       Output filename.  If no directory given, saved to chord files folder.
             Defaults to chord_name.jpg in that folder.

--fret  ADFSB   4 fret numbers in A-D-F#-B string order.  0 = open string.
--finger ADFSB  (optional) 4 finger numbers in A-D-F#-B order.  0 = open/unused.
                If omitted, fingers are auto-assigned 1→4 sorted by fret ASC.
--barre ADFSB   (optional) Barre fret for each string; 0 = string not in barre.
                All non-zero values must be the same fret number.
                e.g. --barre 3333 → full barre at fret 3 across all strings.
--nfrets N      Number of frets to draw (default 4, min 4, max 15).
                Image height grows to keep cell size constant.
--scale N       Size multiplier (default 1 → 55×75 px JPEG, same as micuatro.com).

String order on the cuatro neck (left → right):  A  D  F#  B
"""

import argparse
from PIL import Image, ImageDraw, ImageFont, ImageColor
import os, sys

CHORD_DIR   = "/home/eklein/Documents/Cuatro/CuatroAcordes/Lista de acordes_files/"
CREATED_DIR = "/home/eklein/Documents/Cuatro/CuatroAcordes/CreatedDiagrams/"


# ── Drawing helpers ────────────────────────────────────────────────────────────

def _capsule(draw, x1, x2, cy, r, fill):
    """Filled horizontal capsule for barre chords."""
    draw.rectangle([x1, cy - r, x2, cy + r], fill=fill)
    draw.ellipse([x1 - r, cy - r, x1 + r, cy + r], fill=fill)
    draw.ellipse([x2 - r, cy - r, x2 + r, cy + r], fill=fill)


def _try_font(path, size):
    try:    return ImageFont.truetype(path, size)
    except: return ImageFont.load_default()


# ── Core diagram function ─────────────────────────────────────────────────────

def make_chord_diagram(chord_name, frets, fingers=None, barre=None,
                       output_path=None, scale=2, n_frets=4, name_color='black'):
    """
    Parameters
    ----------
    chord_name : str
    frets      : list[int]  length-4, A-D-F#-B order; 0 = open
    fingers    : list[int] | None   finger number per string (0 = unused)
    barre      : list[int] | None   barre fret per string   (0 = not in barre)
    output_path: str | None
    scale      : int   size multiplier (base 55×75 px)
    n_frets    : int   number of frets to draw (4–15); image grows taller to keep cell size constant
    name_color : str   color name for the chord label (e.g. 'black', 'red', 'navy')
    """
    BG     = (255, 255, 255)
    LINE   = (45,  45,  45)
    NUT    = (30,  30,  30)
    DOT_F  = (35,  35,  35)
    DOT_T  = (255, 255, 255)
    TEXT_C = (0,   0,   0)

    non_zero = [f for f in frets if f > 0]
    max_fret = max(non_zero) if non_zero else 0
    min_fret = min(non_zero) if non_zero else 0
    from_nut = (max_fret <= n_frets)
    start_fr = 1 if from_nut else min_fret

    # ── Finger map ────────────────────────────────────────────────────────────
    if fingers:
        finger_map = {i: fingers[i] for i in range(4) if fingers[i] > 0}
    else:
        sorted_pos = sorted((f, i) for i, f in enumerate(frets) if f > 0)
        finger_map = {i: fn for fn, (f, i) in enumerate(sorted_pos, start=1)}

    # ── Barre properties ──────────────────────────────────────────────────────
    barre_fret    = None
    barre_strings = []
    barre_finger  = None
    if barre and any(b > 0 for b in barre):
        barre_fret    = min(b for b in barre if b > 0)
        barre_strings = [i for i, b in enumerate(barre) if b > 0]
        # finger used for the barre = the finger at the barre fret among barred strings
        barre_finger  = next(
            (finger_map[i] for i in barre_strings
             if frets[i] == barre_fret and finger_map.get(i)),
            1
        )

    # ── Layout — image height grows with n_frets to keep cell height constant ─
    SANS_B   = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    SANS_R   = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    name_h   = int(13 * scale)
    nut_t    = max(2, int(2.5 * scale))
    cell_h   = int(13 * scale)   # fixed cell height from original 4-fret design
    fb_left  = int(10 * scale)
    fb_top   = name_h + int(3 * scale) + (nut_t if from_nut else 0)
    fb_h     = n_frets * cell_h
    fb_bot   = fb_top + fb_h
    W        = 58 * scale          # 3 extra units on right so B-string dots don't clip
    H        = fb_bot + int(4 * scale)
    fb_right = W - int(7 * scale)  # keeps fretboard at same position as original
    fb_w     = fb_right - fb_left

    f_name = _try_font(SANS_B, int(13 * scale))
    f_fr   = _try_font(SANS_R, int(9 * scale))   # was 6.5 — larger fret indicator
    f_dot  = _try_font(SANS_B, int(8 * scale))   # was 6.5 — larger finger numbers

    # ── Canvas ────────────────────────────────────────────────────────────────
    img  = Image.new('RGB', (W, H), BG)
    draw = ImageDraw.Draw(img)

    str_xs  = [fb_left + round(i * fb_w / 3) for i in range(4)]
    fret_ys = [fb_top  + round(i * cell_h) for i in range(n_frets + 1)]
    lw      = max(1, scale // 2)
    dot_r   = int(5 * scale)

    # ── Chord name ────────────────────────────────────────────────────────────
    draw.text((W // 2, int(2 * scale) + name_h // 2),
              chord_name, fill=name_color, font=f_name, anchor='mm')

    # ── Nut or fret indicator ─────────────────────────────────────────────────
    if from_nut:
        draw.rectangle([fb_left, fb_top - nut_t, fb_right, fb_top], fill=NUT)
    else:
        mid_y = (fret_ys[0] + fret_ys[1]) // 2
        draw.text((int(2.5 * scale), mid_y), str(start_fr),
                  fill=TEXT_C, font=f_fr, anchor='mm')

    # ── Grid ──────────────────────────────────────────────────────────────────
    for y in fret_ys:
        draw.line([(fb_left, y), (fb_right, y)], fill=LINE, width=lw)
    for x in str_xs:
        draw.line([(x, fb_top), (x, fb_bot)], fill=LINE, width=lw)

    # ── Barre (drawn first so dots appear on top) ─────────────────────────────
    if barre_fret is not None:
        barre_row = barre_fret - start_fr
        if 0 <= barre_row < n_frets:
            cy = (fret_ys[barre_row] + fret_ys[barre_row + 1]) // 2
            x1 = str_xs[min(barre_strings)]
            x2 = str_xs[max(barre_strings)]
            barre_r = int(dot_r * 0.75)
            _capsule(draw, x1, x2, cy, barre_r, DOT_F)

    # ── Individual dots and open-string markers ────────────────────────────────
    for i, f in enumerate(frets):
        x = str_xs[i]
        if f == 0:
            pass  # open strings: no marker drawn
        else:
            # String already represented by the barre at this fret → skip individual dot
            if barre and barre[i] > 0 and f == barre_fret:
                continue
            rel = f - start_fr
            if 0 <= rel < n_frets:
                cy = (fret_ys[rel] + fret_ys[rel + 1]) // 2
                draw.ellipse([x - dot_r, cy - dot_r, x + dot_r, cy + dot_r], fill=DOT_F)
                fn_s = str(finger_map.get(i, ''))
                if fn_s:
                    draw.text((x, cy), fn_s, fill=DOT_T, font=f_dot, anchor='mm')

    if output_path:
        img.save(output_path, 'JPEG', quality=95)
    return img


# ── CLI ───────────────────────────────────────────────────────────────────────

def _parse4(s):
    """Accept '2313' or '2 3 1 3' or '2,3,1,3' → [2, 3, 1, 3]."""
    s = s.strip()
    if len(s) == 4 and s.isdigit():
        return [int(c) for c in s]
    parts = s.replace(',', ' ').split()
    if len(parts) == 4:
        return [int(p) for p in parts]
    raise argparse.ArgumentTypeError(f"Expected 4 digits, got: {s!r}")


if __name__ == '__main__':
    p = argparse.ArgumentParser(description="Cuatro chord diagram generator",
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                epilog=__doc__)
    p.add_argument('chord_name', help='Chord label, e.g. "G7" or "Bø"')
    p.add_argument('output', nargs='?', default=None,
                   help='Output filename (default: chord_name.jpg in chord files folder)')
    p.add_argument('--fret',   required=True, type=_parse4,
                   help='4-digit fret numbers A-D-F#-B, e.g. 2313')
    p.add_argument('--finger', default=None,  type=_parse4,
                   help='4-digit finger numbers A-D-F#-B, e.g. 2314')
    p.add_argument('--barre',  default=None,  type=_parse4,
                   help='4-digit barre frets A-D-F#-B, e.g. 3333')
    p.add_argument('--nfrets', type=int, default=4, metavar='N',
                   help='Number of frets to draw (default 4, min 4, max 15)')
    p.add_argument('--color',  default='black', metavar='COLOR',
                   help='Color of the chord name label (default: black). '
                        'Use plain names: black, red, navy, darkgreen, etc.')
    p.add_argument('--scale',  type=int, default=1,
                   help='Size multiplier (default 1 → 55×75 px, same as micuatro.com)')
    args = p.parse_args()

    if not (4 <= args.nfrets <= 15):
        p.error(f'--nfrets must be between 4 and 15, got {args.nfrets}')
    try:
        ImageColor.getrgb(args.color)
    except ValueError:
        p.error(f'unknown color name: {args.color!r}')

    out = args.output
    if out is None:
        safe = args.chord_name.lower().replace('#', 's').replace('ø', 'o').replace(' ', '_')
        out  = safe + '.jpg'
    if os.path.dirname(out) == '':
        out = os.path.join(CREATED_DIR, out)

    make_chord_diagram(args.chord_name, args.fret, args.finger, args.barre, out, args.scale,
                       n_frets=args.nfrets, name_color=args.color)
    print(f"Saved: {out}")
