#!/usr/bin/env python3
"""
4diagramas.py — Diagramas ASCII de acordes para Cuatro Venezolano
Las digitaciones se leen de chords_v2.csv (debe estar en el mismo directorio).

Uso básico:
    python 4diagramas.py Am
    python 4diagramas.py C G Am F
    python 4diagramas.py Dm7 G7 Cmaj7

Escalas y modos  (--escala NOTA  --tipo TIPO):
    python 4diagramas.py --escala C                      (mayor, tríadas)
    python 4diagramas.py --escala A --tipo menor         (menor natural)
    python 4diagramas.py --escala A --tipo armonica      (menor armónica)
    python 4diagramas.py --escala A --tipo melodica      (menor melódica)
    python 4diagramas.py --escala D --tipo dorica        (modo dórico)
    python 4diagramas.py --escala E --tipo frigia        (modo frigio)
    python 4diagramas.py --escala F --tipo lidia         (modo lidio)
    python 4diagramas.py --escala G --tipo mixolidia     (modo mixolidio)
    python 4diagramas.py --escala B --tipo locria        (modo locrio)

Opciones combinables con --escala:
    --sep   usa acordes de 7ª en lugar de tríadas
    --dom   añade sección de dominantes secundarios

    python 4diagramas.py --escala Bb --tipo menor --sep --dom

Otras opciones:
    python 4diagramas.py --lista             (calidades y tipos disponibles)
    python 4diagramas.py --todos m7          (los 12 acordes m7)
    python 4diagramas.py --ancho Bb7         (diagrama más grande)
    python 4diagramas.py -R Bb7              (Digitación en orden A D F# B)

Cuerdas (izquierda a derecha en el diagrama): A3  D4  F#4  B
Orden de los dígitos en el código "Digitación": B F# D A (igual que chords_v2.csv)
                                    por defecto — usa -R para A D F# B.
"""

import sys
import os
import csv
import io
import contextlib
import argparse

# ── Afinación ─────────────────────────────────────────────────────────────────
# Orden de visualización del diagrama (grilla de trastes), izquierda→derecha: A  D  F#  B
# Esto no cambia con -R — es la disposición física real de las cuerdas.
DISPLAY_ORDER = [3, 2, 1, 0]

# Orden del texto "Digitación": por defecto B F# D A (igual que en chords_v2.csv).
# Se reasigna a DISPLAY_ORDER (A D F# B) en main() cuando se pasa -R.
ORDEN_CODIGO = [0, 1, 2, 3]


def codigo_str(dig):
    """Código numérico de digitación como texto, según ORDEN_CODIGO."""
    return ''.join(str(dig[i]) for i in ORDEN_CODIGO)

# ── Notas ─────────────────────────────────────────────────────────────────────
SHARP_NAMES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
FLAT_NAMES  = ['C','Db','D','Eb','E','F','Gb','G','Ab','A','Bb','B']

NOTE_TO_NUM = {n: i for i, n in enumerate(SHARP_NAMES)}
NOTE_TO_NUM.update({n: i for i, n in enumerate(FLAT_NAMES)})

# ── Calidades de acordes ──────────────────────────────────────────────────────
# (intervalos: solo informativo/documental — las digitaciones vienen de chords_v2.csv)
QUALITIES = {
    'maj':  ([0,4,7],       ''),
    'm':    ([0,3,7],       'm'),
    '7':    ([0,4,7,10],    '7'),
    'maj7': ([0,4,7,11],    'maj7'),
    'M7':   ([0,4,7,11],    'M7'),
    'm7':   ([0,3,7,10],    'm7'),
    'dim':  ([0,3,6],       'dim'),
    'aug':  ([0,4,8],       'aug'),
    'sus2': ([0,2,7],       'sus2'),
    'sus4': ([0,5,7],       'sus4'),
    '6':    ([0,4,7,9],     '6'),
    'm6':   ([0,3,7,9],     'm6'),
    '9':    ([0,4,7,10,2],  '9'),
    'add9': ([0,4,7,2],     'add9'),
    'dim7': ([0,3,6,9],     'dim7'),
    'm7b5': ([0,3,6,10],    'm7b5'),
}

# Calidad interna → sufijo usado en el nombre de acorde de chords_v2.csv
CALIDAD_TO_CSV_SUFFIX = {
    'maj': 'maj', 'm': 'm', '7': '7', 'maj7': 'Maj7', 'M7': 'Maj7',
    'm7': 'm7', 'dim': 'dim', 'aug': 'aug', 'sus2': 'sus2', 'sus4': 'sus4',
    '6': '6', 'm6': 'm6', '9': '9', 'add9': 'add9', 'dim7': 'dim7', 'm7b5': 'm7b5',
}

