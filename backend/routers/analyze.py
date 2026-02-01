from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
import requests
import json
import re
from pathlib import Path

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "../frontend"
templates = Jinja2Templates(directory=str(FRONTEND_DIR))

API_URL = "http://127.0.0.1:5000/v1/completions"

SYSTEM_PROMPT = """
You are a deterministic text classification module inside an information security system.

Your ONLY task is to classify incoming messages.

DO NOT:
- explain
- justify
- apologize
- speak conversationally
- add extra text

Return ONLY valid JSON.

Tone labels (choose exactly one):
NEUTRAL
POSITIVE
NEGATIVE
AGGRESSIVE
TOXIC
THREAT

Information security risk levels:
LOW
MEDIUM
HIGH

Confidence must be a number between 0.00 and 1.00.

STRICT OUTPUT FORMAT:

{
"tone": "LABEL",
"confidence": 0.00,
"security_risk": "LEVEL"
}

Analyze ONLY the LAST user message.
Never generate messages on behalf of the user.
Never simulate a dialogue.
Your response must contain exactly ONE JSON object.
""".strip()


def normalize_text(text: str) -> str:
    # Убирает лишние пробелы, но сохраняет переносы для читаемости
    return " ".join(text.split())


def extract_json(text: str) -> dict:
    # Достаёт первый JSON-объект из текста
    match = re.search(r'\{[\s\S]*\}', text)
    if not match:
        raise ValueError("JSON not found in model output")
    return json.loads(match.group())


@router.post("/analyze", response_class=HTMLResponse)
async def analyze(request: Request, message: str = Form(...)):
    normalized_message = normalize_text(message)

    prompt = f"""
{SYSTEM_PROMPT}

INPUT_MESSAGE:
\"\"\"{normalized_message}\"\"\"
""".strip()

    data = {
        "model": "default",
        "prompt": prompt,
        "max_tokens": 150,
        "temperature": 0.0,
        "top_p": 1.0
    }

    try:
        resp = requests.post(API_URL, json=data, timeout=60)
        resp.raise_for_status()
        response_json = resp.json()

        raw_text = response_json["choices"][0]["text"].strip()
        result = extract_json(raw_text)

    except Exception as e:
        result = {
            "tone": "ERROR",
            "confidence": 0.0,
            "security_risk": "UNKNOWN"
        }

    # Возвращаем рендер HTML через Jinja2
    return templates.TemplateResponse("analyze.html", {
        "request": request,
        "message": message,
        "tone": result.get("tone"),
        "confidence": result.get("confidence"),
        "security_risk": result.get("security_risk")
    })
