#!/usr/bin/env python3
# generate_chord_table.py
# Generates a CSV of all chords and fingerings for the Venezuelan Cuatro.
# Usage: python3 generate_chord_table.py > chords.csv

import json, csv, sys
from itertools import product

with open('cuatro_acordes.json', encoding='utf-8') as f:
    CFG = json.load(f)

STRING_BASES = CFG['algoritmo']['bases_cuerdas']  # [11, 6, 2, 9] → B, F#, D, A
W = CFG['algoritmo']['pesos']

def nota_a_num(nota):
    s = CFG['notas']['sostenidos']
    b = CFG['notas']['bemoles']
    return s.index(nota) if nota in s else b.index(nota)

def nombre_acorde(nota, calidad):
    q = CFG['calidades'].get(calidad, {})
    return nota + q.get('simbolo', calidad)

def calcular_digitacion(raiz_num, calidad):
    q = CFG['calidades'].get(calidad)
    if not q:
        return [0, 0, 0, 0]
    intervalos = q['intervalos']
    notas_acorde = set((raiz_num + i) % 12 for i in intervalos)

    # Check overrides
    nota_s = CFG['notas']['sostenidos'][raiz_num]
    key_s = nombre_acorde(nota_s, calidad)
    if key_s in CFG['digitaciones_override']:
        return CFG['digitaciones_override'][key_s]
    nota_b = CFG['notas']['bemoles'][raiz_num]
    key_b = nombre_acorde(nota_b, calidad)
    if key_b in CFG['digitaciones_override']:
        return CFG['digitaciones_override'][key_b]

    # Build fret options per string
    opciones = []
    for base in STRING_BASES:
        opts = [f for f in range(10) if (base + f) % 12 in notas_acorde]
        opciones.append(opts if opts else [0])

    mejor = None
    mejor_punt = float('inf')

    for combo in product(*opciones):
        cubiertos = set((STRING_BASES[i] + combo[i]) % 12 for i in range(4))
        if raiz_num % 12 not in cubiertos:
            continue

        faltantes  = len([n for n in notas_acorde if n not in cubiertos])
        presionados = [f for f in combo if f > 0]
        distinto   = len(set(presionados))
        fspan      = (max(presionados) - min(presionados)) if presionados else 0
        fp = [i for i, f in enumerate(combo) if f > 0]
        op = [i for i, f in enumerate(combo) if f == 0]
        guia     = len([i for i in op if not fp or i < fp[0]])
        arrastre = len([i for i in op if not fp or i > fp[-1]])
        medio    = len([i for i in op if fp and fp[0] < i < fp[-1]])
        min_traste  = min(presionados) if presionados else 0
        barre_puro  = presionados[0] if presionados and len(set(presionados)) == 1 else 0
        mx = max(combo)
        sm = sum(combo)

        punt = (faltantes  * W['nota_faltante']
              + distinto   * W['distintas']
              + guia * min_traste * W['escala_guia']
              + arrastre   * W['arrastre']
              + medio      * W['medio']
              + barre_puro * W['barre_puro']
              + fspan      * W['amplitud']
              + mx         * W['maximo']
              + sm)

        if punt < mejor_punt:
            mejor_punt = punt
            mejor = list(combo)

    return mejor or [0, 0, 0, 0]


writer = csv.writer(sys.stdout)
writer.writerow(['Chord', 'Root (EN)', 'Root (ES)', 'Quality', 'Symbol', 'B', 'F#', 'D', 'A', 'Fingering'])

for nota in CFG['notas']['sostenidos']:
    raiz_num = nota_a_num(nota)
    nota_es  = CFG['notas']['nombres_display'].get(nota, nota)

    for cal_key, cal in CFG['calidades'].items():
        symbol = cal['simbolo'] or cal_key
        chord  = nota + symbol
        dig    = calcular_digitacion(raiz_num, cal_key)
        writer.writerow([chord, nota, nota_es, cal['nombre'], symbol,
                         dig[0], dig[1], dig[2], dig[3], ''.join(map(str, dig))])
