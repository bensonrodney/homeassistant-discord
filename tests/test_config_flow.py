"""Tests for config_flow.py — verifies the HA config flow interface contract."""

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


# ---------------------------------------------------------------------------
# User step
# ---------------------------------------------------------------------------


async def test_user_step_shows_form(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_user_step_creates_entry_with_required_fields(
    hass: HomeAssistant,
) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_WEBHOOK_URL: WEBHOOK_URL, CONF_NAME: "My Discord"},
    )
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
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_WEBHOOK_URL: WEBHOOK_URL},
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == DEFAULT_NAME
    assert result["data"][CONF_NAME] == DEFAULT_NAME


async def test_user_step_stores_all_optional_fields(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_WEBHOOK_URL: WEBHOOK_URL,
            CONF_USERNAME: "BotName",
            CONF_AVATAR_URL: "https://example.com/avatar.png",
            CONF_TTS: True,
        },
    )
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
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_WEBHOOK_URL: WEBHOOK_URL,
            CONF_USERNAME: "",
            CONF_AVATAR_URL: "   ",
        },
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_USERNAME] is None
    assert result["data"][CONF_AVATAR_URL] is None


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


async def test_user_step_aborts_on_duplicate_url(hass: HomeAssistant) -> None:
    # First entry succeeds
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_WEBHOOK_URL: WEBHOOK_URL},
    )

    # Second entry with the same URL must abort
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
    await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_WEBHOOK_URL: WEBHOOK_URL},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_WEBHOOK_URL: WEBHOOK_URL_2},
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY


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
