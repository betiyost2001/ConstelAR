"""
Cliente HTTP para NASA Harmony (OGC Coverages + cookie session)
"""
from typing import List, Tuple, Optional

import httpx

from core.config.config import get_settings
from core.logging import get_logger
from utils.exceptions.exceptions import DataSourceError

logger = get_logger("nasa_harmony_client")


class NasaHarmonyClient:
    """
    Cliente Harmony con fallbacks:
      - OGC API Coverages v1.0.0 con collection_id (concept-id tipo C29...-LARC_CLOUD)
      - Fallback a short-name (si se configura en settings como tempo_coverages_*)

    AUTENTICACIÓN:
      - Intercambia el EARTHDATA_TOKEN (Bearer) por una cookie de sesión llamando a /oauth2/token
      - Reutiliza la cookie en el mismo Client para las siguientes requests
    """

    def __init__(self, settings=None):
        # acepta settings opcional para compatibilidad
        self.settings = settings or get_settings()
        self.root = (self.settings.harmony_root or "https://harmony.earthdata.nasa.gov").rstrip("/")
        self._bearer = self.settings.earthdata_token or ""
        if not self._bearer:
            raise DataSourceError("EARTHDATA_TOKEN no configurado en el entorno.")

        # headers base (Client-Id y UA ayudan a identificar la app)
        self._base_headers = {
            "Client-Id": "argentinaspace-app",
            "User-Agent": "ArgentinaSpace/1.0 (+https://example.org)",
        }
        # guardamos Authorization por si Harmony lo acepta además de la cookie
        self._auth_headers = {**self._base_headers, "Authorization": f"Bearer {self._bearer}"}

        # short-names opcionales
        self.coverages_ids = {
            "no2": getattr(self.settings, "tempo_coverages_no2", None),
            "so2": getattr(self.settings, "tempo_coverages_so2", None),
            "o3": getattr(self.settings, "tempo_coverages_o3", None),
            "hcho": getattr(self.settings, "tempo_coverages_hcho", None),
        }

        # Cliente httpx con cookies persistentes; NO seguir redirects (queremos ver 303)
        self.client = httpx.Client(timeout=30, follow_redirects=False)
        self._has_session_cookie = False

    # ────────────────────────── Auth helpers ──────────────────────────

    def _ensure_cookie_session(self):
        """Llama una vez a /oauth2/token con el Bearer para obtener cookie de sesión (204 esperado)."""
        if self._has_session_cookie:
            return
        url = f"{self.root}/oauth2/token"
        logger.info("Intercambiando Bearer por cookie en %s", url)
        r = self.client.get(url, headers=self._auth_headers)
        # Respuestas esperadas: 204 No Content (cookie seteada)
        if r.status_code == 204:
            self._has_session_cookie = True
            logger.info("Cookie de sesión establecida correctamente.")
            return
        # 200 con algo, o 303 -> igualmente Harmony puede dejar cookie; probamos
        if "set-cookie" in (k.lower() for k in r.headers.keys()):
            self._has_session_cookie = True
            logger.info("Cookie de sesión establecida (vía set-cookie).")
            return
        raise DataSourceError(f"Harmony /oauth2/token devolvió {r.status_code}: {r.text[:200]}")

    # ────────────────────────── URL builders ──────────────────────────

    def _build_coverages_url(self, collection_key: str) -> str:
        # variables vía rangeSubset en params (no la usamos por ahora)
        return f"{self.root}/ogc-api-coverages/1.0.0/collections/{collection_key}/coverage/rangeset"

    def _build_coverages_var_url(self, collection_key: str, variable: str) -> str:
        # variable en el path
        return f"{self.root}/ogc-api-coverages/1.0.0/collections/{collection_key}/coverage/rangeset/variables/{variable}"

    # ────────────────────────── Core request ──────────────────────────

    def _get(self, url: str, params: List[Tuple[str, str]]):
        # Asegurar cookie antes del primer GET real
        self._ensure_cookie_session()

        # Intento 1: con cookie + headers base (sin Authorization ya no debería ser necesario)
        logger.debug(f"Making request to: {url}")
        r = self.client.get(url, params=params, headers=self._base_headers)
        # Si aún así reenvía a URS (303), probamos una vez con Authorization también
        if r.status_code == 303 or r.status_code == 401 or r.status_code == 403:
            logger.info("Reintentando con Authorization Bearer por respuesta %s", r.status_code)
            r = self.client.get(url, params=params, headers=self._auth_headers)
        return r

    def _collection_keys_for(self, parameter: Optional[str], collection_id: str):
        keys = [collection_id]
        cov = self.coverages_ids.get((parameter or "").lower(), None)
        if cov and cov not in keys:
            keys.append(cov)
        return keys

    def _try_coverages(self, urls: List[str], params: List[Tuple[str, str]]):
        last_text, last_status = "", None
        for url in urls:
            r = self._get(url, params)
            logger.info(f"Coverages GET {url} -> {r.status_code}")
            if r.status_code == 200:
                return r
            last_status, last_text = r.status_code, r.text[:400]
            if r.status_code in (401, 403):
                raise DataSourceError(f"Harmony auth {r.status_code}: {last_text}")
            if r.status_code == 303:
                # todavía pidiendo OAuth interactivo → cookie no válida / token inválido
                raise DataSourceError(f"Harmony 303: requiere autorización interactiva. {last_text}")
        raise DataSourceError(f"Harmony error {last_status}: {last_text}")

    # ────────────────────────── API GEOJSON ──────────────────────────

    def get_geojson_data(
        self,
        collection_id: str,
        params: List[Tuple[str, str]],
        parameter: Optional[str] = None,
        variable: Optional[str] = None,
    ) -> dict:
        # variable en el path si está
        keys = self._collection_keys_for(parameter, collection_id)
        urls = (
            [self._build_coverages_var_url(k, variable) for k in keys]
            if variable else
            [self._build_coverages_url(k) for k in keys]
        )
        r = self._try_coverages(urls, params)
        try:
            return r.json()
        except Exception as e:
            raise DataSourceError(f"Harmony JSON parse error: {e}")

    # ────────────────────────── API NetCDF ──────────────────────────

    def get_netcdf_data(
        self,
        collection_id: str,
        params: List[Tuple[str, str]],
        parameter: Optional[str] = None,
        variable: Optional[str] = None,
    ) -> bytes:
        keys = self._collection_keys_for(parameter, collection_id)
        urls = (
            [self._build_coverages_var_url(k, variable) for k in keys]
            if variable else
            [self._build_coverages_url(k) for k in keys]
        )
        r = self._try_coverages(urls, params)
        return r.content if r.status_code == 200 else b""