# ── Digitaciones desde chords_v2.csv ─────────────────────────────────────────
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chords_v2.csv')


def _cargar_chords_csv():
    chords = {}
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            fr = row['Fret']
            chords[row['Chord']] = (int(fr[0]), int(fr[1]), int(fr[2]), int(fr[3]))
    return chords


CHORDS_CSV = _cargar_chords_csv()

# ── Parser de nombre de acorde ────────────────────────────────────────────────
def parsear_acorde(nombre):
    """
    Devuelve (raiz_num, calidad_key, nombre_display) o None si no se reconoce.
    Ejemplos: 'Am' → (9, 'm'), 'F#maj7' → (6, 'maj7'), 'Bb7' → (10, '7')
    """
    # Separar la nota raíz (1 o 2 caracteres)
    if len(nombre) >= 2 and nombre[1] in '#b':
        raiz_str = nombre[:2]
        resto    = nombre[2:]
    else:
        raiz_str = nombre[:1]
        resto    = nombre[1:]

    if raiz_str not in NOTE_TO_NUM:
        return None

    raiz_num = NOTE_TO_NUM[raiz_str]

    # Calidad: vacío → mayor
    calidad_key = resto if resto else 'maj'
    if calidad_key not in QUALITIES:
        return None

    return raiz_num, calidad_key


# ── Digitación (lookup en chords_v2.csv) ─────────────────────────────────────
def calcular_digitacion(raiz_num, calidad_key):
    """Devuelve tupla (B, F#, D, A) leyendo la digitación desde chords_v2.csv."""
    suffix = CALIDAD_TO_CSV_SUFFIX.get(calidad_key)
    if suffix is None:
        print(f'⚠  Calidad sin equivalente en chords_v2.csv: {calidad_key}', file=sys.stderr)
        return (0, 0, 0, 0)

    key = SHARP_NAMES[raiz_num % 12] + suffix
    dig = CHORDS_CSV.get(key)
    if dig is None:
        print(f'⚠  Acorde no encontrado en chords_v2.csv: {key}', file=sys.stderr)
        return (0, 0, 0, 0)
    return dig


# ── Renderizado ASCII ─────────────────────────────────────────────────────────
def nombre_acorde(raiz_num, calidad_key):
    _, simbolo = QUALITIES[calidad_key]
    raiz = SHARP_NAMES[raiz_num]
    return raiz + simbolo


def diagrama_ascii(nombre, dig, compact=False):
    """
    Genera el diagrama ASCII de un acorde.

    dig = (B, F#, D, A)  en orden interno
    Visualización: A  D  F#  B  (izquierda a derecha)

    Retorna lista de líneas de texto.
    """
    # Reordenar para visualización
    frets_display = [dig[i] for i in DISPLAY_ORDER]  # A D F# B
    max_fret = max(f for f in frets_display if f > 0) if any(f > 0 for f in frets_display) else 0
    show_frets = max(max_fret, 4)  # Mínimo 4 trastes visibles

    lines = []
    ancho_nombre = max(len(nombre), 13)

    # ── Título centrado ──
    lines.append(nombre.center(ancho_nombre))
    lines.append('─' * ancho_nombre)

    # ── Cejilla (nut) ──
    lines.append('  ╔═══╦═══╦═══╦═══╗')

    # ── Trastes ──
    for traste in range(1, show_frets + 1):
        fila = f'{traste:1d} ║'
        for f in frets_display:
            if f == traste:
                fila += ' ● ║'
            else:
                fila += '   ║'
        lines.append(fila)

        # Línea separadora de traste (excepto el último)
        if traste < show_frets:
            lines.append('  ╠═══╬═══╬═══╬═══╣')

    # ── Cierre ──
    lines.append('  ╚═══╩═══╩═══╩═══╝')

    # ── Código numérico ──
    lines.append(codigo_str(dig).center(ancho_nombre))

    return lines


