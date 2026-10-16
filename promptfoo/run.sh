#!/usr/bin/env bash
# Run the Promptfoo evals and red team against the bank RAG API,
# first with guardrails OFF and then ON, and save results separately.
#
# Usage (from anywhere; the API must be running on :8001):
#   ./promptfoo/run.sh              # evals + red team
#   ./promptfoo/run.sh evals        # evals only
#   ./promptfoo/run.sh redteam      # red team only (reuses redteam-tests.yaml)
#   ./promptfoo/run.sh redteam --regenerate   # generate new attacks first
#
# Results:  promptfoo/results/{evals,redteam}-{off,on}.{json,html}
# Browse:   ./promptfoo/view.sh   (promptfoo view on http://localhost:15500)
set -uo pipefail
cd "$(dirname "$0")"

WHAT="${1:-all}"
REGENERATE="${2:-}"

# ---- keep everything on this machine ----------------------------------------
export PROMPTFOO_DISABLE_TELEMETRY=1            # no usage telemetry
export PROMPTFOO_DISABLE_UPDATE=1               # no "new version" check
export PROMPTFOO_DISABLE_REMOTE_GENERATION=true # no hosted attack generation / grading
export PROMPTFOO_DISABLE_SHARING=1              # no share links
export PROMPTFOO_CONFIG_DIR="$PWD/.promptfoo"   # results DB lives in this folder

# Every promptfoo command runs inside a macOS sandbox that blocks all outbound
# network traffic except localhost (see localhost-only.sb).
promptfoo() {
  sandbox-exec -f localhost-only.sb npx --no-install promptfoo "$@"
}

if ! curl -sf http://localhost:8001/health >/dev/null; then
  echo "The RAG API is not running. Start it first:  uvicorn api:app --port 8001"
  exit 1
fi
mkdir -p results

run_evals() {
  for mode in off on; do
    echo; echo "=== Evals, guardrails $mode ==="
    GUARDRAILS_MODE=$mode promptfoo eval -c promptfooconfig.yaml --no-cache --no-table \
      --no-progress-bar --description "Evals - guardrails $mode" \
      -o "results/evals-$mode.json" "results/evals-$mode.html"
  done
}

run_redteam() {
  if [[ ! -f redteam-tests.yaml || "$REGENERATE" == "--regenerate" ]]; then
    echo; echo "=== Generating red team attacks with local Ollama ==="
    promptfoo redteam generate -c redteamconfig.yaml -o redteam-tests.yaml --force \
      --no-progress-bar || exit 1
  fi
  for mode in off on; do
    echo; echo "=== Red team, guardrails $mode ==="
    GUARDRAILS_MODE=$mode promptfoo eval -c redteam-tests.yaml --no-cache --no-table \
      --no-progress-bar --description "Red team - guardrails $mode" \
      -o "results/redteam-$mode.json" "results/redteam-$mode.html"
  done
}

# promptfoo exits non-zero when tests fail; that is expected here, so we carry on.
case "$WHAT" in
  evals)   run_evals ;;
  redteam) run_redteam ;;
  all)     run_evals; run_redteam ;;
  *)       echo "unknown option: $WHAT (use evals | redteam | all)"; exit 1 ;;
esac

echo
python3 summary.py
