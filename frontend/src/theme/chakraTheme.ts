import { extendTheme } from "@chakra-ui/react";
import { colors } from "./colors"; // si preferís default, ver nota abajo

const chakraTheme = extendTheme({
  colors: { space: colors }, // ← sin "as any"
  fonts: {
    heading: "'Fira Sans', system-ui, sans-serif",
    body: "'Overpass', system-ui, sans-serif",
    mono: "'Fira Code', ui-monospace, monospace",
  },
  styles: {
    global: {
      "html, body": {
        bg: "space.deepBlue",
        color: "space.white",
        minHeight: "100%",
      },
      a: { color: "space.neonYel", textUnderlineOffset: "3px" },
      "*::selection": { background: "space.neonYel", color: "black" },
      ".spaceapps-bg": {
        background: `linear-gradient(45deg, ${colors.electric} 0%, ${colors.deepBlue} 100%)`,
      },
      ".glow-hover": { transition: "filter .2s ease, transform .2s ease" },
      ".glow-hover:hover": {
        filter: "drop-shadow(0 0 0.6rem rgba(234,254,7,.75))",
        transform: "translateY(-1px)",
      },
    },
  },
  components: {
    Button: {
      baseStyle: { fontWeight: 700, borderRadius: "xl" },
      variants: {
        solid: {
          bg: "space.electric",
          _hover: { bg: "space.neonBlue" },
          _active: { bg: "space.blueYdr" },
        },
        outline: {
          borderColor: "space.neonYel",
          color: "space.white",
          _hover: { bg: "rgba(234,254,7,.1)" },
        },
      },
      defaultProps: { variant: "solid" },
    },
    Heading: { baseStyle: { fontWeight: 900, letterSpacing: "-0.02em" } },
    Card: {
      baseStyle: {
        container: {
          bg: "rgba(7,23,63,.6)",
          border: "1px solid",
          borderColor: "rgba(255,255,255,.08)",
          backdropFilter: "blur(6px)",
          rounded: "2xl",
        },
      },
    },
  },
});

export default chakraTheme; // ← clave
