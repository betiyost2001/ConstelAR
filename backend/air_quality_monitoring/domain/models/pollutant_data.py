"""
Modelo de dominio para datos de contaminantes
"""
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class PollutantConfig:
    """Configuración de un contaminante"""
    
    name: str
    collection_id: str
    variable_name: str
    description: str
    health_impact: str
    
    def __post_init__(self):
        """Validar configuración"""
        if not self.name:
            raise ValueError("Nombre es requerido")
        if not self.collection_id:
            raise ValueError("Collection ID es requerido")
        if not self.variable_name:
            raise ValueError("Variable name es requerido")


class PollutantType:
    """Tipos de contaminantes soportados"""
    
    NO2 = "no2"
    SO2 = "so2"
    O3 = "o3"
    HCHO = "hcho"
    
    @classmethod
    def get_all_types(cls) -> list[str]:
        """Obtener todos los tipos de contaminantes"""
        return [cls.NO2, cls.SO2, cls.O3, cls.HCHO]
    
    @classmethod
    def is_valid(cls, pollutant_type: str) -> bool:
        """Validar si un tipo de contaminante es válido"""
        return pollutant_type.lower() in cls.get_all_types()
    
    @classmethod
    def get_description(cls, pollutant_type: str) -> str:
        """Obtener descripción de un contaminante"""
        descriptions = {
            cls.NO2: "Dióxido de nitrógeno - indicador de emisiones del transporte y centrales eléctricas",
            cls.SO2: "Dióxido de azufre - proviene de combustibles con azufre y procesos industriales",
            cls.O3: "Ozono troposférico - formado por reacciones fotoquímicas",
            cls.HCHO: "Formaldehído - generado por incendios y procesos industriales"
        }
        return descriptions.get(pollutant_type.lower(), "Contaminante desconocido")
    
    @classmethod
    def get_health_impact(cls, pollutant_type: str) -> str:
        """Obtener impacto en salud de un contaminante"""
        impacts = {
            cls.NO2: "Agrava enfermedades respiratorias",
            cls.SO2: "Causa irritación y lluvia ácida",
            cls.O3: "Afecta pulmones y cultivos",
            cls.HCHO: "Precursor de ozono, irritante"
        }
        return impacts.get(pollutant_type.lower(), "Impacto desconocido")


class PollutantRegistry:
    """Registro de contaminantes con sus configuraciones"""
    
    def __init__(self, configs: Dict[str, Tuple[str, str]]):
        """
        Inicializar registro
        
        Args:
            configs: Diccionario con {pollutant: (collection_id, variable_name)}
        """
        self._configs = {}
        for pollutant, (collection_id, variable_name) in configs.items():
            self._configs[pollutant] = PollutantConfig(
                name=pollutant,
                collection_id=collection_id,
                variable_name=variable_name,
                description=PollutantType.get_description(pollutant),
                health_impact=PollutantType.get_health_impact(pollutant)
            )
    
    def get_config(self, pollutant: str) -> PollutantConfig:
        """Obtener configuración de un contaminante"""
        pollutant_lower = pollutant.lower()
        if pollutant_lower not in self._configs:
            raise ValueError(f"Contaminante desconocido: {pollutant}")
        return self._configs[pollutant_lower]
    
    def get_collection_and_variable(self, pollutant: str) -> Tuple[str, str]:
        """Obtener collection ID y variable name de un contaminante"""
        config = self.get_config(pollutant)
        return config.collection_id, config.variable_name
    
    def get_all_pollutants(self) -> list[str]:
        """Obtener todos los contaminantes disponibles"""
        return list(self._configs.keys())
    
    def is_supported(self, pollutant: str) -> bool:
        """Verificar si un contaminante está soportado"""
        return pollutant.lower() in self._configs
