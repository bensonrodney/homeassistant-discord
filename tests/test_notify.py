"""Tests for notify.py — verifies DiscordNotificationService and get_service."""

import aiohttp
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.components.notify import ATTR_DATA, ATTR_TITLE
from homeassistant.core import HomeAssistant

from custom_components.discord_webhook.notify import (
    DiscordNotificationService,
    get_service,
)
from custom_components.discord_webhook.const import (
    ATTR_EMBEDS,
    ATTR_IMAGES,
    CONF_NAME,
    CONF_TTS,
    CONF_WEBHOOK_URL,
    DEFAULT_TTS,
)

WEBHOOK_URL = "https://discord.com/api/webhooks/123456789/abcdefghijklmnop"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_service(
    hass: HomeAssistant,
    *,
    name: str = "Test",
    webhook_url: str = WEBHOOK_URL,
    username: str | None = None,
    avatar_url: str | None = None,
    tts: bool = DEFAULT_TTS,
) -> DiscordNotificationService:
    return DiscordNotificationService(
        hass=hass,
        name=name,
        webhook_url=webhook_url,
        username=username,
        avatar_url=avatar_url,
        tts=tts,
    )


def _make_mock_session(status: int = 204, response_text: str = ""):
    """Return a mock aiohttp session whose post() returns the given HTTP status."""
    mock_response = MagicMock()
    mock_response.status = status
    mock_response.text = AsyncMock(return_value=response_text)

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_response
    mock_cm.__aexit__.return_value = False

    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_cm)
    mock_session.close = AsyncMock()
    return mock_session


def _sent_payload(mock_session) -> dict:
    """Extract the JSON payload from the first post() call."""
    return mock_session.post.call_args.kwargs["json"]


# ---------------------------------------------------------------------------
# get_service
# ---------------------------------------------------------------------------


def test_get_service_returns_none_without_discovery_info(hass: HomeAssistant) -> None:
    assert get_service(hass, {}, discovery_info=None) is None


def test_get_service_returns_none_when_webhook_url_missing(hass: HomeAssistant) -> None:
    assert get_service(hass, {}, discovery_info={CONF_NAME: "Test"}) is None


def test_get_service_returns_service_with_valid_discovery_info(
    hass: HomeAssistant,
) -> None:
    result = get_service(hass, {}, discovery_info={CONF_WEBHOOK_URL: WEBHOOK_URL})
    assert isinstance(result, DiscordNotificationService)


# ---------------------------------------------------------------------------
# async_send_message — payload construction
# ---------------------------------------------------------------------------


async def test_send_message_posts_content_to_webhook_url(hass: HomeAssistant) -> None:
    service = _make_service(hass)
    mock_session = _make_mock_session()

    with patch(
        "custom_components.discord_webhook.notify.async_get_clientsession",
        return_value=mock_session,
    ):
        await service.async_send_message("Hello world")

    args, kwargs = mock_session.post.call_args
    assert args[0] == WEBHOOK_URL
    assert kwargs["json"]["content"] == "Hello world"


async def test_send_message_includes_default_tts(hass: HomeAssistant) -> None:
    service = _make_service(hass, tts=False)
    mock_session = _make_mock_session()

    with patch(
        "custom_components.discord_webhook.notify.async_get_clientsession",
        return_value=mock_session,
    ):
        await service.async_send_message("Hello")

    assert _sent_payload(mock_session)["tts"] is False


async def test_send_message_with_title_prepends_bold_prefix(hass: HomeAssistant) -> None:
    service = _make_service(hass)
    mock_session = _make_mock_session()

    with patch(
        "custom_components.discord_webhook.notify.async_get_clientsession",
        return_value=mock_session,
    ):
        await service.async_send_message("Body text", **{ATTR_TITLE: "Alert"})

    assert _sent_payload(mock_session)["content"] == "**Alert**\nBody text"


async def test_content_is_truncated_to_2000_characters(hass: HomeAssistant) -> None:
    service = _make_service(hass)
    mock_session = _make_mock_session()

    with patch(
        "custom_components.discord_webhook.notify.async_get_clientsession",
        return_value=mock_session,
    ):
        await service.async_send_message("x" * 3000)

    assert len(_sent_payload(mock_session)["content"]) == 2000


