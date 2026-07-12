#!/usr/bin/env python3
"""Genera p1_p6_mayor.pdf — Progresión 1 y Progresión 6 (Ángel Martínez),
   lado a lado, para los 12 tonos de la escala mayor."""

import csv, io, os, sys
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from make_chord_diagram import make_chord_diagram
from progresiones import prog_p1, prog_p6, HYBRID_NOTES, CFG

CSV_PATH = os.path.join(SCRIPT_DIR, 'chords_v2.csv')
OUT_PDF  = '/home/eklein/Documents/Cuatro/00-Clases/Practicas/p1_p6_mayor.pdf'

PAGE_W, PAGE_H = A4   # Portrait 595 × 842 pts

N_FRETS       = 4
DIAGRAM_SCALE = 2
# W = 58*s, H = (13 + 3 + 2.5 + N_FRETS*13 + 10)*s  (show_notes=True)
IMG_ASPECT = 58 / (13 + 3 + 2.5 + N_FRETS * 13 + 10)   # ≈ 0.720

SHARP_NOTES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']

# Nombres en español para la columna de tonalidad (misma convención híbrida
# que progresiones.py: sostenidos para todo excepto Bb).
NOMBRES_ES = [CFG['notas']['nombres_display'][n] for n in HYBRID_NOTES]

QUALITY_TO_SUFFIX = {'maj': 'maj', '7': '7'}

# Etiquetas de columna (función armónica, no cambian con la tonalidad)
P1_LABELS = ['V7', 'I']
P6_LABELS = ['IV', 'I', 'V7', 'I']
N_P1 = len(P1_LABELS)
N_P6 = len(P6_LABELS)
N_COLS = N_P1 + N_P6

# ── Estilo ────────────────────────────────────────────────────────────────────
HDR_BG      = colors.HexColor('#7A4A00')
HDR_TEXT    = colors.white
TITLE_CLR   = colors.HexColor('#7A4A00')
GRID_CLR    = colors.HexColor('#CCCCCC')
DIVIDER_CLR = colors.HexColor('#333333')
BORDER_CLR  = colors.HexColor('#333333')
FOOT_CLR    = colors.HexColor('#555555')
KEY_CLR     = colors.HexColor('#1A1A1A')
ROW_COLORS  = ['#FFFFFF', '#FFF6E0'] * 6   # alternating white / light amber


# ── CSV loading ───────────────────────────────────────────────────────────────

def load_chords():
    data = {}
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            data[row['Chord']] = row
    return data


def csv_key(root_semi, quality):
    return SHARP_NOTES[root_semi % 12] + QUALITY_TO_SUFFIX[quality]


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


def make_img_reader(root_semi, quality, chords):
    key = csv_key(root_semi, quality)
    if key not in chords:
        print(f'  Warning: {key!r} not found in CSV', file=sys.stderr)
        return None
    frets, fingers, barre = csv_to_params(chords[key])
    name = HYBRID_NOTES[root_semi % 12] + ('7' if quality == '7' else '')
    img = make_chord_diagram(name, frets, fingers, barre,
                             output_path=None, scale=DIAGRAM_SCALE,
                             n_frets=N_FRETS, show_notes=True,
                             name_color='#7A4A00')
    buf = io.BytesIO()
    img.save(buf, 'JPEG', quality=92)
    buf.seek(0)
    return ImageReader(buf)


# ── PDF layout ────────────────────────────────────────────────────────────────

