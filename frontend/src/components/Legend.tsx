import {
  Box,
  Flex,
  Text,
  Stack,
  FormControl,
  FormLabel,
  Select,
  Button,
  ButtonGroup,
  IconButton,
  Tooltip,
} from "@chakra-ui/react";
import { legendFor, LegendItem } from "../constants/aqi.ts";
import { DeleteIcon, RepeatIcon } from "@chakra-ui/icons";
import { PollutantType, SelectionMode } from "../App";

interface LegendProps {
  pollutant?: PollutantType;
  position?: "bottom-right" | "bottom-left" | "top-right" | "top-left";
  onPollutantChange?: (value: PollutantType) => void;
  selectionMode?: SelectionMode;
  onSelectionModeChange?: (value: SelectionMode) => void;
  onClearSelection?: () => void;
  onResetView?: () => void;
}

export default function Legend({
  pollutant = "pm25",
  position = "bottom-right",
  onPollutantChange,
  selectionMode = "point",
  onSelectionModeChange,
  onClearSelection,
  onResetView,
}: LegendProps): React.ReactElement {
  const items: LegendItem[] = legendFor(pollutant);
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
            onChange={(e) =>
              onPollutantChange?.(e.target.value as PollutantType)
            }
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

        {/* Selection Mode Controls */}
        <FormControl mb={4}>
          <FormLabel mb={2} fontSize="sm" color="white">
            Modo de Selección
          </FormLabel>
          <ButtonGroup size="sm" isAttached variant="outline">
            <Button
              colorScheme={selectionMode === "point" ? "blue" : "gray"}
              onClick={() => onSelectionModeChange?.("point")}
              bg={selectionMode === "point" ? "blue.500" : "transparent"}
              color={selectionMode === "point" ? "white" : "white"}
              _hover={{
                bg: selectionMode === "point" ? "blue.600" : "gray.700",
              }}
            >
              Punto
            </Button>
            <Button
              colorScheme={selectionMode === "polygon" ? "blue" : "gray"}
              onClick={() => onSelectionModeChange?.("polygon")}
              bg={selectionMode === "polygon" ? "blue.500" : "transparent"}
              color={selectionMode === "polygon" ? "white" : "white"}
              _hover={{
                bg: selectionMode === "polygon" ? "blue.600" : "gray.700",
              }}
            >
              Polígono ( Área )
            </Button>
          </ButtonGroup>
        </FormControl>

        {/* Action Buttons */}
        <Flex gap={2} mb={4}>
          <Tooltip label="Limpiar selección">
            <IconButton
              size="sm"
              icon={<DeleteIcon />}
              onClick={onClearSelection}
              aria-label="Clear selection"
              bg="red.500"
              color="white"
              _hover={{ bg: "red.600" }}
            />
          </Tooltip>
          <Tooltip label="Reiniciar vista">
            <IconButton
              size="sm"
              icon={<RepeatIcon />}
              onClick={onResetView}
              aria-label="Reset view"
              bg="orange.500"
              color="white"
              _hover={{ bg: "orange.600" }}
            />
          </Tooltip>
        </Flex>

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
