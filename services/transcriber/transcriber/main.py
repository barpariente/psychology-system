from common.config import load_settings
from common.log import setup_logging
from common.messaging import TRANSCRIPTION_QUEUE, run_consumer
from common.pipeline import mark_failed_on_dead_letter
from common.sessions import SessionRepository
from common.storage import ObjectStorage

from transcriber.engines import build_transcriber
from transcriber.handler import make_handler


def main() -> None:
    settings = load_settings()
    setup_logging("transcriber")
    repo = SessionRepository.from_settings(settings)
    storage = ObjectStorage.from_settings(settings)
    run_consumer(
        settings.rabbitmq_url,
        TRANSCRIPTION_QUEUE,
        make_handler(repo, storage, build_transcriber(settings)),
        max_retries=settings.max_retries,
        on_dead_letter=mark_failed_on_dead_letter(repo),
    )


if __name__ == "__main__":
    main()
