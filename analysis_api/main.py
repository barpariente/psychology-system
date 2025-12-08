from fastapi import FastAPI
from routers import videos, stats

app = FastAPI(
    title="Psychology Session Analysis API",
    description="Read-only API for listing and inspecting analyzed therapy session videos.",
    version="1.0.0",
)


@app.get("/health", tags=["health"], summary="Health check")
def health():
    return {"status": "ok"}

app.include_router(videos.router)
app.include_router(stats.router)
