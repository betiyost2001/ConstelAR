"""
Cliente earthaccess (CMR + acceso a datos en la nube)
"""
from dataclasses import dataclass
from typing import List, Tuple, Optional
import earthaccess as ea

from core.config.config import get_settings
from core.logging import get_logger
from utils.exceptions.exceptions import DataSourceError

logger = get_logger("earthaccess_client")


@dataclass
class SearchResult:
    granules: list  # objetos de earthaccess.search_data


class EarthaccessClient:
    def __init__(self, token: Optional[str] = None):
        self.settings = get_settings()
        # No pasamos 'token=' porque earthaccess >=0.9 no lo admite;
        # toma EARTHDATA_TOKEN del entorno con strategy="environment".
        logger.info("earthaccess: intentando login por entorno…")
        try:
            ea.login(strategy="environment")
        except Exception:
            # fallback interactivo/no netrc: que use auto
            ea.login()
        if not getattr(ea.__auth__, "authenticated", False):
            raise DataSourceError("No se pudo autenticar con Earthdata (EARTHDATA_TOKEN).")
        logger.info("earthaccess: autenticado correctamente.")

    def search(
        self,
        concept_id: str,
        temporal: Tuple[str, str],
        bbox: Optional[Tuple[float, float, float, float]] = None,
        max_items: int = 3,
    ) -> SearchResult:
        """
        Busca granules en CMR por collection (concept-id), ventana temporal
        y opcionalmente bbox. Si bbox no trae resultados, reintenta sin bbox.
        """
        start_iso, end_iso = temporal
        logger.info(f"earthaccess.search: coll={concept_id}, time={start_iso}/{end_iso}, bbox={bbox}, max={max_items}")
        try:
            # 1er intento: con bbox (si se pasó)
            if bbox is not None:
                west, south, east, north = bbox
                results = ea.search_data(
                    concept_id=concept_id,
                    temporal=(start_iso, end_iso),
                    bounding_box=(west, south, east, north),
                    count=max_items,
                )
                granules = list(results)
                logger.info(f"earthaccess.search (con bbox) -> {len(granules)}")
                if granules:
                    return SearchResult(granules=granules)

            # Fallback: SIN bbox (muchos productos TEMPO devuelven 0 con bbox)
            results = ea.search_data(
                concept_id=concept_id,
                temporal=(start_iso, end_iso),
                count=max_items,
            )
            granules = list(results)
            logger.info(f"earthaccess.search (sin bbox) -> {len(granules)}")
            return SearchResult(granules=granules)
        except Exception as e:
            raise DataSourceError(f"earthaccess search error: {e}") from e

    def download(self, granules: list) -> List[str]:
        """
        Descarga los archivos; earthaccess retorna paths locales.
        """
        try:
            if not granules:
                return []
            logger.info(f"earthaccess.download: {len(granules)} granules")
            # 'show_progress' en vez de 'quiet'; provider en mayúsculas
            paths = ea.download(granules, provider="LARC_CLOUD", show_progress=False)
            files = [str(p) for p in paths if p is not None]
            logger.info(f"earthaccess.download -> {len(files)} archivos")
            return files
        except Exception as e:
            raise DataSourceError(f"earthaccess download error: {e}") from e
