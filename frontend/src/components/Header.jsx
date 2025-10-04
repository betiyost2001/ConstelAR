import {
  Box, Flex, HStack, IconButton, Link, Stack, useDisclosure, Text, Button,
  Modal, ModalOverlay, ModalContent, ModalHeader, ModalBody, ModalCloseButton
} from "@chakra-ui/react";
import { CloseIcon, HamburgerIcon } from "@chakra-ui/icons";

const NAV = [
  { href: "#map", label: "Mapa" },
  { href: "#metodo", label: "Metodología" },
  { href: "#docs", label: "Docs" },
];

function ContaminantsInfoModalBtn() {
  const { isOpen, onOpen, onClose } = useDisclosure();
  return (
    <>
      <Button size="sm" variant="outline" onClick={onOpen}>
        ¿Qué mide cada contaminante?
      </Button>
      <Modal isOpen={isOpen} onClose={onClose} size="lg" isCentered>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Contaminantes y por qué importan</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Stack spacing={3} fontSize="sm">
              <Text><b>NO₂</b>: indicador de emisiones del transporte y centrales eléctricas; agrava enfermedades respiratorias.</Text>
              <Text><b>SO₂</b>: proviene de combustibles con azufre y procesos industriales; causa irritación y lluvia ácida.</Text>
              <Text><b>O₃</b>: ozono troposférico formado por reacciones fotoquímicas; afecta pulmones y cultivos.</Text>
              <Text><b>HCHO</b>: formaldehído generado por incendios y procesos industriales; precursor de ozono.</Text>
              <Link href="#metodo" color="space.neonYel">Leer metodología</Link>
            </Stack>
          </ModalBody>
        </ModalContent>
      </Modal>
    </>
  );
}

export default function Header() {
  const { isOpen, onOpen, onClose } = useDisclosure();
  return (
    <Box as="header" position="sticky" top="0" zIndex="docked" bg="transparent" backdropFilter="blur(6px)">
      <Flex className="spaceapps-bg"
        px={{ base: 4, md: 8 }} py={3} align="center"
        borderBottom="1px solid" borderColor="rgba(255,255,255,.08)">
        {/* Brand */}
        <Text as="a" href="/" fontFamily="'Fira Sans', system-ui, sans-serif" fontWeight="900" fontSize="xl">
          ConstelAR
        </Text>

        <HStack spacing={6} ml={8} display={{ base: "none", md: "flex" }}>
          {NAV.map((item) => (
            <Link key={item.href} href={item.href} className="glow-hover" _hover={{ color: "space.neonYel" }}>
              {item.label}
            </Link>
          ))}
        </HStack>

        <Flex ml="auto" align="center" gap={3}>
          <ContaminantsInfoModalBtn />
          <IconButton
            aria-label="Abrir menú"
            display={{ base: "inline-flex", md: "none" }}
            icon={isOpen ? <CloseIcon /> : <HamburgerIcon />}
            onClick={isOpen ? onClose : onOpen}
            variant="ghost"
          />
        </Flex>
      </Flex>

      {/* Menú mobile */}
      {isOpen && (
        <Box bg="rgba(7,23,63,.9)" px={4} pb={4} display={{ md: "none" }}>
          <Stack as="nav" spacing={3} pt={3}>
            {NAV.map((item) => (
              <Link key={item.href} href={item.href} onClick={onClose} _hover={{ color: "space.neonYel" }}>
                {item.label}
              </Link>
            ))}
          </Stack>
        </Box>
      )}
    </Box>
  );
}
