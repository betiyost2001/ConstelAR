import {
  Box, Flex, HStack, IconButton, Button, Link, Stack, useDisclosure, Text
} from "@chakra-ui/react";
import { CloseIcon, HamburgerIcon } from "@chakra-ui/icons";

const NAV = [
  { href: "#map", label: "Mapa" },
  { href: "#metodo", label: "Metodología" },
  { href: "#docs", label: "Docs" },
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
          <Button className="glow-hover" size="sm" variant="outline">
            Documentación
          </Button>
          <Button className="glow-hover" size="sm">
            Iniciar sesión
          </Button>
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
            <Button className="glow-hover" size="sm" w="full" mt={2}>
              Iniciar sesión
            </Button>
          </Stack>
        </Box>
      )}
    </Box>
  );
}
