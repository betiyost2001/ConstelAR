import { Box, Flex, Text, Stack } from "@chakra-ui/react";
import { legendFor } from "../constants/aqi";
import { DEFAULT_POLLUTANT, getPollutantLabel, getPollutantUnit } from "../constants/pollutants";

export default function Legend({ pollutant = DEFAULT_POLLUTANT, position = "bottom-right" }) {
  const items = legendFor(pollutant);
  const pos = {
    "bottom-right": { bottom: 4, right: 4 },
    "bottom-left": { bottom: 4, left: 4 },
    "top-right": { top: 4, right: 4 },
    "top-left": { top: 4, left: 4 },
  }[position];
  const label = getPollutantLabel(pollutant);
  const unit = getPollutantUnit(pollutant);

  return (
    <Box position="absolute" {...pos} zIndex={1000}>
      <Box
        p={4}
        bg="rgba(7,23,63,.85)"
        border="1px solid"
        borderColor="rgba(255,255,255,.10)"
        rounded="xl"
        minW="240px"
      >
        <Text fontWeight="900" mb={3}>
          {label} ({unit})
        </Text>
        <Stack spacing={2}>
          {items.map((it, i) => (
            <Flex key={i} align="center" gap={3}>
              <Box w="18px" h="18px" rounded="sm" border="1px solid rgba(255,255,255,.25)" style={{ background: it.color }} />
              <Text fontSize="sm" opacity={0.95}>{it.label}</Text>
            </Flex>
          ))}
        </Stack>
      </Box>
    </Box>
  );
}
