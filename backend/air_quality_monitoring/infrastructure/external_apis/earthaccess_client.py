# backend/air_quality_monitoring/infrastructure/external_apis/earthaccess_client.py
import os
from pathlib import Path
import time
import shutil
import earthaccess  # asumiendo que ya lo usás
from core.logging import get_logger

log = get_logger("earthaccess_client")

CACHE_DIR = Path(os.getenv("EARTHACCESS_CACHE_DIR", "backend/data/tempo_cache")).resolve()
CACHE_DIR.mkdir(parents=True, exist_ok=True)

MAX_CACHE_GB = float(os.getenv("EARTHACCESS_MAX_CACHE_GB", "2"))  # 2 GB
MAX_FILE_AGE_H = int(os.getenv("EARTHACCESS_MAX_FILE_AGE_H", "6"))  # 6 horas

def _bytes_to_gb(n): return n / (1024**3)

def _cleanup_cache():
    # borra por edad
    now = time.time()
    for p in CACHE_DIR.rglob("*"):
        try:
            if p.is_file():
                age_h = (now - p.stat().st_mtime) / 3600.0
                if age_h > MAX_FILE_AGE_H:
                    p.unlink(missing_ok=True)
        except Exception:
            pass

    # borra por tamaño si excede MAX_CACHE_GB
    total = 0
    files = []
    for p in CACHE_DIR.rglob("*"):
        if p.is_file():
            s = p.stat().st_size
            total += s
            files.append((p, p.stat().st_mtime, s))
    if _bytes_to_gb(total) > MAX_CACHE_GB:
        # ordenar por viejo → nuevo y eliminar hasta bajar el umbral
        files.sort(key=lambda t: t[1])  # mtime asc
        for p, _, sz in files:
            try:
                p.unlink(missing_ok=True)
                total -= sz
                if _bytes_to_gb(total) <= MAX_CACHE_GB:
                    break
            except Exception:
                pass

class EarthaccessClient:
    def __init__(self):
        token = os.getenv("EARTHDATA_TOKEN")
        earthaccess.login(strategy="environment")  # token via ENV
        log.info("earthaccess: autenticado correctamente.")
    
    def search(self, concept_id, temporal, bbox=None, max_items=3):
        return earthaccess.search_data(
            concept_id=concept_id,
            temporal=temporal,
            bounding_box=bbox,
            page_size=max_items,
        )

    def download(self, granules):
        # Descarga SIEMPRE en un solo dir, sin sobreescribir
        files = earthaccess.download(
            granules,
            path=str(CACHE_DIR),
            overwrite=False,   # no duplica
        )

        # A veces earthaccess crea subcarpetas; traete todo a plano
        normalized = []
        for f in files:
            pf = Path(f)
            if pf.is_file() and pf.parent != CACHE_DIR:
                dst = CACHE_DIR / pf.name
                try:
                    if not dst.exists():
                        shutil.move(str(pf), str(dst))
                    # limpiar padre vacío
                    try:
                        if pf.parent.exists() and not any(pf.parent.iterdir()):
                            pf.parent.rmdir()
                    except Exception:
                        pass
                    normalized.append(str(dst))
                except Exception:
                    normalized.append(str(pf))
            else:
                normalized.append(str(pf))

        _cleanup_cache()
        return normalized
