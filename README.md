# Discord Webhook for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/v/release/bensonrodney/homeassistant-discord)](https://github.com/bensonrodney/homeassistant-discord/releases)
[![License](https://img.shields.io/github/license/bensonrodney/homeassistant-discord)](LICENSE)

A Home Assistant custom integration that sends rich notifications to Discord via [webhooks](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks) — no bot, token, or extra permissions required. Configure everything from the UI, send messages with titles/embeds/images, and route different automations to different channels or servers.

## Features

- 🖥️ **UI Config Flow** — add, edit, and test webhooks entirely from Settings → Devices & Services, no YAML required
- 🚀 **Multiple Webhooks** — each configured webhook becomes its own `notify` service, so you can post to as many channels/servers as you like
- 📬 **Rich Notifications** — titles, embeds, and images in addition to plain text messages
- ✅ **Built-in Test Message** — send a test message to Discord before saving a webhook, right from the config flow
- 🔄 **YAML Import & Backward Compatibility** — existing `configuration.yaml` setups are automatically imported as UI entries

## Installation

### HACS (recommended)

This integration isn't in the default HACS store, so add it as a custom repository:

1. In Home Assistant, go to **HACS → Integrations**.
2. Click the **⋮** menu (top right) → **Custom repositories**.
3. Add `https://github.com/bensonrodney/homeassistant-discord`, category **Integration**.
4. Find **Discord Webhook** in HACS and click **Download**.
5. Restart Home Assistant.

### Manual

1. Copy the `custom_components/discord_webhook` folder from this repository into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

## Configuration

After installing and restarting, add the integration from the UI:

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for and select **Discord Webhook**.
3. Fill in the form:
   - **Name** — used to generate the notify service name (e.g. `Home Alerts` → `notify.home_alerts`)
   - **Webhook URL** *(required)* — from your Discord channel's **Integrations → Webhooks** settings
   - **Username** *(optional)* — overrides the webhook's default posting name
   - **Avatar URL** *(optional)* — overrides the webhook's default avatar
   - **Text-to-Speech** *(optional)* — send the message as a Discord TTS message
4. On the confirmation screen you can **Send test message** to verify Discord accepts the webhook before committing, **Edit settings** to go back, or **Save** to create the entry.

### Configuring multiple webhooks (different channels/servers)

Each Discord webhook URL is tied to one specific channel in one specific server. To post to multiple channels or multiple servers, repeat the **Add Integration** flow once per destination:

1. In Discord, create a separate webhook for each channel/server you want Home Assistant to post to (**Channel Settings → Integrations → Webhooks → New Webhook**), and copy each one's URL.
2. In Home Assistant, go to **Settings → Devices & Services → Add Integration → Discord Webhook** again for each webhook, giving each one a distinct **Name** (e.g. `Home Alerts`, `Security Alerts`, `Family Server`) and pasting in that webhook's URL.
3. Each entry appears separately under **Devices & Services** and creates its own `notify.<name>` service — there's no limit on how many you can add, and duplicate entries with the same webhook URL are automatically prevented.
4. Target a specific channel/server by calling that entry's service, e.g.:

   ```yaml
   service: notify.home_alerts
   data:
     message: "Front door unlocked"
   ---
   service: notify.security_alerts
   data:
     message: "Motion detected in the garage"
   ```

You can edit any entry later (including changing its webhook URL, name, or other options) from its **Configure** button on the integration's card, which reuses the same test/edit/save flow as adding a new one.

### YAML configuration (optional)

YAML setup is still supported and is automatically imported into UI entries on startup, but the UI flow above is the recommended path for new setups.

<details>
<summary>Multiple webhooks</summary>

```yaml
discord_webhook:
  webhooks:
    - name: "Home Alerts"
      webhook_url: "https://discord.com/api/webhooks/your_webhook_id/your_webhook_token"
      username: "Home Assistant"  # Optional
      avatar_url: "https://www.home-assistant.io/images/favicon-192x192-full.png"  # Optional
      tts: false  # Optional, default false
    - name: "Security Alerts"
      webhook_url: "https://discord.com/api/webhooks/another_webhook_id/another_token"
      username: "Home Security"
```

</details>

<details>
<summary>Single webhook (legacy)</summary>

```yaml
discord_webhook:
  webhook_url: "https://discord.com/api/webhooks/your_webhook_id/your_webhook_token"
  username: "Home Assistant"  # Optional
  avatar_url: "https://www.home-assistant.io/images/favicon-192x192-full.png"  # Optional
  tts: false  # Optional, default false
```

</details>

<details>
<summary>Directly on the notify platform</summary>

```yaml
notify:
  - name: discord_alerts
    platform: discord_webhook
    webhook_url: "https://discord.com/api/webhooks/your_webhook_id/your_webhook_token"
    username: "Home Assistant"  # Optional
    avatar_url: "https://www.home-assistant.io/images/favicon-192x192-full.png"  # Optional
    tts: false  # Optional, default false
```

</details>

When you configure webhooks in `configuration.yaml`, they're imported as config entries on startup (normalized the same way as the UI flow, deduplicated by `webhook_url`), and from then on can be managed from **Settings → Devices & Services** like any other entry.

## Usage

Call the `notify` service created for your webhook from an automation, script, or Developer Tools → Actions:

```yaml
service: notify.home_alerts
data:
  title: "Important Alert"  # Optional
  message: "This is a test message to the home alerts channel"
```

For advanced usage — embeds, images, TTS overrides, and the full service data reference — see the [advanced usage guide](docs/advanced-usage.md).

## Contributing

Issues and pull requests are welcome at [bensonrodney/homeassistant-discord](https://github.com/bensonrodney/homeassistant-discord/issues).

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
