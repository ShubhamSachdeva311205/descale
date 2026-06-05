# Backend image for a Hugging Face Docker Space (or any container host).
# Serves the Descale FastAPI API on port 7860 (the HF Spaces default).
FROM python:3.12-slim

# tesseract powers the OCR attack-success check
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend ./backend

ENV PORT=7860
EXPOSE 7860

# allow the GitHub Pages origin to call this API (override at deploy time)
ENV DESCALE_ALLOWED_ORIGINS="https://shubhamsachdeva311205.github.io"

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}"]
