# Publishing to HACS

Complete checklist for getting this integration listed in HACS and its icon
showing in the Home Assistant UI.  Work through the sections in order — each
one is a prerequisite for the next.

---

## 1. Create a public GitHub repository

HACS only works with GitHub.  Your current remote is a private Gitea instance.

```bash
# Create a new public repo on github.com, then:
git remote add github git@github.com:<YOUR_GITHUB_USERNAME>/homeassistant-discord.git
git push github main
```

> **Repo name** — `homeassistant-discord` is fine, but note that the HACS
> listing name comes from `hacs.json`, not the repo name.

---

## 2. Update `manifest.json`

Replace the three fields that still point at the upstream author's repo, and
add the minimum HA version constraint (required because the code uses
`ConfigFlowResult`, introduced in HA 2024.4).

`custom_components/discord_webhook/manifest.json`:

```json
{
  "domain": "discord_webhook",
  "name": "Discord Webhook",
  "documentation": "https://github.com/<YOUR_GITHUB_USERNAME>/homeassistant-discord",
  "dependencies": [],
  "codeowners": ["@<YOUR_GITHUB_USERNAME>"],
  "requirements": ["aiohttp>=3.7.4"],
  "version": "1.0.0",
  "iot_class": "cloud_push",
  "config_flow": true,
  "homeassistant": "2024.4.0",
  "after_dependencies": ["http"],
  "issue_tracker": "https://github.com/<YOUR_GITHUB_USERNAME>/homeassistant-discord/issues"
}
```

---

## 3. Create `hacs.json`

This file tells HACS that the repo is an integration and sets the display name
shown in the HACS UI.  Create it at the **root** of the repo:

```json
{
  "name": "Discord Webhook",
  "render_readme": true,
  "homeassistant": "2024.4.0"
}
```

`render_readme: true` uses your existing `README.md` as the HACS info page.

---

## 4. Add the HACS validation GitHub Action

This action validates your integration on every push and is required before the
HACS maintainers will accept a default-store submission.

Create `.github/workflows/hacs.yml`:

```yaml
name: HACS validation
on:
  push:
  pull_request:
  schedule:
    - cron: "0 0 * * *"
jobs:
  hacs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hacs/action@main
        with:
          category: integration
```

---

## 5. Commit and push to GitHub

```bash
# assuming you've made all the changes above
git add custom_components/discord_webhook/manifest.json hacs.json .github/
git commit -m "Add hacs.json, update manifest for HACS publication"
git push github main
```

---

## 6. Create a GitHub release

HACS discovers versions via GitHub releases, not commits.  The release tag must
match `version` in `manifest.json`.

1. Go to your GitHub repo → **Releases** → **Draft a new release**
2. Tag: `v1.0.0`  (or `1.0.0` — HACS accepts both)
3. Title: `v1.0.0`
4. Add release notes describing what the integration does
5. Click **Publish release**

> Every future version bump needs two things: update `"version"` in
> `manifest.json` and create a matching GitHub release tag.

---

## 7. Add as a custom HACS repository (immediate)

Any user (including yourself) can install right now without waiting for
default-store approval:

1. In HA → **HACS** → ⋮ menu → **Custom repositories**
2. URL: `https://github.com/<YOUR_GITHUB_USERNAME>/homeassistant-discord`
3. Category: **Integration**
4. Click **Add**

The integration then appears in HACS search and installs like any other.

---

## 8. Submit the icon to the HA brands repository

HA fetches integration icons from the brands CDN
(`brands.home-assistant.io`), which is built from
[home-assistant/brands](https://github.com/home-assistant/brands).

**Check for an existing entry first**

Visit:
```
https://github.com/home-assistant/brands/tree/master/custom_integrations/discord_webhook
```
If a directory already exists (from the upstream author), open an issue or PR
to update it rather than creating a duplicate.

**Generate the PNGs from the SVG source**

```bash
make icons
# produces:
#   assets/brands/discord_webhook/icon.png     (256×256)
#   assets/brands/discord_webhook/icon@2x.png  (512×512)
```

**Fork, copy, and PR**

```bash
# fork home-assistant/brands on GitHub, then:
git clone git@github.com:<YOUR_GITHUB_USERNAME>/brands.git
cd brands
mkdir -p custom_integrations/discord_webhook
cp ../homeassistant-discord/assets/brands/discord_webhook/icon.png    custom_integrations/discord_webhook/
cp ../homeassistant-discord/assets/brands/discord_webhook/icon@2x.png custom_integrations/discord_webhook/
git add custom_integrations/discord_webhook/
git commit -m "Add discord_webhook integration icon"
git push origin main
```

Open a PR to `home-assistant/brands`.  The PR description should link to your
public GitHub integration repo so the maintainers can verify the domain exists.

The brands repo runs its own validation action that checks PNG dimensions and
file size — your `make icons` output already satisfies these requirements.

Once the PR is merged the icon appears in HA within minutes (CDN cache).

---

## 9. Submit to the HACS default store (optional)

This makes the integration discoverable by anyone browsing HACS without needing
to add a custom repo URL.  It requires the HACS validation action (step 4) to
be passing on your GitHub repo before submitting.

1. Fork [hacs/default](https://github.com/hacs/default)
2. Add one line to `integration` (alphabetical order):
   ```
   <YOUR_GITHUB_USERNAME>/homeassistant-discord
   ```
3. Open a PR — the HACS bot will run validation automatically

> **Potential conflict**: the domain `discord_webhook` may already be
> registered in the default store by the upstream author.  If it is, the
> maintainers will flag this.  You may need to either coordinate with the
> original author or rename the domain (e.g. `discord_webhook_notify`) and
> update `manifest.json`, `const.py`, and the `translations/` directory
> accordingly.

---

## Releasing new versions

For every subsequent release:

1. Update `"version"` in `custom_components/discord_webhook/manifest.json`
2. Commit and push to GitHub
3. Create a GitHub release with a matching tag (e.g. `v1.1.0`)

HACS detects the new release automatically and notifies users of the update.
