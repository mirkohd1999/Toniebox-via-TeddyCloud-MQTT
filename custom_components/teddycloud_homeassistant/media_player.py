"""TeddyCloud MQTT media player (read only)."""
import json
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit
from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerEntityFeature, MediaPlayerState
from homeassistant.helpers.entity import DeviceInfo
from .artwork_archive import ArtworkArchive
from .const import (DOMAIN, CONF_BOX_NAME, CONF_BOX_COLOR, CONF_CATALOG, CONF_FALLBACK_COVER, DEFAULT_COLOR)


def mqtt_text(payload):
    """HA versions and MQTT callbacks may deliver bytes or text."""
    if isinstance(payload, (bytes, bytearray, memoryview)):
        return bytes(payload).decode('utf-8', errors='replace').strip()
    return str(payload).strip()


def resolved_picture(value, server_url):
    """Replace TeddyCloud's container-local `localhost` with a LAN-reachable host."""
    value = mqtt_text(value) if value is not None else ''
    if not value:
        return None
    try:
        original = urlsplit(value)
        if original.scheme not in ('http', 'https'):
            return value if value.startswith('/local/') else None
        if original.hostname not in ('localhost', '127.0.0.1', '::1'):
            return value
        host = urlsplit(server_url.strip().rstrip('/'))
        if host.scheme not in ('http', 'https') or not host.netloc:
            return None
        return urlunsplit((host.scheme, host.netloc, original.path, original.query, ''))
    except ValueError:
        return None


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([hass.data[DOMAIN][entry.entry_id]])


