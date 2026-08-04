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


async def _async_test_webhook(
    hass,
    webhook_url: str,
    username: str | None = None,
    avatar_url: str | None = None,
) -> bool:
    """POST a test message to the webhook. Returns True on HTTP 204."""
    session = async_get_clientsession(hass)
    payload: dict[str, Any] = {
        "content": "🔔 Test message from Home Assistant Discord Webhook integration."
    }
    if username:
        payload["username"] = username
    if avatar_url:
        payload["avatar_url"] = avatar_url
    try:
        async with session.post(webhook_url, json=payload) as response:
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
        }
    )


class DiscordWebhookConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Discord Webhook."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._test_result: str = ""

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
            data: dict[str, Any] = {
                CONF_NAME: user_input.get(CONF_NAME) or DEFAULT_NAME,
                CONF_WEBHOOK_URL: (user_input.get(CONF_WEBHOOK_URL) or "").strip(),
                CONF_USERNAME: (user_input.get(CONF_USERNAME) or "").strip() or None,
                CONF_AVATAR_URL: (user_input.get(CONF_AVATAR_URL) or "").strip()
                or None,
                CONF_TTS: bool(user_input.get(CONF_TTS, DEFAULT_TTS)),
            }

            if not data[CONF_WEBHOOK_URL].startswith("http"):
                errors[CONF_WEBHOOK_URL] = "invalid_url"

            if not errors:
                await self.async_set_unique_id(data[CONF_WEBHOOK_URL])
                self._abort_if_unique_id_configured()
                self._data = data
                self._test_result = ""
                return await self.async_step_confirm()

        defaults = user_input or self._data
        return self.async_show_form(
            step_id="user",
            data_schema=_schema(defaults),
            errors=errors,
            last_step=False,
        )

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="confirm",
            menu_options=["test_webhook", "edit_settings", "save"],
            description_placeholders={"test_result": self._test_result},
        )

    async def async_step_test_webhook(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        test_ok = await _async_test_webhook(
            self.hass,
            self._data[CONF_WEBHOOK_URL],
            self._data.get(CONF_USERNAME),
            self._data.get(CONF_AVATAR_URL),
        )
        self._test_result = (
            "✅ Test message sent successfully!"
            if test_ok
            else "❌ Test failed — check the webhook URL and try again."
        )
        return await self.async_step_confirm()

    async def async_step_edit_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self.async_step_user()

    async def async_step_save(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self.async_create_entry(
            title=self._data.get(CONF_NAME) or DEFAULT_NAME,
            data=self._data,
        )

    async def async_step_import(self, user_input: dict[str, Any]) -> ConfigFlowResult:
        """Handle import from YAML configuration."""
        data: dict[str, Any] = {
            CONF_NAME: user_input.get(CONF_NAME) or DEFAULT_NAME,
            CONF_WEBHOOK_URL: (user_input.get(CONF_WEBHOOK_URL) or "").strip(),
            CONF_USERNAME: (user_input.get(CONF_USERNAME) or "").strip() or None,
            CONF_AVATAR_URL: (user_input.get(CONF_AVATAR_URL) or "").strip() or None,
            CONF_TTS: bool(user_input.get(CONF_TTS, DEFAULT_TTS)),
        }

        if not data[CONF_WEBHOOK_URL].startswith("http"):
            return self.async_abort(reason="invalid_url")

        await self.async_set_unique_id(data[CONF_WEBHOOK_URL])
        self._abort_if_unique_id_configured()

        title = data.get(CONF_NAME) or DEFAULT_NAME
        return self.async_create_entry(title=title, data=data)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Discord Webhook (edit an existing entry)."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._test_result: str = ""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
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
                existing_urls = {
                    e.unique_id
                    for e in self.hass.config_entries.async_entries(DOMAIN)
                    if e.entry_id != self.config_entry.entry_id
                }
                if data[CONF_WEBHOOK_URL] in existing_urls:
                    errors[CONF_WEBHOOK_URL] = "already_configured"

            if not errors:
                self._data = data
                self._test_result = ""
                return await self.async_step_confirm()

        # self._data holds the user's pending edits if they navigated back from confirm
        defaults = user_input or self._data or current
        return self.async_show_form(
            step_id="init",
            data_schema=_schema(defaults, suggested_values=True),
            errors=errors,
            last_step=False,
        )

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="confirm",
            menu_options=["test_webhook", "edit_settings", "save"],
            description_placeholders={"test_result": self._test_result},
        )

    async def async_step_test_webhook(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        test_ok = await _async_test_webhook(
            self.hass,
            self._data[CONF_WEBHOOK_URL],
            self._data.get(CONF_USERNAME) or None,
            self._data.get(CONF_AVATAR_URL) or None,
        )
        self._test_result = (
            "✅ Test message sent successfully!"
            if test_ok
            else "❌ Test failed — check the webhook URL and try again."
        )
        return await self.async_step_confirm()

    async def async_step_edit_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self.async_step_init()

    async def async_step_save(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        updates: dict[str, Any] = {}
        if self._data[CONF_WEBHOOK_URL] != self.config_entry.unique_id:
            updates["unique_id"] = self._data[CONF_WEBHOOK_URL]
        new_title = self._data.get(CONF_NAME) or DEFAULT_NAME
        if new_title != self.config_entry.title:
            updates["title"] = new_title
        if updates:
            self.hass.config_entries.async_update_entry(self.config_entry, **updates)
        return self.async_create_entry(data=self._data)
