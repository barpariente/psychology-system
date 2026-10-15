FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY libs/common /libs/common
RUN pip install --no-cache-dir /libs/common
COPY services/audio_extractor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/audio_extractor/audio_extractor ./audio_extractor
CMD ["python", "-m", "audio_extractor.main"]
