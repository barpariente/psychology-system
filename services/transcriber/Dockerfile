FROM python:3.11-slim
WORKDIR /app
COPY libs/common /libs/common
RUN pip install --no-cache-dir /libs/common
COPY services/transcriber/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/transcriber/transcriber ./transcriber
CMD ["python", "-m", "transcriber.main"]
