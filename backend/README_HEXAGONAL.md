# 🏗️ ConstelAR Backend - Arquitectura Hexagonal

## 📋 Resumen

El backend de **ConstelAR** ha sido refactorizado para implementar una **arquitectura hexagonal** (Ports and Adapters), proporcionando una base sólida, mantenible y escalable para el monitoreo de calidad del aire con datos NASA TEMPO.

## 🎯 Arquitectura Implementada

### **Separación de Capas**

```
📁 core/                           # 🎯 CAPA CORE (Compartida)
├── config/                        # Configuración global
├── security/                      # Middleware y dependencias
└── logging.py                     # Sistema de logging

📁 air_quality_monitoring/         # 🔥 CONTEXTO PRINCIPAL
├── api/v1/                        # API Layer
│   ├── controllers/               # Controladores HTTP
│   ├── dtos/                      # Data Transfer Objects
│   └── mappers/                   # Mappers DTO ↔ Domain
├── domain/                        # Domain Layer
│   ├── models/                    # Modelos de dominio
│   └── services/                  # Servicios de negocio
└── infrastructure/                # Infrastructure Layer
    ├── repositories/              # Repositorios de datos
    ├── entities/                  # Entidades de infraestructura
    └── external_apis/             # Clientes de APIs externas

📁 utils/                          # 🛠️ UTILIDADES COMPARTIDAS
├── exceptions/                    # Excepciones personalizadas
└── helpers/                       # Utilidades comunes
```

## 🚀 Características Implementadas

### **✅ Arquitectura Hexagonal Completa**
- **Separación clara** de responsabilidades
- **Inyección de dependencias** con FastAPI
- **Interfaces bien definidas** entre capas
- **Testabilidad** mejorada

### **✅ FastAPI con Swagger**
- **Documentación automática** en `/docs`
- **Validación de datos** con Pydantic
- **Respuestas tipadas** y estructuradas
- **Manejo de errores** centralizado

### **✅ Funcionalidad Completa**
- **Endpoint principal**: `/api/v1/tempo/normalized`
- **Contaminantes soportados**: NO₂, SO₂, O₃, HCHO
- **Múltiples formatos**: GeoJSON y NetCDF
- **Muestreo inteligente** para optimizar rendimiento

### **✅ Mejoras Técnicas**
- **Logging centralizado** con niveles configurables
- **Configuración por variables** de entorno
- **Manejo robusto de errores** con excepciones personalizadas
- **CORS configurado** para desarrollo

## 📚 Endpoints Disponibles

### **🌍 Datos de Calidad del Aire**
- `GET /api/v1/tempo/normalized` - Mediciones normalizadas
- `GET /api/v1/tempo/pollutants/supported` - Contaminantes soportados
- `GET /api/v1/tempo/pollutants/{parameter}/info` - Info de contaminante
- `GET /api/v1/tempo/health` - Health check del servicio

### **🔧 Sistema**
- `GET /` - Health check principal
- `GET /info` - Información de la API
- `GET /docs` - Documentación Swagger
- `GET /redoc` - Documentación ReDoc

## 🛠️ Instalación y Uso

### **1. Instalar Dependencias**
```bash
pip install -r requirements.txt
```

### **2. Configurar Variables de Entorno**
```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Configurar token NASA (opcional pero recomendado)
export EARTHDATA_TOKEN="your_nasa_token_here"
```

### **3. Ejecutar la Aplicación**
```bash
# Desarrollo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Producción
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### **4. Acceder a la Documentación**
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 Configuración

### **Variables de Entorno Principales**
```bash
# Aplicación
APP_NAME="ArgentinaSpace API"
DEBUG=false
LOG_LEVEL="INFO"

# NASA TEMPO
HARMONY_ROOT="https://harmony.earthdata.nasa.gov"
EARTHDATA_TOKEN="your_token_here"

# CORS
CORS_ORIGINS=["http://localhost:5173","http://localhost:8080"]
```

## 📊 Ejemplo de Uso

### **Obtener Mediciones de NO₂**
```bash
curl "http://localhost:8000/api/v1/tempo/normalized?parameter=no2&lat=-34.6&lon=-58.4&limit=10"
```

### **Respuesta**
```json
{
  "source": "nasa-tempo",
  "results": [
    [-34.6, -58.4, "no2", 15.5, "mol/m^2", "2024-01-01T12:00:00Z"]
  ]
}
```

## 🧪 Testing

### **Health Check**
```bash
curl http://localhost:8000/
```

### **Información de la API**
```bash
curl http://localhost:8000/info
```

### **Contaminantes Soportados**
```bash
curl http://localhost:8000/api/v1/tempo/pollutants/supported
```

## 🔄 Migración desde Versión Anterior

### **Archivos Preservados**
- `app/main_original.py` - Aplicación original respaldada
- `app/api/tempo.py` - Código original preservado

### **Nueva Estructura**
- **Misma funcionalidad** con mejor arquitectura
- **Endpoints compatibles** con la versión anterior
- **Mejor documentación** y manejo de errores

## 🎯 Beneficios de la Nueva Arquitectura

### **✅ Mantenibilidad**
- Código organizado por contexto de negocio
- Separación clara de responsabilidades
- Fácil localización de funcionalidades

### **✅ Escalabilidad**
- Nuevos contextos se agregan sin afectar existentes
- Cada contexto puede evolucionar independientemente
- Reutilización de componentes core

### **✅ Testabilidad**
- Cada capa se puede testear independientemente
- Mocking fácil de dependencias
- Tests unitarios y de integración claros

### **✅ Flexibilidad**
- Cambio de fuente de datos sin afectar lógica de negocio
- Cambio de framework web sin afectar dominio
- Integración con diferentes sistemas externos

## 🚀 Próximos Pasos

1. **Testing**: Implementar tests unitarios y de integración
2. **Monitoreo**: Agregar métricas y alertas
3. **Cache**: Implementar cache para optimizar rendimiento
4. **Nuevos Contaminantes**: Agregar más tipos de contaminantes
5. **Datos Históricos**: Implementar análisis temporal

## 👥 Equipo ConstelAR

Desarrollado por el equipo argentino **ConstelAR** para el **NASA Space Apps Challenge 2025**.

- **Betina Yost** – Frontend & Coordinación
- **Agustina Fiorella Silva** – Backend & APIs
- **Kevin Agustín Ruiz** – Full Stack
- **Ludmila Gandur** – Investigación
- **Trinidad Bernardez** – Comunicación
- **Eduardo Alejandro Ponce Cobos** – Arquitectura & Backend

---

**🌌 ConstelAR - Monitoreo Ambiental Espacial para Argentina** 🚀
