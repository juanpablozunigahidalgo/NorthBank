# Build UI + API into one free container (Render free tier)
FROM node:20-alpine AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
# Same-origin API: leave VITE_API_URL empty so the UI calls /api on this host
ENV VITE_API_URL=
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY --from=frontend /fe/dist ./static
ENV PORT=8000
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
