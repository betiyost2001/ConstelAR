import {
  Box, Flex, HStack, IconButton, Link, Stack, useDisclosure, Text,
} from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";
import { CloseIcon, HamburgerIcon } from "@chakra-ui/icons";
import InfoModalBtn from "./InfoModalBtn";

// MODIFICACIÓN: Se agrega la nueva ruta para TEMPO y se traducen los labels.
const NAV = [
  { href: "/", label: "Map" },
  { href: "/tempo", label: "TEMPO Satellite" }, // NUEVA RUTA
  { href: "/contaminantes", label: "What Pollutants Measure" },
  { href: "/proyecto", label: "About the Project" },
];

export default function Header() {
  const { isOpen, onOpen, onClose } = useDisclosure();
  return (
    <Box as="header" position="sticky" top="0" zIndex="docked" bg="transparent" backdropFilter="blur(6px)">
      <Flex
        className="spaceapps-bg"
        px={{ base: 4, md: 8 }}
        py={3}
        align="center"
        borderBottom="1px solid"
        borderColor="rgba(255,255,255,.08)"
      >
        <Text as={RouterLink} to="/" className="fira-sans-bold text-2xl md:text-3xl">
          ConstelAR
        </Text>

        <HStack spacing={6} ml={8} display={{ base: "none", md: "flex" }}>
          {NAV.map((item) => (
            <Link
              as={RouterLink}
              key={item.href}
              to={item.href}
              className="glow-hover"
              _hover={{ color: "space.neonYel" }}
            >
              {item.label}
            </Link>
          ))}
        </HStack>

        <Flex ml="auto" align="center" gap={3}>
          <InfoModalBtn />
          <IconButton
            aria-label="Open menu" // Traducido
            display={{ base: "inline-flex", md: "none" }}
            icon={isOpen ? <CloseIcon /> : <HamburgerIcon />}
            onClick={isOpen ? onClose : onOpen}
            variant="ghost"
          />
        </Flex>
      </Flex>

      {isOpen && (
        <Box bg="rgba(7,23,63,.9)" px={4} pb={4} display={{ md: "none" }}>
          <Stack as="nav" spacing={3} pt={3}>
            {NAV.map((item) => (
              <Link
                as={RouterLink}
                key={item.href}
                to={item.href}
                onClick={onClose}
                _hover={{ color: "space.neonYel" }}
              >
                {item.label}
              </Link>
            ))}
          </Stack>
        </Box>
      )}
    </Box>
  );
}