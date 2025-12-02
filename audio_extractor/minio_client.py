from minio import Minio

minio_client = Minio(
    "minio:9000",
    access_key="minio",
    secret_key="minio123",
    secure=False
)

def download_video(bucket, filename):
    local_path = f"/tmp/{filename}"

    response = minio_client.get_object(bucket, filename)

    with open(local_path, "wb") as f:
        for chunk in response.stream(32 * 1024):
            f.write(chunk)

    return local_path

def upload_audio(bucket, filename, bytes_data):
    import io
    minio_client.put_object(
        bucket,
        filename,
        io.BytesIO(bytes_data),
        length=len(bytes_data),
        content_type="audio/mpeg"
    )
