#!/usr/bin/env python3
"""Genera acordes_por_tonalidad_mayor.pdf — mismo estilo que el original,
   diagramas generados desde chords.csv con make_chord_diagram (6 trastes)."""

import csv, io, os, sys
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from make_chord_diagram import make_chord_diagram

CSV_PATH  = os.path.join(SCRIPT_DIR, 'chords_v2.csv')
OUT_PDF   = "/home/eklein/Documents/Cuatro/00-Clases/Practicas/acordes_por_tonalidad_mayor.pdf"

PAGE_W, PAGE_H = A4[1], A4[0]   # Landscape A4 (~842 × 595 pts)

N_FRETS        = 6
DIAGRAM_SCALE  = 2
# Aspect ratio W/H for a 6-fret from-nut diagram at any scale:
#   W = 55*s,  H = (13 + 3 + 2.5 + N_FRETS*13 + 4)*s
IMG_ASPECT = 58 / (13 + 3 + 2.5 + N_FRETS * 13 + 10)   # ≈ 0.541 (includes note-label row)

SHARP_NOTES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
FLAT_NOTES  = ['C','Db','D','Eb','E','F','Gb','G','Ab','A','Bb','B']

# Major scale degrees: (semitones_from_root, quality, roman_label, is_single_col)
MAJOR_DEGREES = [
    (0,  'maj',  'I',    False),
    (2,  'm',    'IIm',  False),
    (4,  'm',    'IIIm', False),
    (5,  'maj',  'IV',   False),
    (7,  'maj',  'V',    False),
    (9,  'm',    'VIm',  False),
    (11, 'm7b5', 'VIIø', True),
]

KEYS = [
    (0,  'Do'),
    (2,  'Re'),
    (4,  'Mi'),
    (5,  'Fa'),
    (7,  'Sol'),
    (9,  'La'),
    (11, 'Si'),
]

ROW_COLORS = [
    '#FFF2F2',   # Do  – light pink
    '#F2FFF2',   # Re  – light green
    '#FFFFF2',   # Mi  – light yellow
    '#FFF8F2',   # Fa  – light peach
    '#F2F8FF',   # Sol – light blue
    '#F2FFF8',   # La  – light cyan-green
    '#F8F2FF',   # Si  – light lavender
]

# ── Style colours ─────────────────────────────────────────────────────────────
TITLE_CLR  = colors.HexColor('#0A7878')
HDR_BG     = colors.HexColor('#1E3A5C')
HDR_TEXT   = colors.white
DOM_CLR    = colors.HexColor('#CC2200')
CHORD_CLR  = colors.HexColor('#1A1A1A')
GRID_CLR   = colors.HexColor('#AAAAAA')
BORDER_CLR = colors.HexColor('#333333')
FOOT_CLR   = colors.HexColor('#555555')


# ── Chord naming ──────────────────────────────────────────────────────────────

def chord_name(root_semi, quality):
    """Return display name with correct enharmonic spelling.

    Rules derived from standard cuatro chart conventions:
    - m7b5 (VIIø): always sharp (D#ø not Ebø, A#ø not Bbø)
    - semitone 3  (D#/Eb): Eb for m and 7, D# for m7b5
    - semitone 8  (G#/Ab): Ab for m, G# for 7 and m7b5
    - semitone 10 (A#/Bb): Bb for maj and 7, A# for m7b5
    - all others: sharp notation
    """
    idx = root_semi % 12

    if quality == 'm7b5':
        return SHARP_NOTES[idx] + 'ø'

    if idx == 3:    # D# / Eb
        note = 'Eb'
    elif idx == 8:  # G# / Ab — Ab for minor, G# for dominant
        note = 'Ab' if quality == 'm' else 'G#'
    elif idx == 10: # A# / Bb
        note = 'Bb'
    else:
        note = SHARP_NOTES[idx]

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
    root = SHARP_NOTES[root_semi % 12]
    return root + quality  # e.g. 'G7', 'Dm', 'Cmaj', 'Bm7b5'


