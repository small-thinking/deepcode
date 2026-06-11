#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")/.."

if ! command -v uv >/dev/null 2>&1; then
  printf '%s\n' "uv is required to set up the DeepCode development environment."
  printf '%s\n' "Install uv from: https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
fi

export UV_CACHE_DIR="${UV_CACHE_DIR:-$PWD/.uv-cache}"

uv sync

printf '%s\n' "DeepCode environment is ready."
printf '%s\n' "Run the app with: uv run python -m deepcode --port 8000"
