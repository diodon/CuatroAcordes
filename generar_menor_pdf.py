#!/usr/bin/env python3
"""Genera acordes_por_tonalidad_menor.pdf — mismo estilo que el original,
   diagramas generados desde chords.csv con make_chord_diagram (6 trastes)."""

import csv, io, os, sys
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from make_chord_diagram import make_chord_diagram

CSV_PATH  = os.path.join(SCRIPT_DIR, 'chords.csv')
OUT_PDF   = "/home/eklein/Documents/Cuatro/00-Clases/Practicas/acordes_por_tonalidad_menor.pdf"

PAGE_W, PAGE_H = A4[1], A4[0]   # Landscape A4 (~842 × 595 pts)

N_FRETS        = 6
DIAGRAM_SCALE  = 2
IMG_ASPECT     = 58 / (13 + 3 + 2.5 + N_FRETS * 13 + 4)   # ≈ 0.577

SHARP_NOTES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
FLAT_NOTES  = ['C','Db','D','Eb','E','F','Gb','G','Ab','A','Bb','B']

# Natural minor scale degrees: (semitones_from_root, quality, roman_label, is_single_col)
# V uses quality '7' (harmonic minor dominant); IIø has no secondary dominant.
MINOR_DEGREES = [
    (0,  'm',    'Im',   False),
    (2,  'm7b5', 'IIø',  True),
    (3,  'maj',  'bIII', False),
    (5,  'm',    'IVm',  False),
    (7,  '7',    'V',    False),
    (8,  'maj',  'bVI',  False),
    (10, 'maj',  'bVII', False),
]

KEYS = [
    (0,  'Do menor'),
    (2,  'Re menor'),
    (4,  'Mi menor'),
    (5,  'Fa menor'),
    (7,  'Sol menor'),
    (9,  'La menor'),
    (11, 'Si menor'),
]

ROW_COLORS = [
    '#FFF2F2',   # Do menor  – light pink
    '#F2FFF2',   # Re menor  – light green
    '#FFFFF2',   # Mi menor  – light yellow
    '#FFF8F2',   # Fa menor  – light peach
    '#F2F8FF',   # Sol menor – light blue
    '#F2FFF8',   # La menor  – light cyan-green
    '#F8F2FF',   # Si menor  – light lavender
]

# ── Style colours ─────────────────────────────────────────────────────────────
TITLE_CLR  = colors.HexColor('#0A7878')
HDR_BG     = colors.HexColor('#1E3A5C')
HDR_TEXT   = colors.white
CHORD_CLR  = colors.HexColor('#1A1A1A')
GRID_CLR   = colors.HexColor('#AAAAAA')
BORDER_CLR = colors.HexColor('#333333')
FOOT_CLR   = colors.HexColor('#555555')


# ── Chord naming ──────────────────────────────────────────────────────────────

# For each minor key root, the set of ambiguous semitones (1,3,6,8,10)
# that belong to that key's natural minor scale as flat notes.
FLAT_SEMIS = {
    0:  {3, 8, 10},         # C minor : Eb Ab Bb
    2:  {10},                # D minor : Bb
    4:  set(),               # E minor : F# (sharp)
    5:  {1, 3, 8, 10},      # F minor : Db Eb Ab Bb
    7:  {3, 10},             # G minor : Eb Bb
    9:  set(),               # A minor : all naturals
    11: set(),               # B minor : C# F# (sharp)
}


def chord_name(root_semi, quality, key_root):
    """Return display name using each key's flat/sharp convention.

    m7b5 always uses sharp notation (C#ø, F#ø, etc.).
    All other qualities follow the key's natural minor scale accidentals.
    """
    idx = root_semi % 12

    if quality == 'm7b5':
        return SHARP_NOTES[idx] + 'ø'

    fs   = FLAT_SEMIS.get(key_root, set())
    note = FLAT_NOTES[idx] if idx in fs else SHARP_NOTES[idx]

    if quality == 'maj': return note
    if quality == 'm':   return note + 'm'
    if quality == '7':   return note + '7'
    return note + quality


# ── CSV loading & diagram generation ─────────────────────────────────────────

def load_chords():
    data = {}
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            data[row['Chord']] = row
    return data


def to_csv_key(root_semi, quality):
    """Map (semitone, quality) to the CSV chord key (always sharp notation)."""
    root = SHARP_NOTES[root_semi % 12]
    return root + quality   # e.g. 'G7', 'Cm', 'Ebmaj' → wait, need 'D#m' not 'Ebm'
    # CSV always uses sharp roots, so this is correct.


