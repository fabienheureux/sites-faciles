#!/usr/bin/env bash
set -euo pipefail

# Configuration
CONFIG_FILE="${SYNC_CONFIG_FILE:-sync-config.txt}"
TEMP_DIR="sites_faciles_temp"
TARGET_DIR="sites_faciles"

# Read version/tag from config file
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Error: Config file '$CONFIG_FILE' not found" >&2
    echo "Please create it with the tag/version to sync (e.g., 'v2.1.0')" >&2
    exit 1
fi

# Read first non-empty line, trimming whitespace
TAG=$(grep -v '^[[:space:]]*$' "$CONFIG_FILE" | head -n1 | xargs)

if [[ -z "$TAG" ]]; then
    echo "Error: No tag specified in '$CONFIG_FILE'" >&2
    exit 1
fi

echo "Syncing sites-faciles from tag: $TAG"

# Clone fresh repo
git clone --quiet -c advice.detachedHead=false --branch "$TAG" --depth 1 \
    git@github.com:numerique-gouv/sites-faciles.git "$TEMP_DIR"

cd "$TEMP_DIR"

# Run refactor
../packagify.py -v

# Cleanup
cd ..
rm -rf "$TARGET_DIR"
mv "$TEMP_DIR" "$TARGET_DIR"
rm -rf "${TARGET_DIR}/.git" \
    "${TARGET_DIR}/.github" \
    "${TARGET_DIR}/pyproject.toml"

git restore --source=fork/main "**/apps.py"
git restore --source=fork/main "**/__init__.py"

echo "Sync completed successfully!"
