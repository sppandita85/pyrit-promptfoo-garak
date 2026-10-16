#!/usr/bin/env bash
# Record every TCP connection opened by node (promptfoo) processes until Ctrl+C,
# then print the distinct remote endpoints. Run it in a second terminal during run.sh.
# Expect only 127.0.0.1 / ::1 (ports 8001 = RAG API, 11434 = Ollama).
LOG="${1:-/tmp/promptfoo-connections.log}"
: > "$LOG"
trap 'echo; echo "Distinct remote endpoints seen:"; sort -u "$LOG"; exit 0' INT TERM
echo "Watching node TCP connections (Ctrl+C to stop)..."
while true; do
  lsof -nP -a -c node -iTCP 2>/dev/null | awk 'NR>1 && /->/ {split($9,a,"->"); print a[2]}' >> "$LOG"
  sleep 0.2
done
