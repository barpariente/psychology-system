from fastapi import APIRouter, Depends

from api import deps

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/topics", summary="Topic counts across all analyzed sessions")
def topics(repo=Depends(deps.get_repository)):
    return {"topics": repo.count_by("topic")}


@router.get("/emotions", summary="Emotion counts across all analyzed sessions")
def emotions(repo=Depends(deps.get_repository)):
    return {"emotions": repo.count_by("emotion")}
