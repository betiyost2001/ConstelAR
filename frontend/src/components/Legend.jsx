// src/components/Legend.jsx
import { Box, HStack, Text } from "@chakra-ui/react";
import { BREAKSETS } from "../constants/aqi";

export default function Legend({ pollutant = "pm25", title }) {
  const breaks = BREAKSETS[pollutant] || [];
  return (
    <Box position="absolute" bottom="16px" right="16px" bg="white" p={3} rounded="md" boxShadow="md">
      <Text fontWeight="bold" mb={2}>{title}</Text>
      {breaks.map((b, i) => (
        <HStack key={i} spacing={2} mb={1}>
          <Box w="14px" h="14px" borderRadius="3px" bg={b.color} />
          <Text fontSize="sm">{b.label}</Text>
        </HStack>
      ))}
    </Box>
  );
}
