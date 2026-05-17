# syntax=docker/dockerfile:1.6

# ---------- CSS build stage ----------
FROM node:22-alpine AS css-builder

WORKDIR /app

RUN echo "==> [css] installing node dependencies"
COPY package*.json ./
RUN npm ci --no-audit --no-fund

RUN echo "==> [css] copying tailwind sources"
COPY static/css/input.css ./static/css/input.css
COPY templates/ ./templates/

RUN echo "==> [css] building tailwind output.css" \
 && npm run build:css \
 && echo "==> [css] done ($(wc -c < ./static/css/output.css) bytes)"


# ---------- Python runtime stage ----------
FROM python:3.12-alpine

WORKDIR /app

# Unbuffered stdout/stderr so Coolify (and `docker logs`) sees output in real
# time instead of waiting for Python to flush a 4KB block.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN echo "==> [py] installing build deps" \
 && apk add --no-cache gcc musl-dev libffi-dev curl

RUN echo "==> [py] installing python dependencies"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn \
 && echo "==> [py] python deps installed"

RUN echo "==> [app] copying application source"
COPY . .
COPY --from=css-builder /app/static/css/output.css ./static/css/output.css

RUN mkdir -p instance static/avatars \
 && echo "==> [app] runtime dirs ready" \
 && echo "==> [app] image build complete"

EXPOSE 8080

ENV FLASK_APP=app.py \
    GUNICORN_WORKERS=2 \
    GUNICORN_THREADS=4 \
    GUNICORN_TIMEOUT=60

# gthread worker class lets each worker handle multiple concurrent requests
# (important when one slow iCal fetch would otherwise pin an entire sync
# worker). Access + error logs go to stdout/stderr so Coolify captures them.
CMD ["sh", "-c", "exec gunicorn \
  --bind 0.0.0.0:8080 \
  --worker-class gthread \
  --workers ${GUNICORN_WORKERS} \
  --threads ${GUNICORN_THREADS} \
  --timeout ${GUNICORN_TIMEOUT} \
  --graceful-timeout 30 \
  --keep-alive 5 \
  --forwarded-allow-ips='*' \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  --access-logformat '%(h)s xff=%({X-Forwarded-For}i)s xri=%({X-Real-IP}i)s xfp=%({X-Forwarded-Proto}i)s \"%(r)s\" %(s)s %(b)s %(L)ss \"%(f)s\" \"%(a)s\"' \
  wsgi:app"]
