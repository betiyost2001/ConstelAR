// src/components/FilterBar.jsx
import { Box, FormControl, FormLabel, Select } from "@chakra-ui/react";

export default function FilterBar({ pollutant, onChange }) {
  return (
    <Box
      px={{ base: 4, md: 8 }}
      py={3}
      bg="rgba(7,23,63,.85)"
      borderBottom="1px solid"
      borderColor="rgba(255,255,255,.08)"
      display="flex"
      gap={4}
      alignItems="center"
    >
      <FormControl w={{ base: "100%", sm: "320px" }}>
        <FormLabel mb={1}>Contaminante</FormLabel>
        <Select
          value={pollutant}
          onChange={(e) => onChange(e.target.value)}
          bg="white"
          color="black"
        >
          <option value="pm25">PM2.5</option>
          <option value="pm10">PM10</option>
          <option value="no2">NO₂</option>
          <option value="o3">O₃</option>
          <option value="so2">SO₂</option>
          <option value="co">CO</option>
        </Select>
      </FormControl>
    </Box>
  );
}
