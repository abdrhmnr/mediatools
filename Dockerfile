FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    tesseract-ocr \
    tesseract-ocr-ara \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libheif-dev \
    imagemagick \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Create directories
RUN mkdir -p static/uploads static/outputs

# Expose port
EXPOSE 5000

# Run with gunicorn for production
RUN pip install gunicorn

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "600", "--max-requests", "100", "app:app"]
