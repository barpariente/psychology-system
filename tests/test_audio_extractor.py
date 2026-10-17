import shutil
import subprocess

import pytest
from audio_extractor.extractor import extract_audio
from audio_extractor.handler import make_handler
from common.messaging import PermanentError
from common.sessions import SessionStatus


def fake_ffmpeg(video_path, audio_path):
    audio_path.write_bytes(b"mp3:" + video_path.read_bytes())


def must_not_run(video_path, audio_path):
    raise AssertionError("ffmpeg should not run")


def test_extracts_audio_and_advances(repo, storage, published):
    session_id = repo.create("a.mp4")
    storage.objects[("videos", session_id)] = b"video"
    make_handler(repo, storage, run_ffmpeg=fake_ffmpeg)({"session_id": session_id}, published)
    assert storage.objects[("audio", f"{session_id}.mp3")] == b"mp3:video"
    assert repo.get(session_id)["status"] == "AUDIO_EXTRACTED"
    assert published.events == [("session.audio_extracted", {"session_id": session_id})]


def test_duplicate_after_finish_republishes_without_work(repo, storage, published):
    session_id = repo.create("a.mp4")
    repo.advance(session_id, SessionStatus.UPLOADED, SessionStatus.AUDIO_EXTRACTED)
    make_handler(repo, storage, run_ffmpeg=must_not_run)({"session_id": session_id}, published)
    assert published.events == [("session.audio_extracted", {"session_id": session_id})]


def test_duplicate_for_later_stage_is_skipped(repo, storage, published):
    session_id = repo.create("a.mp4")
    repo.mark_failed(session_id, "boom")
    make_handler(repo, storage, run_ffmpeg=must_not_run)({"session_id": session_id}, published)
    assert published.events == []


def test_ffmpeg_failure_is_permanent(repo, storage, published):
    session_id = repo.create("a.mp4")
    storage.objects[("videos", session_id)] = b"video"

    def no_audio_stream(video_path, audio_path):
        raise subprocess.CalledProcessError(1, "ffmpeg")

    with pytest.raises(PermanentError):
        handler = make_handler(repo, storage, run_ffmpeg=no_audio_stream)
        handler({"session_id": session_id}, published)
    assert published.events == []


needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")


def _make_video(path, with_audio):
    inputs = ["-f", "lavfi", "-i", "color=c=black:s=64x64:d=1"]
    if with_audio:
        inputs += ["-f", "lavfi", "-i", "sine=frequency=440:duration=1"]
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-shortest", str(path)], check=True
    )


@needs_ffmpeg
def test_real_ffmpeg_extracts_mp3(tmp_path):
    video = tmp_path / "in.mp4"
    _make_video(video, with_audio=True)
    extract_audio(video, tmp_path / "out.mp3")
    assert (tmp_path / "out.mp3").stat().st_size > 0


@needs_ffmpeg
def test_real_ffmpeg_fails_on_video_without_audio(tmp_path):
    video = tmp_path / "silent.mp4"
    _make_video(video, with_audio=False)
    with pytest.raises(subprocess.CalledProcessError):
        extract_audio(video, tmp_path / "out.mp3")
