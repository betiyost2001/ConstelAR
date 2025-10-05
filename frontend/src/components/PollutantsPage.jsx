import {
  Box, Container, Heading, SimpleGrid, Text, Badge, Stack,
} from "@chakra-ui/react";
import { TEMPO_POLLUTANTS } from "../constants/pollutants";

const EXTRA = {
  no2: {
    mide: "Columna troposférica de NO₂ (mol/m²)",
    fuentes: "Tráfico, centrales eléctricas, combustión fósil.",
    riesgos: "Irritación y agravamiento de asma; precursor de ozono.",
    tips: "Menos emisiones móviles; evitar ejercicio intenso en picos.",
  },
  so2: {
    mide: "Columna total de SO₂ (mol/m²)",
    fuentes: "Quema de carbón/petróleo, refinerías, procesos industriales.",
    riesgos: "Irritación respiratoria; lluvia ácida; daño a vegetación.",
    tips: "Combustibles con bajo azufre; control de emisiones industriales.",
  },
  o3: {
    mide: "Columna total de ozono (DU)",
    fuentes: "Formado fotoquímicamente desde NOx + COV; transporte regional.",
    riesgos: "Disminuye función pulmonar; afecta cultivos.",
    tips: "Reducir NOx/COV; evitar exteriores en picos; seguir alertas.",
  },
  hcho: {
    mide: "Columna troposférica de formaldehído (mol/m²)",
    fuentes: "Incendios, procesos petroquímicos, fuentes biogénicas.",
    riesgos: "Irritación; contribuye a formación de ozono troposférico.",
    tips: "Minimizar quemas; ventilación; control de emisiones.",
  },
};

function Card({ id, label, unit }) {
  const info = EXTRA[id];
  return (
    <Box
      rounded="2xl"
      bg="whiteAlpha.100"
      border="1px solid"
      borderColor="whiteAlpha.200"
      p={5}
      _hover={{ bg: "whiteAlpha.150" }}
      transition="all .2s"
    >
      <Heading as="h3" size="md" color="white">
        {label}{" "}
        <Badge ml={2} colorScheme="blue" variant="subtle">
          {unit}
        </Badge>
      </Heading>
      <Stack spacing={2} mt={3} fontSize="sm">
        <Text color="whiteAlpha.800"><b>¿Qué mide?</b> {info.mide}</Text>
        <Text color="whiteAlpha.800"><b>Fuentes</b> {info.fuentes}</Text>
        <Text color="whiteAlpha.800"><b>Riesgos</b> {info.riesgos}</Text>
        <Text color="whiteAlpha.800"><b>Buenas prácticas</b> {info.tips}</Text>
      </Stack>
    </Box>
  );
}

export default function PollutantsPage() {
  return (
    <Container maxW="7xl" py={8}>
      <Heading as="h1" size="lg" color="white" mb={2}>
        ¿Qué mide cada contaminante?
      </Heading>
      <Text color="whiteAlpha.800" mb={6}>
        Guía rápida para interpretar el mapa y los valores satelitales (TEMPO).
      </Text>
      <SimpleGrid columns={{ base: 1, sm: 2, lg: 4 }} spacing={5}>
        {TEMPO_POLLUTANTS.map((p) => (
          <Card key={p.id} id={p.id} label={p.label} unit={p.unit} />
        ))}
      </SimpleGrid>
    </Container>
  );
}
