// theme/index.js
import { extendTheme } from "@chakra-ui/react";
import { colors } from "./colors";

export default extendTheme({
  colors,
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
      },
      p: { color: "space.white" }, // cuerpo sobre Deep/Electric/White
      a: { color: "space.neonYel" }, // destacar links con Neon Yellow (uso medido)
    },
  },
  components: {
    Button: {
      baseStyle: { fontWeight: 700 },
      variants: {
        solid: {
          bg: "space.electric",
          _hover: { bg: "space.neonBlue" },
        },
        link: { color: "space.neonYel" },
      },
    },
  },
});
