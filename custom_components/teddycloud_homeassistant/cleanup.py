"""Remove only integration-owned resources when the last box is deleted."""
import asyncio
import logging
from pathlib import Path

from homeassistant.components.lovelace.const import LOVELACE_DATA

from .const import DOMAIN
from .card_registration import CARD_PATH

_LOGGER = logging.getLogger(__name__)


async def async_remove_owned_data(hass, removed_entry_id):
    """Remove our resource and local archive, never unrelated /config/www files."""
    remaining = [
        entry for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.entry_id != removed_entry_id
    ]
    if remaining:
        return

    lovelace = hass.data.get(LOVELACE_DATA)
    resources = getattr(lovelace, "resources", None)
    if resources is not None and getattr(lovelace, "resource_mode", None) == "storage":
        try:
            if not getattr(resources, "loaded", False):
                await resources.async_load()
            for item in list(resources.async_items()):
                if item.get("url", "").split("?")[0] == CARD_PATH:
                    await resources.async_delete_item(item["id"])
        except Exception:
            _LOGGER.exception("Could not remove TeddyCloud Lovelace resource")

    # Delete only the dedicated directory created by our own image archive.
    directory = Path(hass.config.path("www", DOMAIN, "figures"))
    parent = Path(hass.config.path("www", DOMAIN))
    try:
        if directory.is_dir() and not directory.is_symlink():
            for child in directory.iterdir():
                # Only audio-ID named images downloaded by this integration.
                if child.is_file() and not child.is_symlink() and child.stem.isdecimal() and child.suffix in (".png", ".jpg", ".webp"):
                    await asyncio.to_thread(child.unlink)
            await asyncio.to_thread(directory.rmdir)
        # Remove the empty parent folder only. Do not touch extra user files.
        if parent.is_dir() and not parent.is_symlink():
            await asyncio.to_thread(parent.rmdir)
    except OSError:
        _LOGGER.info("TeddyCloud images cleaned up; keeping nonempty or custom directory")
    hass.data.pop("teddycloud_homeassistant_card_registered", None)
