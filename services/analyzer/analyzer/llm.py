import json
from collections import Counter
from typing import Protocol

from common.config import Settings

SPEAKER_PROMPT = """You are analyzing a transcript of a psychology therapy session.
Speakers are labelled (for example "A" and "B"). Decide which speaker is the THERAPIST
and which is the PATIENT. The therapist asks guiding questions and reflects; the patient
talks about personal issues, feelings and experiences.

Respond with JSON only: {"therapist": "<label>", "patient": "<label>", "reasoning": "<short>"}

Transcript:
{{TRANSCRIPT}}"""

SENTENCE_PROMPT = """You are analyzing one sentence a patient said in a therapy session.
Identify the main topic (for example: family, work, school, relationships, self-esteem),
the emotion expressed, and its valence (positive, negative or neutral).

Respond with JSON only:
{"topic": "<one or two words>", "emotion": "<one word>",
 "valence": "positive|negative|neutral", "explanation": "<one sentence>"}

Sentence: "{{TEXT}}" """


class LLMClient(Protocol):
    def identify_patient(self, utterances: list[dict]) -> str: ...

    def analyze_sentence(self, text: str) -> dict: ...


def speaker_with_most_words(utterances: list[dict]) -> str:
    words = Counter()
    for utterance in utterances:
        words[utterance["speaker"]] += len(utterance["text"].split())
    return words.most_common(1)[0][0]


class OpenAIClient:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def _ask_json(self, prompt: str) -> dict:
        response = self._client.chat.completions.create(
            model=self._model,
            response_format={"type": "json_object"},
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        return json.loads(response.choices[0].message.content)

    def identify_patient(self, utterances: list[dict]) -> str:
        """Returns "" when the model's answer is unusable; the caller then falls back."""
        transcript = "\n".join(f'{u["speaker"]}: {u["text"]}' for u in utterances)
        try:
            answer = self._ask_json(SPEAKER_PROMPT.replace("{{TRANSCRIPT}}", transcript))
        except json.JSONDecodeError:
            return ""
        return str(answer.get("patient") or "") if isinstance(answer, dict) else ""

    def analyze_sentence(self, text: str) -> dict:
        return self._ask_json(SENTENCE_PROMPT.replace("{{TEXT}}", text))


class FakeLLMClient:
    """Keyword-based stand-in for local demos and CI (FAKE_AI=true)."""

    KEYWORDS = {
        "mother": ("family", "anxiety", "negative"),
        "work": ("work", "pride", "positive"),
    }

    def identify_patient(self, utterances: list[dict]) -> str:
        return speaker_with_most_words(utterances)

    def analyze_sentence(self, text: str) -> dict:
        lowered = text.lower()
        for keyword, (topic, emotion, valence) in self.KEYWORDS.items():
            if keyword in lowered:
                return {"topic": topic, "emotion": emotion, "valence": valence,
                        "explanation": f"mentions {keyword}"}
        return {"topic": "other", "emotion": "neutral", "valence": "neutral", "explanation": ""}


def build_llm(settings: Settings) -> LLMClient:
    if settings.fake_ai:
        return FakeLLMClient()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required when FAKE_AI is false")
    return OpenAIClient(settings.openai_api_key)
