// citiesApi.js - GeoDB Cities API integration for US locations

const RAPIDAPI_KEY =
  import.meta.env.VITE_RAPIDAPI_KEY || "YOUR_RAPIDAPI_KEY_HERE"; // Add to .env
const RAPIDAPI_HOST = "wft-geo-db.p.rapidapi.com";
const BASE_URL = "https://wft-geo-db.p.rapidapi.com/v1/geo";

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
    // If stateCode is "US", search all US cities
    if (stateCode === "US") {
      const endpoint = `/cities?countryIds=US&namePrefix=${encodeURIComponent(
        query
      )}&limit=${limit}`;

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
    }

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
