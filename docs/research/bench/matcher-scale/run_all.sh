#!/usr/bin/env bash
# Reproduce every number in docs/research/matcher-scale-in-python.md.
#
#   cd docs/research/bench/matcher-scale
#   python3.11 -m venv .venv && .venv/bin/pip install fastapi uvicorn numpy orjson psutil
#   make -C native
#   PY=.venv/bin/python ./run_all.sh > results.md
#
# Takes about fifteen minutes and wants the machine otherwise idle.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PY:-python3}"

echo "# Captured run"
echo
echo '```'
"$PY" - <<'EOF'
import os, platform, sys
print("python   :", sys.version.replace("\n", " "))
print("platform :", platform.platform())
print("machine  :", os.uname().machine)
EOF
uname -a
if command -v sysctl >/dev/null; then
  sysctl -n machdep.cpu.brand_string hw.ncpu hw.memsize 2>/dev/null || true
fi
echo '```'
echo

for b in scan_bench terms_bench doubles_bench memory_bench fork_bench \
         port_bench rebuild_bench lowend_bench loop_bench gc_bench \
         saturation_bench; do
  echo
  echo "---"
  echo
  "$PY" "$b.py"
done
