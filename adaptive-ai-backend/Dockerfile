FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
RUN useradd --create-home appuser && mkdir -p /srv/data && chown appuser /srv/data
USER appuser
ENV APP_ENV=production DATABASE_URL=sqlite:////srv/data/adaptive.db
EXPOSE 8000
# Secrets (GROQ_API_KEY, APP_API_KEYS) come from the environment, never from the image.
# One worker: the rate limiter is per-process. For several workers use a shared limiter.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
