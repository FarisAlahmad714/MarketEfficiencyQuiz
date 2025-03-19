FROM python:3.10-slim

WORKDIR /app

# Install system dependencies required by OpenCV and Tesseract
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Install numpy first
RUN pip install numpy==1.24.0

# Then install the rest of requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . .

# Set environment variables
ENV PORT=8080

# Run the application
CMD gunicorn --bind 0.0.0.0:$PORT app:app