// src/constants/aqi.js

// Conjuntos de cortes por contaminante (puedes ajustar colores/umbrales)
export const BREAKSETS = {
  pm25: [
    { max: 12,  color: '#2ecc71', label: '0–12 (Bueno)' },
    { max: 35,  color: '#f1c40f', label: '12–35 (Moderado)' },
    { max: 55,  color: '#e67e22', label: '35–55 (Alto)' },
    { max: 500, color: '#e74c3c', label: '55+ (Muy alto)' },
  ],
  pm10: [
    { max: 54,  color: '#2ecc71', label: '0–54 (Bueno)' },
    { max: 154, color: '#f1c40f', label: '55–154 (Moderado)' },
    { max: 254, color: '#e67e22', label: '155–254 (Alto)' },
    { max: 1000,color: '#e74c3c', label: '255+ (Muy alto)' },
  ],
  o3: [
    { max: 60,  color: '#2ecc71', label: '0–60 (Bueno)' },
    { max: 120, color: '#f1c40f', label: '60–120 (Moderado)' },
    { max: 180, color: '#e67e22', label: '120–180 (Alto)' },
    { max: 1000,color: '#e74c3c', label: '180+ (Muy alto)' },
  ],
  // agrega más (no2, o3, etc.) si los usas
};

// Expresión de MapLibre para colorear círculos por valor
export function colorExpression(field = 'value', pollutant = 'pm25') {
  const breaks = BREAKSETS[pollutant] || BREAKSETS.pm25; // fallback seguro
  if (!breaks || breaks.length < 2) {
    console.warn(`No hay breaks definidos para '${pollutant}'. Usando pm25.`);
  }
  const b = breaks || BREAKSETS.pm25;

  // step(value, color0, umbral1, color1, umbral2, color2, ...)
  const expr = ['step', ['coalesce', ['to-number', ['get', field]], 0], b[0].color];
  for (let i = 0; i < b.length - 1; i++) {
    expr.push(b[i].max, b[i + 1].color);
  }
  return expr;
}