def csv_to_params(row):
    """Return (frets, fingers) in A,D,F#,B order from a CSV row."""
    frets   = [int(row['A']), int(row['D']), int(row['F#']), int(row['B'])]
    fg      = row['Fingering']          # 4 chars in B,F#,D,A order
    fingers = [int(fg[3]), int(fg[2]), int(fg[1]), int(fg[0])]
    return frets, fingers


def detect_barre(frets, fingers):
    """Return barre list [A,D,F#,B] or None."""
    f1 = [i for i in range(4) if fingers[i] == 1 and frets[i] > 0]
    if len(f1) < 2:
        return None
    if len({frets[i] for i in f1}) != 1:
        return None
    bf = frets[f1[0]]
    return [bf if i in f1 else 0 for i in range(4)]


def make_img_reader(root_semi, quality, display_name, chords):
    """Generate a chord diagram and return a ReportLab ImageReader."""
    csv_key = to_csv_key(root_semi, quality)
    if csv_key not in chords:
        print(f'  Warning: {csv_key!r} not found in chords CSV', file=sys.stderr)
        return None
    row = chords[csv_key]
    frets, fingers = csv_to_params(row)
    barre = detect_barre(frets, fingers)
    img = make_chord_diagram(display_name, frets, fingers, barre,
                             output_path=None, scale=DIAGRAM_SCALE,
                             n_frets=N_FRETS, name_color='darkred')
    buf = io.BytesIO()
    img.save(buf, 'JPEG', quality=92)
    buf.seek(0)
    return ImageReader(buf)


# ── PDF generation ────────────────────────────────────────────────────────────