def diagrama_ancho(nombre, dig):
    """Versión más ancha con números de traste y más espacio."""
    frets_display = [dig[i] for i in DISPLAY_ORDER]
    max_fret = max((f for f in frets_display if f > 0), default=0)
    show_frets = max(max_fret, 5)

    lines = []

    # Título
    titulo = f'♩ {nombre}'
    lines.append(titulo)
    lines.append('━' * (len(titulo) + 4))

    # Nut
    lines.append('    ┌────┬────┬────┬────┐')

    for t in range(1, show_frets + 1):
        row = f' {t:1d}  │'
        for f in frets_display:
            row += (' ◉  │' if f == t else '    │')
        lines.append(row)
        if t < show_frets:
            lines.append('    ├────┼────┼────┼────┤')

    lines.append('    └────┴────┴────┴────┘')
    lines.append(f'    {codigo_str(dig)}')
    return lines


# ── Imprimir varios acordes en columnas ──────────────────────────────────────
def imprimir_acordes(acordes_data, columnas=4, estilo='normal'):
    """
    acordes_data = lista de (nombre_display, dig)
    """
    if estilo == 'ancho':
        for nombre, dig in acordes_data:
            for linea in diagrama_ancho(nombre, dig):
                print(linea)
            print()
        return

    # Estilo normal: en columnas
    todos_diagramas = [diagrama_ascii(nombre, dig) for nombre, dig in acordes_data]
    n = len(todos_diagramas)
    col_w = 22  # ancho fijo por diagrama

    for bloque_inicio in range(0, n, columnas):
        bloque = todos_diagramas[bloque_inicio:bloque_inicio + columnas]
        # Normalizar altura
        alto = max(len(d) for d in bloque)
        bloque = [d + [''] * (alto - len(d)) for d in bloque]
        # Imprimir fila a fila
        for fila_idx in range(alto):
            linea = '   '.join(d[fila_idx].ljust(col_w) for d in bloque)
            print(linea.rstrip())
        print()


def imprimir_acordes_pares(items, estilo='normal'):
    """
    Imprime un bloque tónica+dominante por línea (dos diagramas lado a lado).
    Si el grado no tiene dominante (disminuido/semidisminuido), se muestra
    solo el diagrama de la tónica.

    items = lista de dicts de acordes_escala(), cada uno con 'etiqueta',
            'dig' y 'dominante' (dict con 'etiqueta'/'dig', o None).
    """
    diagrama_fn = diagrama_ancho if estilo == 'ancho' else diagrama_ascii

    for item in items:
        izq = diagrama_fn(item['etiqueta'], item['dig'])
        dom = item['dominante']
        der = diagrama_fn(dom['etiqueta'], dom['dig']) if dom else []

        if der:
            col_w = max(len(l) for l in izq)
            alto  = max(len(izq), len(der))
            izq   = izq + [''] * (alto - len(izq))
            der   = der + [''] * (alto - len(der))
            for i in range(alto):
                print((izq[i].ljust(col_w) + '   ' + der[i]).rstrip())
        else:
            for linea in izq:
                print(linea)
        print()


# ── Lista de todos los acordes ────────────────────────────────────────────────
def imprimir_lista():
    print('\nCalidades de acorde disponibles:\n')
    for key, (intervalos, simbolo) in QUALITIES.items():
        ejemplo = 'C' + simbolo
        print(f'  {key:8s}  ejemplo: {ejemplo:10s}  intervalos: {intervalos}')
    print()
    print('Notas raíz (sostenidos): C  C#  D  D#  E  F  F#  G  G#  A  A#  B')
    print('Notas raíz (bemoles):    C  Db  D  Eb  E  F  Gb  G  Ab  A  Bb  B')
    print()
    print('Tipos de escala (--tipo):\n')
    for key, esc in ESCALAS.items():
        aliases = [a for a, v in TIPO_ALIASES.items() if v == key and a != key]
        alias_str = f'  (alias: {", ".join(aliases[:4])})' if aliases else ''
        print(f'  {key:12s}  {esc["nombre"]}{alias_str}')
    print()
    print('Ejemplos de uso:')
    print('  python cuatro_diagramas.py Am')
    print('  python cuatro_diagramas.py C G Am F')
    print('  python cuatro_diagramas.py Dm7 G7 Cmaj7')
    print()
    print('  python cuatro_diagramas.py --escala C                    (mayor, tríadas)')
    print('  python cuatro_diagramas.py --escala A --tipo menor       (menor natural)')
    print('  python cuatro_diagramas.py --escala A --tipo armonica    (menor armónica)')
    print('  python cuatro_diagramas.py --escala D --tipo dorica      (modo dórico)')
    print('  python cuatro_diagramas.py --escala G --tipo mixolidia   (modo mixolidio)')
    print('  python cuatro_diagramas.py --escala E --tipo frigia      (modo frigio)')
    print('  python cuatro_diagramas.py --escala C --sep              (con 7ªs)')
    print('  python cuatro_diagramas.py --escala G --dom              (+ dominantes sec.)')
    print('  python cuatro_diagramas.py --escala Bb --tipo menor --sep --dom')
    print()
    print('  python cuatro_diagramas.py --todos maj   (los 12 acordes mayores)')
    print('  python cuatro_diagramas.py --todos m7    (los 12 acordes m7)')
    print('  python cuatro_diagramas.py --ancho Bb7   (diagrama más grande)')


