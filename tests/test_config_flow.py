"""Tests for config_flow.py — verifies the HA config flow interface contract."""

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.discord_webhook.const import (
    CONF_AVATAR_URL,
    CONF_NAME,
    CONF_TTS,
    CONF_USERNAME,
    CONF_WEBHOOK_URL,
    DEFAULT_NAME,
    DEFAULT_TTS,
    DOMAIN,
)

WEBHOOK_URL = "https://discord.com/api/webhooks/123456789/abcdefghijklmnop"
WEBHOOK_URL_2 = "https://discord.com/api/webhooks/987654321/qrstuvwxyz"


async def _save(hass: HomeAssistant, flow_id: str, user_input: dict) -> dict:
    """Submit the user/init form then pick Save from the confirm menu."""
    result = await hass.config_entries.flow.async_configure(flow_id, user_input=user_input)
    assert result["type"] == FlowResultType.MENU, result
    assert result["step_id"] == "confirm"
    return await hass.config_entries.flow.async_configure(
        flow_id, user_input={"next_step_id": "save"}
    )


# ---------------------------------------------------------------------------
# User step — form behaviour
# ---------------------------------------------------------------------------


async def test_user_step_shows_form(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_user_step_rejects_invalid_url(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_WEBHOOK_URL: "not-a-url"},
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"][CONF_WEBHOOK_URL] == "invalid_url"


# ---------------------------------------------------------------------------
# User step → confirm menu → save
# ---------------------------------------------------------------------------


async def test_user_step_creates_entry_with_required_fields(
    hass: HomeAssistant,
) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await _save(hass, result["flow_id"], {CONF_WEBHOOK_URL: WEBHOOK_URL, CONF_NAME: "My Discord"})
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "My Discord"
    data = result["data"]
    assert data[CONF_WEBHOOK_URL] == WEBHOOK_URL
    assert data[CONF_NAME] == "My Discord"
    assert data[CONF_TTS] == DEFAULT_TTS
    assert data[CONF_USERNAME] is None
    assert data[CONF_AVATAR_URL] is None


async def test_user_step_defaults_name_when_omitted(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await _save(hass, result["flow_id"], {CONF_WEBHOOK_URL: WEBHOOK_URL})
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == DEFAULT_NAME
    assert result["data"][CONF_NAME] == DEFAULT_NAME


async def test_user_step_stores_all_optional_fields(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await _save(hass, result["flow_id"], {
        CONF_WEBHOOK_URL: WEBHOOK_URL,
        CONF_USERNAME: "BotName",
        CONF_AVATAR_URL: "https://example.com/avatar.png",
        CONF_TTS: True,
    })
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_USERNAME] == "BotName"
    assert result["data"][CONF_AVATAR_URL] == "https://example.com/avatar.png"
    assert result["data"][CONF_TTS] is True


async def test_user_step_normalizes_empty_optional_strings_to_none(
    hass: HomeAssistant,
) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await _save(hass, result["flow_id"], {
        CONF_WEBHOOK_URL: WEBHOOK_URL,
        CONF_USERNAME: "",
        CONF_AVATAR_URL: "   ",
    })
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_USERNAME] is None
    assert result["data"][CONF_AVATAR_URL] is None


async def test_user_step_aborts_on_duplicate_url(hass: HomeAssistant) -> None:
    # Complete the first flow fully so a config entry exists with that URL
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await _save(hass, result["flow_id"], {CONF_WEBHOOK_URL: WEBHOOK_URL})

    # Second flow with the same URL should abort during the user step
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_WEBHOOK_URL: WEBHOOK_URL},
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_user_step_allows_different_urls(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await _save(hass, result["flow_id"], {CONF_WEBHOOK_URL: WEBHOOK_URL})

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await _save(hass, result["flow_id"], {CONF_WEBHOOK_URL: WEBHOOK_URL_2})
    assert result["type"] == FlowResultType.CREATE_ENTRY


# ---------------------------------------------------------------------------
# Confirm menu — test and edit_settings paths
# ---------------------------------------------------------------------------


async def test_confirm_menu_test_webhook_shows_success(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_WEBHOOK_URL: WEBHOOK_URL}
    )
    assert result["type"] == FlowResultType.MENU

    with patch(
        "custom_components.discord_webhook.config_flow._async_test_webhook",
        new=AsyncMock(return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={"next_step_id": "test_webhook"}
        )

    assert result["type"] == FlowResultType.MENU
    assert "✅" in result["description_placeholders"]["test_result"]


async def test_confirm_menu_test_webhook_shows_failure(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_WEBHOOK_URL: WEBHOOK_URL}
    )
    assert result["type"] == FlowResultType.MENU

    with patch(
        "custom_components.discord_webhook.config_flow._async_test_webhook",
        new=AsyncMock(return_value=False),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={"next_step_id": "test_webhook"}
        )

    assert result["type"] == FlowResultType.MENU
    assert "❌" in result["description_placeholders"]["test_result"]


async def test_confirm_menu_edit_settings_returns_to_form(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_WEBHOOK_URL: WEBHOOK_URL}
    )
    assert result["type"] == FlowResultType.MENU

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"next_step_id": "edit_settings"}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"


# ---------------------------------------------------------------------------
# Import step
# ---------------------------------------------------------------------------


async def test_import_step_creates_entry(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data={CONF_WEBHOOK_URL: WEBHOOK_URL, CONF_NAME: "Imported Webhook"},
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Imported Webhook"
    assert result["data"][CONF_WEBHOOK_URL] == WEBHOOK_URL


async def test_import_step_defaults_name(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data={CONF_WEBHOOK_URL: WEBHOOK_URL},
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == DEFAULT_NAME


async def test_import_step_aborts_on_invalid_url(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data={CONF_WEBHOOK_URL: "ftp://not-an-http-url"},
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "invalid_url"


async def test_import_step_aborts_on_duplicate_url(hass: HomeAssistant) -> None:
    await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data={CONF_WEBHOOK_URL: WEBHOOK_URL},
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data={CONF_WEBHOOK_URL: WEBHOOK_URL},
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_import_step_normalizes_empty_optional_strings_to_none(
    hass: HomeAssistant,
) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data={CONF_WEBHOOK_URL: WEBHOOK_URL, CONF_USERNAME: "", CONF_AVATAR_URL: ""},
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_USERNAME] is None
    assert result["data"][CONF_AVATAR_URL] is None
