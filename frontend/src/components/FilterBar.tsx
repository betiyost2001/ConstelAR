import { Box, FormControl, FormLabel, Select } from "@chakra-ui/react";
import { PollutantType } from "../App";

interface FilterBarProps {
  pollutant: PollutantType;
  onChange: (value: PollutantType) => void;
}

export default function FilterBar({
  pollutant,
  onChange,
}: FilterBarProps): React.ReactElement {
  return (
    <Box className="px-4 md:px-8 py-3 bg-slate-900/85 border-b border-white/10 flex gap-4 items-center">
      <FormControl w={{ base: "100%", sm: "320px" }}>
        <FormLabel mb={1}>Contaminante</FormLabel>
        <Select
          value={pollutant}
          onChange={(e) => onChange(e.target.value as PollutantType)}
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
