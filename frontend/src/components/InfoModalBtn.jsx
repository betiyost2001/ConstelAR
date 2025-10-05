import React from "react";
import { Link as RouterLink } from "react-router-dom";
import {
  Link,
  Stack,
  useDisclosure,
  Text,
  Button,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
} from "@chakra-ui/react";

export default function InfoModalBtn() {
  const { isOpen, onOpen, onClose } = useDisclosure();
  return (
    <>
      <Button size="sm" variant="outline" onClick={onOpen}>
        ¿Qué mide cada contaminante?
      </Button>
      <Modal isOpen={isOpen} onClose={onClose} size="lg" isCentered>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader className="bg-[#07173F] text-2xl fira-sans-bold rounded-t-md">
            Contaminantes y por qué importan
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody className="bg-[#0042A6] rounded-b-md">
            <Stack spacing={3} fontSize="sm">
              <Text>
                <b>NO₂</b>: indicador de emisiones del transporte y centrales
                eléctricas; agrava enfermedades respiratorias.
              </Text>
              <Text>
                <b>SO₂</b>: proviene de combustibles con azufre y procesos
                industriales; causa irritación y lluvia ácida.
              </Text>
              <Text>
                <b>O₃</b>: ozono troposférico formado por reacciones
                fotoquímicas; afecta pulmones y cultivos.
              </Text>
              <Text>
                <b>HCHO</b>: formaldehído generado por incendios y procesos
                industriales; precursor de ozono.
              </Text>
              <Link as={RouterLink} to="/contaminantes" color="space.neonYel" onClick={onClose}>
                Leer metodología
              </Link>
            </Stack>
          </ModalBody>
        </ModalContent>
      </Modal>
    </>
  );
}
