from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List
from database import analysis_collection, videos_collection

router = APIRouter(prefix="/videos", tags=["videos"])


def _strip_mongo_id(doc: Dict[str, Any]) -> Dict[str, Any]:
    if "_id" in doc:
        doc = dict(doc)
        doc["_id"] = str(doc["_id"])
    return doc


@router.get("/", summary="List analyzed videos")
def list_videos() -> Dict[str, List[Dict[str, Any]]]:
    videos = list(videos_collection.find({}, {"_id": 1, "video_id": 1, "video_name": 1, "customer": 1}))
    if videos:
        return {"videos": [_strip_mongo_id(v) for v in videos]}

    pipeline = [
        {"$group": {"_id": "$video_id", "video_name": {"$first": "$video_name"}, "customer": {"$first": "$customer"}}},
        {"$sort": {"_id": 1}},
    ]
    derived = list(analysis_collection.aggregate(pipeline))
    for d in derived:
        d["video_id"] = d.pop("_id")
    return {"videos": derived}


@router.get("/{video_id}", summary="Get full analysis for a video")
def get_video_analysis(video_id: str) -> Dict[str, Any]:
    doc = analysis_collection.find_one({"video_id": video_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Video analysis not found")
    return doc
