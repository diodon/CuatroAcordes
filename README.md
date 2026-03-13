# Acordes del Cuatro Venezolano

Aplicación web para músicos del cuatro venezolano: transposición de acordes, digitaciones, diagramas de trastes y detección de progresiones armónicas.

**🌐 Live:** https://diodon.github.io/CuatroAcordes/

---

## Características

- **Transposición** — Selecciona tonalidad de origen y destino; todos los acordes se transponen automáticamente mostrando el intervalo en semitonos.
- **Tabla de acordes** — Construye una lista de hasta 12 acordes con nota, calidad, grado romano, acorde transpuesto y digitación.
- **Diagramas de trastes** — Visualización SVG de la digitación en el cuatro para los acordes originales y transpuestos.
- **Explorador de acordes** — Selecciona cualquier nota raíz y visualiza los diagramas de las 15 calidades disponibles (Mayor, Menor, 7ª, Maj7, m7, Dim, Aug, sus2, sus4, 6ª, m6, 9ª, add9, Dim7, m7b5).
- **Detección de progresiones** — Identifica automáticamente progresiones conocidas (Pop, Blues, Jazz, Joropo, Canon de Pachelbel, etc.).
- **Notación latina / inglesa** — Alterna entre notación latina (Do, Re, Mi) e inglesa (C, D, E) en toda la interfaz.
- **Modo oscuro** — Tema claro y oscuro en tonos azules.
- **Sin dependencias** — Aplicación 100% cliente, sin servidor ni instalación. Un solo archivo HTML + JSON.

## Afinación

El cuatro venezolano está afinado en **A3 — D4 — F#4 — B3** (de la cuerda más grave a la más aguda).

## Uso

Abre directamente en el navegador:

```
index.html
```

O visita la versión en línea: https://diodon.github.io/CuatroAcordes/

## Archivos

| Archivo | Descripción |
|---|---|
| `index.html` | Aplicación completa (HTML + CSS + JS) |
| `cuatro_acordes.json` | Base de datos de acordes, calidades y progresiones |

## Créditos

Desarrollado por **Eduardo Klein** con asistencia de [Claude](https://claude.ai) (claude-sonnet-4-6).
