from minio import Minio
import io

minio_client = Minio(
    "minio:9000",
    access_key="minio",
    secret_key="minio123",
    secure=False
)

def upload_file_to_minio(bucket_name: str, object_name: str, data_bytes: bytes, content_type: str):
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)

    minio_client.put_object(
        bucket_name,
        object_name,
        io.BytesIO(data_bytes),
        length=len(data_bytes),
        content_type=content_type
    )

    print(f"Uploaded {object_name} to bucket '{bucket_name}' in MinIO")
