from common.log import setup_logging
from fastapi import FastAPI

from api.routers import sessions, stats


def create_app() -> FastAPI:
    app = FastAPI(
        title="Psychology Session Analysis API",
        description="Upload therapy-session videos and read their analysis.",
        version="2.0.0",
    )
    app.include_router(sessions.router)
    app.include_router(stats.router)

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok"}

    return app


setup_logging("api")
app = create_app()
