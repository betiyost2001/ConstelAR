import {
  Box, Container, Heading, SimpleGrid, Text, Badge, Stack, VStack, Icon 
} from "@chakra-ui/react";
// Debes importar la librería de iconos. Asegúrate de tener 'react-icons' instalado.
import { FaCarSide, FaIndustry, FaGlobeAmericas, FaFire } from 'react-icons/fa'; 

// NOTE: You must replace '../constants/pollutants' with the actual path 
// or define TEMPO_POLLUTANTS here if it's not available.
// Assuming TEMPO_POLLUTANTS looks like: [{id: 'no2', label: 'Nitrogen Dioxide', unit: 'NO₂' }, ...]
// import { TEMPO_POLLUTANTS } from "../constants/pollutants";

// Placeholder for TEMPO_POLLUTANTS data structure for demonstration:
const TEMPO_POLLUTANTS = [
    { id: 'no2', label: 'Nitrogen Dioxide', unit: 'NO₂' },
    { id: 'so2', label: 'Sulfur Dioxide', unit: 'SO₂' },
    { id: 'o3', label: 'Tropospheric Ozone', unit: 'O₃' },
    { id: 'hcho', label: 'Formaldehyde', unit: 'HCHO' },
];


const ACCENT_COLOR = "teal.300";

const EXTRA = {
  no2: {
    icon: FaCarSide, // Icon: Traffic
    mide: "Tropospheric column of NO₂ (mol/m²)",
    fuentes: "Traffic, power plants, fossil fuel combustion.",
    riesgos: "Irritation and asthma aggravation; ozone precursor.",
    tips: "Lower mobile emissions; avoid intense exercise during peaks.",
  },
  so2: {
    icon: FaIndustry, // Icon: Industry
    mide: "Total column of SO₂ (mol/m²)",
    fuentes: "Coal/petroleum burning, refineries, industrial processes.",
    riesgos: "Respiratory irritation; acid rain; vegetation damage.",
    tips: "Low-sulfur fuels; industrial emission control.",
  },
  o3: {
    icon: FaGlobeAmericas, // Icon: Global impact
    mide: "Total column of ozone (DU)",
    fuentes: "Photochemically formed from NOx + VOCs; regional transport.",
    riesgos: "Decreased lung function; affects crops.",
    tips: "Reduce NOx/VOCs; avoid outdoors during peaks; follow alerts.",
  },
  hcho: {
    icon: FaFire, // Icon: Fire/Burning
    mide: "Tropospheric column of formaldehyde (mol/m²)",
    fuentes: "Fires, petrochemical processes, biogenic sources.",
    riesgos: "Irritation; contributes to tropospheric ozone formation.",
    tips: "Minimize burning; ventilation; emission control.",
  },
};

function Card({ id, label, unit }) {
  const info = EXTRA[id];
  
  return (
    <Box
      rounded="xl" // Más redondeado
      bg="whiteAlpha.100"
      border="1px solid"
      borderColor="whiteAlpha.200"
      p={6} // Más padding
      shadow="xl" // Sombra sutil para profundidad
      
      // EFECTO HOVER: Elevar ligeramente la tarjeta e iluminar el borde
      _hover={{ 
        bg: "whiteAlpha.150", 
        transform: "translateY(-4px)", 
        shadow: "2xl",
        borderColor: ACCENT_COLOR, // Ilumina el borde
      }}
      transition="all .3s ease-in-out" // Transición suave
    >
        <VStack spacing={3} align="flex-start">
            
            {/* ICONO DE REFERENCIA */}
            <Box w="full" textAlign="center">
                <Icon as={info.icon} boxSize={10} color={ACCENT_COLOR} mb={2} />
            </Box>

            <Heading as="h3" size="lg" color="white">
                {label}{" "}
                <Badge ml={1} colorScheme="teal" variant="solid" bg={ACCENT_COLOR} fontSize="sm">
                    {unit}
                </Badge>
            </Heading>
            
            {/* Contenido principal de la tarjeta */}
            <Stack spacing={2} mt={3} fontSize="sm">
                <Text color="whiteAlpha.800">
                    <b style={{ color: ACCENT_COLOR }}>What does it measure?</b> {info.mide}
                </Text>
                <Text color="whiteAlpha.800">
                    <b style={{ color: ACCENT_COLOR }}>Sources:</b> {info.fuentes}
                </Text>
                <Text color="whiteAlpha.800">
                    <b style={{ color: ACCENT_COLOR }}>Risks:</b> {info.riesgos}
                </Text>
                <Text color="whiteAlpha.800">
                    <b style={{ color: ACCENT_COLOR }}>Good Practices:</b> {info.tips}
                </Text>
            </Stack>
        </VStack>
    </Box>
  );
}

export default function PollutantsPage() {
  return (
    // minH="100vh" es clave si la página no tiene un Footer fijo
    <Container maxW="7xl" py={12} minH="100vh"> 
        <VStack spacing={10} align="stretch">
            
            <VStack spacing={2} textAlign="center" mb={6}>
                <Heading as="h1" size="2xl" color="white">
                    What Does Each Pollutant Measure?
                </Heading>
                <Text color="whiteAlpha.700" fontSize="lg">
                    A quick guide to interpreting the map and satellite values (TEMPO).
                </Text>
            </VStack>

            <SimpleGrid columns={{ base: 1, sm: 2, lg: 4 }} spacing={6}>
                {TEMPO_POLLUTANTS.map((p) => (
                    <Card key={p.id} id={p.id} label={p.label} unit={p.unit} />
                ))}
            </SimpleGrid>

        </VStack>
    </Container>
  );
}