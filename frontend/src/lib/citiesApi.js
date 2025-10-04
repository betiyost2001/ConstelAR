// citiesApi.js - GeoDB Cities API integration for US locations

const RAPIDAPI_KEY =
  import.meta.env.VITE_RAPIDAPI_KEY || "YOUR_RAPIDAPI_KEY_HERE"; // Add to .env
const RAPIDAPI_HOST = "wft-geo-db.p.rapidapi.com";
const BASE_URL = "https://wft-geo-db.p.rapidapi.com/v1/geo";

// Static US regions and states mapping (to avoid rate limits)
const US_REGIONS = [
  { code: "NE", name: "Northeast" },
  { code: "MW", name: "Midwest" },
  { code: "S", name: "South" },
  { code: "W", name: "West" },
];

const STATES_BY_REGION = {
  NE: [
    { code: "US-ME", name: "Maine" },
    { code: "US-NH", name: "New Hampshire" },
    { code: "US-VT", name: "Vermont" },
    { code: "US-MA", name: "Massachusetts" },
    { code: "US-RI", name: "Rhode Island" },
    { code: "US-CT", name: "Connecticut" },
    { code: "US-NY", name: "New York" },
    { code: "US-NJ", name: "New Jersey" },
    { code: "US-PA", name: "Pennsylvania" },
  ],
  MW: [
    { code: "US-OH", name: "Ohio" },
    { code: "US-IN", name: "Indiana" },
    { code: "US-IL", name: "Illinois" },
    { code: "US-MI", name: "Michigan" },
    { code: "US-WI", name: "Wisconsin" },
    { code: "US-MN", name: "Minnesota" },
    { code: "US-IA", name: "Iowa" },
    { code: "US-MO", name: "Missouri" },
    { code: "US-ND", name: "North Dakota" },
    { code: "US-SD", name: "South Dakota" },
    { code: "US-NE", name: "Nebraska" },
    { code: "US-KS", name: "Kansas" },
  ],
  S: [
    { code: "US-DE", name: "Delaware" },
    { code: "US-MD", name: "Maryland" },
    { code: "US-DC", name: "District of Columbia" },
    { code: "US-VA", name: "Virginia" },
    { code: "US-WV", name: "West Virginia" },
    { code: "US-NC", name: "North Carolina" },
    { code: "US-SC", name: "South Carolina" },
    { code: "US-GA", name: "Georgia" },
    { code: "US-FL", name: "Florida" },
    { code: "US-KY", name: "Kentucky" },
    { code: "US-TN", name: "Tennessee" },
    { code: "US-MS", name: "Mississippi" },
    { code: "US-AL", name: "Alabama" },
    { code: "US-OK", name: "Oklahoma" },
    { code: "US-TX", name: "Texas" },
    { code: "US-AR", name: "Arkansas" },
    { code: "US-LA", name: "Louisiana" },
  ],
  W: [
    { code: "US-MT", name: "Montana" },
    { code: "US-ID", name: "Idaho" },
    { code: "US-WY", name: "Wyoming" },
    { code: "US-CO", name: "Colorado" },
    { code: "US-NM", name: "New Mexico" },
    { code: "US-AZ", name: "Arizona" },
    { code: "US-UT", name: "Utah" },
    { code: "US-NV", name: "Nevada" },
    { code: "US-WA", name: "Washington" },
    { code: "US-OR", name: "Oregon" },
    { code: "US-CA", name: "California" },
    { code: "US-AK", name: "Alaska" },
    { code: "US-HI", name: "Hawaii" },
  ],
};

// Helper function to make API calls
async function apiCall(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    method: "GET",
    headers: {
      "X-RapidAPI-Key": RAPIDAPI_KEY,
      "X-RapidAPI-Host": RAPIDAPI_HOST,
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

// Fetch US regions (e.g., Northeast, South, Midwest, West)
export async function fetchUSRegions() {
  // Use static list to avoid RapidAPI rate limits and CSP friction in dev
  return US_REGIONS;
}

// Fetch states (divisions) in a specific region
export async function fetchStatesInRegion(regionCode) {
  // Return static mapping; ensures stable UX without hitting API limits
  const list = STATES_BY_REGION[regionCode] || [];
  return list;
}

// Fetch cities in a specific state (division)
export async function fetchCitiesInState(stateCode, limit = 100, offset = 0) {
  try {
    const data = await apiCall(
      `/countries/US/divisions/${stateCode}/cities?limit=${limit}&offset=${offset}`
    );
    return data.data || [];
  } catch (error) {
    console.error("Error fetching cities in state:", error);
    return [];
  }
}

// Search cities in a state with query (for autocomplete)
export async function searchCitiesInState(stateCode, query, limit = 10) {
  try {
    // GeoDB Cities sugiere filtrar por regionCode (código de estado de 2 letras)
    // Convertimos "US-XX" -> "XX"
    const alpha2 =
      (stateCode || "").split("-").pop()?.toUpperCase() || stateCode;
    const endpoint = `/cities?countryIds=US&regionCode=${encodeURIComponent(
      alpha2
    )}&namePrefix=${encodeURIComponent(query)}&limit=${limit}`;

    const res = await fetch(`${BASE_URL}${endpoint}`, {
      method: "GET",
      headers: {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
      },
    });

    // 404 indica que no hay coincidencias; devolvemos lista vacía (no es un error funcional)
    if (res.status === 404) {
      return [];
    }
    if (!res.ok) {
      throw new Error(`API Error: ${res.status} ${res.statusText}`);
    }

    const data = await res.json();
    return data.data || [];
  } catch (error) {
    console.error("Error searching cities in state:", error);
    return [];
  }
}
