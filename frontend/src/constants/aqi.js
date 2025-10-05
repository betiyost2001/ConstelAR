// src/constants/aqi.js
import { DEFAULT_POLLUTANT } from "./pollutants";
const BASE_COLORS = ["#2E96F5", "#0960E1", "#E43700", "#8E1100", "#EAFE07"];

export const SCALES = {
  no2:  { breaks: [1e15, 2e15, 4e15, 8e15], colors: BASE_COLORS }, // molecules/cm²
  hcho: { breaks: [5e15, 1e16, 2e16, 3e16], colors: BASE_COLORS }, // molecules/cm²
  o3:   { breaks: [260, 300, 340, 400],     colors: BASE_COLORS }, // DU
  so2:  { breaks: [5e14, 1e15, 2e15, 4e15], colors: BASE_COLORS }, // si lo usan luego
};

export function colorExpression(prop, pollutant) {
  const cfg = SCALES[pollutant] || SCALES[DEFAULT_POLLUTANT];
  const { breaks, colors } = cfg;
  const base = ["to-number", ["get", prop]];
  const expr = ["step", base, colors[0]];
  for (let i = 0; i < breaks.length; i++) expr.push(breaks[i], colors[i + 1] || colors.at(-1));
  return expr;
}
export function legendFor(pollutant) {
  const { breaks, colors } = SCALES[pollutant] || SCALES[DEFAULT_POLLUTANT];
  const fmt = (x) => (Math.abs(x) >= 1e4 ? x.toExponential(1) : String(x));
  const items = [];
  for (let i = 0; i <= breaks.length; i++) {
    const color = colors[i] || colors.at(-1);
    items.push({ color, label: i===0 ? `< ${fmt(breaks[0])}` : i===breaks.length ? `≥ ${fmt(breaks.at(-1))}` : `${fmt(breaks[i-1])} – ${fmt(breaks[i])}` });
  }
  return items;
}