def csv_to_params(row):
    """Return (frets, fingers, barre) in A,D,F#,B order from a CSV row."""
    fr = row['Fret']        # 4 chars in B,F#,D,A order
    fg = row['Fingering']   # 4 chars in B,F#,D,A order
    ba = row['Barre']       # 4 chars in B,F#,D,A order, or empty
    frets   = [int(fr[3]), int(fr[2]), int(fr[1]), int(fr[0])]
    fingers = [int(fg[3]), int(fg[2]), int(fg[1]), int(fg[0])]
    if ba:
        barre = [int(ba[3]), int(ba[2]), int(ba[1]), int(ba[0])]
        barre = barre if any(b > 0 for b in barre) else None
    else:
        barre = None
    return frets, fingers, barre


def make_img_reader(root_semi, quality, display_name, chords):
    """Generate a chord diagram PIL image and return a ReportLab ImageReader."""
    csv_key = to_csv_key(root_semi, quality)
    if csv_key not in chords:
        print(f'  Warning: {csv_key!r} not found in chords CSV', file=sys.stderr)
        return None
    row = chords[csv_key]
    frets, fingers, barre = csv_to_params(row)
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
    KEY_COL   = 52
    INNER_GAP = 2    # gap between Dom and Acorde images in a dual column

    AVAIL_W = PAGE_W - LM - RM
    AVAIL_H = PAGE_H - TM - BM
    DATA_H  = AVAIL_H - TITLE_H - HDR_H - FOOT_H
    ROW_H   = DATA_H / len(KEYS)

    IMG_H = int(ROW_H - 3)
    IMG_W = round(IMG_H * IMG_ASPECT)   # accounts for 6-fret taller aspect ratio

    # Distribute leftover horizontal space evenly between columns
    N_COLS      = len(MAJOR_DEGREES)
    n_dual      = sum(1 for *_, s in MAJOR_DEGREES if not s)
    total_img_w = (n_dual * 2 + (N_COLS - n_dual)) * IMG_W + n_dual * INNER_GAP
    col_space   = (AVAIL_W - KEY_COL - total_img_w) / N_COLS

    col_xs = []    # left-x of image area within each degree column
    x = LM + KEY_COL
    for _, _, _, is_single in MAJOR_DEGREES:
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
    c.setTitle('Acordes por Tonalidad - Mayor (con dominantes secundarias)')
    c.setAuthor('E. Klein')
    c.setSubject('Cuatro Venezolano')

    # ── Title ─────────────────────────────────────────────────────────────────
    c.setFont('Helvetica-Bold', 13)
    c.setFillColor(TITLE_CLR)
    c.drawCentredString(PAGE_W / 2, title_y,
                        'Acordes por Tonalidad - Mayor (con dominantes secundarias)')

    # ── Header bar ────────────────────────────────────────────────────────────
    c.setFillColor(HDR_BG)
    c.rect(LM, hdr_bot, AVAIL_W, HDR_H, stroke=0, fill=1)

    c.setFont('Helvetica-Bold', 8)
    c.setFillColor(HDR_TEXT)
    c.drawCentredString(LM + KEY_COL / 2,
                        (hdr_top + hdr_bot) / 2 - 3, 'Tonalidad')

    for i, (_, _, roman, is_single) in enumerate(MAJOR_DEGREES):
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
        c.drawCentredString(LM + KEY_COL / 2,
                            (row_top + row_bot) / 2 - 3, key_name)

        # Degree cells
        for i, (deg_semi, quality, roman, is_single) in enumerate(MAJOR_DEGREES):
            deg_root  = (key_root + deg_semi) % 12
            cx        = col_xs[i]
            deg_name  = chord_name(deg_root, quality)

            if is_single:
                ir = make_img_reader(deg_root, quality, deg_name, chords)
                if ir:
                    c.drawImage(ir, cx, img_y, width=IMG_W, height=IMG_H,
                                preserveAspectRatio=True, anchor='sw')
            else:
                dom_root  = (deg_root + 7) % 12
                dom_name  = chord_name(dom_root, '7')
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
                        'Cuatro Venezolano · Acordes por Tonalidad · Mayor')
    c.drawRightString(PAGE_W - RM, foot_y, 'Preparado por: E. Klein')

    c.save()
    print(f'Saved: {OUT_PDF}')


if __name__ == '__main__':
    main()
