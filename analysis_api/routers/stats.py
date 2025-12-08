from fastapi import APIRouter
from typing import Any, Dict, List
from database import analysis_collection

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/topics", summary="Aggregate topics across all analyzed videos")
def topics_stats() -> Dict[str, List[Dict[str, Any]]]:
    pipeline = [
        {"$unwind": "$utterances"},
        {"$group": {"_id": "$utterances.topic", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    results = list(analysis_collection.aggregate(pipeline))
    topics = [{"topic": r["_id"], "count": r["count"]} for r in results if r["_id"] is not None]
    return {"topics": topics}


@router.get("/emotions", summary="Aggregate emotions across all analyzed videos")
def emotions_stats() -> Dict[str, List[Dict[str, Any]]]:
    pipeline = [
        {"$unwind": "$utterances"},
        {"$group": {"_id": "$utterances.emotion", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    results = list(analysis_collection.aggregate(pipeline))
    emotions = [{"emotion": r["_id"], "count": r["count"]} for r in results if r["_id"] is not None]
    return {"emotions": emotions}
