#!/usr/bin/env bash
# Deploy the backend to a Hugging Face Docker Space.
#
# Prereqs (one time):
#   pip install -U huggingface_hub
#   export HF_TOKEN=hf_xxx        # a WRITE token from https://hf.co/settings/tokens
#
# Usage:
#   deploy/deploy_hf.sh [hf_username] [space_name]
set -euo pipefail

HF_USER="${1:-bhamdoesweirdstuff}"
SPACE="${2:-descale}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
: "${HF_TOKEN:?set HF_TOKEN to a Hugging Face write token (https://hf.co/settings/tokens)}"

python3 - "$HF_USER" "$SPACE" "$ROOT" <<'PY'
import os, sys, shutil, tempfile
from pathlib import Path
from huggingface_hub import HfApi, create_repo

user, space, root = sys.argv[1], sys.argv[2], Path(sys.argv[3])
token = os.environ["HF_TOKEN"]
repo_id = f"{user}/{space}"

create_repo(repo_id, repo_type="space", space_sdk="docker", exist_ok=True, token=token)
tmp = Path(tempfile.mkdtemp())
shutil.copy(root / "Dockerfile", tmp / "Dockerfile")
shutil.copy(root / ".dockerignore", tmp / ".dockerignore")
shutil.copy(root / "deploy/huggingface/README.md", tmp / "README.md")
shutil.copytree(root / "backend", tmp / "backend",
                ignore=shutil.ignore_patterns(".venv", "venv", "__pycache__",
                                              ".pytest_cache", "*.pyc", ".tmp_ocr"))
HfApi(token=token).upload_folder(folder_path=str(tmp), repo_id=repo_id,
                                 repo_type="space", commit_message="Deploy backend")
print(f"Deployed: https://huggingface.co/spaces/{repo_id}")
print(f"API:      https://{user}-{space}.hf.space/api/info")
PY
