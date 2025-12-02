# Use a lightweight Python base image
FROM python:3.11-slim

# Install FFmpeg for audio extraction
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first (better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire transcriber service code
COPY . .

# Expose port (optional, if you run a health-check server)
EXPOSE 8001

# Run the RabbitMQ consumer when container starts
CMD ["python", "main.py"]
