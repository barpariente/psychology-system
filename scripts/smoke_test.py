"""Uploads samples/sample_session.mp4 to a running stack and waits until it is ANALYZED."""

import sys
import time
from pathlib import Path

import httpx

API = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
SAMPLE = Path(__file__).resolve().parent.parent / "samples" / "sample_session.mp4"
TIMEOUT_SECONDS = 180


def main() -> None:
    with SAMPLE.open("rb") as video:
        response = httpx.post(
            f"{API}/sessions",
            files={"file": (SAMPLE.name, video, "video/mp4")},
            timeout=30,
        )
    response.raise_for_status()
    session_id = response.json()["session_id"]
    print(f"Uploaded session {session_id}")

    deadline = time.monotonic() + TIMEOUT_SECONDS
    status = None
    while time.monotonic() < deadline:
        session = httpx.get(f"{API}/sessions/{session_id}", timeout=10).json()
        if session["status"] != status:
            status = session["status"]
            print(f"  status: {status}")
        if status == "ANALYZED":
            break
        if status == "FAILED":
            sys.exit(f"Pipeline failed: {session['error']}")
        time.sleep(2)
    else:
        sys.exit(f"Timed out after {TIMEOUT_SECONDS}s at status {status}")

    analysis = httpx.get(f"{API}/sessions/{session_id}/analysis", timeout=10).json()
    if not analysis["utterances"]:
        sys.exit("Analysis has no utterances")
    print(f"OK: topics={analysis['topics_summary']} emotions={analysis['emotions_summary']}")


if __name__ == "__main__":
    main()