class BoxPlayer(MediaPlayerEntity):
    _attr_should_poll = False
    _attr_supported_features = MediaPlayerEntityFeature(0)

    def __init__(self, entry, online_catalog):
        self.entry = entry
        self._online_catalog = online_catalog
        self._archive = None
        self._local_artwork = None
        self._online_result = None
        self._online_audio_id = None
        self._lookup_task = None
        self._attr_unique_id = f'{entry.entry_id}_player'
        self._attr_name = f'{entry.data[CONF_BOX_NAME]} Now Playing'
        self._values = {}
        self._started = None
        self._was_playing = False
        self._figure_present = None
        self._figure_removed_at = None

    @property
    def device_info(self):
        return DeviceInfo(identifiers={(DOMAIN, self.entry.unique_id)}, name=self.entry.data[CONF_BOX_NAME], manufacturer='TeddyCloud', model='MQTT box monitor')

    def receive(self, field, payload):
        """Accept asynchronous MQTT metadata without mixing two figurines."""
        text = mqtt_text(payload)
        previous = self._values.get(field)
        if field == 'TagValid':
            if text.startswith('-'):
                self._set_figure_removed()
            elif text:
                # A repeated TagValid is not another figure change.
                # Keep metadata already delivered before the tag event.
                self._figure_present = True
                self._figure_removed_at = None
        elif field == 'TagInvalid' and text.startswith('-'):
            self._set_figure_removed()
        elif field == 'ContentAudioId':
            if text and text != previous:
                # Keep title/picture that may have arrived before the audio ID.
                self._online_result = None
                self._local_artwork = self._archive.lookup(text) if self._archive else None
                self._online_audio_id = text
                if self._lookup_task and not self._lookup_task.done():
                    self._lookup_task.cancel()
                if self.entry.options.get('online_images', True) and self.hass is not None:
                    self._lookup_task = self.hass.async_create_task(self._lookup_image(text))
                if self._was_playing:
                    self._started = datetime.now(timezone.utc)
            elif not text and previous:
                self._set_figure_removed()
            if text:
                self._figure_present = True
                self._figure_removed_at = None
        elif field in ('ContentTitle', 'ContentPicture') and text:
            self._figure_present = True
            self._figure_removed_at = None

        # When a new audio ID arrives without an intervening removal event,
        # never preserve artwork belonging to the previous ID.
        self._values[field] = text
        if field == 'Playback':
            playing = text.upper() in ('ON', '1', 'TRUE', 'PLAYING')
            if playing and not self._was_playing:
                self._started = datetime.now(timezone.utc)
            if not playing:
                self._started = None
            self._was_playing = playing
        if self.hass is not None:
            self.async_write_ha_state()

    def _clear_content(self):
        self._values['ContentAudioId'] = ''
        self._values['ContentTitle'] = ''
        self._values['ContentPicture'] = ''
        self._online_audio_id = None
        self._online_result = None
        self._local_artwork = None
        if self._lookup_task and not self._lookup_task.done():
            self._lookup_task.cancel()

    def _set_figure_removed(self):
        self._clear_content()
        self._figure_present = False
        self._figure_removed_at = datetime.now(timezone.utc)
        self._started = None

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self._archive = self.hass.data.setdefault(DOMAIN, {}).setdefault('artwork_archive', ArtworkArchive(self.hass))
        audio_id = self._values.get('ContentAudioId')
        if audio_id and self.entry.options.get('online_images', True):
            self._online_audio_id = audio_id
            if not self._lookup_task or self._lookup_task.done():
                self._lookup_task = self.hass.async_create_task(self._lookup_image(audio_id))

    async def async_will_remove_from_hass(self):
        """Stop pending catalog requests when the entity is unloaded."""
        if self._lookup_task and not self._lookup_task.done():
            self._lookup_task.cancel()
        await super().async_will_remove_from_hass()

    async def _lookup_image(self, audio_id):
        """Refresh artwork asynchronously without blocking the MQTT callback."""
        try:
            result = await self._online_catalog.find(audio_id)
        except Exception:
            return
        cached = self._archive.lookup(audio_id) if self._archive else None
        if not cached and result and result.get('figure') and self._archive:
            cached = await self._archive.store(audio_id, result['figure'])
        if self._online_audio_id == audio_id and self.hass is not None:
            self._online_result = result
            self._local_artwork = cached
            self.async_write_ha_state()

    @property
    def state(self):
        if 'Playback' not in self._values:
            return MediaPlayerState.IDLE
        return MediaPlayerState.PLAYING if self._was_playing else MediaPlayerState.IDLE

    def _metadata(self):
        try:
            catalog = json.loads(self.entry.options.get(CONF_CATALOG, '{}'))
            return catalog.get(self._values.get('ContentAudioId', ''), {})
        except (ValueError, AttributeError, TypeError):
            return {}

    @property
    def media_title(self):
        if self._figure_present is False:
            return 'Keine Figur aufgestellt'
        return self._metadata().get('title') or self._values.get('ContentTitle') or 'Unbekannter Tonie'

    @property
    def media_duration(self):
        duration = self._metadata().get('duration_seconds')
        return duration if isinstance(duration, (int, float)) and duration > 0 else None

    @property
    def media_image_url(self):
        if self._figure_present is False:
            return None
        custom = self._metadata()
        # User-defined figurine photo overrides catalog; exact Audio-ID match
        # preferred over the book/episode cover reported by TeddyCloud.
        figure = custom.get('figure') or self._local_artwork or (self._online_result or {}).get('figure') or (self._archive.lookup(self._values.get('ContentAudioId')) if self._archive else None)
        url = figure or custom.get('cover') or self._values.get('ContentPicture') or self.entry.options.get(CONF_FALLBACK_COVER, '')
        return resolved_picture(url, self.entry.options.get('teddycloud_url', ''))

    @property
    def extra_state_attributes(self):
        return {
            'content_audio_id': self._values.get('ContentAudioId'),
            'figure_present': self._figure_present,
            'figure_removed_at': self._figure_removed_at.isoformat() if self._figure_removed_at else None,
            'volume_level_raw': self._values.get('VolumeLevel'),
            'volume_db': self._values.get('VolumedB'),
            'charger': self._values.get('Charger'),
            'tag_valid': self._values.get('TagValid'),
            'last_seen': self._values.get('LastSeen'),
            'box_color': self.entry.options.get(CONF_BOX_COLOR, DEFAULT_COLOR),
            'cover_url': self.media_image_url,
            'image_source': ('manual_figure' if self._metadata().get('figure') else
                             'local_archive' if self._local_artwork else
                             'online_catalog' if (self._online_result or {}).get('figure') else
                             'teddycloud_cover' if self._values.get('ContentPicture') else 'fallback'),
            'estimated_playback_started': self._started.isoformat() if self._started else None,
            'progress_is_estimate': True,
            'playback_control_available': False,
        }
