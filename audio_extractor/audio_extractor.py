import subprocess
from minio_client import download_video, upload_audio

def extract_audio(video_path):
    mp3_path = video_path + ".mp3"

    command = [
        "ffmpeg",
        "-i", video_path,
        "-vn",
        "-acodec", "mp3",
        mp3_path
    ]

    subprocess.run(command, check=True)

    return mp3_path

def process_video_file(bucket, video_name):
    print(f"Downloading video from MinIO: {video_name}")

    local_video_path = download_video(bucket, video_name)

    print("Extracting audio...")
    mp3_path = extract_audio(local_video_path)

    with open(mp3_path, "rb") as f:
        mp3_bytes = f.read()

    audio_bucket = "audio-files"
    mp3_filename = video_name + ".mp3"

    upload_audio(audio_bucket, mp3_filename, mp3_bytes)

    print(f"Uploaded MP3 to MinIO: {mp3_filename}")

    # Optional: publish next event session_audio_ready
    # (needed for future stages)
