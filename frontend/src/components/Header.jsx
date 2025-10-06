import React from "react";
import {
  Box,
  Flex,
  HStack,
  IconButton,
  Link,
  Stack,
  useDisclosure,
  Text,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
} from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";
import { CloseIcon, HamburgerIcon } from "@chakra-ui/icons";
import { useTranslation } from "react-i18next";
import LanguageSelector from "./LanguageSelector";

// MODIFICACIÓN: Se agrega la nueva ruta para TEMPO y se traducen los labels.
const NAV = [
  { href: "/", key: "map" },
  { href: "/tempo", key: "tempo" },
  { href: null, key: "pollutants", action: "openModal" }, // Special action for modal
  { href: "/proyecto", key: "about" },
];

export default function Header() {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const {
    isOpen: isModalOpen,
    onOpen: onModalOpen,
    onClose: onModalClose,
  } = useDisclosure();
  const { t } = useTranslation();
  return (
    <Box
      as="header"
      position="sticky"
      top="0"
      zIndex="docked"
      bg="transparent"
      backdropFilter="blur(6px)"
    >
      <Flex
        className="spaceapps-bg"
        px={{ base: 4, md: 8 }}
        py={3}
        align="center"
        borderBottom="1px solid"
        borderColor="rgba(255,255,255,.08)"
      >
        <Text
          as={RouterLink}
          to="/"
          className="text-2xl overpass-bold md:text-3xl"
        >
          {t("header.title")}
        </Text>

        <HStack spacing={6} ml={8} display={{ base: "none", md: "flex" }}>
          {NAV.map((item) =>
            item.action === "openModal" ? (
              <Link
                key={item.key}
                onClick={onModalOpen}
                className="glow-hover"
                _hover={{ color: "space.neonYel" }}
                cursor="pointer"
              >
                {t("nav." + item.key)}
              </Link>
            ) : (
              <Link
                as={RouterLink}
                key={item.key}
                to={item.href}
                className="glow-hover"
                _hover={{ color: "space.neonYel" }}
              >
                {t("nav." + item.key)}
              </Link>
            )
          )}
        </HStack>

        <Flex ml="auto" align="center" gap={3}>
          <LanguageSelector />
          <IconButton
            aria-label={t("header.openMenu")}
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
            {NAV.map((item) =>
              item.action === "openModal" ? (
                <Link
                  key={item.key}
                  onClick={() => {
                    onModalOpen();
                    onClose();
                  }}
                  _hover={{ color: "space.neonYel" }}
                  cursor="pointer"
                >
                  {t("nav." + item.key)}
                </Link>
              ) : (
                <Link
                  as={RouterLink}
                  key={item.key}
                  to={item.href}
                  onClick={onClose}
                  _hover={{ color: "space.neonYel" }}
                >
                  {t("nav." + item.key)}
                </Link>
              )
            )}
          </Stack>
        </Box>
      )}

      <Modal isOpen={isModalOpen} onClose={onModalClose} size="lg" isCentered>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader className="bg-[#07173F] text-2xl overpass-bold rounded-t-md">
            {t("modal.title")}
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody className="bg-[#0042A6] rounded-b-md">
            <Stack spacing={3} fontSize="sm">
              <Text>
                <b>NO₂</b>: {t("modal.no2.description")}
              </Text>
              <Text>
                <b>SO₂</b>: {t("modal.so2.description")}
              </Text>
              <Text>
                <b>O₃</b>: {t("modal.o3.description")}
              </Text>
              <Text>
                <b>HCHO</b>: {t("modal.hcho.description")}
              </Text>
              <Link
                as={RouterLink}
                to="/contaminantes"
                color="space.neonYel"
                onClick={onModalClose}
              >
                {t("modal.readMethodology")}
              </Link>
            </Stack>
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
}