async def test_username_and_avatar_included_in_payload_when_configured(hass: HomeAssistant) -> None:
    service = _make_service(
        hass, username="BotUser", avatar_url="https://example.com/avatar.png"
    )
    mock_session = _make_mock_session()

    with patch(
        "custom_components.discord_webhook.notify.async_get_clientsession",
        return_value=mock_session,
    ):
        await service.async_send_message("Hello")

    payload = _sent_payload(mock_session)
    assert payload["username"] == "BotUser"
    assert payload["avatar_url"] == "https://example.com/avatar.png"


async def test_username_and_avatar_absent_from_payload_when_not_configured(hass: HomeAssistant) -> None:
    service = _make_service(hass)
    mock_session = _make_mock_session()

    with patch(
        "custom_components.discord_webhook.notify.async_get_clientsession",
        return_value=mock_session,
    ):
        await service.async_send_message("Hello")

    payload = _sent_payload(mock_session)
    assert "username" not in payload
    assert "avatar_url" not in payload


async def test_tts_overridden_per_message_via_data(hass: HomeAssistant) -> None:
    service = _make_service(hass, tts=False)
    mock_session = _make_mock_session()

    with patch(
        "custom_components.discord_webhook.notify.async_get_clientsession",
        return_value=mock_session,
    ):
        await service.async_send_message("Hello", **{ATTR_DATA: {CONF_TTS: True}})

    assert _sent_payload(mock_session)["tts"] is True


async def test_embeds_passed_through_to_payload(hass: HomeAssistant) -> None:
    service = _make_service(hass)
    mock_session = _make_mock_session()
    embeds = [{"title": "Embed", "description": "Rich content"}]

    with patch(
        "custom_components.discord_webhook.notify.async_get_clientsession",
        return_value=mock_session,
    ):
        await service.async_send_message("Hello", **{ATTR_DATA: {ATTR_EMBEDS: embeds}})

    assert _sent_payload(mock_session)["embeds"] == embeds


async def test_embeds_capped_at_10(hass: HomeAssistant) -> None:
    service = _make_service(hass)
    mock_session = _make_mock_session()

    with patch(
        "custom_components.discord_webhook.notify.async_get_clientsession",
        return_value=mock_session,
    ):
        await service.async_send_message(
            "Hello",
            **{ATTR_DATA: {ATTR_EMBEDS: [{"title": f"E{i}"} for i in range(15)]}},
        )

    assert len(_sent_payload(mock_session)["embeds"]) == 10


async def test_images_converted_to_embed_objects(hass: HomeAssistant) -> None:
    service = _make_service(hass)
    mock_session = _make_mock_session()
    images = ["https://example.com/img1.jpg", "https://example.com/img2.jpg"]

    with patch(
        "custom_components.discord_webhook.notify.async_get_clientsession",
        return_value=mock_session,
    ):
        await service.async_send_message("Hello", **{ATTR_DATA: {ATTR_IMAGES: images}})

    payload = _sent_payload(mock_session)
    assert len(payload["embeds"]) == 2
    assert payload["embeds"][0] == {"image": {"url": images[0]}}
    assert payload["embeds"][1] == {"image": {"url": images[1]}}


# ---------------------------------------------------------------------------
# async_send_message — error handling
# ---------------------------------------------------------------------------


async def test_non_204_response_logs_error_without_raising(hass: HomeAssistant) -> None:
    service = _make_service(hass)
    mock_session = _make_mock_session(
        status=400, response_text='{"message":"Unknown Webhook"}'
    )

    with patch(
        "custom_components.discord_webhook.notify.async_get_clientsession",
        return_value=mock_session,
    ):
        with patch("custom_components.discord_webhook.notify._LOGGER") as mock_logger:
            await service.async_send_message("Hello")  # must not raise

    mock_logger.error.assert_called_once()


async def test_aiohttp_client_error_is_reraised(hass: HomeAssistant) -> None:
    service = _make_service(hass)

    mock_cm = AsyncMock()
    mock_cm.__aenter__.side_effect = aiohttp.ClientError("connection refused")
    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_cm)

    with patch(
        "custom_components.discord_webhook.notify.async_get_clientsession",
        return_value=mock_session,
    ):
        with pytest.raises(aiohttp.ClientError):
            await service.async_send_message("Hello")


# ---------------------------------------------------------------------------
# Session lifecycle
# ---------------------------------------------------------------------------


async def test_uses_ha_managed_session(hass: HomeAssistant) -> None:
    service = _make_service(hass)
    mock_session = _make_mock_session()

    with patch(
        "custom_components.discord_webhook.notify.async_get_clientsession",
        return_value=mock_session,
    ) as mock_get_session:
        await service.async_send_message("Hello")

    mock_get_session.assert_called_once_with(hass)
