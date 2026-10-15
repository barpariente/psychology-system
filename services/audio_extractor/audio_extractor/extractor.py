import subprocess
from pathlib import Path


def extract_audio(video_path: Path, audio_path: Path) -> None:
    """Writes a mono 16 kHz MP3 of the video's audio track. Fails if there is no audio stream."""
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", str(video_path),
            "-vn", "-ac", "1", "-ar", "16000", "-acodec", "libmp3lame",
            str(audio_path),
        ],
        check=True,
        capture_output=True,
    )