def imprimir_todos_calidad(calidad_key, columnas=4, estilo='normal'):
    """Muestra los 12 acordes de una calidad dada."""
    if calidad_key not in QUALITIES:
        print(f'Calidad desconocida: {calidad_key}')
        print(f'Calidades válidas: {", ".join(QUALITIES.keys())}')
        sys.exit(1)
    _, simbolo = QUALITIES[calidad_key]
    acordes = []
    for num, nota in enumerate(SHARP_NAMES):
        dig = calcular_digitacion(num, calidad_key)
        acordes.append((nota + simbolo, dig))
    print(f'\n── Todos los acordes {calidad_key} ──\n')
    imprimir_acordes(acordes, columnas=columnas, estilo=estilo)


# ── Teoría de escalas ─────────────────────────────────────────────────────────

# Cada entrada: semis (7 semitonos desde la tónica) + grados (calidades diatónicas)
ESCALAS = {
    'mayor': {
        'nombre': 'Mayor (Jónica)',
        'semis': [0, 2, 4, 5, 7, 9, 11],
        'grados': [
            {'romano': 'I',    'triada': 'maj',  'septima': 'maj7', 'nombre': 'Tónica'},
            {'romano': 'II',   'triada': 'm',    'septima': 'm7',   'nombre': 'Supertónica'},
            {'romano': 'III',  'triada': 'm',    'septima': 'm7',   'nombre': 'Mediante'},
            {'romano': 'IV',   'triada': 'maj',  'septima': 'maj7', 'nombre': 'Subdominante'},
            {'romano': 'V',    'triada': 'maj',  'septima': '7',    'nombre': 'Dominante'},
            {'romano': 'VI',   'triada': 'm',    'septima': 'm7',   'nombre': 'Superdominante'},
            {'romano': 'VII',  'triada': 'm7b5', 'septima': 'm7b5', 'nombre': 'Sensible'},
        ],
    },
    'menor': {
        'nombre': 'Menor Natural (Eólica)',
        'semis': [0, 2, 3, 5, 7, 8, 10],
        'grados': [
            {'romano': 'I',    'triada': 'm',    'septima': 'm7',   'nombre': 'Tónica'},
            {'romano': 'II',   'triada': 'm7b5', 'septima': 'm7b5', 'nombre': 'Supertónica'},
            {'romano': 'bIII', 'triada': 'maj',  'septima': 'maj7', 'nombre': 'Mediante'},
            {'romano': 'IV',   'triada': 'm',    'septima': 'm7',   'nombre': 'Subdominante'},
            {'romano': 'V',    'triada': 'm',    'septima': 'm7',   'nombre': 'Dominante'},
            {'romano': 'bVI',  'triada': 'maj',  'septima': 'maj7', 'nombre': 'Superdominante'},
            {'romano': 'bVII', 'triada': 'maj',  'septima': '7',    'nombre': 'Subtónica'},
        ],
    },
    'armonica': {
        'nombre': 'Menor Armónica',
        'semis': [0, 2, 3, 5, 7, 8, 11],
        'grados': [
            {'romano': 'I',    'triada': 'm',    'septima': 'm7',   'nombre': 'Tónica'},
            {'romano': 'II',   'triada': 'm7b5', 'septima': 'm7b5', 'nombre': 'Supertónica'},
            {'romano': 'bIII', 'triada': 'aug',  'septima': 'maj7', 'nombre': 'Mediante (aum.)'},
            {'romano': 'IV',   'triada': 'm',    'septima': 'm7',   'nombre': 'Subdominante'},
            {'romano': 'V',    'triada': 'maj',  'septima': '7',    'nombre': 'Dominante'},
            {'romano': 'bVI',  'triada': 'maj',  'septima': 'maj7', 'nombre': 'Superdominante'},
            {'romano': 'VII',  'triada': 'dim',  'septima': 'dim7', 'nombre': 'Sensible'},
        ],
    },
    'melodica': {
        'nombre': 'Menor Melódica',
        'semis': [0, 2, 3, 5, 7, 9, 11],
        'grados': [
            {'romano': 'I',    'triada': 'm',    'septima': 'm7',   'nombre': 'Tónica'},
            {'romano': 'II',   'triada': 'm',    'septima': 'm7',   'nombre': 'Supertónica'},
            {'romano': 'bIII', 'triada': 'aug',  'septima': 'maj7', 'nombre': 'Mediante (aum.)'},
            {'romano': 'IV',   'triada': 'maj',  'septima': '7',    'nombre': 'Subdominante'},
            {'romano': 'V',    'triada': 'maj',  'septima': '7',    'nombre': 'Dominante'},
            {'romano': 'VI',   'triada': 'm7b5', 'septima': 'm7b5', 'nombre': 'Superdominante'},
            {'romano': 'VII',  'triada': 'm7b5', 'septima': 'm7b5', 'nombre': 'Sensible'},
        ],
    },
    'dorica': {
        'nombre': 'Modo Dórico',
        'semis': [0, 2, 3, 5, 7, 9, 10],
        'grados': [
            {'romano': 'I',    'triada': 'm',    'septima': 'm7',   'nombre': 'Tónica'},
            {'romano': 'II',   'triada': 'm',    'septima': 'm7',   'nombre': 'Supertónica'},
            {'romano': 'bIII', 'triada': 'maj',  'septima': 'maj7', 'nombre': 'Mediante'},
            {'romano': 'IV',   'triada': 'maj',  'septima': '7',    'nombre': 'Subdominante'},
            {'romano': 'V',    'triada': 'm',    'septima': 'm7',   'nombre': 'Dominante'},
            {'romano': 'VI',   'triada': 'm7b5', 'septima': 'm7b5', 'nombre': 'Superdominante'},
            {'romano': 'bVII', 'triada': 'maj',  'septima': 'maj7', 'nombre': 'Subtónica'},
        ],
    },
    'frigia': {
        'nombre': 'Modo Frigio',
        'semis': [0, 1, 3, 5, 7, 8, 10],
        'grados': [
            {'romano': 'I',    'triada': 'm',    'septima': 'm7',   'nombre': 'Tónica'},
            {'romano': 'bII',  'triada': 'maj',  'septima': 'maj7', 'nombre': 'Supertónica'},
            {'romano': 'bIII', 'triada': 'maj',  'septima': '7',    'nombre': 'Mediante'},
            {'romano': 'IV',   'triada': 'm',    'septima': 'm7',   'nombre': 'Subdominante'},
            {'romano': 'V',    'triada': 'm7b5', 'septima': 'm7b5', 'nombre': 'Dominante'},
            {'romano': 'bVI',  'triada': 'maj',  'septima': 'maj7', 'nombre': 'Superdominante'},
            {'romano': 'bVII', 'triada': 'm',    'septima': 'm7',   'nombre': 'Subtónica'},
        ],
    },
    'lidia': {
        'nombre': 'Modo Lidio',
        'semis': [0, 2, 4, 6, 7, 9, 11],
        'grados': [
            {'romano': 'I',    'triada': 'maj',  'septima': 'maj7', 'nombre': 'Tónica'},
            {'romano': 'II',   'triada': 'maj',  'septima': '7',    'nombre': 'Supertónica'},
            {'romano': 'III',  'triada': 'm',    'septima': 'm7',   'nombre': 'Mediante'},
            {'romano': '#IV',  'triada': 'm7b5', 'septima': 'm7b5', 'nombre': 'Tritono'},
            {'romano': 'V',    'triada': 'maj',  'septima': 'maj7', 'nombre': 'Dominante'},
            {'romano': 'VI',   'triada': 'm',    'septima': 'm7',   'nombre': 'Superdominante'},
            {'romano': 'VII',  'triada': 'm',    'septima': 'm7',   'nombre': 'Sensible'},
        ],
    },
    'mixolidia': {
        'nombre': 'Modo Mixolidio',
        'semis': [0, 2, 4, 5, 7, 9, 10],
        'grados': [
            {'romano': 'I',    'triada': 'maj',  'septima': '7',    'nombre': 'Tónica'},
            {'romano': 'II',   'triada': 'm',    'septima': 'm7',   'nombre': 'Supertónica'},
            {'romano': 'III',  'triada': 'm7b5', 'septima': 'm7b5', 'nombre': 'Mediante'},
            {'romano': 'IV',   'triada': 'maj',  'septima': 'maj7', 'nombre': 'Subdominante'},
            {'romano': 'V',    'triada': 'm',    'septima': 'm7',   'nombre': 'Dominante'},
            {'romano': 'VI',   'triada': 'm',    'septima': 'm7',   'nombre': 'Superdominante'},
            {'romano': 'bVII', 'triada': 'maj',  'septima': 'maj7', 'nombre': 'Subtónica'},
        ],
    },
    'locria': {
        'nombre': 'Modo Locrio',
        'semis': [0, 1, 3, 5, 6, 8, 10],
        'grados': [
            {'romano': 'I',    'triada': 'm7b5', 'septima': 'm7b5', 'nombre': 'Tónica'},
            {'romano': 'bII',  'triada': 'maj',  'septima': 'maj7', 'nombre': 'Supertónica'},
            {'romano': 'bIII', 'triada': 'm',    'septima': 'm7',   'nombre': 'Mediante'},
            {'romano': 'IV',   'triada': 'm',    'septima': 'm7',   'nombre': 'Subdominante'},
            {'romano': 'bV',   'triada': 'maj',  'septima': 'maj7', 'nombre': 'Dominante (b5)'},
            {'romano': 'bVI',  'triada': 'maj',  'septima': '7',    'nombre': 'Superdominante'},
            {'romano': 'bVII', 'triada': 'm',    'septima': 'm7',   'nombre': 'Subtónica'},
        ],
    },
}

