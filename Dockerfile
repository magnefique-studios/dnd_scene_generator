FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
RUN pip3 install --no-cache-dir --upgrade pip
RUN pip3 install --no-cache-dir \
    flask \
    pillow \
    torch==2.0.1+cu118 \
    torchvision==0.15.2+cu118 \
    --extra-index-url https://download.pytorch.org/whl/cu118
RUN pip3 install --no-cache-dir \
    diffusers==0.21.4 \
    transformers \
    accelerate \
    xformers==0.0.20

# Copy application code
COPY . .

# Create static directory
RUN mkdir -p static

# Expose port
EXPOSE 7860

# Run the application
CMD ["python3", "app_tiles.py"]