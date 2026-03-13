// generate_chord_table.js
// Generates a CSV of all chords and fingerings for the Venezuelan Cuatro.
// Usage: node generate_chord_table.js > chords.csv

const fs = require('fs');
const CFG = JSON.parse(fs.readFileSync('./cuatro_acordes.json', 'utf8'));

const STRING_BASES = CFG.algoritmo.bases_cuerdas; // [11, 6, 2, 9] → B, F#, D, A

function notaANum(nota) {
  const idx = CFG.notas.sostenidos.indexOf(nota);
  if (idx >= 0) return idx;
  return CFG.notas.bemoles.indexOf(nota);
}

function nombreAcorde(nota, calidad) {
  const q = CFG.calidades[calidad];
  if (!q) return nota;
  return nota + q.simbolo;
}

function calcularDigitacion(raizNum, calidad) {
  const q = CFG.calidades[calidad];
  if (!q) return [0, 0, 0, 0];
  const intervalos = q.intervalos;
  const notasAcorde = new Set(intervalos.map(i => ((raizNum + i) % 12 + 12) % 12));

  // Check overrides first (sharp name, then flat name)
  const notaS = CFG.notas.sostenidos[raizNum];
  const overrideS = CFG.digitaciones_override[nombreAcorde(notaS, calidad)];
  if (overrideS) return overrideS;
  const notaB = CFG.notas.bemoles[raizNum];
  const overrideB = CFG.digitaciones_override[nombreAcorde(notaB, calidad)];
  if (overrideB) return overrideB;

  const w = CFG.algoritmo.pesos;

  const opciones = STRING_BASES.map(base =>
    Array.from({ length: 10 }, (_, f) => f).filter(f => notasAcorde.has((base + f) % 12))
  );
  opciones.forEach(op => { if (op.length === 0) op.push(0); });

  let mejor = null, mejorPuntuacion = Infinity;

  function iterar(s, combo) {
    if (s === 4) {
      const cubiertos = new Set(STRING_BASES.map((b, i) => (b + combo[i]) % 12));
      if (!cubiertos.has(raizNum % 12)) return;
      const faltantes = [...notasAcorde].filter(n => !cubiertos.has(n)).length;
      const presionados = combo.filter(f => f > 0);
      const distinto = new Set(presionados).size;
      const fspan = presionados.length > 0 ? Math.max(...presionados) - Math.min(...presionados) : 0;
      const fp = combo.map((f, i) => f > 0 ? i : -1).filter(i => i >= 0);
      const op = combo.map((f, i) => f === 0 ? i : -1).filter(i => i >= 0);
      const guia     = op.filter(i => fp.length === 0 || i < fp[0]).length;
      const arrastre = op.filter(i => fp.length === 0 || i > fp[fp.length - 1]).length;
      const medio    = op.filter(i => fp.length > 0 && i > fp[0] && i < fp[fp.length - 1]).length;
      const minTraste  = presionados.length > 0 ? Math.min(...presionados) : 0;
      const barrePuro  = (presionados.length > 0 && new Set(presionados).size === 1) ? presionados[0] : 0;
      const mx = Math.max(...combo);
      const sm = combo.reduce((a, b) => a + b, 0);
      const puntuacion = faltantes * w.nota_faltante
        + distinto * w.distintas
        + guia * minTraste * w.escala_guia
        + arrastre * w.arrastre
        + medio * w.medio
        + barrePuro * w.barre_puro
        + fspan * w.amplitud
        + mx * w.maximo
        + sm;
      if (puntuacion < mejorPuntuacion) {
        mejorPuntuacion = puntuacion;
        mejor = [...combo];
      }
      return;
    }
    for (const f of opciones[s]) {
      combo[s] = f;
      iterar(s + 1, combo);
    }
  }
  iterar(0, [0, 0, 0, 0]);
  return mejor || [0, 0, 0, 0];
}

// CSV header
// Strings are ordered B · F# · D · A (high to low)
const rows = ['Chord,Root (EN),Root (ES),Quality,Symbol,B,F#,D,A,Fingering'];

for (const nota of CFG.notas.sostenidos) {
  const raizNum = notaANum(nota);
  const notaES  = CFG.notas.nombres_display[nota] || nota;

  for (const [calKey, cal] of Object.entries(CFG.calidades)) {
    const symbol = cal.simbolo || calKey;
    const chord  = nota + symbol;
    const dig    = calcularDigitacion(raizNum, calKey);
    rows.push(`${chord},${nota},${notaES},${cal.nombre},${symbol},${dig[0]},${dig[1]},${dig[2]},${dig[3]},${dig.join('')}`);
  }
}

process.stdout.write(rows.join('\n') + '\n');
