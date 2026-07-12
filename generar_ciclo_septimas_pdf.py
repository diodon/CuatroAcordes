#!/usr/bin/env python3
"""Genera ciclo_septimas.pdf — serie de séptimas por tonalidad (ciclo de cuartas)."""

import csv, io, os, sys
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from make_chord_diagram import make_chord_diagram

CSV_PATH = os.path.join(SCRIPT_DIR, 'chords_v2.csv')
OUT_PDF  = '/home/eklein/Documents/Cuatro/00-Clases/Practicas/ciclo_septimas.pdf'

PAGE_W, PAGE_H = A4   # Portrait 595 × 842 pts

N_FRETS       = 6
DIAGRAM_SCALE = 2
# W = 58*s, H = (13 + 3 + 2.5 + N_FRETS*13 + 10)*s  (show_notes=True)
IMG_ASPECT = 58 / (13 + 3 + 2.5 + N_FRETS * 13 + 10)   # ≈ 0.545

SHARP_NOTES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
FLAT_NOTES  = ['C','Db','D','Eb','E','F','Gb','G','Ab','A','Bb','B']

# Circle of fourths: (semitone, display key label)
# key_label is used directly as the chord root in display names.
# CSV lookup always uses SHARP_NOTES[semitone].
CYCLE_KEYS = [
    (9,  'A'),
    (11, 'B'),
    (0,  'C'),
    (2,  'D'),
    (4,  'E'),
    (5,  'F'),
    (7,  'G'),
]

# All chords built on the same root (semitone_offset = 0).
# (semitone_offset, quality, header_label, csv_suffix, display_suffix)
DEGREES = [
    (0, 'maj',  'I',      'maj',  ''),
    (0, 'maj7', 'IM7',    'Maj7', 'M7'),
    (0, '7',    'I7',     '7',    '7'),
    (0, 'min7', 'Im7',    'm7',   'm7'),
    (0, 'm7b5', 'Im7b5',  'm7b5', 'm7b5'),
    (0, 'dim',  'Idim',   'dim',  'dim'),
]

# ── Style ─────────────────────────────────────────────────────────────────────
HDR_BG     = colors.HexColor('#1A4040')
HDR_TEXT   = colors.white
TITLE_CLR  = colors.HexColor('#1A4040')
GRID_CLR   = colors.HexColor('#CCCCCC')
BORDER_CLR = colors.HexColor('#333333')
FOOT_CLR   = colors.HexColor('#555555')
KEY_CLR    = colors.HexColor('#1A1A1A')
ROW_COLORS = ['#FFFFFF', '#EEF8F8'] * 7   # alternating white / light teal


# ── Naming ────────────────────────────────────────────────────────────────────

def chord_display_name(key_label, quality):
    suffix = {
        'maj': '', 'maj7': 'M7', '7': '7',
        'min7': 'm7', 'm7b5': 'm7b5', 'dim': 'dim'
    }[quality]
    return key_label + suffix


def csv_key(key_semi, csv_suffix):
    return SHARP_NOTES[key_semi % 12] + csv_suffix


# ── CSV loading ───────────────────────────────────────────────────────────────

def load_chords():
    data = {}
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            data[row['Chord']] = row
    return data


def csv_to_params(row):
    """B,F#,D,A order — matches chords_v2.csv and make_chord_diagram directly."""
    fr, fg, ba = row['Fret'], row['Fingering'], row['Barre']
    frets   = [int(c) for c in fr]
    fingers = [int(c) for c in fg]
    if ba:
        barre = [int(c) for c in ba]
        barre = barre if any(b > 0 for b in barre) else None
    else:
        barre = None
    return frets, fingers, barre


def make_img_reader(key_semi, quality, csv_suffix, display_name, chords):
    key = csv_key(key_semi, csv_suffix)
    if key not in chords:
        print(f'  Warning: {key!r} not found in CSV', file=sys.stderr)
        return None
    frets, fingers, barre = csv_to_params(chords[key])
    img = make_chord_diagram(display_name, frets, fingers, barre,
                             output_path=None, scale=DIAGRAM_SCALE,
                             n_frets=N_FRETS, show_notes=True,
                             name_color='#1A4040')
    buf = io.BytesIO()
    img.save(buf, 'JPEG', quality=92)
    buf.seek(0)
    return ImageReader(buf)


# ── PDF layout ────────────────────────────────────────────────────────────────

