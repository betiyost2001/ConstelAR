// src/theme/muiTheme.ts
import { createTheme } from "@mui/material/styles";
import { colors } from "./colors"; // si "colors" fuera default, usá: import colors from "./colors";

const muiTheme = createTheme({
  palette: {
    mode: "dark",
    primary:   { main: colors.electric },
    secondary: { main: colors.neonBlue },
    error:     { main: colors.rocketRed },
    warning:   { main: colors.neonYel },
    background:{ default: colors.deepBlue, paper: "#0B1C4F" },
    text:      { primary: colors.white },
  },
  typography: {
    fontFamily: "'Overpass', system-ui, sans-serif",
    h1: { fontFamily: "'Fira Sans', system-ui, sans-serif", fontWeight: 900 },
    h2: { fontFamily: "'Fira Sans', system-ui, sans-serif", fontWeight: 900 },
    h3: { fontFamily: "'Fira Sans', system-ui, sans-serif", fontWeight: 900 },
    button: { fontWeight: 700, textTransform: "none" },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          background: `linear-gradient(45deg, ${colors.electric} 0%, ${colors.deepBlue} 100%)`,
          minHeight: "100vh",
        },
        "::selection": { background: colors.neonYel, color: "#000" },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: { borderRadius: 16, fontWeight: 700, boxShadow: "none" },
        containedPrimary: {
          backgroundColor: colors.electric,
          "&:hover": { backgroundColor: colors.neonBlue },
          "&:active": { backgroundColor: colors.blueYdr },
        },
        outlined: {
          borderColor: colors.neonYel,
          color: colors.white,
          "&:hover": { backgroundColor: "rgba(234,254,7,.1)" },
        },
      },
    },
    MuiLink: { styleOverrides: { root: { color: colors.neonYel, textUnderlineOffset: "3px" } } },
    MuiCard: {
      styleOverrides: {
        root: {
          background: "rgba(7,23,63,.6)",
          border: "1px solid rgba(255,255,255,.08)",
          backdropFilter: "blur(6px)",
          borderRadius: 20,
        },
      },
    },
    MuiAppBar: { styleOverrides: { colorPrimary: { background: "transparent", boxShadow: "none" } } },
  },
});

export default muiTheme; // <-- clave
