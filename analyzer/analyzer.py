from venv import logger
import json
from dotenv import load_dotenv
from analyzer.llm_client import analyze_emotion, classify_speaker_role
from minio_client import download_transcript
from redis_client import find_in_cache, store_in_cache

load_dotenv()

def analyze_transcript(bucket: str, transcript_name: str) -> None:
    """
    Downloads transcript JSON from MinIO, analyzes it using OpenAI,
    and uploads the analysis results back to MinIO.
    """

    print(f"Downloading transcript from MinIO bucket '{bucket}' ...")
    local_transcript_path = download_transcript(bucket, transcript_name)

    print(f"Downloaded to local file: {local_transcript_path}")
    print("Starting analysis...")

    with open(local_transcript_path, "r") as f:
        transcript = json.load(f)

    # classify patient vs therapist
    roles = classify_speaker_role(transcript)
    patient_speaker = roles["patient"]

    print(f"Identified patient speaker: {patient_speaker}")

    for u in transcript["utterances"]:
        speaker = u["speaker"]
        text = u["text"]

        # Only analyze patient sentences
        if speaker != patient_speaker:
            continue

        # Check Redis cache
        cached = find_in_cache(text)
        if cached:
            logger.info(f"[CACHE HIT] {text} → {cached}")
            continue
        analysis = analyze_emotion(text)

        logger.info(f"Utterance: {text}\nAnalysis: {analysis}")

        # Store in Redis cache
        store_in_cache(text, analysis)