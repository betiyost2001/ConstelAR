// Mock data generator for contaminant readings
// Generates sample points with realistic contaminant concentrations

import { PollutantType } from "../App";

const POLLUTANTS: PollutantType[] = ["pm25", "pm10", "no2", "o3", "so2", "co"];

const CONCENTRATION_RANGES: Record<PollutantType, [number, number]> = {
  pm25: [5, 150], // µg/m³
  pm10: [10, 200], // µg/m³
  no2: [10, 200], // µg/m³
  o3: [20, 180], // µg/m³
  so2: [5, 350], // µg/m³
  co: [0.1, 15], // mg/m³
};

const UNITS: Record<PollutantType, string> = {
  pm25: "µg/m³",
  pm10: "µg/m³",
  no2: "µg/m³",
  o3: "µg/m³",
  so2: "µg/m³",
  co: "mg/m³",
};

interface MockFeature {
  type: "Feature";
  geometry: {
    type: "Point";
    coordinates: [number, number];
  };
  properties: {
    parameter: PollutantType;
    value: number;
    unit: string;
    datetime: string;
    location: string;
  };
}

interface GeoJSONFeatureCollection {
  type: "FeatureCollection";
  features: MockFeature[];
}

// Generate random point within bounds
function randomPointInBounds(
  west: number,
  south: number,
  east: number,
  north: number
): [number, number] {
  const lng = west + Math.random() * (east - west);
  const lat = south + Math.random() * (north - south);
  return [lng, lat];
}

// Generate concentration based on pollutant with some spatial variation
function generateConcentration(
  pollutant: PollutantType,
  lat: number,
  lng: number
): number {
  const [min, max] = CONCENTRATION_RANGES[pollutant];
  // Add some spatial variation (higher concentrations in certain areas)
  const spatialFactor = Math.sin(lat * 10) * Math.cos(lng * 10) * 0.3 + 0.7;
  const baseValue = min + Math.random() * (max - min);
  return Math.round(baseValue * spatialFactor * 100) / 100;
}

// Generate mock GeoJSON data
export function generateMockData(
  bbox: number[],
  pollutant: PollutantType = "pm25",
  count: number = 150
): GeoJSONFeatureCollection {
  const [west, south, east, north] = bbox;
  const features: MockFeature[] = [];

  for (let i = 0; i < count; i++) {
    const [lng, lat] = randomPointInBounds(west, south, east, north);
    const value = generateConcentration(pollutant, lat, lng);

    features.push({
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: [lng, lat],
      },
      properties: {
        parameter: pollutant,
        value: value,
        unit: UNITS[pollutant],
        datetime: new Date(
          Date.now() - Math.random() * 24 * 60 * 60 * 1000
        ).toISOString(),
        location: `Mock Station ${i + 1}`,
      },
    });
  }

  return {
    type: "FeatureCollection",
    features: features,
  };
}

// Filter mock data by bounding box
export function filterMockDataByBbox(
  mockData: GeoJSONFeatureCollection,
  bbox: number[]
): GeoJSONFeatureCollection {
  const [west, south, east, north] = bbox;

  return {
    ...mockData,
    features: mockData.features.filter((feature) => {
      const [lng, lat] = feature.geometry.coordinates;
      return lng >= west && lng <= east && lat >= south && lat <= north;
    }),
  };
}

// Filter mock data by polygon (point-in-polygon test)
export function filterMockDataByPolygon(
  mockData: GeoJSONFeatureCollection,
  polygonCoordinates: number[][]
): GeoJSONFeatureCollection {
  // Simple point-in-polygon algorithm
  function pointInPolygon(
    point: [number, number],
    polygon: number[][]
  ): boolean {
    const [x, y] = point;
    let inside = false;

    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
      const [xi, yi] = polygon[i];
      const [xj, yj] = polygon[j];

      if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) {
        inside = !inside;
      }
    }

    return inside;
  }

  return {
    ...mockData,
    features: mockData.features.filter((feature) => {
      const point = feature.geometry.coordinates as [number, number];
      return pointInPolygon(point, polygonCoordinates);
    }),
  };
}

// Filter mock data by point and radius (in km)
export function filterMockDataByPoint(
  mockData: GeoJSONFeatureCollection,
  centerPoint: [number, number],
  radiusKm: number = 5
): GeoJSONFeatureCollection {
  const [centerLng, centerLat] = centerPoint;
  const R = 6371; // Earth's radius in km

  function haversineDistance(
    lat1: number,
    lng1: number,
    lat2: number,
    lng2: number
  ): number {
    const dLat = ((lat2 - lat1) * Math.PI) / 180;
    const dLng = ((lng2 - lng1) * Math.PI) / 180;
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos((lat1 * Math.PI) / 180) *
        Math.cos((lat2 * Math.PI) / 180) *
        Math.sin(dLng / 2) *
        Math.sin(dLng / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }

  return {
    ...mockData,
    features: mockData.features.filter((feature) => {
      const [lng, lat] = feature.geometry.coordinates;
      const distance = haversineDistance(centerLat, centerLng, lat, lng);
      return distance <= radiusKm;
    }),
  };
}
