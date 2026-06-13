# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Home Assistant custom integration (`discord_webhook`) that sends notifications to Discord via webhooks. It is installed by copying the `custom_components/discord_webhook/` directory into a Home Assistant instance's `custom_components/` folder.

There is no build step, test suite, or package manager — development means editing Python files and reloading/restarting Home Assistant to test.

## Architecture

The integration follows the Home Assistant custom component pattern with a config-flow-first design:

**Setup flow:**
1. `__init__.py` → `async_setup()` handles YAML import: reads `configuration.yaml`, creates one config entry per webhook via `SOURCE_IMPORT` (deduplicated by `webhook_url` as unique ID)
2. `__init__.py` → `async_setup_entry()` handles each config entry by calling `discovery.async_load_platform()` for the `notify` platform
3. `notify.py` → `get_service()` receives the discovery payload and returns a `DiscordNotificationService` instance
4. `DiscordNotificationService.async_send_message()` POSTs JSON to the Discord webhook URL via `aiohttp`

**Config flow** (`config_flow.py`): `async_step_user` for UI-driven setup, `async_step_import` for YAML-driven import. Both normalize empty optional strings to `None` and use `webhook_url` as the unique ID to prevent duplicates.

**Key design invariant:** The notify platform is never loaded directly from YAML — all paths (UI and YAML) converge on config entries, which then use `discovery.async_load_platform` to register the notify service.

## Key files

| File | Purpose |
|------|---------|
| `__init__.py` | Integration setup, YAML→config-entry import logic |
| `config_flow.py` | UI config flow (add/import webhook entries) |
| `notify.py` | `DiscordNotificationService` — builds payload, POSTs to Discord |
| `const.py` | All string constants and defaults |
| `manifest.json` | HA integration manifest — **has an active merge conflict** |
| `translations/en.json` | UI strings for the config flow |
| `services.yaml` | Service schema definitions |

## Manifest conflict

`manifest.json` currently has unresolved git merge conflict markers. Resolve before testing — Home Assistant will fail to load the integration with malformed JSON.

## Discord API constraints (enforced in `notify.py`)

- Message `content` is truncated to 2000 characters
- Max 10 embeds per message
- Successful POST returns HTTP 204 (no content); anything else is logged as an error

## YAML configuration formats (all supported)

```yaml
# New: multiple webhooks
discord_webhook:
  webhooks:
    - name: "Alerts"
      webhook_url: "https://discord.com/api/webhooks/..."

# Legacy: single webhook (backward compat)
discord_webhook:
  webhook_url: "https://discord.com/api/webhooks/..."

# Notify platform direct
notify:
  - platform: discord_webhook
    name: my_discord
    webhook_url: "https://discord.com/api/webhooks/..."
```