def main():
    print('Loading chords CSV…')
    chords = load_chords()
    print(f'  {len(chords)} chords loaded.')

    # ── Layout ────────────────────────────────────────────────────────────────
    LM, RM, TM, BM = 12, 10, 14, 12
    TITLE_H   = 20
    HDR_H     = 28
    FOOT_H    = 14
    KEY_COL   = 58    # wider than major to fit "Sol menor"
    INNER_GAP = 2

    AVAIL_W = PAGE_W - LM - RM
    AVAIL_H = PAGE_H - TM - BM
    DATA_H  = AVAIL_H - TITLE_H - HDR_H - FOOT_H
    ROW_H   = DATA_H / len(KEYS)

    IMG_H = int(ROW_H - 3)
    IMG_W = round(IMG_H * IMG_ASPECT)

    N_COLS      = len(MINOR_DEGREES)
    n_dual      = sum(1 for *_, s in MINOR_DEGREES if not s)
    total_img_w = (n_dual * 2 + (N_COLS - n_dual)) * IMG_W + n_dual * INNER_GAP
    col_space   = (AVAIL_W - KEY_COL - total_img_w) / N_COLS

    col_xs = []
    x = LM + KEY_COL
    for _, _, _, is_single in MINOR_DEGREES:
        col_xs.append(x + col_space / 2)
        cw = IMG_W if is_single else 2 * IMG_W + INNER_GAP
        x += cw + col_space

    def y(from_top): return PAGE_H - from_top

    title_y  = y(TM + 14)
    hdr_top  = y(TM + TITLE_H)
    hdr_bot  = y(TM + TITLE_H + HDR_H)
    data_top = hdr_bot
    data_bot = y(TM + TITLE_H + HDR_H + DATA_H)
    foot_y   = y(PAGE_H - BM - 4)

    c = canvas.Canvas(OUT_PDF, pagesize=(PAGE_W, PAGE_H))

    # ── Title ─────────────────────────────────────────────────────────────────
    c.setFont('Helvetica-Bold', 13)
    c.setFillColor(TITLE_CLR)
    c.drawCentredString(PAGE_W / 2, title_y,
                        'Acordes por Tonalidad - Menor (con dominantes secundarias)')

    # ── Header bar ────────────────────────────────────────────────────────────
    c.setFillColor(HDR_BG)
    c.rect(LM, hdr_bot, AVAIL_W, HDR_H, stroke=0, fill=1)

    c.setFont('Helvetica-Bold', 8)
    c.setFillColor(HDR_TEXT)
    c.drawCentredString(LM + KEY_COL / 2, (hdr_top + hdr_bot) / 2 - 3, 'Tonalidad')

    for i, (_, _, roman, is_single) in enumerate(MINOR_DEGREES):
        cw = IMG_W if is_single else 2 * IMG_W + INNER_GAP
        cx = col_xs[i] + cw / 2

        c.setFont('Helvetica-Bold', 9)
        c.setFillColor(HDR_TEXT)
        c.drawCentredString(cx, (hdr_top + hdr_bot) / 2 + 2, roman)

        if not is_single:
            c.setFont('Helvetica', 6.5)
            x_d = col_xs[i] + IMG_W / 2
            x_a = col_xs[i] + IMG_W + INNER_GAP + IMG_W / 2
            c.drawCentredString(x_d, hdr_bot + 6, 'Dom 7ª')
            c.drawCentredString(x_a, hdr_bot + 6, 'Acorde')

    # Vertical separators within header
    c.setStrokeColor(colors.HexColor('#3A5070'))
    c.setLineWidth(0.4)
    c.line(LM + KEY_COL, hdr_bot, LM + KEY_COL, hdr_top)
    for i in range(1, N_COLS):
        sx = col_xs[i] - col_space / 2
        c.line(sx, hdr_bot, sx, hdr_top)

    # ── Data rows ─────────────────────────────────────────────────────────────
    for row_idx, (key_root, key_name) in enumerate(KEYS):
        row_top = data_top - row_idx * ROW_H
        row_bot = row_top - ROW_H
        img_y   = row_bot + 1

        # Row background
        c.setFillColor(colors.HexColor(ROW_COLORS[row_idx]))
        c.rect(LM, row_bot, AVAIL_W, ROW_H, stroke=0, fill=1)

        # Row separator
        if row_idx > 0:
            c.setStrokeColor(GRID_CLR)
            c.setLineWidth(0.3)
            c.line(LM, row_top, LM + AVAIL_W, row_top)

        # Vertical column separators
        c.setStrokeColor(GRID_CLR)
        c.setLineWidth(0.3)
        c.line(LM + KEY_COL, row_bot, LM + KEY_COL, row_top)
        for i in range(1, N_COLS):
            sx = col_xs[i] - col_space / 2
            c.line(sx, row_bot, sx, row_top)

        # Key name
        c.setFont('Helvetica-Bold', 8)
        c.setFillColor(CHORD_CLR)
        c.drawCentredString(LM + KEY_COL / 2, (row_top + row_bot) / 2 - 3, key_name)

        # Degree cells
        for i, (deg_semi, quality, roman, is_single) in enumerate(MINOR_DEGREES):
            deg_root = (key_root + deg_semi) % 12
            cx       = col_xs[i]
            deg_name = chord_name(deg_root, quality, key_root)

            if is_single:
                ir = make_img_reader(deg_root, quality, deg_name, chords)
                if ir:
                    c.drawImage(ir, cx, img_y, width=IMG_W, height=IMG_H,
                                preserveAspectRatio=True, anchor='sw')
            else:
                dom_root = (deg_root + 7) % 12
                dom_name = chord_name(dom_root, '7', key_root)
                x_dom = cx
                x_aco = cx + IMG_W + INNER_GAP

                ir_d = make_img_reader(dom_root, '7',   dom_name, chords)
                ir_c = make_img_reader(deg_root, quality, deg_name, chords)

                if ir_d:
                    c.drawImage(ir_d, x_dom, img_y, width=IMG_W, height=IMG_H,
                                preserveAspectRatio=True, anchor='sw')
                if ir_c:
                    c.drawImage(ir_c, x_aco, img_y, width=IMG_W, height=IMG_H,
                                preserveAspectRatio=True, anchor='sw')

    # ── Outer border ──────────────────────────────────────────────────────────
    c.setStrokeColor(BORDER_CLR)
    c.setLineWidth(0.9)
    c.rect(LM, data_bot, AVAIL_W, hdr_top - data_bot, stroke=1, fill=0)

    # ── Footer ────────────────────────────────────────────────────────────────
    c.setFont('Helvetica', 6.5)
    c.setFillColor(FOOT_CLR)
    c.drawString(LM, foot_y, 'Diagramas de acordes: generados con make_chord_diagram')
    c.drawCentredString(PAGE_W / 2, foot_y,
                        'Cuatro Venezolano · Acordes por Tonalidad · Menor')
    c.drawRightString(PAGE_W - RM, foot_y, 'Preparado por: E. Klein')

    c.save()
    print(f'Saved: {OUT_PDF}')


if __name__ == '__main__':
    main()
