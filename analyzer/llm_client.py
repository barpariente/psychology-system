from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

classify_speaker_role_prompt = f"""You are analyzing a transcript of a psychology therapy session.

The transcript includes multiple utterances labeled by speakers such as "A" and "B".
Your task is to determine which speaker is the THERAPIST and which is the PATIENT.

Guidelines:
- The therapist asks guiding questions, reflects statements, gives structure.
- The patient talks about personal issues, feelings, experiences, and emotional struggles.
- Respond ONLY with this exact JSON format:

{
  "therapist": "<speaker>",
  "patient": "<speaker>",
  "reasoning": "<short explanation>"
}

Do not include anything else.

Here is the transcript:
{{TRANSCRIPT}}
"""

analyze_emotion_prompt = """
You are analyzing a single sentence from a psychology therapy session.

For the given sentence, identify:
1. The MAIN TOPIC (e.g., mother, work, school, relationships, self-esteem)
2. The EMOTION expressed in the sentence
3. The emotional VALENCE (positive, negative, or neutral)

Return your analysis in a short natural-language explanation, NOT in JSON.

Format your answer like this:
Topic: <topic>
Emotion: <emotion>
Valence: <positive|negative|neutral>
Explanation: <1–2 sentences explaining why>

Sentence:
"{{TEXT}}"
"""

def analyze_emotion(text: str):
    prompt = analyze_emotion_prompt.replace("{{TEXT}}", text)

    response = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )

    result = response.output_text.strip()
    return result

def classify_speaker_role(transcript): 
    response = client.responses.create(
      model="gpt-5-nano",
      input=classify_speaker_role_prompt.format(TRANSCRIPT=transcript)
    )
    return response


