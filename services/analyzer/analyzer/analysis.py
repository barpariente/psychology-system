from collections import Counter

from analyzer.llm import speaker_with_most_words

VALENCES = {"positive", "negative", "neutral"}


def _clean(value, default: str) -> str:
    text = str(value or "").strip().lower()
    return text or default


def normalize_result(raw: dict) -> dict:
    valence = _clean(raw.get("valence"), "neutral")
    return {
        "topic": _clean(raw.get("topic"), "unknown"),
        "emotion": _clean(raw.get("emotion"), "unknown"),
        "valence": valence if valence in VALENCES else "neutral",
        "explanation": str(raw.get("explanation") or ""),
    }


def analyze_utterances(utterances: list[dict], llm, cache) -> dict:
    if not utterances:
        return {
            "patient_speaker": None,
            "utterances": [],
            "topics_summary": {},
            "emotions_summary": {},
            "valence_summary": {},
        }

    speakers = {u["speaker"] for u in utterances}
    patient = llm.identify_patient(utterances)
    if patient not in speakers:
        patient = speaker_with_most_words(utterances)

    analyzed = []
    for utterance in utterances:
        if utterance["speaker"] != patient:
            continue
        result = cache.get(utterance["text"])
        if result is None:
            result = normalize_result(llm.analyze_sentence(utterance["text"]))
            cache.set(utterance["text"], result)
        analyzed.append({**utterance, **result})

    return {
        "patient_speaker": patient,
        "utterances": analyzed,
        "topics_summary": dict(Counter(u["topic"] for u in analyzed)),
        "emotions_summary": dict(Counter(u["emotion"] for u in analyzed)),
        "valence_summary": dict(Counter(u["valence"] for u in analyzed)),
    }
