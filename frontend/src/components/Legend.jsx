import { Box, Flex, Text, Stack } from "@chakra-ui/react";

// items: [{label: 'PM2.5 Alto', color: '#E43700'}]
const DEFAULT_ITEMS = [
  { label: "Bajo", color: "#2E96F5" },   // blueYdr
  { label: "Medio", color: "#0960E1" },  // neonBlue
  { label: "Alto", color: "#E43700" },   // rocketRed
];

export default function Legend({ title = "Leyenda", items = DEFAULT_ITEMS, position = "bottom-right" }) {
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
        bg="rgba(7,23,63,.7)"
        border="1px solid"
        borderColor="rgba(255,255,255,.10)"
        rounded="xl"
        boxShadow="0 0 18px rgba(0,0,0,.25)"
        minW="220px"
      >
        <Text fontWeight="900" mb={3}>
          {title}
        </Text>
        <Stack spacing={2}>
          {items.map((it) => (
            <Flex key={it.label} align="center" gap={3}>
              <Box w="18px" h="18px" rounded="sm" border="1px solid rgba(255,255,255,.25)" style={{ background: it.color }} />
              <Text fontSize="sm" opacity={0.95}>{it.label}</Text>
            </Flex>
          ))}
        </Stack>
      </Box>
    </Box>
  );
}