# Aliases en español e inglés para --tipo
TIPO_ALIASES = {
    # español
    'mayor': 'mayor', 'jonica': 'mayor', 'jónica': 'mayor',
    'menor': 'menor', 'natural': 'menor', 'eolica': 'menor', 'eólica': 'menor',
    'armonica': 'armonica', 'armónica': 'armonica',
    'melodica': 'melodica', 'melódica': 'melodica',
    'dorica': 'dorica', 'dórica': 'dorica',
    'frigia': 'frigia',
    'lidia': 'lidia',
    'mixolidia': 'mixolidia',
    'locria': 'locria',
    # inglés
    'ionian': 'mayor', 'major': 'mayor',
    'minor': 'menor', 'aeolian': 'menor',
    'harmonic': 'armonica',
    'melodic': 'melodica',
    'dorian': 'dorica',
    'phrygian': 'frigia',
    'lydian': 'lidia',
    'mixolydian': 'mixolidia',
    'locrian': 'locria',
}

# Tonalidades que prefieren bemoles (≥ 1 bemol en la armadura)
TONALIDADES_BEMOL = {'F', 'Bb', 'Eb', 'Ab', 'Db', 'Gb', 'Cb'}


def modo_notacion(tonalidad_str):
    """Devuelve 'flat' si la tonalidad usa bemoles, 'sharp' en otro caso."""
    return 'flat' if tonalidad_str in TONALIDADES_BEMOL else 'sharp'


