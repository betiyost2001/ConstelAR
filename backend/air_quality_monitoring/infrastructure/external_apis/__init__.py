class NasaHarmonyClient:
    """
    Cliente Harmony con fallbacks...
    """

    def __init__(self, settings=None):
        # ✅ acepta settings opcional para ser compatible con código que lo pase
        self.settings = settings or get_settings()
        self.root = self.settings.harmony_root.rstrip("/")
        self._headers = {
    "Authorization": f"Bearer {self.settings.earthdata_token}",
    "Client-Id": "argentinaspace-app",  # cualquier identificador estable de tu app
    "User-Agent": "ArgentinaSpace/1.0 (+https://example.org)"  # algo identificable
}
        self.coverages_ids = {
            "no2": getattr(self.settings, "tempo_coverages_no2", None),
            "so2": getattr(self.settings, "tempo_coverages_so2", None),
            "o3":  getattr(self.settings, "tempo_coverages_o3",  None),
            "hcho":getattr(self.settings, "tempo_coverages_hcho",None),
        }
        import httpx
        self.client = httpx.Client(timeout=30, follow_redirects=False)
