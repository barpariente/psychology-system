from fastapi import FastAPI, UploadFile, File
from minio_client import upload_file_to_minio
from rabbitmq_publisher import publish_uploaded_event
from constants import BUCKET_NAME

app = FastAPI()


@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    contents = await file.read()

    upload_file_to_minio(
        bucket_name=BUCKET_NAME,
        object_name=file.filename,
        data_bytes=contents,
        content_type=file.content_type
    )

    publish_uploaded_event(
        bucket=BUCKET_NAME,
        object_name=file.filename
    )

    return {
        "status": "success",
        "file": file.filename,
        "message": "File uploaded and event sent"
    }
