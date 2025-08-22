import { useState } from "react";
import { Box, Button, Stack, TextField } from "@mui/material";
import Header from "./components/Header";
import MapView from "./components/MapView";
import { getOpenAQLatestByCity, getOpenAQLatestByCoords } from "./lib/api";

export default function App() {
  const [city, setCity] = useState("");

  const probarCity = async () => {
    try {
      const data = await getOpenAQLatestByCity(city || "New York");
      console.log("OpenAQ city:", data);
      alert(`OK por ciudad: ${city || "New York"} (mirá consola)`);
    } catch (e) {
      console.error(e);
      alert("Error por ciudad (probá coords).");
    }
  };

  const probarCoords = async () => {
    try {
      // Córdoba
      const data = await getOpenAQLatestByCoords(-31.4201, -64.1888, 100000, 10);
      console.log("OpenAQ coords:", data);
      alert("OK por coords (mirá consola).");
    } catch (e) {
      console.error(e);
      alert("Error por coords.");
    }
  };

  return (
    <Box>
      <Header />
      <Stack direction="row" spacing={1} sx={{ p: 2 }}>
        <TextField size="small" label="Ciudad" value={city} onChange={(e) => setCity(e.target.value)} />
        <Button variant="contained" onClick={probarCity}>Probar por ciudad</Button>
        <Button variant="outlined" onClick={probarCoords}>Probar por coords</Button>
      </Stack>
      <MapView />
    </Box>
  );
}