def nota_display(num, modo):
    """Nombre de nota según modo de notación."""
    return FLAT_NAMES[num % 12] if modo == 'flat' else SHARP_NAMES[num % 12]


def acordes_escala(raiz_num, tonalidad_str, tipo='mayor',
                   con_septimas=False, con_dominantes=False):
    """
    Devuelve los acordes diatónicos de la escala dada. Cada grado incluye su
    dominante secundario (V7) cuando con_dominantes=True y el grado no es
    disminuido/semidisminuido (esos no se tonicizan con un V7 propio).

    tipo: clave de ESCALAS ('mayor', 'menor', 'armonica', 'dorica', …)
    """
    escala = ESCALAS[tipo]
    modo   = modo_notacion(tonalidad_str)

    items = []
    for i, grado in enumerate(escala['grados']):
        grado_num = (raiz_num + escala['semis'][i]) % 12
        calidad   = grado['septima'] if con_septimas else grado['triada']
        nota_nom  = nota_display(grado_num, modo)
        _, simbolo = QUALITIES[calidad]
        sin_dominante = grado['triada'] in ('dim', 'm7b5')
        nombre_disp = nota_nom + simbolo + ('*' if sin_dominante else '')
        dig = calcular_digitacion(grado_num, calidad)
        etiqueta = f"{grado['romano']:5s} {nombre_disp}"

        dominante = None
        if con_dominantes and not sin_dominante:
            dom_num      = (grado_num + 7) % 12
            nota_dom     = nota_display(dom_num, modo)
            dom_nombre   = f'{nota_dom}7'
            dom_dig      = calcular_digitacion(dom_num, '7')
            dom_etiqueta = f"V7/{grado['romano']}  {dom_nombre}"
            dominante = {'etiqueta': dom_etiqueta, 'nombre': dom_nombre, 'dig': dom_dig}

        items.append({
            'grado': grado, 'idx': i,
            'etiqueta': etiqueta, 'nombre_disp': nombre_disp, 'dig': dig,
            'dominante': dominante,
        })

    tipo_acordes = 'con 7ªs' if con_septimas else 'tríadas'
    return {
        'titulo': f'Acordes diatónicos — {tipo_acordes}',
        'items':  items,
        'escala': escala,
    }


