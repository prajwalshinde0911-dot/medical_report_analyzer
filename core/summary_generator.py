import os
import json
from dotenv import load_dotenv
import streamlit as st
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

def generate_structured_summary(df):
    """
    Generate a structured, sectioned summary of the lab report using Gemini.
    Returns a dict with: overview, findings (list), general_notes.
    Purely descriptive/educational — never diagnostic or prescriptive.
    """

    abnormal = df[df["Status"].isin(["High", "Low"])]
    normal_count = len(df) - len(abnormal)

    if abnormal.empty:
        param_summary = "All tested parameters are within their normal reference ranges."
    else:
        lines = []
        for _, row in abnormal.iterrows():
            lines.append(f"- {row['Parameter']}: {row['Result']} {row['Unit']} ({row['Status']}, normal range {row['Reference Range']})")
        param_summary = "\n".join(lines)

    prompt = f"""You are a medical information assistant helping a patient understand their lab report in plain, reassuring language.

STRICT RULES:
- Never diagnose any condition or disease.
- Never recommend medications, dosages, supplements, or specific treatments.
- Never instruct the patient on what medical action to take.
- Only explain in general terms what a parameter being high/low commonly relates to in the body.
- Always end by reminding the patient to discuss results with their doctor.
- Keep tone calm and non-alarming.

Report data:
- Total parameters tested: {len(df)}
- Normal: {normal_count}
- Abnormal:
{param_summary}

Respond ONLY in valid JSON with this exact structure, no extra text before or after:
{{
  "overview": "2-3 sentence high-level summary of the overall report",
  "findings": [
    {{
      "parameter": "name of the abnormal parameter",
      "explanation": "1-2 sentence plain-language explanation of what this generally relates to in the body, without diagnosing"
    }}
  ],
  "general_notes": "2-3 sentences of general, non-prescriptive wellness context (e.g., common general factors that influence such parameters), ending with a reminder to consult a doctor"
}}

If there are no abnormal findings, return an empty list for "findings" and adjust the overview and general_notes accordingly.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    raw_text = response.text.strip()

    # Clean up potential markdown code fences
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.lower().startswith("json"):
            raw_text = raw_text[4:].strip()

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        result = {
            "overview": "Summary could not be generated in the expected format. Please try again.",
            "findings": [],
            "general_notes": ""
        }

    return result