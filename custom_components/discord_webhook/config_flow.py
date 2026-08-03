"""Config flow for Discord Webhook integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_AVATAR_URL,
    CONF_NAME,
    CONF_TTS,
    CONF_USERNAME,
    CONF_WEBHOOK_URL,
    DEFAULT_NAME,
    DEFAULT_TTS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

CONF_SEND_TEST = "send_test_message"


async def _async_test_webhook(hass, webhook_url: str) -> bool:
    """POST a test message to the webhook. Returns True on HTTP 204."""
    session = async_get_clientsession(hass)
    try:
        async with session.post(
            webhook_url,
            json={"content": "🔔 Test message from Home Assistant Discord Webhook integration."},
        ) as response:
            return response.status == 204
    except aiohttp.ClientError as err:
        _LOGGER.debug("Test webhook request failed: %s", err)
        return False


def _schema(
    defaults: dict[str, Any] | None = None, suggested_values: bool = False
) -> vol.Schema:
    """Build the config/options form schema.

    For the add flow use ``default=`` so optional text fields start empty.
    For the edit (options) flow use ``suggested_value`` instead — HA's frontend
    treats a non-empty ``default`` as immutable, preventing the user from
    clearing it back to empty.
    """
    defaults = defaults or {}

    if suggested_values:
        username_field = vol.Optional(
            CONF_USERNAME,
            description={"suggested_value": defaults.get(CONF_USERNAME) or ""},
        )
        avatar_field = vol.Optional(
            CONF_AVATAR_URL,
            description={"suggested_value": defaults.get(CONF_AVATAR_URL) or ""},
        )
    else:
        username_field = vol.Optional(
            CONF_USERNAME, default=defaults.get(CONF_USERNAME) or ""
        )
        avatar_field = vol.Optional(
            CONF_AVATAR_URL, default=defaults.get(CONF_AVATAR_URL) or ""
        )

    return vol.Schema(
        {
            vol.Optional(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)): str,
            vol.Required(
                CONF_WEBHOOK_URL, default=defaults.get(CONF_WEBHOOK_URL, "")
            ): str,
            username_field: str,
            avatar_field: str,
            vol.Optional(CONF_TTS, default=defaults.get(CONF_TTS, DEFAULT_TTS)): bool,
            vol.Optional(CONF_SEND_TEST, default=False): bool,
        }
    )


class DiscordWebhookConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Discord Webhook."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Return the options flow handler."""
        return OptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            # Normalize empty optional strings to None
            data: dict[str, Any] = {
                CONF_NAME: user_input.get(CONF_NAME) or DEFAULT_NAME,
                CONF_WEBHOOK_URL: (user_input.get(CONF_WEBHOOK_URL) or "").strip(),
                CONF_USERNAME: (user_input.get(CONF_USERNAME) or "").strip() or None,
                CONF_AVATAR_URL: (user_input.get(CONF_AVATAR_URL) or "").strip()
                or None,
                CONF_TTS: bool(user_input.get(CONF_TTS, DEFAULT_TTS)),
            }

            # Basic validation
            if not data[CONF_WEBHOOK_URL].startswith("http"):
                errors[CONF_WEBHOOK_URL] = "invalid_url"

            # Optional test message
            if not errors and user_input.get(CONF_SEND_TEST):
                if not await _async_test_webhook(self.hass, data[CONF_WEBHOOK_URL]):
                    errors["base"] = "test_failed"

            # Prevent duplicate webhook URLs
            if not errors:
                await self.async_set_unique_id(data[CONF_WEBHOOK_URL])
                self._abort_if_unique_id_configured()

            if not errors:
                title = data.get(CONF_NAME) or DEFAULT_NAME
                return self.async_create_entry(title=title, data=data)

        # Always reset the test checkbox so a failed test doesn't re-fire on resubmit
        defaults = {**(user_input or {}), CONF_SEND_TEST: False}
        return self.async_show_form(
            step_id="user", data_schema=_schema(defaults), errors=errors
        )

    async def async_step_import(self, user_input: dict[str, Any]) -> ConfigFlowResult:
        """Handle import from YAML configuration."""
        # Normalize like user step
        data: dict[str, Any] = {
            CONF_NAME: user_input.get(CONF_NAME) or DEFAULT_NAME,
            CONF_WEBHOOK_URL: (user_input.get(CONF_WEBHOOK_URL) or "").strip(),
            CONF_USERNAME: (user_input.get(CONF_USERNAME) or "").strip() or None,
            CONF_AVATAR_URL: (user_input.get(CONF_AVATAR_URL) or "").strip() or None,
            CONF_TTS: bool(user_input.get(CONF_TTS, DEFAULT_TTS)),
        }

        # Basic validation: if invalid, abort import to avoid creating bad entries
        if not data[CONF_WEBHOOK_URL].startswith("http"):
            return self.async_abort(reason="invalid_url")

        await self.async_set_unique_id(data[CONF_WEBHOOK_URL])
        self._abort_if_unique_id_configured()

        title = data.get(CONF_NAME) or DEFAULT_NAME
        return self.async_create_entry(title=title, data=data)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Discord Webhook (edit an existing entry)."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        # Merge options over data so existing options are reflected in the form
        current = {**self.config_entry.data, **self.config_entry.options}

        if user_input is not None:
            data: dict[str, Any] = {
                CONF_NAME: user_input.get(CONF_NAME) or DEFAULT_NAME,
                CONF_WEBHOOK_URL: (user_input.get(CONF_WEBHOOK_URL) or "").strip(),
                # Store "" rather than None so HA's JSON serialization doesn't drop
                # the key, which would leave the old value from entry.data in place
                # after the merge in async_setup_entry.
                CONF_USERNAME: (user_input.get(CONF_USERNAME) or "").strip(),
                CONF_AVATAR_URL: (user_input.get(CONF_AVATAR_URL) or "").strip(),
                CONF_TTS: bool(user_input.get(CONF_TTS, DEFAULT_TTS)),
            }

            if not data[CONF_WEBHOOK_URL].startswith("http"):
                errors[CONF_WEBHOOK_URL] = "invalid_url"

            if not errors and data[CONF_WEBHOOK_URL] != self.config_entry.unique_id:
                # Changing webhook URL — check it isn't already used by another entry
                existing_urls = {
                    e.unique_id
                    for e in self.hass.config_entries.async_entries(DOMAIN)
                    if e.entry_id != self.config_entry.entry_id
                }
                if data[CONF_WEBHOOK_URL] in existing_urls:
                    errors[CONF_WEBHOOK_URL] = "already_configured"

            # Optional test message
            if not errors and user_input.get(CONF_SEND_TEST):
                if not await _async_test_webhook(self.hass, data[CONF_WEBHOOK_URL]):
                    errors["base"] = "test_failed"

            if not errors:
                # Keep title and unique_id in sync with any changes
                updates: dict[str, Any] = {}
                if data[CONF_WEBHOOK_URL] != self.config_entry.unique_id:
                    updates["unique_id"] = data[CONF_WEBHOOK_URL]
                new_title = data.get(CONF_NAME) or DEFAULT_NAME
                if new_title != self.config_entry.title:
                    updates["title"] = new_title
                if updates:
                    self.hass.config_entries.async_update_entry(
                        self.config_entry, **updates
                    )

                return self.async_create_entry(data=data)

        # Always reset the test checkbox so a failed test doesn't re-fire on resubmit
        defaults = {**(user_input or current), CONF_SEND_TEST: False}
        return self.async_show_form(
            step_id="init",
            data_schema=_schema(defaults, suggested_values=True),
            errors=errors,
        )
