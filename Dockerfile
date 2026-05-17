FROM node:22-alpine AS css-builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY static/css/input.css ./static/css/input.css
COPY templates/ ./templates/

RUN npm run build:css


FROM python:3.12-alpine

WORKDIR /app

RUN apk add --no-cache gcc musl-dev libffi-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .
COPY --from=css-builder /app/static/css/output.css ./static/css/output.css

RUN mkdir -p instance static/avatars

EXPOSE 8080

ENV FLASK_APP=app.py

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "wsgi:app"]
