# Acordes del Cuatro Venezolano

Aplicación web para músicos del cuatro venezolano: transposición de acordes, digitaciones, diagramas de trastes, exploración de acordes, detección de progresiones armónicas y reproducción de audio.

**🌐 Live:** https://diodon.github.io/CuatroAcordes/

---

## Características

- **Transposición** — Selecciona tonalidad de origen y destino; todos los acordes se transponen automáticamente mostrando el intervalo en semitonos.
- **Escala Mayor / Menor** — Cambia entre escala mayor (jónica) y menor armónica; determina si la columna Grado y la detección de progresiones usan los grados diatónicos de la escala mayor o de la menor armónica. Al aplicar una progresión del menú, el toggle se ajusta automáticamente al modo de esa progresión (cada una ya trae su propia calidad de acorde codificada).
- **Tabla de acordes** — Construye una lista de hasta 12 acordes con nota, calidad, grado romano (mayúscula = tríada mayor, minúscula = menor/disminuida, V7 = dominante con séptima), acorde transpuesto y digitación. Los acordes son clicables y muestran el diagrama de trastes en un popup.
- **Progresiones** — Selecciona una progresión del menú desplegable y la tabla se llena automáticamente con los acordes correctos (calidad incluida) para la tonalidad seleccionada.
- **Diagramas de trastes** — Visualización SVG de la digitación en el cuatro para los acordes originales y transpuestos.
- **Explorador de acordes** — Selecciona cualquier nota raíz y visualiza los diagramas de las 17 calidades disponibles (Mayor, Menor, 7ª, Maj7, m7, Menor Maj7, Dim, Aug, sus2, sus4, 7ª sus4, 6ª, m6, 9ª, add9, Dim7, m7b5).
- **Detección de progresiones** — Identifica automáticamente progresiones conocidas a partir de los acordes introducidos.
- **Reproducción de audio** — Escucha cualquier acorde con un clic: síntesis Web Audio API con tres armónicos y envolvente de decaimiento para imitar el sonido del cuatro. Botón ▶ Tocar en cada diagrama individual.
- **Reproducción de secuencias** — Toca toda la progresión detectada o las columnas de diagramas originales y transpuestos en secuencia, con control de tempo (Lento / Normal / Rápido / Muy rápido) y resaltado de acorde activo.
- **Notación latina / inglesa** — Alterna entre notación latina (Do, Re, Mi) e inglesa (C, D, E) en toda la interfaz.
- **Modo oscuro** — Tema claro y oscuro en tonos azules con toggle de sol/luna.
- **Sin dependencias** — Aplicación 100% cliente, sin servidor ni instalación. Un solo archivo HTML + JSON.

## Progresiones incluidas

Cada numeral romano refleja la calidad real del acorde: **mayúscula** = tríada mayor, **minúscula** = menor o disminuida, **V7** = dominante con séptima (siempre). Por eso una misma progresión de posiciones puede dar dos entradas distintas, una en Mayor y otra en menor (p. ej. Seis Corrido vs. Pajarillo).

