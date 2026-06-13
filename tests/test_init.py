"""Tests for __init__.py — verifies the HA integration setup interface."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.discord_webhook import (
    async_setup,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.discord_webhook.const import (
    CONF_NAME,
    CONF_WEBHOOK_URL,
    DOMAIN,
)

WEBHOOK_URL = "https://discord.com/api/webhooks/123456789/abcdefghijklmnop"
WEBHOOK_URL_2 = "https://discord.com/api/webhooks/987654321/qrstuvwxyz"


def _task_sink() -> MagicMock:
    """Mock for hass.async_create_task that closes coroutines to avoid RuntimeWarning."""

    def _side_effect(coro):
        if asyncio.iscoroutine(coro):
            coro.close()

    return MagicMock(side_effect=_side_effect)


# ---------------------------------------------------------------------------
# async_setup — YAML import path
# ---------------------------------------------------------------------------


async def test_async_setup_returns_true_when_domain_absent(hass: HomeAssistant) -> None:
    assert await async_setup(hass, {}) is True


async def test_async_setup_legacy_single_webhook_creates_one_import_task(
    hass: HomeAssistant,
) -> None:
    mock_task = _task_sink()
    with patch.object(hass, "async_create_task", mock_task):
        result = await async_setup(hass, {DOMAIN: {CONF_WEBHOOK_URL: WEBHOOK_URL}})
    assert result is True
    assert mock_task.call_count == 1


async def test_async_setup_webhooks_list_creates_one_task_per_webhook(
    hass: HomeAssistant,
) -> None:
    mock_task = _task_sink()
    with patch.object(hass, "async_create_task", mock_task):
        result = await async_setup(
            hass,
            {
                DOMAIN: {
                    "webhooks": [
                        {CONF_WEBHOOK_URL: WEBHOOK_URL},
                        {CONF_WEBHOOK_URL: WEBHOOK_URL_2},
                    ]
                }
            },
        )
    assert result is True
    assert mock_task.call_count == 2


async def test_async_setup_skips_webhook_already_in_config_entries(
    hass: HomeAssistant,
) -> None:
    existing = MagicMock(spec=ConfigEntry)
    existing.unique_id = WEBHOOK_URL
    mock_task = _task_sink()

    with patch.object(hass.config_entries, "async_entries", return_value=[existing]):
        with patch.object(hass, "async_create_task", mock_task):
            result = await async_setup(hass, {DOMAIN: {CONF_WEBHOOK_URL: WEBHOOK_URL}})

    assert result is True
    assert mock_task.call_count == 0


async def test_async_setup_skips_only_the_duplicate_in_a_list(
    hass: HomeAssistant,
) -> None:
    existing = MagicMock(spec=ConfigEntry)
    existing.unique_id = WEBHOOK_URL
    mock_task = _task_sink()

    with patch.object(hass.config_entries, "async_entries", return_value=[existing]):
        with patch.object(hass, "async_create_task", mock_task):
            result = await async_setup(
                hass,
                {
                    DOMAIN: {
                        "webhooks": [
                            {
                                CONF_WEBHOOK_URL: WEBHOOK_URL
                            },  # already configured → skip
                            {CONF_WEBHOOK_URL: WEBHOOK_URL_2},  # new → schedule import
                        ]
                    }
                },
            )

    assert result is True
    assert mock_task.call_count == 1


# ---------------------------------------------------------------------------
# async_setup_entry — config-entry setup path
# ---------------------------------------------------------------------------


async def test_async_setup_entry_returns_true(hass: HomeAssistant) -> None:
    entry = MagicMock(spec=ConfigEntry)
    entry.data = {CONF_NAME: "Test", CONF_WEBHOOK_URL: WEBHOOK_URL}
    entry.title = "Test"

    with patch(
        "custom_components.discord_webhook.discovery.async_load_platform",
        new_callable=AsyncMock,
    ):
        result = await async_setup_entry(hass, entry)

    assert result is True


async def test_async_setup_entry_schedules_notify_platform_load(
    hass: HomeAssistant,
) -> None:
    entry = MagicMock(spec=ConfigEntry)
    entry.data = {CONF_NAME: "Test", CONF_WEBHOOK_URL: WEBHOOK_URL}
    entry.title = "Test"
    mock_task = _task_sink()

    with patch(
        "custom_components.discord_webhook.discovery.async_load_platform",
        new_callable=AsyncMock,
    ):
        with patch.object(hass, "async_create_task", mock_task):
            await async_setup_entry(hass, entry)

    assert mock_task.call_count == 1


# ---------------------------------------------------------------------------
# async_unload_entry
# ---------------------------------------------------------------------------


async def test_async_unload_entry_returns_true(hass: HomeAssistant) -> None:
    entry = MagicMock(spec=ConfigEntry)
    entry.title = "Test"
    assert await async_unload_entry(hass, entry) is True