def imprimir_escala(tonalidad_str, tipo='mayor', con_septimas=False,
                    con_dominantes=False, columnas=4, estilo='normal'):
    """Muestra todos los acordes de la escala/modo dada."""

    if tonalidad_str not in NOTE_TO_NUM:
        print(f'⚠  Tonalidad no reconocida: "{tonalidad_str}"', file=sys.stderr)
        print('   Usa notas como: C  D  E  F  G  A  B  F#  Bb  Eb  Ab …', file=sys.stderr)
        sys.exit(1)

    tipo = TIPO_ALIASES.get(tipo.lower(), tipo.lower())
    if tipo not in ESCALAS:
        print(f'⚠  Tipo de escala no reconocido: "{tipo}"', file=sys.stderr)
        print(f'   Tipos válidos: {", ".join(ESCALAS.keys())}', file=sys.stderr)
        sys.exit(1)

    escala    = ESCALAS[tipo]
    raiz_num  = NOTE_TO_NUM[tonalidad_str]
    modo      = modo_notacion(tonalidad_str)
    raiz_disp = nota_display(raiz_num, modo)
    tipo_acordes = 'con 7ªs' if con_septimas else 'tríadas'
    separador = '═' * 60

    print()
    print(separador)
    print(f'  {raiz_disp} {escala["nombre"]} — {tipo_acordes}')
    if con_dominantes:
        print(f'  (incluye dominantes secundarios)')
    print(separador)

    sec   = acordes_escala(raiz_num, tonalidad_str, tipo, con_septimas, con_dominantes)
    items = sec['items']

    print(f'\n  ── {sec["titulo"]} ──\n')

    hay_sin_dominante = False
    if con_dominantes:
        print(f'  {"Semi":>4}  {"Romano":<6} {"Acorde":<10} {"Dominante":<10} '
              f'{"Función":<18} {"Digitación Tónica":<18} {"Digitación Dominante"}')
        print(f'  {"────":>4}  {"──────":<6} {"──────────":<10} {"──────────":<10} '
              f'{"──────────────────":<18} {"─────────────────":<18} {"────────────────────"}')
        for item in items:
            grado, idx = item['grado'], item['idx']
            if item['nombre_disp'].endswith('*'):
                hay_sin_dominante = True
            codigo = codigo_str(item['dig'])
            if item['dominante']:
                dom_nombre = item['dominante']['nombre']
                dom_codigo = codigo_str(item['dominante']['dig'])
            else:
                dom_nombre = '—'
                dom_codigo = '—'
            print(f'  {escala["semis"][idx]:>4}  {grado["romano"]:<6} {item["nombre_disp"]:<10} '
                  f'{dom_nombre:<10} {grado["nombre"]:<18} {codigo:<18} {dom_codigo}')
    else:
        print(f'  {"Semi":>4}  {"Romano":<6} {"Acorde":<10} {"Función":<18} {"Digitación"}')
        print(f'  {"────":>4}  {"──────":<6} {"──────────":<10} {"──────────────────":<18} {"──────────"}')
        for item in items:
            grado, idx = item['grado'], item['idx']
            if item['nombre_disp'].endswith('*'):
                hay_sin_dominante = True
            codigo = codigo_str(item['dig'])
            print(f'  {escala["semis"][idx]:>4}  {grado["romano"]:<6} {item["nombre_disp"]:<10} '
                  f'{grado["nombre"]:<18} {codigo}')
    print()
    if hay_sin_dominante:
        print('  * Disminuido/semidisminuido: sin dominante secundario propio.\n')

    if con_dominantes:
        imprimir_acordes_pares(items, estilo=estilo)
    else:
        imprimir_acordes(
            [(item['etiqueta'], item['dig']) for item in items],
            columnas=min(columnas, 4),
            estilo=estilo,
        )


