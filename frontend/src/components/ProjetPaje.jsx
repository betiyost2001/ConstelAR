import { Container, Heading, Text, Box, List, ListItem, VStack, HStack } from "@chakra-ui/react";
import { FaLaptopCode, FaCloudUploadAlt, FaGitAlt } from 'react-icons/fa';
import { SiVercel } from 'react-icons/si';

export default function ProjectPage() {
    // Define accent colors and box styles, suited for the dark background
    const accentColor = "teal.300"; 
    const boxBg = "whiteAlpha.100";
    const boxBorder = "whiteAlpha.300";

    return (
        // FIX APPLIED HERE: minH="100vh" ensures the container is at least the full screen height
        <Container maxW="3xl" py={12} minH="100vh">
            <VStack spacing={8} align="stretch">
                <Heading as="h1" size="2xl" color="white" mb={4} textAlign="center">
                    About the Project <span role="img" aria-label="rocket">🚀</span>
                </Heading>

                <Text color="whiteAlpha.800" fontSize="lg" textAlign="center">
                    <b style={{ color: accentColor }}>ConstelAR</b> is our proposal for the{" "}
                    <span style={{ color: accentColor }}>NASA Space Apps Challenge</span>.
                    We visualize measurements from the <span style={{ color: accentColor }}>NASA TEMPO</span> mission
                    to understand **air quality** in near real-time.
                </Text>

                {/* Technology Section */}
                <Box
                    rounded="lg"
                    bg={boxBg}
                    border="1px solid"
                    borderColor={boxBorder}
                    p={6}
                    shadow="xl"
                >
                    <HStack mb={4} spacing={3}>
                        <FaLaptopCode color={accentColor} size="20px" />
                        <Heading as="h2" size="lg" color={accentColor}>Technology</Heading>
                    </HStack>
                    <List spacing={3} color="whiteAlpha.800" pl={5}>
                        <ListItem>
                            <span style={{ color: accentColor, fontWeight: 'bold' }}>Frontend:</span> React + Vite + Chakra + MapLibre.
                        </ListItem>
                        <ListItem>
                            <span style={{ color: accentColor, fontWeight: 'bold' }}>Backend:</span> FastAPI; we ingest TEMPO data via Earthdata.
                        </ListItem>
                        <ListItem>
                            <span style={{ color: accentColor, fontWeight: 'bold' }}>Architecture:</span> Hexagonal; normalized endpoints.
                        </ListItem>
                    </List>
                </Box>

                {/* Challenge Resources Section */}
                <Box
                    rounded="lg"
                    bg={boxBg}
                    border="1px solid"
                    borderColor={boxBorder}
                    p={6}
                    shadow="xl"
                >
                    <HStack mb={4} spacing={3}>
                        <FaCloudUploadAlt color={accentColor} size="20px" />
                        <Heading as="h2" size="lg" color={accentColor}>
                            Challenge Resources <span role="img" aria-label="tools">🛠️</span>
                        </Heading>
                    </HStack>
                    <List spacing={3} color="whiteAlpha.800" pl={0}> 
                        
                        <ListItem>
                            <HStack align="flex-start"> 
                                <SiVercel color={accentColor} size="16px" style={{ marginTop: '4px' }}/>
                                <Text>
                                    <span style={{ fontWeight: 'bold' }}>Reader (or Vercel)</span>: Platform used for frontend deployment and global distribution.
                                </Text>
                            </HStack>
                        </ListItem>

                        <ListItem>
                            <HStack align="flex-start">
                                <FaGitAlt color={accentColor} size="16px" style={{ marginTop: '4px' }}/>
                                <Text>
                                    <span style={{ fontWeight: 'bold' }}>GitHub</span>: Open-source repository for project collaboration and management.
                                </Text>
                            </HStack>
                        </ListItem>

                        <ListItem>
                            <span style={{ fontWeight: 'bold', color: accentColor }}>NASA TEMPO & Earthdata</span>: Primary sources for air quality data.
                        </ListItem>
                        <ListItem>
                            <span style={{ fontWeight: 'bold', color: accentColor }}>Weather/Climate API</span>: Used to correlate meteorological events with contaminant measurements.
                        </ListItem>
                    </List>
                </Box>

                <Text color="whiteAlpha.700" mt={6} fontSize="sm" textAlign="center">
                    Open Source 🌎 · Argentine Team <b style={{ color: accentColor }}>ConstelAR</b>.
                </Text>
            </VStack>
        </Container>
    );
}