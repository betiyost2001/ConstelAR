export const TEMPO_POLLUTANTS = [
  {
    id: "no2",
    apiId: "NO2",
    label: "Dióxido de nitrógeno (NO₂)",
    shortLabel: "NO₂",
    unit: "mol/m²",
  },
  {
    id: "so2",
    apiId: "SO2",
    label: "Dióxido de azufre (SO₂)",
    shortLabel: "SO₂",
    unit: "mol/m²",
  },
  {
    id: "o3",
    apiId: "O3",
    label: "Ozono troposférico (O₃)",
    shortLabel: "O₃",
    unit: "DU",
  },


{
    id: "hcho",
    apiId: "HCHO",
    label: "Formaldehído (HCHO)",
    shortLabel: "HCHO",
    unit: "mol/m²",
  },
];

export const DEFAULT_POLLUTANT = TEMPO_POLLUTANTS[0].id;

export const POLLUTANTS_BY_ID = Object.fromEntries(
  TEMPO_POLLUTANTS.map((item) => [item.id, item])
);
export const UI_TO_API = Object.fromEntries(
  TEMPO_POLLUTANTS.map((item) => [item.id, item.apiId])
);

export const API_TO_UI = Object.fromEntries(
  TEMPO_POLLUTANTS.map((item) => [item.apiId, item.id])
);

export const getPollutantLabel = (id) =>
  POLLUTANTS_BY_ID[id]?.shortLabel ?? id?.toUpperCase?.() ?? "";

export const getPollutantLongLabel = (id) =>
  POLLUTANTS_BY_ID[id]?.label ?? id?.toUpperCase?.() ?? "";

export const getPollutantUnit = (id) =>
  POLLUTANTS_BY_ID[id]?.unit ?? "µg/m³";