| Progresión | Género |
|---|---|
| Pop — I·V7·vi·IV | Pop internacional |
| Blues básico — I·IV·V7 | Blues |
| Do-Wop / 50s — I·vi·IV·V7 | Doo-wop |
| Jazz (cadencia) — ii·V7·I | Jazz |
| Canon de Pachelbel — I·V7·vi·iii·IV | Clásico |
| Tradicional / Folk — I·IV·I·V7 | Folk |
| Seis Corrido / Seis por Derecho — I·IV·V7·I | Joropo (Mayor) |
| Pajarillo / Catira — i·iv·V7·i | Joropo (menor) |
| Paso doble — I·iii·IV·V7 | Paso doble |
| Variante pop menor — vi·IV·I·V7 | Pop |
| Valse Venezolano / Turnaround jazz — I·vi·ii·V7 | Vals venezolano |
| Rock clásico — I·IV·V7·IV | Rock |
| Blues de 12 compases — I·I·IV·IV·V7·IV | Blues |
| Gabán — i·V7·V7·i | Joropo (menor) |
| Paloma / Gabana — I·V7·V7·I | Joropo (Mayor) |
| Guacharaca — I·IV·IV·I·I·V7·V7·I | Joropo (Mayor) |
| Seis Numerao — I·I·IV·V7 | Joropo (Mayor) |
| Nuevo Callao — I·V7·I·iii·vi·iii·vi·vi·V7·V7·I·IV·I·V7·I·I | Joropo (Mayor) |
| Periquera — I·I·V7·I·I·I·I·IV·IV·IV·ii·V7·IV·I·V7·I | Joropo (Mayor) |
| Zumba que zumba — i·i·V7·i·i·i·i·iv·iv·iv·ii·V7·iv·i·V7·i | Joropo (menor) |
| Merengue Venezolano — I·bVII·IV·I | Merengue caraqueño |
| Gaita Zuliana — I·V7·IV·I | Gaita de furro |
| Polo Llanero — I·IV·bVII·I | Polo |
| Cadencia Andaluza I / Tonada Llanera — i·bVII·bVI·V7 | Flamenco / Llanera |
| Cadencia Andaluza II — iv·bIII·ii·i | Flamenco |

Los ciclos de golpes de joropo (Seis Corrido, Gabán/Paloma, Guacharaca, Seis Numerao, Nuevo Callao, Periquera, Zumba que zumba) provienen de: Calderón Sáenz, C. (2015). "Aspectos musicales del Joropo de Venezuela y Colombia". *Música Oral del Sur*, N° 12, ISSN 1138-8579, pp. 436–438 — ver tabla completa en [`Referencia/golpes_joropo_calderon.md`](Referencia/golpes_joropo_calderon.md).

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
| `index.html` | Aplicación web completa (HTML + CSS + JS) |
| `cuatro_acordes.json` | Base de datos de acordes, calidades y progresiones (embebida en `index.html` como `DATOS_ACORDES`) |
| `chords_v2.csv` | Base de datos maestra de digitaciones (204 acordes), embebida en `index.html` como `CHORDS_V2` |

## Tablas de referencia — `Referencia/`

Hojas en PDF, listas para imprimir o descargar, con los diagramas de todos los acordes:

| Archivo | Contenido |
|---|---|
| `acordes_completo.pdf` | Las 12 tonalidades × 12 calidades de acorde en una sola página vertical |
| `acordes_completo_landscape.pdf` | La misma tabla en formato horizontal, repartida en 2 páginas (Do–Fa / Fa#–Si), con diagramas más grandes (6 trastes) |
| [`golpes_joropo_calderon.md`](Referencia/golpes_joropo_calderon.md) | Catálogo de golpes del joropo venezolano y sus ciclos armónicos, tomado de Calderón Sáenz, C. (2015), *Música Oral del Sur* N°12, pp. 436–438 — base de las progresiones de joropo incluidas en la app |

Los PDF se generan con las herramientas de desarrollo internas del proyecto (repositorio privado, no público).

## Licencia

Este proyecto (código, datos y tablas de referencia) se distribuye bajo **[Creative Commons Atribución-NoComercial 4.0 Internacional (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/deed.es)**.

**Permitido:**
- Copiar y redistribuir el material en cualquier medio o formato.
- Adaptar, remezclar, transformar y crear a partir del material.
- Usarlo para fines personales, educativos o de estudio.

**No permitido:**
- Uso con fines comerciales (venta, inclusión en productos de pago, monetización, etc.) sin autorización expresa del autor.
- Aplicar términos legales o medidas tecnológicas que restrinjan a otros hacer cualquier cosa que la licencia permite.

**Condición:**
- Se debe dar crédito apropiado, indicar si se hicieron cambios, e incluir un enlace a la licencia.

## Créditos

Desarrollado por **Eduardo Klein** con asistencia de [Claude](https://claude.ai) (claude-sonnet-5).

### Cómo citar

Si usas o adaptas este material (código, datos o tablas de referencia), por favor da crédito así:

```
Klein, E. (2026). Acordes del Cuatro Venezolano [Software].
https://github.com/diodon/CuatroAcordes
```
