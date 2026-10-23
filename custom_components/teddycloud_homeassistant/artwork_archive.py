"""Small persistent artwork archive for recognized Tonies.

Files remain on Home Assistant's local disk after a restart and are served from
/local/. No bulk redistribution of third-party artwork.
"""
import asyncio
import logging
from pathlib import Path
from urllib.parse import urlsplit

from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)
MAX_IMAGE_BYTES = 3 * 1024 * 1024
ALLOWED_TYPES = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}


class ArtworkArchive:
    def __init__(self, hass):
        self.hass = hass
        self.path = Path(hass.config.path("www", "teddycloud_homeassistant", "figures"))
        self._tasks = {}

    def lookup(self, audio_id):
        """Return local artwork URL if the ID has a cached image."""
        key = str(audio_id or "").strip()
        if not key.isdecimal():
            return None
        for extension in ALLOWED_TYPES.values():
            if (self.path / f"{key}{extension}").is_file():
                return f"/local/teddycloud_homeassistant/figures/{key}{extension}"
        return None

    async def store(self, audio_id, url):
        """Cache an image by exact audio ID. Never replace an existing image."""
        key = str(audio_id or "").strip()
        if not key.isdecimal() or not isinstance(url, str):
            return None
        if self.lookup(key):
            return self.lookup(key)
        parts = urlsplit(url)
        if parts.scheme != "https" or not parts.hostname:
            return None
        # Avoid parallel duplicate downloads for multiple boxes.
        if key in self._tasks:
            return await self._tasks[key]
        task = self.hass.async_create_task(self._download(key, url))
        self._tasks[key] = task
        try:
            return await task
        finally:
            if self._tasks.get(key) is task:
                self._tasks.pop(key, None)

    async def _download(self, key, url):
        try:
            session = async_get_clientsession(self.hass)
            async with asyncio.timeout(15):
                async with session.get(url, allow_redirects=False) as resp:
                    if resp.status != 200:
                        return None
                    media_type = resp.headers.get("Content-Type", "").split(";")[0].lower().strip()
                    ext = ALLOWED_TYPES.get(media_type)
                    if not ext or (resp.content_length and resp.content_length > MAX_IMAGE_BYTES):
                        return None
                    data = await resp.content.read(MAX_IMAGE_BYTES + 1)
                    if len(data) > MAX_IMAGE_BYTES:
                        return None
            if not data:
                return None
            await asyncio.to_thread(self._write, key, ext, data)
            return self.lookup(key)
        except Exception as err:
            _LOGGER.debug("Tonie artwork cache unavailable for audio ID %s: %s", key, err)
            return None

    def _write(self, key, ext, data):
        self.path.mkdir(parents=True, exist_ok=True)
        target = self.path / f"{key}{ext}"
        if not target.exists():
            target.write_bytes(data)
