from database import save_analysis, save_video_metadata

def analyze_transcript(bucket, transcript_name):
    video_id = transcript_name.replace(".json", "")
    video_name = transcript_name

    save_video_metadata(video_id, video_name)

    analysis = {
        "video_id": video_id,
        "utterances": [...],
        "topics_summary": {...},
        "emotions_summary": {...},
    }

    save_analysis(video_id, analysis)
