import { DEFAULT_POLLUTANT } from "./pollutants";

// Escalas simplificadas para columnas troposféricas (mol/m² o DU según parámetro).
const BASE_COLORS = ["#2E96F5", "#0960E1", "#E43700", "#8E1100", "#EAFE07"];

export const SCALES = {
  no2:  { breaks: [0.0005, 0.001, 0.002, 0.004], colors: BASE_COLORS },
  so2:  { breaks: [0.0001, 0.0003, 0.0006, 0.001], colors: BASE_COLORS },
  o3:   { breaks: [0.02, 0.04, 0.08, 0.12], colors: BASE_COLORS }, // DU aprox.
  hcho: { breaks: [0.0003, 0.0006, 0.0012, 0.0024], colors: BASE_COLORS },
};

export function colorExpression(prop, pollutant) {
  const cfg = SCALES[pollutant] || SCALES[DEFAULT_POLLUTANT];
  const { breaks, colors, multiplier = 1 } = cfg;
  const base = ["*", ["to-number", ["get", prop]], multiplier];
  const expr = ["step", base, colors[0]];
  for (let i = 0; i < breaks.length; i++) {
    expr.push(breaks[i], colors[i + 1] || colors[colors.length - 1]);
  }
  return expr;
}

export function legendFor(pollutant) {
  const cfg = SCALES[pollutant] || SCALES[DEFAULT_POLLUTANT];
  const { breaks, colors } = cfg;
  const items = [];
  for (let i = 0; i <= breaks.length; i++) {
    const color = colors[i] || colors[colors.length - 1];
    let label;
    if (i === 0) label = `< ${breaks[0]}`;
    else if (i === breaks.length) label = `≥ ${breaks[breaks.length - 1]}`;
    else label = `${breaks[i - 1]} – ${breaks[i]}`;
    items.push({ color, label });
  }
  return items;
}
