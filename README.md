# Acordes del Cuatro Venezolano

Aplicación web para músicos del cuatro venezolano: transposición de acordes, digitaciones, diagramas de trastes, exploración de acordes, detección de progresiones armónicas y reproducción de audio.

**🌐 Live:** https://diodon.github.io/CuatroAcordes/

---

## Características

- **Transposición** — Selecciona tonalidad de origen y destino; todos los acordes se transponen automáticamente mostrando el intervalo en semitonos.
- **Escala Mayor / Menor** — Cambia entre escala mayor (jónica) y menor armónica; afecta las calidades de los acordes generados por las progresiones.
- **Tabla de acordes** — Construye una lista de hasta 12 acordes con nota, calidad, grado romano, acorde transpuesto y digitación. Los acordes son clicables y muestran el diagrama de trastes en un popup.
- **Progresiones** — Selecciona una progresión del menú desplegable y la tabla se llena automáticamente con los acordes correctos para la tonalidad y escala seleccionadas.
- **Diagramas de trastes** — Visualización SVG de la digitación en el cuatro para los acordes originales y transpuestos.
- **Explorador de acordes** — Selecciona cualquier nota raíz y visualiza los diagramas de las 15 calidades disponibles (Mayor, Menor, 7ª, Maj7, m7, Dim, Aug, sus2, sus4, 6ª, m6, 9ª, add9, Dim7, m7b5).
- **Detección de progresiones** — Identifica automáticamente progresiones conocidas a partir de los acordes introducidos.
- **Reproducción de audio** — Escucha cualquier acorde con un clic: síntesis Web Audio API con tres armónicos y envolvente de decaimiento para imitar el sonido del cuatro. Botón ▶ Tocar en cada diagrama individual.
- **Reproducción de secuencias** — Toca toda la progresión detectada o las columnas de diagramas originales y transpuestos en secuencia, con control de tempo (Lento / Normal / Rápido / Muy rápido) y resaltado de acorde activo.
- **Notación latina / inglesa** — Alterna entre notación latina (Do, Re, Mi) e inglesa (C, D, E) en toda la interfaz.
- **Modo oscuro** — Tema claro y oscuro en tonos azules con toggle de sol/luna.
- **Sin dependencias** — Aplicación 100% cliente, sin servidor ni instalación. Un solo archivo HTML + JSON.

## Progresiones incluidas

| Progresión | Género |
|---|---|
| Pop — I·V·VI·IV | Pop internacional |
| Blues básico — I·IV·V | Blues |
| Do-Wop / 50s — I·VI·IV·V | Doo-wop |
| Jazz (cadencia) — II·V·I | Jazz |
| Canon de Pachelbel — I·V·VI·III·IV | Clásico |
| Tradicional / Folk — I·IV·I·V | Folk |
| Joropo básico — I·II·IV·I | Joropo venezolano |
| Joropo en Seis — I·IV·V·I | Joropo venezolano |
| Joropo Recio — I·V·I·V | Joropo venezolano |
| Merengue Venezolano — I·bVII·IV·I | Merengue caraqueño |
| Tonada Llanera — I·bVII·bVI·V | Llanera |
| Gaita Zuliana — I·V·IV·I | Gaita de furro |
| Polo Llanero — I·IV·bVII·I | Polo |
| Valse Venezolano — I·VI·II·V | Vals venezolano |
| Paso doble — I·III·IV·V | Paso doble |
| Rock clásico — I·IV·V·IV | Rock |
| Blues de 12 compases — I·I·IV·IV·V·IV | Blues |

## Afinación

El cuatro venezolano está afinado en **A3 — D4 — F#4 — B3** (de la cuerda más grave a la más aguda).

## Uso

Abre directamente en el navegador:

```
index.html
```

O visita la versión en línea: https://diodon.github.io/CuatroAcordes/

## Herramienta de línea de comandos — `cuatro_diagramas.py`

Script Python (sin dependencias externas) que genera diagramas ASCII de acordes y escalas para el cuatro venezolano directamente en la terminal.

### Uso básico

```bash
# Un acorde
python cuatro_diagramas.py Am

# Varios acordes
python cuatro_diagramas.py C G Am F

# Acordes de 7ª
python cuatro_diagramas.py Dm7 G7 Cmaj7

# Diagrama más grande
python cuatro_diagramas.py --ancho Bb7

# Los 12 acordes de una calidad
python cuatro_diagramas.py --todos m7

# Ver calidades disponibles
python cuatro_diagramas.py --lista
```

### Escalas y modos

```bash
# Escala mayor (tríadas)
python cuatro_diagramas.py --escala C

# Menor natural
python cuatro_diagramas.py --escala A --tipo menor

# Menor armónica con 7ªs y dominantes secundarios
python cuatro_diagramas.py --escala A --tipo armonica --sep --dom

# Modo dórico
python cuatro_diagramas.py --escala D --tipo dorica
```

Tipos de escala disponibles: `mayor`, `menor`, `armonica`, `melodica`, `dorica`, `frigia`, `lidia`, `mixolidia`, `locria` (también acepta nombres en inglés: `major`, `minor`, `dorian`, etc.)

### Opciones

| Opción | Descripción |
|---|---|
| `--escala NOTA` | Muestra los acordes diatónicos de la escala |
| `--tipo TIPO` | Tipo de escala o modo (default: `mayor`) |
| `--sep` | Con `--escala`: usa acordes de 7ª en lugar de tríadas |
| `--dom` | Con `--escala`: añade dominantes secundarios |
| `--ancho` | Diagrama más grande con más detalle |
| `--todos CALIDAD` | Los 12 acordes de una calidad (ej: `--todos m7`) |
| `--columnas N` | Número de columnas en el display (default: 4) |
| `--lista` | Muestra todas las calidades y tipos disponibles |

---

## Archivos

| Archivo | Descripción |
|---|---|
| `index.html` | Aplicación web completa (HTML + CSS + JS) |
| `cuatro_acordes.json` | Base de datos de acordes, calidades y progresiones |
| `cuatro_diagramas.py` | Herramienta CLI: diagramas ASCII de acordes y escalas |

## Créditos

Desarrollado por **Eduardo Klein** con asistencia de [Claude](https://claude.ai) (claude-sonnet-4-6).
