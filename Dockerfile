# Stage 1: Builder
FROM node:18-alpine AS builder

WORKDIR /app/frontend

# Copy package files and install dependencies
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy the rest of the frontend and build
COPY frontend/ ./
RUN npm run build

# Stage 2: Runner
FROM python:3.9-slim AS runner

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory to /app/backend
WORKDIR /app/backend

# Install backend dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./

# Copy core and binance_klines to /app (maintaining relative structure)
# The backend expects core/ and binance_klines/ to be siblings of backend/
COPY core/ /app/core/
COPY binance_klines/ /app/binance_klines/

# Copy built frontend from builder stage
COPY --from=builder /app/frontend/dist /app/frontend/dist

# Expose port 8000
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
