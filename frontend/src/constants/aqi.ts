import { PollutantType } from "../App";

// Escalas simplificadas (µg/m³). Ajustalas si tenés tablas oficiales.
interface ScaleConfig {
  breaks: number[];
  colors: string[];
  multiplier?: number;
}

export const SCALES: Record<PollutantType, ScaleConfig> = {
  pm25: {
    breaks: [12, 35.4, 55.4, 150.4],
    colors: ["#2E96F5", "#0960E1", "#E43700", "#8E1100", "#EAFE07"],
  },
  pm10: {
    breaks: [54, 154, 254, 354],
    colors: ["#2E96F5", "#0960E1", "#E43700", "#8E1100", "#EAFE07"],
  },
  no2: {
    breaks: [53, 100, 360, 649],
    colors: ["#2E96F5", "#0960E1", "#E43700", "#8E1100", "#EAFE07"],
  },
  o3: {
    breaks: [70, 120, 160, 200],
    colors: ["#2E96F5", "#0960E1", "#E43700", "#8E1100", "#EAFE07"],
  },
  so2: {
    breaks: [75, 185, 304, 604],
    colors: ["#2E96F5", "#0960E1", "#E43700", "#8E1100", "#EAFE07"],
  },
  // CO: si tu backend viene en mg/m³ y querés llevarlo a escala similar de µg/m³, usa multiplier 1000.
  co: {
    breaks: [4400, 9400, 15400, 30400],
    colors: ["#2E96F5", "#0960E1", "#E43700", "#8E1100", "#EAFE07"],
    multiplier: 1000,
  },
};

export function colorExpression(prop: string, pollutant: PollutantType): any[] {
  const cfg = SCALES[pollutant] || SCALES.pm25;
  const { breaks, colors, multiplier = 1 } = cfg;
  const base = ["*", ["to-number", ["get", prop]], multiplier];
  const expr: any[] = ["step", base, colors[0]];
  for (let i = 0; i < breaks.length; i++) {
    expr.push(breaks[i], colors[i + 1] || colors[colors.length - 1]);
  }
  return expr;
}

export interface LegendItem {
  color: string;
  label: string;
}

export function legendFor(pollutant: PollutantType): LegendItem[] {
  const cfg = SCALES[pollutant] || SCALES.pm25;
  const { breaks, colors } = cfg;
  const items: LegendItem[] = [];
  for (let i = 0; i <= breaks.length; i++) {
    const color = colors[i] || colors[colors.length - 1];
    let label: string;
    if (i === 0) label = `< ${breaks[0]}`;
    else if (i === breaks.length) label = `≥ ${breaks[breaks.length - 1]}`;
    else label = `${breaks[i - 1]} – ${breaks[i]}`;
    items.push({ color, label });
  }
  return items;
}
