AGENT_DIR="example-scratch/agents-original/test"
RUN_LOG="/tmp/kinnoo-run-py312.log"

# 1) Verify Python 3.12 is available
if ! command -v python3.12 >/dev/null 2>&1; then
  echo "python3.12 not found in PATH"
  exit 1
fi
python3.12 --version

# 2) Recreate the agent venv with Python 3.12
rm -rf "$AGENT_DIR/.venv"
python3.12 -m venv "$AGENT_DIR/.venv"

# 3) Install requirements into that 3.12 venv
"$AGENT_DIR/.venv/bin/python" -m pip install --upgrade pip
"$AGENT_DIR/.venv/bin/pip" install -r "$AGENT_DIR/requirements.txt"

# 4) Confirm venv interpreter version
"$AGENT_DIR/.venv/bin/python" --version

# 5) Run via local source CLI (ensures you use this repo's current code)
python3 src/kinnoo/cli.py run "$AGENT_DIR" "what is 2+2?" 2>&1 | tee "$RUN_LOG"

# 6) Check whether that warning is still present
if grep -Fq "Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater." "$RUN_LOG"; then
  echo "RESULT: warning still present"
else
  echo "RESULT: warning disappeared"
fi
