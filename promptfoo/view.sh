#!/usr/bin/env bash
# Open the Promptfoo results viewer (local web UI) on http://localhost:15500
cd "$(dirname "$0")"
export PROMPTFOO_DISABLE_TELEMETRY=1 PROMPTFOO_DISABLE_UPDATE=1 \
       PROMPTFOO_DISABLE_REMOTE_GENERATION=true PROMPTFOO_DISABLE_SHARING=1 \
       PROMPTFOO_CONFIG_DIR="$PWD/.promptfoo"
sandbox-exec -f localhost-only.sb npx --no-install promptfoo view --yes "$@"