def main():
    print('Loading chords CSV…')
    chords = load_chords()
    print(f'  {len(chords)} chords loaded.')

    LM, RM, TM, BM = 15, 12, 14, 12
    TITLE_H     = 24
    SUBTITLE_H  = 16
    SUPERHDR_H  = 16
    HDR_H       = 16
    FOOT_H      = 14
    KEY_COL     = 34

    AVAIL_W = PAGE_W - LM - RM
    AVAIL_H = PAGE_H - TM - BM
    DATA_H  = AVAIL_H - TITLE_H - SUBTITLE_H - SUPERHDR_H - HDR_H - FOOT_H
    ROW_H   = DATA_H / 12

    IMG_H = int(ROW_H - 4)
    IMG_W = round(IMG_H * IMG_ASPECT)

    col_w  = (AVAIL_W - KEY_COL) / N_COLS
    col_xs = [LM + KEY_COL + i * col_w for i in range(N_COLS)]
    divider_x = col_xs[N_P1]   # línea gruesa entre P1 y P6

    def y(from_top): return PAGE_H - from_top

    title_y      = y(TM + 16)
    subtitle_y   = y(TM + TITLE_H + 10)
    superhdr_top = y(TM + TITLE_H + SUBTITLE_H)
    superhdr_bot = y(TM + TITLE_H + SUBTITLE_H + SUPERHDR_H)
    hdr_top      = superhdr_bot
    hdr_bot      = y(TM + TITLE_H + SUBTITLE_H + SUPERHDR_H + HDR_H)
    data_top     = hdr_bot
    data_bot     = y(TM + TITLE_H + SUBTITLE_H + SUPERHDR_H + HDR_H + DATA_H)
    foot_y       = y(PAGE_H - BM - 4)

    c = canvas.Canvas(OUT_PDF, pagesize=(PAGE_W, PAGE_H))
    c.setTitle('Progresión 1 y Progresión 6 — Escala Mayor')
    c.setAuthor('E. Klein')
    c.setSubject('Cuatro Venezolano')

    # ── Título ────────────────────────────────────────────────────────────────
    c.setFont('Helvetica-Bold', 18)
    c.setFillColor(TITLE_CLR)
    c.drawCentredString(PAGE_W / 2, title_y, 'Progresión 1 y Progresión 6')

    c.setFont('Helvetica-Oblique', 11)
    c.setFillColor(colors.HexColor('#444444'))
    c.drawCentredString(PAGE_W / 2, subtitle_y,
                        'Escala Mayor · V7–I · IV–I–V7–I  (Prof. Ángel Martínez)')

    # ── Super-encabezado (Progresión 1 / Progresión 6) ───────────────────────
    c.setFillColor(HDR_BG)
    c.rect(LM, superhdr_bot, AVAIL_W, SUPERHDR_H, stroke=0, fill=1)

    c.setFont('Helvetica-Bold', 10)
    c.setFillColor(HDR_TEXT)
    mid_superhdr = (superhdr_top + superhdr_bot) / 2 - 3.5
    p1_center = LM + KEY_COL + (N_P1 * col_w) / 2
    p6_center = LM + KEY_COL + N_P1 * col_w + (N_P6 * col_w) / 2
    c.drawCentredString(p1_center, mid_superhdr, 'Progresión 1')
    c.drawCentredString(p6_center, mid_superhdr, 'Progresión 6')

    # ── Encabezado de columnas (V7, I, IV, I, V7, I) ─────────────────────────
    c.setFillColor(colors.HexColor('#9A6A20'))
    c.rect(LM, hdr_bot, AVAIL_W, HDR_H, stroke=0, fill=1)

    c.setFont('Helvetica-Bold', 8)
    c.setFillColor(HDR_TEXT)
    mid_hdr = (hdr_top + hdr_bot) / 2 - 3
    col_labels = P1_LABELS + P6_LABELS
    for i, label in enumerate(col_labels):
        c.drawCentredString(col_xs[i] + col_w / 2, mid_hdr, label)

    # Separadores verticales en encabezados
    c.setStrokeColor(colors.HexColor('#5A3A00'))
    c.setLineWidth(0.4)
    c.line(LM + KEY_COL, superhdr_bot, LM + KEY_COL, superhdr_top)
    for i in range(1, N_COLS):
        c.line(col_xs[i], hdr_bot, col_xs[i], superhdr_top)

    # ── Filas de datos ────────────────────────────────────────────────────────
    for row_idx, root_es in enumerate(NOMBRES_ES):
        root_semi = row_idx
        row_top = data_top - row_idx * ROW_H
        row_bot = row_top - ROW_H
        img_y   = row_bot + (ROW_H - IMG_H) / 2

        c.setFillColor(colors.HexColor(ROW_COLORS[row_idx]))
        c.rect(LM, row_bot, AVAIL_W, ROW_H, stroke=0, fill=1)

        if row_idx > 0:
            c.setStrokeColor(GRID_CLR)
            c.setLineWidth(0.3)
            c.line(LM, row_top, LM + AVAIL_W, row_top)

        c.setStrokeColor(GRID_CLR)
        c.setLineWidth(0.3)
        c.line(LM + KEY_COL, row_bot, LM + KEY_COL, row_top)
        for i in range(1, N_COLS):
            if i == N_P1:
                continue  # el divisor grueso se dibuja aparte
            c.line(col_xs[i], row_bot, col_xs[i], row_top)

        # Etiqueta de tonalidad
        c.setFont('Helvetica-Bold', 12)
        c.setFillColor(KEY_CLR)
        c.drawCentredString(LM + KEY_COL / 2, (row_top + row_bot) / 2 - 4, root_es)

        # Acordes de P1 y P6
        p1_chords = prog_p1(root_semi, 'major')
        p6_chords = prog_p6(root_semi, 'major')
        for col_idx, (chord_root, quality) in enumerate(p1_chords + p6_chords):
            ir = make_img_reader(chord_root, quality, chords)
            if ir:
                img_x = col_xs[col_idx] + (col_w - IMG_W) / 2
                c.drawImage(ir, img_x, img_y, width=IMG_W, height=IMG_H,
                            preserveAspectRatio=True, anchor='sw')

    # ── Divisor grueso entre Progresión 1 y Progresión 6 ─────────────────────
    c.setStrokeColor(DIVIDER_CLR)
    c.setLineWidth(1.3)
    c.line(divider_x, data_bot, divider_x, superhdr_top)

    # ── Borde exterior ────────────────────────────────────────────────────────
    c.setStrokeColor(BORDER_CLR)
    c.setLineWidth(0.9)
    c.rect(LM, data_bot, AVAIL_W, superhdr_top - data_bot, stroke=1, fill=0)

    # ── Pie de página ─────────────────────────────────────────────────────────
    c.setFont('Helvetica', 6.5)
    c.setFillColor(FOOT_CLR)
    c.drawString(LM, foot_y, 'Diagramas de acordes: generados con make_chord_diagram')
    c.drawCentredString(PAGE_W / 2, foot_y,
                        'Cuatro Venezolano · Progresión 1 y Progresión 6 · Prof. Ángel Martínez')
    c.drawRightString(PAGE_W - RM, foot_y, 'Preparado por: E. Klein')

    c.save()
    print(f'Saved: {OUT_PDF}')


if __name__ == '__main__':
    main()