# ── Actualizar imprimir_lista ─────────────────────────────────────────────────

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        prog='4diagramas.py',
        description='Diagramas ASCII de acordes para Cuatro Venezolano '
                     '(digitaciones desde chords_v2.csv).',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    modo = parser.add_argument_group(
        'Modo de uso (elige uno)',
        'Sin ninguna de estas opciones se muestra esta ayuda.'
    )
    modo.add_argument('acordes', nargs='*', metavar='ACORDE',
                       help='Uno o más nombres de acorde a mostrar, ej: Am F#m7 Bbsus4')
    modo.add_argument('--lista', action='store_true',
                       help='Lista todas las calidades de acorde y tipos de escala disponibles')
    modo.add_argument('--todos', metavar='CALIDAD', choices=sorted(QUALITIES),
                       help='Muestra los 12 acordes (todas las raíces) de una calidad. '
                            f'Opciones: {", ".join(sorted(QUALITIES))}')
    modo.add_argument('--escala', metavar='NOTA',
                       help='Muestra los acordes diatónicos de una escala/modo, ej: --escala G')

    esc = parser.add_argument_group(
        'Opciones de escala',
        'Solo tienen efecto junto con --escala.'
    )
    esc.add_argument('--tipo', metavar='TIPO', default='mayor',
                      help='Tipo de escala o modo (default: mayor). Opciones: '
                           + ', '.join(ESCALAS) + '. Acepta alias en inglés '
                           '(major, minor, dorian, …) — ver --lista.')
    esc.add_argument('--sep', action='store_true',
                      help='Usa acordes de séptima en lugar de tríadas')
    esc.add_argument('--dom', action='store_true',
                      help='Añade una sección con los dominantes secundarios (V7 de cada grado)')

    pres = parser.add_argument_group('Presentación')
    pres.add_argument('--ancho', action='store_true',
                       help='Dibuja diagramas más grandes, uno debajo del otro '
                            '(en vez de en columnas)')
    pres.add_argument('--columnas', type=int, metavar='N', default=None,
                       help='Cuántos diagramas mostrar por fila (default: 4; '
                            'con --md: 2)')
    pres.add_argument('-R', '--reverse', action='store_true',
                       help='Muestra la "Digitación" en orden A D F# B en vez '
                            'del orden por defecto B F# D A (igual que en '
                            'chords_v2.csv)')
    pres.add_argument('--md', action='store_true',
                       help='Envuelve la salida en un bloque de código Markdown '
                            '(```) para pegarla en un documento .md. Usa 2 '
                            'columnas por defecto, más angostas para que se '
                            'lean bien sin scroll horizontal.')

    args = parser.parse_args()

    if args.reverse:
        global ORDEN_CODIGO
        ORDEN_CODIGO = DISPLAY_ORDER

    columnas = args.columnas if args.columnas is not None else (2 if args.md else 4)
    estilo   = 'ancho' if args.ancho else 'normal'

    if args.md:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            _ejecutar(parser, args, columnas, estilo)
        print('```')
        print(buf.getvalue().strip('\n'))
        print('```')
    else:
        _ejecutar(parser, args, columnas, estilo)


def _ejecutar(parser, args, columnas, estilo):
    if args.lista:
        imprimir_lista()
        return

    if args.todos:
        imprimir_todos_calidad(args.todos, columnas=columnas, estilo=estilo)
        return

    if args.escala:
        imprimir_escala(
            args.escala,
            tipo=args.tipo,
            con_septimas=args.sep,
            con_dominantes=args.dom,
            columnas=columnas,
            estilo=estilo,
        )
        return

    if not args.acordes:
        parser.print_help()
        return

    # Parsear acordes dados
    acordes_validos = []
    for nombre in args.acordes:
        resultado = parsear_acorde(nombre)
        if resultado is None:
            print(f'⚠  Acorde no reconocido: "{nombre}"  (usa --lista para ver opciones)',
                  file=sys.stderr)
            continue
        raiz_num, calidad_key = resultado
        dig = calcular_digitacion(raiz_num, calidad_key)
        _, simbolo = QUALITIES[calidad_key]
        nombre_display = SHARP_NAMES[raiz_num] + simbolo
        acordes_validos.append((nombre_display, dig))

    if not acordes_validos:
        sys.exit(1)

    print()
    imprimir_acordes(acordes_validos, columnas=columnas, estilo=estilo)


if __name__ == '__main__':
    main()
