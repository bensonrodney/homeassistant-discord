# Discord Webhook Integration for Home Assistant

A powerful Home Assistant integration for sending rich notifications to Discord using webhooks. This integration supports multiple webhooks, rich embeds, images, and more.

## Features

- 🚀 **Multiple Webhooks** - Configure multiple Discord webhooks with different settings
- 📱 **Rich Notifications** - Send formatted messages with titles, images, and embeds
- 🔔 **Flexible Configuration** - Multiple configuration options to suit your needs
- 🔄 **Backward Compatible** - Supports legacy configuration format

## Installation

1. Copy the `discord_webhook` folder to your Home Assistant's `custom_components` directory (found in the `config` directory of your Home Assistant installation).
2. Restart Home Assistant to load the integration.

## Configuration

### Option 1: UI Config Flow (Recommended)

You can configure this integration entirely from the Home Assistant UI:

1. Go to: Settings > Devices & Services > Add Integration.
2. Search for and select "Discord Webhook".
3. Enter the details for the webhook:
   - Name (used for the service name)
   - Webhook URL (required)
   - Username (optional)
   - Avatar URL (optional)
   - TTS (optional)
4. Submit to create the entry.

Notes:
- Each config flow entry creates its own notify service, allowing you to maintain multiple distinct Discord webhooks (e.g., alerts vs. general updates).
- You can add multiple instances by repeating the above steps. Duplicate entries with the same `webhook_url` are prevented.

### Option 2: YAML — Multiple Webhooks

Configure multiple Discord webhooks in YAML. Each webhook will be available as a separate notification service.

```yaml
# Example configuration.yaml entry
discord_webhook:
  webhooks:
    - name: "Home Alerts"  # Optional, defaults to "Discord Webhook"
      webhook_url: "https://discord.com/api/webhooks/your_webhook_id/your_webhook_token"
      username: "Home Assistant"  # Optional
      avatar_url: "https://www.home-assistant.io/images/favicon-192x192-full.png"  # Optional
      tts: false  # Optional, default false
    - name: "Security Alerts"
      webhook_url: "https://discord.com/api/webhooks/another_webhook_id/another_token"
      username: "Home Security"
```

### Option 3: YAML — Using the Notification Platform

You can also configure webhooks directly in the notify platform:

```yaml
notify:
  - name: discord_alerts
    platform: discord_webhook
    webhook_url: "https://discord.com/api/webhooks/your_webhook_id/your_webhook_token"
    username: "Home Assistant"  # Optional
    avatar_url: "https://www.home-assistant.io/images/favicon-192x192-full.png"  # Optional
    tts: false  # Optional, default false
```

### Option 4: YAML — Legacy Configuration (Single Webhook)

For backward compatibility, a single webhook can still be configured:

```yaml
discord_webhook:
  webhook_url: "https://discord.com/api/webhooks/your_webhook_id/your_webhook_token"
  username: "Home Assistant"  # Optional
  avatar_url: "https://www.home-assistant.io/images/favicon-192x192-full.png"  # Optional
  tts: false  # Optional, default false
```

## Basic Usage

Send a notification to a specific webhook:

```yaml
service: notify.discord_home_alerts  # Based on the 'name' in configuration
data:
  message: "This is a test message to the home alerts channel"
  title: "Important Alert"  # Optional
```

## Documentation

For complete documentation, including advanced features like embeds, images, and automation examples, please see the [advanced usage guide](docs/advanced-usage.md).

## YAML Import (How YAML becomes UI entries)

If you configure webhooks in `configuration.yaml` under `discord_webhook:`, they will be imported into the UI as Config Entries on startup or when the integration is reloaded. Behavior details:

- Each imported entry is normalized like the UI flow (optional empty strings become `null`, and `tts` defaults if omitted).
- Import uses the `webhook_url` as a unique identifier to prevent duplicates. If an entry with the same `webhook_url` already exists, it will be skipped.
- Invalid entries (e.g., `webhook_url` not starting with `http`) are safely ignored during import.

After import, you can manage these entries from Settings > Devices & Services > Integrations like any other UI-added instance.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
