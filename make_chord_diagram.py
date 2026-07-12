#!/usr/bin/env python3
"""
Cuatro chord diagram generator — matches micuatro.com style.

Usage:
    python3 make_chord_diagram.py "G7"  g7.jpg  --fret 3132 --finger 4132
    python3 make_chord_diagram.py "Bb"  bb.jpg  --fret 3435 --finger 1213 --barre 3333
    python3 make_chord_diagram.py "Bø"  bm7b5.jpg --fret 3332
    python3 make_chord_diagram.py "C"   c.jpg   --fret 3000 --nfrets 6
    python3 make_chord_diagram.py --name G7
    python3 make_chord_diagram.py --name Cmaj --nfrets 6

Arguments
---------
chord_name   Display label shown at top of diagram (e.g. "G7", "Bø", "Bb").
             Optional when --name is used (defaults to the chord name from CSV).
output       Output filename.  If no directory given, saved to chord files folder.
             Defaults to chord_name.jpg in that folder.

--name CHORD    Look up chord in chords_v2.csv and use its fret/fingering/barre.
                --fret, --finger, and --barre are not needed when --name is given.
--fret  BFDA    4 fret numbers in B-F#-D-A string order (matches chords_v2.csv).
                0 = open string.
--finger BFDA   (optional) 4 finger numbers in B-F#-D-A order.  0 = open/unused.
                If omitted, fingers are auto-assigned 1→4 sorted by fret ASC.
--barre BFDA    (optional) Barre fret for each string; 0 = string not in barre.
                All non-zero values must be the same fret number.
                e.g. --barre 3333 → full barre at fret 3 across all strings.
--nfrets N      Number of frets to draw (default 4, min 4, max 15).
                Image height grows to keep cell size constant.
--scale N       Size multiplier (default 2 → ~116×200 px JPEG).
-R              Reverse input order: treat --fret/--finger/--barre as A-D-F#-B
                instead of the default B-F#-D-A.

String order on the cuatro neck (left → right):  A  D  F#  B
"""

import argparse, csv
from PIL import Image, ImageDraw, ImageFont, ImageColor
import os, sys

CHORD_DIR   = "/home/eklein/Documents/Cuatro/CuatroAcordes/Lista de acordes_files/"
CREATED_DIR = "/home/eklein/Documents/Cuatro/CuatroAcordes/CreatedDiagrams/"
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
CSV_PATH    = os.path.join(SCRIPT_DIR, 'chords_v2.csv')

SHARP_NOTES  = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
STRING_OPEN  = [9, 2, 6, 11]   # open-string semitones for A, D, F#, B (C=0)

