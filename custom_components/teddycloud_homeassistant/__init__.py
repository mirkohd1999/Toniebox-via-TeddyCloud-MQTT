"""Local MQTT listener for TeddyCloud box status."""
from homeassistant.core import callback
from homeassistant.components import mqtt
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, CONF_PREFIX, CONF_BOX_ID
from .online_catalog import OnlineCatalog
from .card_registration import async_register_card
from .cleanup import async_remove_owned_data

FIELDS = {"Playback", "ContentTitle", "ContentAudioId", "VolumeLevel", "VolumedB", "Charger", "TagValid", "LastSeen", "ContentPicture"}

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if not await mqtt.async_wait_for_mqtt_client(hass):
        return False
    await async_register_card(hass)
    from .media_player import BoxPlayer
    catalog = hass.data.setdefault(DOMAIN, {}).setdefault("online_catalog", OnlineCatalog(hass))
    player = BoxPlayer(entry, catalog)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = player
    prefix = entry.data[CONF_PREFIX].strip('/')
    box = entry.data[CONF_BOX_ID].strip('/')
    topic = f"{prefix}/box/{box}/+"

    @callback
    def incoming(message):
        field = message.topic.rsplit('/', 1)[-1]
        if field in FIELDS:
            player.receive(field, message.payload)

    await hass.config_entries.async_forward_entry_setups(entry, ["media_player", "number", "sensor"])
    try:
        unsubscribe = await mqtt.async_subscribe(hass, topic, incoming, 0)
    except Exception:
        await hass.config_entries.async_unload_platforms(entry, ["media_player", "number", "sensor"])
        hass.data[DOMAIN].pop(entry.entry_id, None)
        raise
    hass.data[DOMAIN][f"{entry.entry_id}_unsubscribe"] = unsubscribe
    entry.async_on_unload(entry.add_update_listener(_update_options))
    return True

async def _update_options(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass, entry):
    unsubscribe = hass.data[DOMAIN].pop(f"{entry.entry_id}_unsubscribe", None)
    if unsubscribe:
        unsubscribe()
    unloaded = await hass.config_entries.async_unload_platforms(entry, ["media_player", "number", "sensor"])
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove integration-owned data when a configuration entry is deleted."""
    await async_remove_owned_data(hass, entry.entry_id)
