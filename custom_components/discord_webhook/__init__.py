"""The Discord Webhook integration."""

from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, SOURCE_IMPORT
from homeassistant.const import CONF_PLATFORM, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, discovery
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_AVATAR_URL,
    CONF_NAME,
    CONF_TTS,
    CONF_USERNAME,
    CONF_WEBHOOKS,
    CONF_WEBHOOK_URL,
    DEFAULT_NAME,
    DEFAULT_TTS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

WEBHOOK_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_WEBHOOK_URL): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_USERNAME): cv.string,
        vol.Optional(CONF_AVATAR_URL): cv.url,
        vol.Optional(CONF_TTS, default=DEFAULT_TTS): cv.boolean,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            # Support legacy configuration format for backward compatibility
            vol.Any(
                WEBHOOK_SCHEMA,
                {vol.Required(CONF_WEBHOOKS): [WEBHOOK_SCHEMA]},
            )
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def _discovery_payload(
    name: str,
    webhook_url: str,
    username: str | None,
    avatar_url: str | None,
    tts: bool,
):
    """Build discovery payload for notify platform."""
    return {
        CONF_PLATFORM: DOMAIN,
        CONF_NAME: name,
        CONF_WEBHOOK_URL: webhook_url,
        **({CONF_USERNAME: username} if username else {}),
        **({CONF_AVATAR_URL: avatar_url} if avatar_url else {}),
        **({CONF_TTS: tts} if tts != DEFAULT_TTS else {}),
    }


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Discord Webhook component from YAML (legacy).

    If YAML config is present, import each webhook as a config entry (one per webhook)
    via the config entries flow. This migrates users to the UI while keeping YAML
    as the source of truth during import.
    """
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]

    # Handle both legacy and new configuration formats
    if CONF_WEBHOOKS in conf:
        webhooks = conf[CONF_WEBHOOKS]
    else:
        # Convert legacy config to new format
        webhooks = [conf]

    # Import each webhook as a config entry if not already present
    existing = {entry.unique_id for entry in hass.config_entries.async_entries(DOMAIN)}
    for webhook in webhooks:
        name = webhook.get(CONF_NAME, DEFAULT_NAME)
        webhook_url = webhook[CONF_WEBHOOK_URL]
        username = webhook.get(CONF_USERNAME)
        avatar_url = webhook.get(CONF_AVATAR_URL)
        tts = webhook.get(CONF_TTS, DEFAULT_TTS)

        if webhook_url in existing:
            _LOGGER.debug("Webhook already imported; skipping: %s", name)
            continue

        _LOGGER.debug("Importing YAML webhook into config entry: %s", name)
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data={
                    CONF_NAME: name,
                    CONF_WEBHOOK_URL: webhook_url,
                    **({CONF_USERNAME: username} if username else {}),
                    **({CONF_AVATAR_URL: avatar_url} if avatar_url else {}),
                    **({CONF_TTS: tts} if tts != DEFAULT_TTS else {}),
                },
            )
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Discord Webhook from a config entry."""
    data = entry.data
    name = data.get(CONF_NAME, DEFAULT_NAME)
    webhook_url = data[CONF_WEBHOOK_URL]
    username = data.get(CONF_USERNAME)
    avatar_url = data.get(CONF_AVATAR_URL)
    tts = data.get(CONF_TTS, DEFAULT_TTS)

    _LOGGER.debug("Setting up config entry for Discord Webhook: %s", name)

    hass.async_create_task(
        discovery.async_load_platform(
            hass,
            Platform.NOTIFY,
            DOMAIN,
            _discovery_payload(name, webhook_url, username, avatar_url, tts),
            {},
        )
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # The notify platform handles its own unload lifecycle; return True to allow removal.
    _LOGGER.debug("Unloading config entry for Discord Webhook: %s", entry.title)
    return True