INTERVAL_TO_GRADE = {
    0: '1',  1: '♭2', 2: '2',  3: '♭3', 4: '3',
    5: '4',  6: '♭5', 7: '5',  8: '♭6', 9: '6',
    10: '♭7', 11: '7',
}


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
                       output_path=None, scale=2, n_frets=4, name_color='black',
                       show_notes=True, root=None):
    """
    Parameters
    ----------
    chord_name : str
    frets      : list[int]  length-4, B-F#-D-A order (matches chords_v2.csv); 0 = open
    fingers    : list[int] | None   finger number per string, B-F#-D-A order (0 = unused)
    barre      : list[int] | None   barre fret per string, B-F#-D-A order (0 = not in barre)
    output_path: str | None
    scale      : int   size multiplier (base 55×75 px)
    n_frets    : int   number of frets to draw (4–15); image grows taller to keep cell size constant
    name_color : str   color name for the chord label (e.g. 'black', 'red', 'navy')
    root       : int | None  root semitone 0–11 (C=0); when given, draws interval grades
                             above the fretboard (below chord name), same font as note labels
    """
    BG     = (255, 255, 255)
    LINE   = (45,  45,  45)
    NUT    = (30,  30,  30)
    DOT_F  = (35,  35,  35)
    DOT_T  = (255, 255, 255)
    TEXT_C = (0,   0,   0)

    # El resto de esta función dibuja en orden físico izquierda→derecha A D F# B;
    # se invierte aquí una sola vez desde el orden de entrada B F# D A.
    frets   = list(reversed(frets))
    fingers = list(reversed(fingers)) if fingers else None
    barre   = list(reversed(barre)) if barre else None

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
    SANS_B    = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    SANS_R    = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    DEJAVU_R  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    name_h       = int(13 * scale)
    nut_t        = max(2, int(2.5 * scale))
    cell_h       = int(13 * scale)   # fixed cell height from original 4-fret design
    fb_left      = int(10 * scale)
    grade_area_h = max(8, int(6 * scale)) if root is not None else 0
    fb_top       = name_h + grade_area_h + int(3 * scale) + (nut_t if from_nut else 0)
    fb_h         = n_frets * cell_h
    fb_bot       = fb_top + fb_h
    note_area_h  = max(12, int(10 * scale)) if show_notes else 0
    W        = 58 * scale          # 3 extra units on right so B-string dots don't clip
    H        = fb_bot + note_area_h
    fb_right = W - int(7 * scale)  # keeps fretboard at same position as original
    fb_w     = fb_right - fb_left

    f_name  = _try_font(SANS_B, int(13 * scale))
    f_fr    = _try_font(SANS_R, int(9 * scale))   # was 6.5 — larger fret indicator
    f_dot   = _try_font(SANS_B, int(8 * scale))   # was 6.5 — larger finger numbers
    f_note  = _try_font(SANS_R, max(9, int(7 * scale)))
    f_grade = _try_font(DEJAVU_R, max(6, int(5 * scale)))

    # ── Canvas ────────────────────────────────────────────────────────────────
    img  = Image.new('RGB', (W, H), BG)
    draw = ImageDraw.Draw(img)

    str_xs  = [fb_left + round(i * fb_w / 3) for i in range(4)]
    fret_ys = [fb_top  + round(i * cell_h) for i in range(n_frets + 1)]
    lw      = max(1, scale // 2)
    dot_r   = int(5 * scale)

    # ── Chord name ────────────────────────────────────────────────────────────
    # Shrink the font if the label is too wide for the canvas (e.g. "C#m(Maj7)").
    name_max_w = W - int(4 * scale)
    name_size  = int(13 * scale)
    while name_size > int(7 * scale) and draw.textlength(chord_name, font=f_name) > name_max_w:
        name_size -= 1
        f_name = _try_font(SANS_B, name_size)
    draw.text((W // 2, int(2 * scale) + name_h // 2),
              chord_name, fill=name_color, font=f_name, anchor='mm')

    # ── Interval grades ───────────────────────────────────────────────────────
    if root is not None:
        grade_y = fb_top - nut_t - int(1 * scale)   # sits flush above the nut
        for i, f in enumerate(frets):
            note_semi = (STRING_OPEN[i] + f) % 12
            grade = INTERVAL_TO_GRADE[(note_semi - root) % 12]
            draw.text((str_xs[i], grade_y), grade, fill=TEXT_C, font=f_grade, anchor='mb')

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

    # ── String note labels ────────────────────────────────────────────────────
    if show_notes:
        note_y = fb_bot + note_area_h // 2
        for i, f in enumerate(frets):
            note_semi = (STRING_OPEN[i] + f) % 12
            draw.text((str_xs[i], note_y), SHARP_NOTES[note_semi],
                      fill=TEXT_C, font=f_note, anchor='mm')

    if output_path:
        img.save(output_path, 'JPEG', quality=95)
    return img


# ── CLI ───────────────────────────────────────────────────────────────────────

FLAT_TO_SHARP_ROOT = {'db': 'C#', 'eb': 'D#', 'gb': 'F#', 'ab': 'G#', 'bb': 'A#'}

_FLAT_ROOTS = {'Db':'C#','Eb':'D#','Fb':'E','Gb':'F#','Ab':'G#','Bb':'A#','Cb':'B'}

def _parse_root(s):
    """Accept a root note name (C, C#, Bb, …) or integer 0–11."""
    try:
        v = int(s)
        if 0 <= v <= 11:
            return v
        raise argparse.ArgumentTypeError(f'root integer must be 0–11, got {v}')
    except ValueError:
        pass
    name = s[0].upper() + s[1:] if len(s) > 1 else s.upper()
    if name in SHARP_NOTES:
        return SHARP_NOTES.index(name)
    if name in _FLAT_ROOTS:
        return SHARP_NOTES.index(_FLAT_ROOTS[name])
    raise argparse.ArgumentTypeError(f'unknown root note: {s!r}')

def _enharmonic(name):
    """Return sharp-root equivalent of a flat-root chord name, or None.
    e.g. 'Bbm7b5' → 'A#m7b5',  'Eb' → 'D#'
    """
    if len(name) >= 2 and name[:2].lower() in FLAT_TO_SHARP_ROOT:
        return FLAT_TO_SHARP_ROOT[name[:2].lower()] + name[2:]
    return None


def _load_chord(name):
    """Case-insensitive lookup with enharmonic fallback.
    Returns (frets, fingers, barre) in B,F#,D,A order, or None if not found.
    """
    enh = _enharmonic(name)
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            chord = row['Chord'].lower()
            if chord == name.lower() or (enh and chord == enh.lower()):
                fr, fg, ba = row['Fret'], row['Fingering'], row['Barre']
                frets   = [int(c) for c in fr]
                fingers = [int(c) for c in fg]
                if ba:
                    barre = [int(c) for c in ba]
                    barre = barre if any(b > 0 for b in barre) else None
                else:
                    barre = None
                return frets, fingers, barre
    return None


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
    p.add_argument('chord_name', nargs='?', default=None,
                   help='Display label (optional when --name is used)')
    p.add_argument('output', nargs='?', default=None,
                   help='Output filename (default: chord_name.jpg in CreatedDiagrams/)')
    p.add_argument('--name',   default=None, metavar='CHORD',
                   help='Look up chord in chords_v2.csv (e.g. G7, Cmaj, Bm7b5)')
    p.add_argument('--fret',   default=None, type=_parse4,
                   help='4-digit fret numbers B-F#-D-A (matches chords_v2.csv), e.g. 3132')
    p.add_argument('--finger', default=None, type=_parse4,
                   help='4-digit finger numbers B-F#-D-A, e.g. 4132')
    p.add_argument('--barre',  default=None, type=_parse4,
                   help='4-digit barre frets B-F#-D-A, e.g. 3333')
    p.add_argument('--nfrets', type=int, default=4, metavar='N',
                   help='Number of frets to draw (default 4, min 4, max 15)')
    p.add_argument('--color',  default='black', metavar='COLOR',
                   help='Color of the chord name label (default: black). '
                        'Use plain names: black, red, navy, darkgreen, etc.')
    p.add_argument('--scale',  type=int, default=2,
                   help='Size multiplier (default 2 → 116×200 px approx)')
    p.add_argument('-R', action='store_true',
                   help='Reverse string order: read --fret/--finger/--barre as A-D-F#-B '
                        'instead of the default B-F#-D-A')
    p.add_argument('--names', dest='show_notes', action='store_true', default=True,
                   help='Show note names below the diagram (default: on)')
    p.add_argument('--no-names', dest='show_notes', action='store_false',
                   help='Hide note names below the diagram')
    p.add_argument('--root', default=None, type=_parse_root, metavar='NOTE',
                   help='Root note (e.g. D, C#, Bb or integer 0-11); '
                        'draws interval grades above the fretboard')
    args = p.parse_args()

    # ── Resolve fret/finger/barre from CSV or CLI args ─────────────────────────
    if args.name:
        result = _load_chord(args.name)
        if result is None:
            p.error(f'chord {args.name!r} not found in chords_v2.csv')
        frets, fingers, barre = result
        # Capitalise first letter so 'bbm7b5' displays as 'Bbm7b5'
        auto_name = args.name[0].upper() + args.name[1:]
        display_name = args.chord_name or auto_name
    else:
        if not args.fret:
            p.error('--fret is required when --name is not given')
        if not args.chord_name:
            p.error('chord_name is required when --name is not given')
        if args.R:
            args.fret = args.fret[::-1]
            if args.finger: args.finger = args.finger[::-1]
            if args.barre:  args.barre  = args.barre[::-1]
        frets, fingers, barre = args.fret, args.finger, args.barre
        display_name = args.chord_name

    if not (4 <= args.nfrets <= 15):
        p.error(f'--nfrets must be between 4 and 15, got {args.nfrets}')
    try:
        ImageColor.getrgb(args.color)
    except ValueError:
        p.error(f'unknown color name: {args.color!r}')

    out = args.output
    if out is None:
        safe = display_name.lower().replace('#', 's').replace('ø', 'o').replace(' ', '_')
        out  = safe + '.jpg'
    if os.path.dirname(out) == '':
        out = os.path.join(CREATED_DIR, out)

    make_chord_diagram(display_name, frets, fingers, barre, out, args.scale,
                       n_frets=args.nfrets, name_color=args.color,
                       show_notes=args.show_notes, root=args.root)
    print(f"Saved: {out}")
