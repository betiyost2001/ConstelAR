export const TEMPO_POLLUTANTS = [
  {
    id: "no2",
    apiId: "NO2",
    labelKey: "pollutantsPage.pollutants.no2.label",
    shortLabel: "NO₂",
    unit: "molecules/cm²",
  },
  {
    id: "so2",
    apiId: "SO2",
    labelKey: "pollutantsPage.pollutants.so2.label",
    shortLabel: "SO₂",
    unit: "molecules/cm²",
  },
  {
    id: "o3",
    apiId: "O3",
    labelKey: "pollutantsPage.pollutants.o3.label",
    shortLabel: "O₃",
    unit: "DU",
  },
  {
    id: "hcho",
    apiId: "HCHO",
    labelKey: "pollutantsPage.pollutants.hcho.label",
    shortLabel: "HCHO",
    unit: "molecules/cm²",
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

export const getPollutantLongLabel = (id, t) =>
  t(POLLUTANTS_BY_ID[id]?.labelKey) ?? id?.toUpperCase?.() ?? "";

export const getPollutantUnit = (id) => POLLUTANTS_BY_ID[id]?.unit ?? "µg/m³";
