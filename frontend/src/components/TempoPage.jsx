import { Container, Heading, Text, Box, List, ListItem, VStack, SimpleGrid, Icon, HStack } from "@chakra-ui/react";
import { FaSatellite, FaClock, FaGlobeAmericas, FaCloudSun, FaChartLine } from 'react-icons/fa';

const ACCENT_COLOR = "teal.300";

// Datos clave sobre la misión TEMPO
const tempoFeatures = [
    {
        icon: FaClock,
        title: "GEOSTATIONARY ORBIT",
        description: "TEMPO is the first instrument to measure air quality from a geostationary orbit, allowing for continuous, hourly coverage over North America.",
    },
    {
        icon: FaGlobeAmericas,
        title: "FULL CONTINENTAL VIEW",
        description: "It monitors the atmosphere from the Atlantic to the Pacific and from the tropics to the middle of Canada, providing a massive dataset.",
    },
    {
        icon: FaCloudSun,
        title: "HOURLY DATA RESOLUTION",
        description: "The mission provides near-real-time data, offering hourly updates during the daytime to track rapid changes in pollution.",
    },
    {
        icon: FaChartLine,
        title: "CRITICAL POLLUTANTS",
        description: "Measures key pollutants like NO₂, O₃, SO₂, and Formaldehyde (HCHO) to combat health hazards and climate change.",
    },
];

export default function TempoPage() {
    return (
        <Container maxW="6xl" py={12} minH="100vh">
            <VStack spacing={10} align="stretch">
                
                <VStack spacing={2} textAlign="center" mb={6}>
                    <Icon as={FaSatellite} boxSize={12} color={ACCENT_COLOR} />
                    <Heading as="h1" size="2xl" color="white">
                        TEMPO Satellite: The Air Quality Revolution
                    </Heading>
                    <Text color="whiteAlpha.700" fontSize="lg">
                        The Tropospheric Emissions: Monitoring of Pollution (TEMPO) mission is changing how we see the air we breathe.
                    </Text>
                </VStack>

                {/* Main Description Box */}
                <Box
                    p={8}
                    rounded="xl"
                    bg="whiteAlpha.100"
                    border="1px solid"
                    borderColor={ACCENT_COLOR}
                    shadow="2xl"
                >
                    <Heading as="h2" size="xl" color={ACCENT_COLOR} mb={4}>
                        Why TEMPO is a Game-Changer
                    </Heading>
                    <Text color="whiteAlpha.800" fontSize="md">
                        Prior to TEMPO, air quality data from space was available only once a day. TEMPO breaks this barrier by being mounted on a commercial communications satellite in a **geostationary orbit**. This revolutionary positioning allows it to stare continuously at the same large area (North America), capturing **hourly snapshots of pollution** during the entire day. This level of detail is critical for understanding pollution sources, forecasting air quality, and protecting public health across the continent.
                    </Text>
                </Box>

                {/* Features Grid */}
                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={8} pt={4}>
                    {tempoFeatures.map((item, index) => (
                        <Box
                            key={index}
                            p={6}
                            rounded="lg"
                            bg="whiteAlpha.0"
                            borderLeft={`4px solid ${ACCENT_COLOR}`}
                            _hover={{ bg: "whiteAlpha.100" }}
                            transition="background-color 0.2s"
                        >
                            <HStack align="flex-start" spacing={4}>
                                <Icon as={item.icon} boxSize={6} color={ACCENT_COLOR} mt={1} />
                                <VStack align="flex-start" spacing={1}>
                                    <Heading as="h3" size="md" color="white">{item.title}</Heading>
                                    <Text color="whiteAlpha.700">{item.description}</Text>
                                </VStack>
                            </HStack>
                        </Box>
                    ))}
                </SimpleGrid>

            </VStack>
        </Container>
    );
}