def main():
    print('Loading chords CSV…')
    chords = load_chords()
    print(f'  {len(chords)} chords loaded.')

    LM, RM, TM, BM = 12, 10, 14, 12
    TITLE_H    = 24
    SUBTITLE_H = 16
    HDR_H      = 22
    FOOT_H     = 14
    KEY_COL    = 38

    AVAIL_W = PAGE_W - LM - RM
    AVAIL_H = PAGE_H - TM - BM
    DATA_H  = AVAIL_H - TITLE_H - SUBTITLE_H - HDR_H - FOOT_H
    ROW_H   = DATA_H / len(CYCLE_KEYS)

    IMG_H = int(ROW_H - 4)
    IMG_W = round(IMG_H * IMG_ASPECT)

    N_COLS = len(DEGREES)
    col_w  = (AVAIL_W - KEY_COL) / N_COLS
    col_xs = [LM + KEY_COL + i * col_w for i in range(N_COLS)]

    def y(from_top): return PAGE_H - from_top

    title_y    = y(TM + 16)
    subtitle_y = y(TM + TITLE_H + 10)
    hdr_top    = y(TM + TITLE_H + SUBTITLE_H)
    hdr_bot    = y(TM + TITLE_H + SUBTITLE_H + HDR_H)
    data_top   = hdr_bot
    data_bot   = y(TM + TITLE_H + SUBTITLE_H + HDR_H + DATA_H)
    foot_y     = y(PAGE_H - BM - 4)

    c = canvas.Canvas(OUT_PDF, pagesize=(PAGE_W, PAGE_H))
    c.setTitle('Ciclo de Séptimas')
    c.setAuthor('E. Klein')
    c.setSubject('Cuatro Venezolano')

    # ── Title ─────────────────────────────────────────────────────────────────
    c.setFont('Helvetica-Bold', 18)
    c.setFillColor(TITLE_CLR)
    c.drawCentredString(PAGE_W / 2, title_y, 'Ciclo de Séptimas')

    c.setFont('Helvetica-Oblique', 11)
    c.setFillColor(colors.HexColor('#444444'))
    c.drawCentredString(PAGE_W / 2, subtitle_y,
                        'Mayor · M7 · Dom7 · m7 · m7b5 · dim')

    # ── Header bar ────────────────────────────────────────────────────────────
    c.setFillColor(HDR_BG)
    c.rect(LM, hdr_bot, AVAIL_W, HDR_H, stroke=0, fill=1)

    c.setFont('Helvetica-Bold', 8)
    c.setFillColor(HDR_TEXT)
    mid_hdr = (hdr_top + hdr_bot) / 2 - 4
    c.drawCentredString(LM + KEY_COL / 2, mid_hdr, 'Ton.')
    for i, (_, _, hdr_label, _, _) in enumerate(DEGREES):
        c.drawCentredString(col_xs[i] + col_w / 2, mid_hdr, hdr_label)

    # Vertical separators in header
    c.setStrokeColor(colors.HexColor('#2A5A5A'))
    c.setLineWidth(0.4)
    c.line(LM + KEY_COL, hdr_bot, LM + KEY_COL, hdr_top)
    for i in range(1, N_COLS):
        c.line(col_xs[i], hdr_bot, col_xs[i], hdr_top)

    # ── Data rows ─────────────────────────────────────────────────────────────
    for row_idx, (key_semi, key_label) in enumerate(CYCLE_KEYS):
        row_top = data_top - row_idx * ROW_H
        row_bot = row_top - ROW_H
        img_y   = row_bot + (ROW_H - IMG_H) / 2

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
            c.line(col_xs[i], row_bot, col_xs[i], row_top)

        # Key label
        c.setFont('Helvetica-Bold', 13)
        c.setFillColor(KEY_CLR)
        c.drawCentredString(LM + KEY_COL / 2, (row_top + row_bot) / 2 - 5, key_label)

        # Chord diagrams
        for col_idx, (_, quality, _, csv_suffix, _) in enumerate(DEGREES):
            name = chord_display_name(key_label, quality)
            ir = make_img_reader(key_semi, quality, csv_suffix, name, chords)
            if ir:
                img_x = col_xs[col_idx] + (col_w - IMG_W) / 2
                c.drawImage(ir, img_x, img_y, width=IMG_W, height=IMG_H,
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
                        'Cuatro Venezolano · Ciclo de Séptimas')
    c.drawRightString(PAGE_W - RM, foot_y, 'Preparado por: E. Klein')

    c.save()
    print(f'Saved: {OUT_PDF}')


if __name__ == '__main__':
    main()
