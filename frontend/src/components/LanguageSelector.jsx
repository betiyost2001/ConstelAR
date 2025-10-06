import React from "react";
import { useTranslation } from "react-i18next";
import { Select, Box } from "@chakra-ui/react";

export default function LanguageSelector() {
  const { i18n, t } = useTranslation();

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
  };

  return (
    <Box>
      <Select
        value={i18n.language}
        onChange={(e) => changeLanguage(e.target.value)}
        size="sm"
        variant="outline"
        bg="transparent"
        borderColor="rgba(255,255,255,.2)"
        color="white"
        _hover={{ borderColor: "space.neonYel" }}
        _focus={{ borderColor: "space.neonYel" }}
        width="120px"
      >
        <option
          value="es"
          style={{ backgroundColor: "#07173F", color: "white" }}
        >
          {t("language.es")}
        </option>
        <option
          value="en"
          style={{ backgroundColor: "#07173F", color: "white" }}
        >
          {t("language.en")}
        </option>
      </Select>
    </Box>
  );
}
