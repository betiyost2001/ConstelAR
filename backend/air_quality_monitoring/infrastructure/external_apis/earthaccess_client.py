import os
from pathlib import Path
import time
import shutil
import earthaccess
from typing import Any, Dict

# -------------------------------------------------------------------
# ⬇️ TUS IMPORTACIONES REALES ⬇️
from core.logging import get_logger 
from core.config.config import get_settings, Settings 
# -------------------------------------------------------------------

log = get_logger("earthaccess_client")

# Usar la variable de entorno EARTHACCESS_CACHE definida en docker-compose
CACHE_DIR = Path(os.getenv("EARTHACCESS_CACHE", "/tmp/tempo-cache")).resolve()
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Variables de limpieza de caché (usa los valores de tu .env)
MAX_CACHE_GB = float(os.getenv("EARTHACCESS_MAX_CACHE_GB", "2"))
MAX_FILE_AGE_H = int(os.getenv("EARTHACCESS_MAX_FILE_AGE_H", "6"))
def _bytes_to_gb(n): return n / (1024**3)

def _cleanup_cache():
    now = time.time()
    # Limpieza por edad
    for p in CACHE_DIR.rglob("*"):
        try:
            if p.is_file():
                age_h = (now - p.stat().st_mtime) / 3600.0
                if age_h > MAX_FILE_AGE_H:
                    p.unlink(missing_ok=True)
        except Exception:
            pass

    # Limpieza por tamaño total
    total = 0
    files = []
    for p in CACHE_DIR.rglob("*"):
        if p.is_file():
            s = p.stat().st_size
            total += s
            files.append((p, p.stat().st_mtime, s))
            
    if _bytes_to_gb(total) > MAX_CACHE_GB:
        log.info(f"Cache size exceeded ({_bytes_to_gb(total):.2f} GB > {MAX_CACHE_GB} GB). Cleaning up.")
        files.sort(key=lambda t: t[1]) 
        for p, _, sz in files:
            try:
                p.unlink(missing_ok=True)
                total -= sz
                if _bytes_to_gb(total) <= MAX_CACHE_GB:
                    break
            except Exception:
                pass
        log.info(f"Cache cleaned. Remaining size: {_bytes_to_gb(total):.2f} GB")


class EarthaccessClient:
    """Cliente wrapper para la librería earthaccess."""

    def __init__(self, settings: Settings | None = None):
        self.settings: Settings = settings or get_settings()
        self.cache_dir = CACHE_DIR
        
        # 🔐 Login con token si está disponible
        token = self.settings.earthdata_token
        if token:
            try:
                earthaccess.login(strategy="environment", token=token)
                log.info("Earthaccess login exitoso con token de entorno.")
            except Exception as e:
                 log.error(f"Earthaccess login falló con token: {e}", exc_info=True)
                 earthaccess.login() 
        else:
            log.warning("EARTHDATA_TOKEN no encontrado en settings. Intentando login automático.")
            earthaccess.login()
            
    # -------------------------------------------------------------------
    # 🎯 FUNCIÓN CORREGIDA (SOLUCIONA EL ERROR DE INDENTACIÓN Y EL DE "limit")
    # -------------------------------------------------------------------

    def search(self, **kwargs) -> Any:
        
        search_kwargs: Dict[str, Any] = kwargs.copy()
        
        # 1. Limpieza de claves problemáticas por si acaso.
        if 'limit' in search_kwargs:
            search_kwargs.pop('limit') 
        if 'max_items' in search_kwargs:
            search_kwargs.pop('max_items')
        if 'page_size' in search_kwargs:
            search_kwargs.pop('page_size')
        return earthaccess.search_data(**search_kwargs)

    # -------------------------------------------------------------------
    # ⬇️ FUNCIÓN DOWNLOAD CORREGIDA (SOLO LA INDENTACIÓN) ⬇️
    # -------------------------------------------------------------------

    def download(self, granules):
        files = earthaccess.download(
            granules,
            local_path=str(CACHE_DIR),
            overwrite=False,
        )

        normalized = []
        for f in files:
            pf = Path(f)
            if pf.is_file() and pf.parent != CACHE_DIR:
                dst = CACHE_DIR / pf.name
                try:
                    if not dst.exists():
                        shutil.move(str(pf), str(dst))
                    normalized.append(str(dst))
                    try:
                        if pf.parent.exists() and not any(pf.parent.iterdir()):
                            pf.parent.rmdir()
                    except Exception:
                        pass
                except Exception:
                    normalized.append(str(pf))
            else:
                normalized.append(str(pf))

        _cleanup_cache()
        return normalized