"""Support for Discord Webhook notifications."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from homeassistant.components.notify import (
    ATTR_DATA,
    ATTR_TITLE,
    BaseNotificationService,
)
from homeassistant.const import CONF_NAME, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    ATTR_EMBEDS,
    ATTR_IMAGES,
    CONF_AVATAR_URL,
    CONF_TTS,
    CONF_WEBHOOK_URL,
    DEFAULT_NAME,
    DEFAULT_TTS,
)

_LOGGER = logging.getLogger(__name__)


def get_service(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: DiscoveryInfoType | None = None,
) -> DiscordNotificationService | None:
    """Get the Discord notification service."""
    if discovery_info is None:
        _LOGGER.error("This platform is only available through discovery")
        return None

    # Get the service name from discovery info or use default
    name = discovery_info.get(CONF_NAME, DEFAULT_NAME)

    # Get the webhook URL and other parameters from discovery info
    webhook_url = discovery_info.get(CONF_WEBHOOK_URL)
    if not webhook_url:
        _LOGGER.error("No webhook URL provided for %s", name)
        return None

    username = discovery_info.get(CONF_USERNAME)
    avatar_url = discovery_info.get(CONF_AVATAR_URL)
    tts = discovery_info.get(CONF_TTS, DEFAULT_TTS)

    _LOGGER.info("Setting up Discord webhook notification service: %s", name)

    return DiscordNotificationService(
        name=name,
        webhook_url=webhook_url,
        username=username,
        avatar_url=avatar_url,
        tts=tts,
    )


class DiscordNotificationService(BaseNotificationService):
    """Implement the notification service for Discord."""

    def __init__(
        self,
        name: str,
        webhook_url: str,
        username: str | None = None,
        avatar_url: str | None = None,
        tts: bool = DEFAULT_TTS,
    ) -> None:
        """Initialize the service."""
        self._name = name
        self._webhook_url = webhook_url
        self._username = username
        self._avatar_url = avatar_url
        self._tts = tts
        self._session: aiohttp.ClientSession | None = None
        _LOGGER.debug("Initialized Discord webhook service: %s", name)

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp client session."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    async def async_will_remove_from_hass(self) -> None:
        """Clean up resources when the service is unloaded."""
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def async_send_message(self, message: str, **kwargs: Any) -> None:
        """Send a message to a Discord webhook."""
        title = kwargs.get(ATTR_TITLE)
        data = kwargs.get(ATTR_DATA) or {}

        # Build the message content
        if title:
            text = f"**{title}**\n{message}"
        else:
            text = message

        payload = {
            "content": text[:2000],  # Discord has a 2000 character limit for content
            "tts": data.get(CONF_TTS, self._tts),
        }

        # Add optional parameters
        if self._username:
            payload["username"] = self._username
        if self._avatar_url:
            payload["avatar_url"] = self._avatar_url

        # Handle embeds if provided
        if ATTR_EMBEDS in data:
            embeds = data[ATTR_EMBEDS]
            if isinstance(embeds, list):
                payload["embeds"] = embeds[
                    :10
                ]  # Discord allows max 10 embeds per message

        # Handle images if provided (as URLs)
        if ATTR_IMAGES in data and isinstance(data[ATTR_IMAGES], list):
            if "embeds" not in payload:
                payload["embeds"] = []
            for image_url in data[ATTR_IMAGES]:
                payload["embeds"].append({"image": {"url": image_url}})

        _LOGGER.debug("Sending payload to Discord: %s", payload)

        # Get or create session and send the request
        session = await self._get_session()
        try:
            async with session.post(self._webhook_url, json=payload) as response:
                if response.status != 204:
                    response_text = await response.text()
                    _LOGGER.error(
                        "Error sending message to Discord webhook %s. Status: %s, Response: %s",
                        self._name,
                        response.status,
                        response_text,
                    )
                else:
                    _LOGGER.debug(
                        "Successfully sent message to Discord webhook: %s", self._name
                    )
        except aiohttp.ClientError as err:
            _LOGGER.error(
                "Error communicating with Discord webhook %s: %s", self._name, err
            )
            raise
