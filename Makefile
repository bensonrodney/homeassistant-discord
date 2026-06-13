PYTHON := .venv/bin/python
VENV   := .venv
SRC    := custom_components tests

.PHONY: help install lint format format-check typecheck test check fix

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
