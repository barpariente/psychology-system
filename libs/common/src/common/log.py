import logging


def setup_logging(service: str) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format=f"%(asctime)s [{service}] %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger("pika").setLevel(logging.WARNING)
