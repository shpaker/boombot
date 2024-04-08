#!/usr/bin/env just --justfile

SOURCE_DIR := "chatushka"
TESTS_DIR := "tests"

lint: ruff mypy

mypy:
    poetry run python -m mypy --pretty --package {{ SOURCE_DIR }}

ruff:
    poetry run python -m ruff check --fix --unsafe-fixes {{ SOURCE_DIR }}

format:
    poetry run python -m ruff format {{ SOURCE_DIR }}
    poetry run python -m ruff format {{ TESTS_DIR }}

tests:
    poetry run python -m pytest {{ TESTS_DIR }}
