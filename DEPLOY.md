# Deploying Descale

Descale is split for free hosting: the **React frontend** goes on **GitHub
Pages** (static), and the **FastAPI backend** runs in a **Hugging Face Docker
Space** (it needs Python). The VLM model-eval (`eval/`) is local-only.

```
 GitHub Pages (UI)  ───calls───▶  Hugging Face Space (API)
 ShubhamSachdeva311205.github.io/descale     bhamdoesweirdstuff-descale.hf.space
```

## 1. Backend → Hugging Face Space

One time:

```bash
pip install -U huggingface_hub
export HF_TOKEN=hf_xxx        # a WRITE token from https://hf.co/settings/tokens
```

Deploy (creates the Space if missing, uploads the backend + Dockerfile):

```bash
deploy/deploy_hf.sh bhamdoesweirdstuff descale
```

When the build finishes, confirm: `https://bhamdoesweirdstuff-descale.hf.space/api/info`.

> The Dockerfile sets `DESCALE_ALLOWED_ORIGINS` so the API accepts requests from
> the Pages site. Adjust it in the Space's settings if your Pages URL differs.

## 2. Frontend → GitHub Pages

The workflow `.github/workflows/deploy-pages.yml` builds the frontend with the
Space URL baked in and publishes to Pages on every push to `main`.

Enable Pages once (Settings → Pages → Source = **GitHub Actions**), or:

```bash
gh api -X POST repos/ShubhamSachdeva311205/descale/pages \
  -f build_type=workflow >/dev/null 2>&1 || true
gh workflow run deploy-pages.yml
```

Site: `https://shubhamsachdeva311205.github.io/descale/`.

If you rename the Space or use a different HF username, update `VITE_API_URL` in
the workflow and `DESCALE_ALLOWED_ORIGINS` in the Dockerfile.
