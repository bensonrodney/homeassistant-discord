# Brand Icons

Home Assistant displays integration icons/logos from the central brands service. If you prefer not to submit a PR to the official brands repository yet, you can still show the Discord icon locally using a HACS add-on like "custom-brand-icons" (or similar community tools).

This repository includes a scaffold for the required brand assets at:

- `assets/brands/discord_webhook/`

Expected PNG files (per Home Assistant brands spec):

- `icon.png` — 256x256, square
- `icon@2x.png` — 512x512, square
- `logo.png` — landscape; shortest side 256 px (max 256)
- `logo@2x.png` — landscape; shortest side 512 px (max 512)

Notes:

- The directory name must match the integration domain: `discord_webhook`.
- All files should be PNG, trimmed (minimal transparent padding), optimized, and preferably interlaced.
- If you only have the square Discord Clyde glyph, the icon can be used without logos; some tools will fall back to the icon when a logo is missing.

Using HACS custom-brand-icons (example):

1. Install HACS if not already installed.
2. Add and install the community repository for custom brand icons (follow their documentation).
3. Place the prepared images (`icon.png`, `icon@2x.png`, and optionally `logo*.png`) in the path expected by that tool (commonly under your Home Assistant `config/www/` directory). Refer to the tool's README for the exact path.
4. Restart Home Assistant and clear the browser cache. The Integrations UI tile for `discord_webhook` should display the Discord icon.

When you're ready to make the icon official, submit these files to the Home Assistant `brands` repository under `custom_integrations/discord_webhook/`.
