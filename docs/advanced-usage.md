# Advanced Usage

## Service Reference

### Notification Service

Each webhook is available as `notify.[service_name]` where `[service_name]` is derived from the webhook name (lowercase, spaces replaced by underscores).

| Service data attribute | Optional | Description |
|------------------------|----------|-------------|
| `message` | No | The message to send (max 2000 characters) |
| `title` | Yes | Message title (displayed in bold above the message) |
| `data` | Yes | Additional data (see below) |

### Data Attributes

Additional options passed in the `data` dictionary:

| Attribute | Type | Description |
|-----------|------|-------------|
| `username` | string | Override the default username for this message |
| `avatar_url` | string | Override the default avatar URL for this message |
| `tts` | boolean | Whether to use text-to-speech (default: false) |
| `images` | list | List of image URLs to include in the message |
| `embeds` | list | List of Discord embeds (see below) |

### Legacy Service (`discord_webhook.send_message`)

For backward compatibility, the legacy service is still available but not recommended for new configurations.

| Service data attribute | Optional | Description |
|------------------------|----------|-------------|
| `message` | No | The message to send |
| `username` | Yes | Override the default username |
| `avatar_url` | Yes | Override the default avatar URL |
| `tts` | Yes | Whether to use text-to-speech (default: false) |
| `data` | Yes | Additional data including `images` and `embeds` |

## Usage Examples

```yaml
# Basic notification to a specific webhook
service: notify.discord_home_alerts  # Based on the 'name' in configuration
data:
  message: "This is a test message to the home alerts channel"
  title: "Important Alert"  # Optional

# Notification with images
service: notify.discord
data:
  message: "Check out these images!"
  data:
    images:
      - "https://example.com/image1.jpg"
      - "https://example.com/image2.jpg"

# Custom username and avatar for a specific message
service: notify.discord
data:
  message: "Custom message"
  data:
    username: "Custom Bot"
    avatar_url: "https://example.com/avatar.png"
    tts: true  # Enable text-to-speech
```

## Sending Embeds

You can send rich embeds using the `embeds` field in the `data` parameter:

```yaml
service: notify.discord
data:
  message: "Check out this embed!"
  data:
    embeds:
      - title: "Embed Title"
        description: "This is a rich embed"
        color: 5814783
        fields:
          - name: "Field 1"
            value: "Value 1"
            inline: true
          - name: "Field 2"
            value: "Value 2"
            inline: true
```

## Example Automations

```yaml
# Notify when front door opens
automation:
  - alias: "Front door opened notification"
    trigger:
      platform: state
      entity_id: binary_sensor.front_door
      to: 'on'
    action:
      service: notify.discord
      data:
        title: "🚪 Door Alert"
        message: "Front door has been opened!"

# Send daily summary with images
automation:
  - alias: "Daily summary"
    trigger:
      platform: time
      at: "09:00:00"
    action:
      service: notify.discord
      data:
        message: "🌅 Good morning! Here's your daily summary."
        data:
          images:
            - "https://example.com/weather.png"
            - "https://example.com/calendar.png"
```

## Troubleshooting

If messages are not being sent, check the Home Assistant logs for error messages. Common issues:

- Incorrect webhook URL
- Network connectivity issues
- Discord rate limiting (max 2000 messages per 10 minutes per webhook)
- Missing required permissions for the webhook
