"""Config flow for Discord Webhook integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult

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


def _schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Optional(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)): str,
            vol.Required(
                CONF_WEBHOOK_URL, default=defaults.get(CONF_WEBHOOK_URL, "")
            ): str,
            vol.Optional(CONF_USERNAME, default=defaults.get(CONF_USERNAME, "")): str,
            vol.Optional(
                CONF_AVATAR_URL, default=defaults.get(CONF_AVATAR_URL, "")
            ): str,
            vol.Optional(CONF_TTS, default=defaults.get(CONF_TTS, DEFAULT_TTS)): bool,
        }
    )


class DiscordWebhookConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Discord Webhook."""

    VERSION = 1

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

            # Prevent duplicate webhook URLs
            if not errors:
                await self.async_set_unique_id(data[CONF_WEBHOOK_URL])
                self._abort_if_unique_id_configured()

            if not errors:
                title = data.get(CONF_NAME) or DEFAULT_NAME
                return self.async_create_entry(title=title, data=data)

        return self.async_show_form(
            step_id="user", data_schema=_schema(user_input), errors=errors
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
