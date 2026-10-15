from common.config import load_settings
from common.log import setup_logging
from common.messaging import ANALYSIS_QUEUE, run_consumer
from common.pipeline import mark_failed_on_dead_letter
from common.sessions import SessionRepository
from common.storage import ObjectStorage

from analyzer.cache import AnalysisCache
from analyzer.handler import make_handler
from analyzer.llm import build_llm


def main() -> None:
    settings = load_settings()
    setup_logging("analyzer")
    repo = SessionRepository.from_settings(settings)
    storage = ObjectStorage.from_settings(settings)
    handler = make_handler(
        repo, storage, build_llm(settings), AnalysisCache.from_url(settings.redis_url)
    )
    run_consumer(
        settings.rabbitmq_url,
        ANALYSIS_QUEUE,
        handler,
        max_retries=settings.max_retries,
        on_dead_letter=mark_failed_on_dead_letter(repo),
    )


if __name__ == "__main__":
    main()
