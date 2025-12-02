import assemblyai as aai
from dotenv import load_dotenv
import os
from minio_client import download_audio, upload_transcript

load_dotenv()
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")


def process_audio_file(bucket: str, mp3_name: str) -> bytes:
    """
    Downloads MP3 from MinIO, sends it to AssemblyAI, 
    and returns transcript JSON (bytes).
    """

    print(f"Downloading audio from MinIO bucket '{bucket}' ...")
    local_mp3_path = download_audio(bucket, mp3_name)

    print(f"Downloaded to local file: {local_mp3_path}")
    print("Starting transcription...")

    config = aai.TranscriptionConfig(
        speaker_labels=True,
        speakers_expected=None
    )

    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(local_mp3_path, config=config)

    # Wait for AssemblyAI job to finish
    while transcript.status in ["queued", "processing"]:
        print(f"   Status = {transcript.status} ... waiting...")
        transcript = aai.Transcriber.get_by_id(transcript.id)

    if transcript.status == "error":
        raise Exception(f"AssemblyAI error: {transcript.error}")

    print("Transcription finished!")

    # Convert to bytes for uploading
    json_bytes = transcript.json().encode("utf-8")

    # Upload transcript to MinIO
    transcripts_bucket = "transcripts"
    transcript_filename = mp3_name + ".json"

    print(f"Uploading transcript to MinIO as {transcript_filename}...")
    upload_transcript(transcripts_bucket, transcript_filename, json_bytes)

    print("Transcript uploaded successfully!")

    return json_bytes
