FROM python:3.11-slim
WORKDIR /app
COPY libs/common /libs/common
RUN pip install --no-cache-dir /libs/common
COPY services/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/api/api ./api
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
