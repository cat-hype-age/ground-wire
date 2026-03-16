#!/usr/bin/env bash
# Download the Sentient Arena CLI
# Requires authentication — log in at https://arena.sentient.xyz first,
# then grab the download URL or auth token from the portal.
#
# Manual download:
#   1. Log in at https://arena.sentient.xyz
#   2. Download the CLI from the portal
#   3. Move it to the project root: mv ~/Downloads/arena ./arena
#   4. Make it executable: chmod +x arena

set -euo pipefail

DEST="${1:-./arena}"
URL="https://arena.sentient.xyz/api/download/cli"

echo "Downloading Arena CLI to ${DEST}..."
if curl -fSL -o "${DEST}" "${URL}"; then
    chmod +x "${DEST}"
    echo "Done. Arena CLI installed at ${DEST}"
else
    echo "ERROR: Download failed (likely needs authentication)."
    echo "Log in at https://arena.sentient.xyz and download manually."
    exit 1
fi
