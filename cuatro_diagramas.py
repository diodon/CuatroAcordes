#!/usr/bin/env python3
"""
cuatro_diagramas.py — Diagramas ASCII de acordes para Cuatro Venezolano

Uso básico:
    python cuatro_diagramas.py Am
    python cuatro_diagramas.py C G Am F
    python cuatro_diagramas.py Dm7 G7 Cmaj7

Escalas y modos  (--escala NOTA  --tipo TIPO):
    python cuatro_diagramas.py --escala C                      (mayor, tríadas)
    python cuatro_diagramas.py --escala A --tipo menor         (menor natural)
    python cuatro_diagramas.py --escala A --tipo armonica      (menor armónica)
    python cuatro_diagramas.py --escala A --tipo melodica      (menor melódica)
    python cuatro_diagramas.py --escala D --tipo dorica        (modo dórico)
    python cuatro_diagramas.py --escala E --tipo frigia        (modo frigio)
    python cuatro_diagramas.py --escala F --tipo lidia         (modo lidio)
    python cuatro_diagramas.py --escala G --tipo mixolidia     (modo mixolidio)
    python cuatro_diagramas.py --escala B --tipo locria        (modo locrio)

Opciones combinables con --escala:
    --sep   usa acordes de 7ª en lugar de tríadas
    --dom   añade sección de dominantes secundarios

    python cuatro_diagramas.py --escala Bb --tipo menor --sep --dom

Otras opciones:
    python cuatro_diagramas.py --lista             (calidades y tipos disponibles)
    python cuatro_diagramas.py --todos m7          (los 12 acordes m7)
    python cuatro_diagramas.py --ancho Bb7         (diagrama más grande)

Cuerdas (izquierda a derecha en el diagrama): A3  D4  F#4  B
Orden de los dígitos en el código:  dígito[0]=B  dígito[1]=F#  dígito[2]=D  dígito[3]=A
"""

import sys
import argparse
from itertools import product as iproduct

# ── Afinación ─────────────────────────────────────────────────────────────────
# Orden interno: [B, F#, D, A]  (semitonos desde C=0)
STRING_BASES = [11, 6, 2, 9]

# Orden de visualización izquierda→derecha: A  D  F#  B
# Índice en STRING_BASES:                    3  2   1  0
DISPLAY_ORDER = [3, 2, 1, 0]
STRING_LABELS = ['A3 ', 'D4 ', 'F#4', 'B  ']   # etiquetas visuales

# ── Notas ─────────────────────────────────────────────────────────────────────
SHARP_NAMES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
FLAT_NAMES  = ['C','Db','D','Eb','E','F','Gb','G','Ab','A','Bb','B']

NOTE_TO_NUM = {n: i for i, n in enumerate(SHARP_NAMES)}
NOTE_TO_NUM.update({n: i for i, n in enumerate(FLAT_NAMES)})

# ── Calidades de acordes ──────────────────────────────────────────────────────
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

# ── Overrides manuales ────────────────────────────────────────────────────────
# Casos irresolubles por el algoritmo de puntuación
OVERRIDES = {
    'Am':  (1,3,2,0),
    'F':   (1,3,3,0),
    'F#m': (2,3,4,4),
    'Gbm': (2,3,4,4),
}

# ── Pesos del algoritmo ───────────────────────────────────────────────────────
W = dict(
    nota_faltante = 10000,
    distintas     =    20,
    escala_guia   =    25,
    arrastre      =     5,
    medio         =    35,
    barre_puro    =    16,
    amplitud      =   100,
    maximo        =    40,
)

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


