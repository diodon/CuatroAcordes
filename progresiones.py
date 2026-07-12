#!/usr/bin/env python3
# progresiones.py
# Progresiones armónicas del Cuatro Venezolano (sistema de Ángel Martínez).
# Usage: python3 progresiones.py --prog P1 --escala D
#        python3 progresiones.py --prog P3 --escala Dm

import json, sys, argparse

with open('cuatro_acordes.json', encoding='utf-8') as f:
    CFG = json.load(f)

SHARP_NOTES = CFG['notas']['sostenidos']
FLAT_NOTES  = CFG['notas']['bemoles']

# Notación de salida: sostenidos para todo excepto Bb (convención del proyecto,
# ver make_chord_diagram/generar_degrade_menor_pdf ROOT_LABELS).
HYBRID_NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'Bb', 'B']


def nota_a_num(nota):
    s = SHARP_NOTES
    b = FLAT_NOTES
    return s.index(nota) if nota in s else b.index(nota)


def chord_display(root_num, quality):
    sym = CFG['calidades'][quality]['simbolo']
    return HYBRID_NOTES[root_num % 12] + sym


# ── Teoría de escalas ─────────────────────────────────────────────────────────

# Grados de escala: (semitonos desde la tónica, calidad)
MAJOR_SCALE = {
    1: (0,  'maj'),
    2: (2,  'min'),
    3: (4,  'min'),
    4: (5,  'maj'),
    5: (7,  'maj'),
    6: (9,  'min'),
    7: (11, 'dim'),
}

MINOR_SCALE = {
    1: (0,  'min'),
    2: (2,  'm7b5'),   # semidisminuido, no diminuido puro
    3: (3,  'maj'),
    4: (5,  'min'),
    5: (7,  'maj'),
    6: (8,  'maj'),
    7: (10, 'maj'),
}


def parse_escala(escala_str):
    """Parse 'D' → ('D', 'major'), 'Dm' → ('D', 'minor'), 'F#m' → ('F#', 'minor')."""
    all_notes = set(SHARP_NOTES) | set(FLAT_NOTES)
    if escala_str.endswith('m') and escala_str[:-1] in all_notes:
        return escala_str[:-1], 'minor'
    if escala_str in all_notes:
        return escala_str, 'major'
    raise ValueError(
        f"Escala desconocida: '{escala_str}'. Ejemplos válidos: D, Dm, F#, Bbm"
    )


def scale_degree(degree, root_num, mode):
    scale = MAJOR_SCALE if mode == 'major' else MINOR_SCALE
    offset, quality = scale[degree]
    return ((root_num + offset) % 12, quality)


# ── Progresiones de Ángel Martínez ────────────────────────────────────────────

def p1_of(chord):
    """P1(chord) = dominante 7ma de chord + chord."""
    root, quality = chord
    dom_root = (root + 7) % 12
    return [(dom_root, '7'), chord]


def prog_p1(root_num, mode):
    I = scale_degree(1, root_num, mode)
    return p1_of(I)


def prog_p2(root_num, mode):
    I  = scale_degree(1, root_num, mode)
    II = scale_degree(2, root_num, mode)
    return [II] + p1_of(I)


def prog_p3(root_num, mode):
    if mode != 'major':
        raise ValueError(
            "P3 solo existe en la escala mayor: el ii de la escala menor es "
            "semidisminuido (m7b5) y no tiene dominante propio."
        )
    I  = scale_degree(1, root_num, mode)
    II = scale_degree(2, root_num, mode)
    return p1_of(II) + p1_of(I)


def prog_p4(root_num, mode):
    I  = scale_degree(1, root_num, mode)
    IV = scale_degree(4, root_num, mode)
    return [IV] + p1_of(I)


def prog_p5(root_num, mode):
    I  = scale_degree(1, root_num, mode)
    IV = scale_degree(4, root_num, mode)
    return p1_of(IV) + p1_of(I)


def prog_p6(root_num, mode):
    I  = scale_degree(1, root_num, mode)
    IV = scale_degree(4, root_num, mode)
    return [IV, I] + p1_of(I)


def prog_p6_1(root_num, mode):
    I  = scale_degree(1, root_num, mode)
    IV = scale_degree(4, root_num, mode)
    II = scale_degree(2, root_num, mode)
    if mode == 'major':
        IVm = (IV[0], 'min')
        return [IV, IVm, I] + p1_of(II) + p1_of(I)
    # Menor: iv → VII7 → III → VI → ii(m7b5) → V7 → i
    # (cadena descendente de cuartas iv-bVII-III-bVI, luego cadencia ii-V-i)
    VII7 = (scale_degree(7, root_num, mode)[0], '7')
    III  = scale_degree(3, root_num, mode)
    VI   = scale_degree(6, root_num, mode)
    return [IV, VII7, III, VI, II] + p1_of(I)


PROGRESSIONS = {
    'P1':   prog_p1,
    'P2':   prog_p2,
    'P3':   prog_p3,
    'P4':   prog_p4,
    'P5':   prog_p5,
    'P6':   prog_p6,
    'P6.1': prog_p6_1,
}


def build_progression(prog_name, root_num, mode):
    if prog_name not in PROGRESSIONS:
        raise ValueError(
            f"Progresión desconocida: '{prog_name}'. "
            f"Opciones: {', '.join(PROGRESSIONS)}"
        )
    return PROGRESSIONS[prog_name](root_num, mode)


def print_progression(prog_name, escala_str):
    note_str, mode = parse_escala(escala_str)
    root_num = nota_a_num(note_str)

    chords      = build_progression(prog_name, root_num, mode)
    chord_names = [chord_display(r, q) for r, q in chords]

    mode_label = 'menor' if mode == 'minor' else 'mayor'
    print(f"{prog_name} en {escala_str} ({mode_label}):")
    print(' → '.join(chord_names))


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Progresiones armónicas del Cuatro Venezolano (sistema de Ángel Martínez)'
    )
    parser.add_argument('--prog', required=True, help='Progresión (P1, P2, P3, P4, P5, P6, P6.1)')
    parser.add_argument('--escala', required=True, help='Tonalidad, ej: D, Dm, F#, Bbm')
    args = parser.parse_args()

    try:
        print_progression(args.prog, args.escala)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
