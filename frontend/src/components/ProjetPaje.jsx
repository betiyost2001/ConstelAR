import { Container, Heading, Text, Box, List, ListItem } from "@chakra-ui/react";

export default function ProjectPage() {
  return (
    <Container maxW="3xl" py={8}>
      <Heading as="h1" size="lg" color="white" mb={3}>
        Sobre el proyecto
      </Heading>

      <Text color="whiteAlpha.800" mb={4}>
        <b className="text-white">ConstelAR</b> es nuestra propuesta para el{" "}
        <span className="text-white">NASA Space Apps Challenge</span>.
        Visualizamos mediciones de la misión <span className="text-white">NASA TEMPO</span>
        para entender la calidad del aire en tiempo casi real.
      </Text>

      <Box
        rounded="2xl"
        bg="whiteAlpha.100"
        border="1px solid"
        borderColor="whiteAlpha.200"
        p={5}
        mb={4}
      >
        <Heading as="h2" size="md" color="white" mb={2}>Tecnología</Heading>
        <List spacing={1} color="whiteAlpha.800" styleType="disc" pl={5}>
          <ListItem>Frontend: React + Vite + Chakra + MapLibre.</ListItem>
          <ListItem>Backend: FastAPI; ingestamos TEMPO vía Earthdata.</ListItem>
          <ListItem>Arquitectura hexagonal; endpoints normalizados.</ListItem>
        </List>
      </Box>

      <Box
        rounded="2xl"
        bg="whiteAlpha.100"
        border="1px solid"
        borderColor="whiteAlpha.200"
        p={5}
      >
        <Heading as="h2" size="md" color="white" mb={2}>
          Recursos del desafío
        </Heading>
        <List spacing={1} color="whiteAlpha.800" styleType="disc" pl={5}>
          <ListItem><b>GoDaddy</b>: dominio/hosting del sitio.</ListItem>
          <ListItem><b>Google Cloud</b>: despliegue (Firebase/Cloud Run), mapas e IA.</ListItem>
          <ListItem><b>Meteomatics</b>: API de tiempo/clima para correlacionar eventos.</ListItem>
          <ListItem><b>Microsoft</b>: Azure, Planetary Computer y GitHub Copilot.</ListItem>
        </List>
      </Box>

      <Text color="whiteAlpha.700" mt={6} fontSize="sm">
        Código abierto · Equipo argentino <b>ConstelAR</b>.
      </Text>
    </Container>
  );
}