# ── Algoritmo de digitación ───────────────────────────────────────────────────
def calcular_digitacion(raiz_num, calidad_key, max_traste=9):
    """Devuelve tupla (B, F#, D, A) con el traste de cada cuerda."""

    # Override manual
    # Reconstruir nombre para buscar en overrides
    raiz_sharp = SHARP_NAMES[raiz_num]
    raiz_flat  = FLAT_NAMES[raiz_num]
    _, simbolo = QUALITIES[calidad_key]
    for raiz in [raiz_sharp, raiz_flat]:
        nombre_acorde = raiz + (simbolo if simbolo != '' else '')
        if calidad_key == 'maj':
            nombre_acorde = raiz
        if nombre_acorde in OVERRIDES:
            return OVERRIDES[nombre_acorde]

    intervalos, _ = QUALITIES[calidad_key]
    notas_acorde  = {(raiz_num + i) % 12 for i in intervalos}

    # Opciones por cuerda (orden interno B F# D A)
    opciones = []
    for base in STRING_BASES:
        ops = [f for f in range(max_traste + 1) if (base + f) % 12 in notas_acorde]
        opciones.append(ops if ops else [0])

    mejor, mejor_puntaje = None, float('inf')

    for combo in iproduct(*opciones):
        cubiertas = {(STRING_BASES[s] + combo[s]) % 12 for s in range(4)}
        if raiz_num % 12 not in cubiertas:
            continue

        faltantes   = len(notas_acorde - cubiertas)
        presionados = [f for f in combo if f > 0]
        distintas   = len(set(presionados))
        fspan       = (max(presionados) - min(presionados)) if presionados else 0
        fp          = [s for s in range(4) if combo[s] > 0]
        op          = [s for s in range(4) if combo[s] == 0]
        guia        = sum(1 for s in op if not fp or s < fp[0])
        arrastre    = sum(1 for s in op if not fp or s > fp[-1])
        medio       = sum(1 for s in op if fp and fp[0] < s < fp[-1])
        min_traste  = min(presionados) if presionados else 0
        barre_puro  = presionados[0] if presionados and len(set(presionados)) == 1 else 0
        mx, sm      = max(combo), sum(combo)

        puntaje = (
            faltantes  * W['nota_faltante']
            + distintas  * W['distintas']
            + guia * min_traste * W['escala_guia']
            + arrastre   * W['arrastre']
            + medio      * W['medio']
            + barre_puro * W['barre_puro']
            + fspan      * W['amplitud']
            + mx         * W['maximo']
            + sm
        )
        if puntaje < mejor_puntaje:
            mejor_puntaje, mejor = puntaje, combo

    return mejor if mejor else (0, 0, 0, 0)


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

    # ── Etiquetas de cuerdas ──
    etiquetas = [STRING_LABELS[DISPLAY_ORDER.index(i)] for i in range(4)]
    # Display order: A D F# B → labels
    etiq_line = '  '.join(STRING_LABELS)
    lines.append('  ' + etiq_line)

    # ── Fila de abiertos/mudos ──
    fila_nut = '  '
    for f in frets_display:
        if f == 0:
            fila_nut += ' ○  '
        else:
            fila_nut += '    '
    lines.append(fila_nut.rstrip())

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
    codigo = ''.join(str(dig[i]) for i in DISPLAY_ORDER)
    lines.append(f'  {codigo}  ({dig[0]}{dig[1]}{dig[2]}{dig[3]})'.center(ancho_nombre))

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

    # Etiquetas
    lines.append('     A3   D4   F#4  B')

    # Abiertos
    row = '    '
    for f in frets_display:
        row += (' ◯   ' if f == 0 else '     ')
    lines.append(row)

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
    codigo_display = ''.join(str(dig[i]) for i in DISPLAY_ORDER)
    lines.append(f'    {codigo_display}  [B:{dig[0]} F#:{dig[1]} D:{dig[2]} A:{dig[3]}]')
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


