from fastapi import FastAPI
from database import get_analysis_collection

app = FastAPI()

@app.get("/videos")
def list_videos():
    collection = get_analysis_collection()
    return list(collection.find({}, {"_id": 0, "video_id": 1}))

@app.get("/videos/{video_id}")
def get_video_analysis(video_id: str):
    collection = get_analysis_collection()
    result = collection.find_one({"video_id": video_id}, {"_id": 0})
    return result
