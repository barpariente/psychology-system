import fakeredis
import redis
from analyzer.analysis import analyze_utterances, normalize_result
from analyzer.cache import AnalysisCache

UTTERANCES = [
    {"speaker": "A", "text": "How are you?"},
    {"speaker": "B", "text": "My mother makes me anxious."},
    {"speaker": "B", "text": "My mother makes me anxious."},
    {"speaker": "B", "text": "Work is going great."},
]


class ScriptedLLM:
    def __init__(self, patient="B"):
        self.patient = patient
        self.calls = []

    def identify_patient(self, utterances):
        return self.patient

    def analyze_sentence(self, text):
        self.calls.append(text)
        if "mother" in text:
            return {"topic": "Family", "emotion": "Anxiety", "valence": "NEGATIVE",
                    "explanation": "conflict"}
        return {"topic": "work", "emotion": "pride", "valence": "very good", "explanation": ""}


class BrokenRedis:
    def get(self, key):
        raise redis.ConnectionError("down")

    def set(self, key, value, ex=None):
        raise redis.ConnectionError("down")


def cache():
    return AnalysisCache(fakeredis.FakeRedis(decode_responses=True))


def test_only_patient_utterances_are_analyzed_and_summarized():
    result = analyze_utterances(UTTERANCES, ScriptedLLM(), cache())
    assert result["patient_speaker"] == "B"
    assert [u["text"] for u in result["utterances"]] == [u["text"] for u in UTTERANCES[1:]]
    assert result["topics_summary"] == {"family": 2, "work": 1}
    assert result["valence_summary"] == {"negative": 2, "neutral": 1}


def test_repeated_sentence_hits_cache():
    llm = ScriptedLLM()
    analyze_utterances(UTTERANCES, llm, cache())
    assert llm.calls == ["My mother makes me anxious.", "Work is going great."]


def test_unknown_patient_label_falls_back_to_most_words():
    result = analyze_utterances(UTTERANCES, ScriptedLLM(patient="Patient"), cache())
    assert result["patient_speaker"] == "B"


def test_empty_transcript():
    result = analyze_utterances([], ScriptedLLM(), cache())
    assert result == {
        "patient_speaker": None,
        "utterances": [],
        "topics_summary": {},
        "emotions_summary": {},
        "valence_summary": {},
    }


def test_redis_down_still_analyzes():
    result = analyze_utterances(UTTERANCES, ScriptedLLM(), AnalysisCache(BrokenRedis()))
    assert len(result["utterances"]) == 3


def test_normalize_result_cleans_values():
    assert normalize_result({"topic": " Work ", "emotion": None, "valence": "Positive"}) == {
        "topic": "work",
        "emotion": "unknown",
        "valence": "positive",
        "explanation": "",
    }