def imprimir_todos_calidad(calidad_key):
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
    imprimir_acordes(acordes, columnas=4)


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
            {'romano': 'VII',  'triada': 'dim',  'septima': 'm7b5', 'nombre': 'Sensible'},
        ],
    },
    'menor': {
        'nombre': 'Menor Natural (Eólica)',
        'semis': [0, 2, 3, 5, 7, 8, 10],
        'grados': [
            {'romano': 'I',    'triada': 'm',    'septima': 'm7',   'nombre': 'Tónica'},
            {'romano': 'II',   'triada': 'dim',  'septima': 'm7b5', 'nombre': 'Supertónica'},
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
            {'romano': 'II',   'triada': 'dim',  'septima': 'm7b5', 'nombre': 'Supertónica'},
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
            {'romano': 'VI',   'triada': 'dim',  'septima': 'm7b5', 'nombre': 'Superdominante'},
            {'romano': 'VII',  'triada': 'dim',  'septima': 'm7b5', 'nombre': 'Sensible'},
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
            {'romano': 'VI',   'triada': 'dim',  'septima': 'm7b5', 'nombre': 'Superdominante'},
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
            {'romano': 'V',    'triada': 'dim',  'septima': 'm7b5', 'nombre': 'Dominante'},
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
            {'romano': '#IV',  'triada': 'dim',  'septima': 'm7b5', 'nombre': 'Tritono'},
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
            {'romano': 'III',  'triada': 'dim',  'septima': 'm7b5', 'nombre': 'Mediante'},
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
            {'romano': 'I',    'triada': 'dim',  'septima': 'm7b5', 'nombre': 'Tónica'},
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
    Devuelve la lista de secciones para la escala dada.

    tipo: clave de ESCALAS ('mayor', 'menor', 'armonica', 'dorica', …)
    """
    escala = ESCALAS[tipo]
    modo   = modo_notacion(tonalidad_str)
    secciones = []

    # ── Sección 1: acordes diatónicos ──
    diatonicos = []
    for i, grado in enumerate(escala['grados']):
        grado_num = (raiz_num + escala['semis'][i]) % 12
        calidad   = grado['septima'] if con_septimas else grado['triada']
        nota_nom  = nota_display(grado_num, modo)
        _, simbolo = QUALITIES[calidad]
        nombre_disp = nota_nom + simbolo
        dig = calcular_digitacion(grado_num, calidad)
        etiqueta = f"{grado['romano']:5s} {nombre_disp}"
        diatonicos.append((etiqueta, dig, grado, i))

    tipo_acordes = 'con 7ªs' if con_septimas else 'tríadas'
    secciones.append({
        'titulo':  f'Acordes diatónicos — {tipo_acordes}',
        'acordes': [(n, d) for n, d, _, _ in diatonicos],
        'grados':  [(g, idx) for _, _, g, idx in diatonicos],
        'escala':  escala,
    })

    # ── Sección 2: dominantes secundarios ──
    if con_dominantes:
        dominantes = []
        for i, grado in enumerate(escala['grados']):
            grado_num  = (raiz_num + escala['semis'][i]) % 12
            dom_num    = (grado_num + 7) % 12
            nota_dom   = nota_display(dom_num, modo)
            nombre_disp = f'{nota_dom}7'
            dig = calcular_digitacion(dom_num, '7')
            resuelve_a = nota_display(grado_num, modo)
            _, sim_grado = QUALITIES[grado['triada']]
            etiqueta = f"V7/{grado['romano']} → {resuelve_a}{sim_grado}"
            dominantes.append((etiqueta, dig, grado, i))

        secciones.append({
            'titulo':  'Dominantes secundarios  (V7 de cada grado)',
            'acordes': [(n, d) for n, d, _, _ in dominantes],
            'grados':  None,
            'dom_data': [(g, idx, raiz_num) for _, _, g, idx in dominantes],
            'escala':  escala,
        })

    return secciones


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

    secciones = acordes_escala(raiz_num, tonalidad_str, tipo,
                               con_septimas, con_dominantes)

    for sec in secciones:
        print(f'\n  ── {sec["titulo"]} ──\n')

        if sec['grados'] is not None:
            # Tabla de acordes diatónicos
            esc = sec['escala']
            print(f'  {"Semi":>4}  {"Romano":<6} {"Acorde":<10} {"Función":<18} {"Digitación"}')
            print(f'  {"────":>4}  {"──────":<6} {"──────────":<10} {"──────────────────":<18} {"──────────"}')
            for (etiq, dig), (grado, idx) in zip(sec['acordes'], sec['grados']):
                acorde_nom = etiq.split(None, 1)[1] if ' ' in etiq else etiq
                codigo = ''.join(str(dig[i]) for i in DISPLAY_ORDER)
                print(f'  {esc["semis"][idx]:>4}  {grado["romano"]:<6} {acorde_nom:<10} '
                      f'{grado["nombre"]:<18} {codigo}')
            print()
        else:
            # Tabla de dominantes secundarios
            esc = sec['escala']
            print(f'  {"Función":<22} {"Acorde":<8} {"Resuelve a":<14} {"Digitación"}')
            print(f'  {"──────────────────────":<22} {"──────":<8} {"──────────────":<14} {"──────────"}')
            for (etiq, dig), (grado, idx, rn) in zip(sec['acordes'], sec['dom_data']):
                grado_num = (rn + esc['semis'][idx]) % 12
                dom_num   = (grado_num + 7) % 12
                nota_dom  = nota_display(dom_num, modo)
                resuelve  = nota_display(grado_num, modo)
                _, sim    = QUALITIES[grado['triada']]
                codigo    = ''.join(str(dig[i2]) for i2 in DISPLAY_ORDER)
                print(f'  {"V7/"+grado["romano"]:<22} {nota_dom+"7":<8} '
                      f'{resuelve+sim:<14} {codigo}')
            print()

        imprimir_acordes(
            [(etiq, dig) for etiq, dig in sec['acordes']],
            columnas=min(columnas, 4),
            estilo=estilo,
        )


# ── Actualizar imprimir_lista ─────────────────────────────────────────────────

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description='Diagramas ASCII de acordes para Cuatro Venezolano',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('acordes', nargs='*',
                        help='Nombre(s) de acorde: Am, F#m7, Bbsus4, …')
    parser.add_argument('--lista', action='store_true',
                        help='Muestra todas las calidades disponibles')
    parser.add_argument('--todos', metavar='CALIDAD',
                        help='Muestra los 12 acordes de una calidad (ej: --todos m7)')
    parser.add_argument('--escala', metavar='NOTA',
                        help='Muestra todos los acordes de la escala (ej: --escala G)')
    parser.add_argument('--tipo', metavar='TIPO', default='mayor',
                        help='Tipo de escala: mayor, menor, armonica, melodica, '
                             'dorica, frigia, lidia, mixolidia, locria '
                             '(default: mayor)')
    parser.add_argument('--sep', action='store_true',
                        help='Con --escala: usa acordes de 7ª en lugar de tríadas')
    parser.add_argument('--dom', action='store_true',
                        help='Con --escala: incluye dominantes secundarios (V7 de cada grado)')
    parser.add_argument('--ancho', action='store_true',
                        help='Diagrama más grande con más detalle')
    parser.add_argument('--columnas', type=int, default=4,
                        help='Número de columnas en el display (default: 4)')

    args = parser.parse_args()

    if args.lista:
        imprimir_lista()
        return

    if args.todos:
        imprimir_todos_calidad(args.todos)
        return

    if args.escala:
        estilo = 'ancho' if args.ancho else 'normal'
        imprimir_escala(
            args.escala,
            tipo=args.tipo,
            con_septimas=args.sep,
            con_dominantes=args.dom,
            columnas=args.columnas,
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
    estilo = 'ancho' if args.ancho else 'normal'
    imprimir_acordes(acordes_validos, columnas=args.columnas, estilo=estilo)


if __name__ == '__main__':
    main()
