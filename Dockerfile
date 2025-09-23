# Dockerfile (at repo root)
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends libgl1 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir --upgrade pip && \
    if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; else \
      pip install --no-cache-dir fastapi uvicorn[standard] python-multipart pydantic openai; fi

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PORT=8080
# You can keep defaults; override at deploy time
ENV API_KEY=charlie305$ VD_MODEL=openai

EXPOSE 8080
CMD bash -lc "export PYTHONPATH=. && uvicorn api.app:app --host 0.0.0.0 --port ${PORT}"
