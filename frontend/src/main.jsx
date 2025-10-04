// src/main.jsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";

// MUI
import { StyledEngineProvider } from "@mui/material/styles";
import { ThemeProvider as MUIThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import muiTheme from "./theme/muiTheme"; // <= usa TU tema (JS)
// si lo tenés .ts, convertí a .js o configura TS

// Chakra
import { ChakraProvider } from "@chakra-ui/react";
import chakraTheme from "./theme/chakraTheme"; // <= usa TU tema (JS)

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    {/* MUI afuera + injectFirst para que su CSS se inyecte primero */}
    <StyledEngineProvider injectFirst>
      <MUIThemeProvider theme={muiTheme}>
        <CssBaseline />
        {/* Chakra adentro: no pisa el theme de MUI */}
        <ChakraProvider theme={chakraTheme}>
          <App />
        </ChakraProvider>
      </MUIThemeProvider>
    </StyledEngineProvider>
  </React.StrictMode>
);
