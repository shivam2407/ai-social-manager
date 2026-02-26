# Stage 1: Build React frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
ARG VITE_GOOGLE_CLIENT_ID
ARG VITE_GITHUB_CLIENT_ID
ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID
ENV VITE_GITHUB_CLIENT_ID=$VITE_GITHUB_CLIENT_ID
RUN npm run build

# Stage 2: Python backend + built frontend
FROM python:3.11-slim
WORKDIR /app

# Install backend dependencies
COPY langgraph-api/pyproject.toml langgraph-api/
COPY langgraph-api/app/ langgraph-api/app/
RUN pip install --no-cache-dir ./langgraph-api

# Copy built frontend into the location the backend expects
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

WORKDIR /app/langgraph-api

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
