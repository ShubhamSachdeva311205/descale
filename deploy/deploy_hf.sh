#!/usr/bin/env bash
# Push the Descale backend to a Hugging Face Docker Space.
#
# Prereqs (one time):
#   pip install -U huggingface_hub
#   huggingface-cli login          # paste a WRITE token from hf.co/settings/tokens
#
# Usage:
#   deploy/deploy_hf.sh [hf_username] [space_name]
set -euo pipefail

HF_USER="${1:-bhamdoesweirdstuff}"
SPACE="${2:-descale}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d)"

echo "Creating/locating Space ${HF_USER}/${SPACE} ..."
huggingface-cli repo create "${SPACE}" --type space --space_sdk docker -y >/dev/null 2>&1 || true

echo "Cloning Space repo ..."
git clone "https://huggingface.co/spaces/${HF_USER}/${SPACE}" "${WORK}"

# Copy only what the backend needs.
cp "${REPO_ROOT}/Dockerfile" "${WORK}/Dockerfile"
cp "${REPO_ROOT}/.dockerignore" "${WORK}/.dockerignore"
cp "${REPO_ROOT}/deploy/huggingface/README.md" "${WORK}/README.md"
rm -rf "${WORK}/backend"
cp -R "${REPO_ROOT}/backend" "${WORK}/backend"
find "${WORK}/backend" -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
rm -rf "${WORK}/backend/.venv" "${WORK}/backend/.tmp_ocr"

cd "${WORK}"
git add -A
git -c user.email="shubhamsachdeva245@gmail.com" -c user.name="Shubham Sachdeva" \
    commit -m "Deploy Descale backend" >/dev/null 2>&1 || { echo "Nothing to deploy."; exit 0; }
git push

echo "Done. Space: https://huggingface.co/spaces/${HF_USER}/${SPACE}"
echo "API will be live at: https://${HF_USER}-${SPACE}.hf.space/api/info"
