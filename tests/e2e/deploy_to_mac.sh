#!/usr/bin/env bash
# Deploy vom Linux-Rechner auf den Dev-Test-Mac (GitHub dort SNI-geblockt -> rsync).
# Nutzt den SSH-Helper ~/.config/pyro-mac/ (Tailscale, askpass).
set -euo pipefail

HELPER_DIR="$HOME/.config/pyro-mac"
MAC_SSH="$HELPER_DIR/mac-ssh.sh"
MAC_HOST="sk@100.93.94.0"
REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
REMOTE_DIR="whisper-key-local"

export SSH_ASKPASS="$HELPER_DIR/mac-askpass.sh" SSH_ASKPASS_REQUIRE=force DISPLAY=:0
setsid -w rsync -az --delete \
    --exclude '.git' --exclude '.venv' --exclude '__pycache__' --exclude '*.pyc' \
    -e "ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=12" \
    "$REPO_DIR/" "$MAC_HOST:$REMOTE_DIR/"

"$MAC_SSH" "export PATH=/opt/homebrew/bin:\$PATH && cd $REMOTE_DIR && \
    (test -d .venv || uv venv --python 3.12 .venv) && \
    VIRTUAL_ENV=\$PWD/.venv uv pip install -q -e . && \
    .venv/bin/python -c 'import whisper_key; print(\"import ok\")'"
