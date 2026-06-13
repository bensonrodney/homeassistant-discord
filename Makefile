PYTHON := .venv/bin/python
VENV   := .venv
SRC    := custom_components tests

.PHONY: help install lint format format-check typecheck test check fix icons

help:
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'

$(VENV):
	uv venv $(VENV)

install: $(VENV)  ## Create venv and install all dependencies
	uv pip install --python $(PYTHON) -r requirements_test.txt

lint:          ## Check code with ruff
	$(PYTHON) -m ruff check $(SRC)

format:        ## Format code in-place with ruff
	$(PYTHON) -m ruff format $(SRC)

format-check:  ## Check formatting without making changes
	$(PYTHON) -m ruff format --check $(SRC)

typecheck:     ## Run mypy type checker
	$(PYTHON) -m mypy custom_components --ignore-missing-imports

test:          ## Run the test suite
	$(PYTHON) -m pytest tests/

check: lint format-check typecheck test  ## Run all checks (CI)

fix:           ## Auto-fix lint issues and reformat
	$(PYTHON) -m ruff check --fix $(SRC)
	$(PYTHON) -m ruff format $(SRC)

ICON_SVG   := assets/brands/discord_webhook/icon.svg
ICON_DIR   := assets/brands/discord_webhook
BRAND_DIR  := custom_components/discord_webhook/brand

icons: $(ICON_DIR)/icon.png $(ICON_DIR)/icon@2x.png $(BRAND_DIR)/icon.png $(BRAND_DIR)/icon@2x.png  ## Render icon.svg → PNG assets (assets/ and component brand/)

$(ICON_DIR)/icon.png $(ICON_DIR)/icon@2x.png $(BRAND_DIR)/icon.png $(BRAND_DIR)/icon@2x.png: $(ICON_SVG)
	mkdir -p $(BRAND_DIR)
	$(PYTHON) -c "\
import cairosvg; \
cairosvg.svg2png(url='$(ICON_SVG)', write_to='$(ICON_DIR)/icon.png',    output_width=256, output_height=256); \
cairosvg.svg2png(url='$(ICON_SVG)', write_to='$(ICON_DIR)/icon@2x.png', output_width=512, output_height=512); \
cairosvg.svg2png(url='$(ICON_SVG)', write_to='$(BRAND_DIR)/icon.png',    output_width=256, output_height=256); \
cairosvg.svg2png(url='$(ICON_SVG)', write_to='$(BRAND_DIR)/icon@2x.png', output_width=512, output_height=512)"
