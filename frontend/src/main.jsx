// src/main.jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'

// MUI
import { ThemeProvider as MUIThemeProvider, createTheme, StyledEngineProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'

// Chakra
import { ChakraProvider, extendTheme } from '@chakra-ui/react'

const muiTheme = createTheme()
const chakraTheme = extendTheme({})

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {/* Chakra afuera para que no pise el theme de MUI */}
    <ChakraProvider theme={chakraTheme}>
      {/* injectFirst: que los estilos de MUI se inyecten primero y no haya conflictos */}
      <StyledEngineProvider injectFirst>
        <MUIThemeProvider theme={muiTheme}>
          <CssBaseline />
          <App />
        </MUIThemeProvider>
      </StyledEngineProvider>
    </ChakraProvider>
  </React.StrictMode>
)
