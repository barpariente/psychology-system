FROM python:3.11-slim
WORKDIR /app
COPY libs/common /libs/common
RUN pip install --no-cache-dir /libs/common
COPY services/analyzer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/analyzer/analyzer ./analyzer
CMD ["python", "-m", "analyzer.main"]
