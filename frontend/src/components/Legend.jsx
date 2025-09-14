import {
  Box,
  Flex,
  Text,
  Stack,
  FormControl,
  FormLabel,
  Select,
} from "@chakra-ui/react";
import { legendFor } from "../constants/aqi";

export default function Legend({
  pollutant = "pm25",
  position = "bottom-right",
  onPollutantChange,
}) {
  const items = legendFor(pollutant);
  const pos = {
    "bottom-right": { bottom: 4, right: 4 },
    "bottom-left": { bottom: 4, left: 4 },
    "top-right": { top: 4, right: 4 },
    "top-left": { top: 4, left: 4 },
  }[position];

  return (
    <Box position="absolute" {...pos} zIndex={1000}>
      <Box
        p={4}
        bg="rgba(7,23,63,.85)"
        border="1px solid"
        borderColor="rgba(255,255,255,.10)"
        rounded="xl"
        minW="280px"
      >
        {/* Selector de contaminante integrado en la leyenda */}
        <FormControl mb={4}>
          <FormLabel mb={2} fontSize="sm" color="white">
            Contaminante
          </FormLabel>
          <Select
            value={pollutant}
            onChange={(e) => onPollutantChange?.(e.target.value)}
            bg="white"
            color="black"
            size="sm"
            borderRadius="md"
          >
            <option value="pm25">PM2.5</option>
            <option value="pm10">PM10</option>
            <option value="no2">NO₂</option>
            <option value="o3">O₃</option>
            <option value="so2">SO₂</option>
            <option value="co">CO</option>
          </Select>
        </FormControl>

        <Text fontWeight="900" mb={3}>
          {pollutant.toUpperCase()} (µg/m³)
        </Text>
        <Stack spacing={2}>
          {items.map((it, i) => (
            <Flex key={i} align="center" gap={3}>
              <Box
                w="18px"
                h="18px"
                rounded="sm"
                border="1px solid rgba(255,255,255,.25)"
                style={{ background: it.color }}
              />
              <Text fontSize="sm" opacity={0.95}>
                {it.label}
              </Text>
            </Flex>
          ))}
        </Stack>
      </Box>
    </Box>
  );
}
