"""
Cliente para NASA Harmony API
"""
import requests
from typing import Dict, Any, List, Tuple, Union, Optional
from backend.core.config.config import Settings
from backend.core.logging import get_logger
from backend.utils.exceptions.exceptions import NasaHarmonyError, AuthenticationError, DataSourceError


class NasaHarmonyClient:
    """Cliente para interactuar con NASA Harmony API"""
    
    def __init__(self, settings: Settings):
        """
        Inicializar cliente
        
        Args:
            settings: Configuración de la aplicación
        """
        self.settings = settings
        self.logger = get_logger("nasa_harmony_client")
        self.base_url = settings.harmony_root
        self.token = settings.earthdata_token
        
        if not self.token:
            self.logger.warning("EARTHDATA_TOKEN no configurado - algunas funcionalidades pueden estar limitadas")
    
    def _get_headers_json(self) -> Dict[str, str]:
        """Obtener headers para requests JSON"""
        headers = {"Accept": "application/geo+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def _get_headers_netcdf(self) -> Dict[str, str]:
        """Obtener headers para requests NetCDF"""
        headers = {"Accept": "application/x-netcdf"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def _make_request(self, url: str, params: Union[Dict[str, Any], List[Tuple[str, Any]]], 
                     headers: Dict[str, str], timeout: int = 90) -> requests.Response:
        """
        Realizar request HTTP con manejo de errores
        
        Args:
            url: URL del request
            params: Parámetros del request
            headers: Headers del request
            timeout: Timeout en segundos
        
        Returns:
            Response del request
        
        Raises:
            NasaHarmonyError: Error en la comunicación con NASA Harmony
            AuthenticationError: Error de autenticación
        """
        try:
            self.logger.debug(f"Making request to: {url}")
            response = requests.get(url, params=params, headers=headers, timeout=timeout)
            
            if response.status_code in (401, 403):
                raise AuthenticationError("Earthdata token/credenciales inválidas o faltantes")
            
            if response.status_code >= 400:
                error_detail = {
                    "status": response.status_code,
                    "url": response.request.url if response.request else url,
                    "body": response.text[:4000]
                }
                raise NasaHarmonyError(
                    f"Harmony API error: {response.status_code}",
                    status_code=response.status_code,
                    url=url,
                    response_body=response.text
                )
            
            return response
            
        except requests.RequestException as e:
            self.logger.error(f"Request error: {e}")
            raise NasaHarmonyError(f"Harmony connection error: {e}") from e
    
    def get_geojson_data(self, collection_id: str, params: List[Tuple[str, Any]]) -> Dict[str, Any]:
        """
        Obtener datos en formato GeoJSON
        
        Args:
            collection_id: ID de la colección TEMPO
            params: Parámetros del request
        
        Returns:
            Datos en formato GeoJSON
        
        Raises:
            NasaHarmonyError: Error en la comunicación
            AuthenticationError: Error de autenticación
        """
        url = f"{self.base_url}/ogc-api-coverages/collections/{collection_id}/coverage/rangeset"
        headers = self._get_headers_json()
        
        response = self._make_request(url, params, headers)
        
        try:
            return response.json()
        except ValueError:
            self.logger.warning("Invalid JSON response, returning empty feature collection")
            return {"type": "FeatureCollection", "features": []}
    
    def get_netcdf_data(self, collection_id: str, params: List[Tuple[str, Any]]) -> bytes:
        """
        Obtener datos en formato NetCDF
        
        Args:
            collection_id: ID de la colección TEMPO
            params: Parámetros del request
        
        Returns:
            Datos en formato NetCDF como bytes
        
        Raises:
            NasaHarmonyError: Error en la comunicación
            AuthenticationError: Error de autenticación
        """
        url = f"{self.base_url}/ogc-api-coverages/collections/{collection_id}/coverage/rangeset"
        headers = self._get_headers_netcdf()
        
        response = self._make_request(url, params, headers, timeout=180)
        return response.content or b""
    
    def get_geojson_data_alternative_path(self, collection_id: str, variable_name: str, 
                                        params: List[Tuple[str, Any]]) -> Dict[str, Any]:
        """
        Obtener datos GeoJSON usando ruta alternativa (variable en el path)
        
        Args:
            collection_id: ID de la colección TEMPO
            variable_name: Nombre de la variable
            params: Parámetros del request
        
        Returns:
            Datos en formato GeoJSON
        """
        url = f"{self.base_url}/{collection_id}/ogc-api-coverages/1.0.0/{variable_name}/coverage/rangeset"
        headers = self._get_headers_json()
        
        response = self._make_request(url, params, headers)
        
        try:
            return response.json()
        except ValueError:
            self.logger.warning("Invalid JSON response, returning empty feature collection")
            return {"type": "FeatureCollection", "features": []}
    
    def get_netcdf_data_alternative_path(self, collection_id: str, variable_name: str, 
                                       params: List[Tuple[str, Any]]) -> bytes:
        """
        Obtener datos NetCDF usando ruta alternativa
        
        Args:
            collection_id: ID de la colección TEMPO
            variable_name: Nombre de la variable
            params: Parámetros del request
        
        Returns:
            Datos en formato NetCDF como bytes
        """
        url = f"{self.base_url}/{collection_id}/ogc-api-coverages/1.0.0/{variable_name}/coverage/rangeset"
        headers = self._get_headers_netcdf()
        
        response = self._make_request(url, params, headers, timeout=180)
        return response.content or b""
    
    def health_check(self) -> bool:
        """
        Verificar salud del servicio NASA Harmony
        
        Returns:
            True si el servicio está disponible
        """
        try:
            # Intentar hacer un request simple
            url = f"{self.base_url}/ogc-api-coverages/collections"
            headers = self._get_headers_json()
            response = requests.get(url, headers=headers, timeout=10)
            return response.status_code < 500
        except Exception:
            return False
