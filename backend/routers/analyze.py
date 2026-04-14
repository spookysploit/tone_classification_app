from fastapi import APIRouter, Form, Request, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import requests
import json
import re
from pathlib import Path

from ..auth import get_user_by_session, log_analysis
from ..database import get_user_history, get_all_history

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
    return " ".join(text.split())


def extract_json(text: str) -> dict:
    match = re.search(r'\{[\s\S]*\}', text)
    if not match:
        raise ValueError("JSON not found in model output")
    return json.loads(match.group())


# ---------------------------------------------------------------------------
# Анализ сообщения
# ---------------------------------------------------------------------------

@router.post("/analyze", response_class=HTMLResponse)
async def analyze(
    request: Request,
    message: str = Form(...),
    session_id: str = Cookie(default=None),
):
    user = get_user_by_session(session_id)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

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
        "top_p": 1.0,
    }

    try:
        resp = requests.post(API_URL, json=data, timeout=60)
        resp.raise_for_status()
        response_json = resp.json()
        raw_text = response_json["choices"][0]["text"].strip()
        result = extract_json(raw_text)
    except Exception:
        result = {
            "tone": "ERROR",
            "confidence": 0.0,
            "security_risk": "UNKNOWN",
        }

    # Сохраняем результат в БД (с username)
    log_analysis(
        user_id=user["id"],
        username=user["username"],
        message=message,
        tone=result.get("tone", "ERROR"),
        confidence=float(result.get("confidence", 0.0)),
        security_risk=result.get("security_risk", "UNKNOWN"),
    )

    return templates.TemplateResponse(
        "analyze.html",
        {
            "request": request,
            "message": message,
            "tone": result.get("tone"),
            "confidence": result.get("confidence"),
            "security_risk": result.get("security_risk"),
            "username": user["username"],
        },
    )


# ---------------------------------------------------------------------------
# История запросов пользователя
# ---------------------------------------------------------------------------

@router.get("/history", response_class=HTMLResponse)
async def history(
    request: Request,
    session_id: str = Cookie(default=None),
):
    user = get_user_by_session(session_id)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    records = get_user_history(user_id=user["id"], limit=100)

    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
            "username": user["username"],
            "records": records,
            "total": len(records),
        },
    )


# ---------------------------------------------------------------------------
# История всех запросов (только для admin)
# ---------------------------------------------------------------------------

@router.get("/admin/history", response_class=HTMLResponse)
async def admin_history(
    request: Request,
    session_id: str = Cookie(default=None),
):
    user = get_user_by_session(session_id)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    if user.get("role") != "admin":
        return RedirectResponse(url="/", status_code=303)

    records = get_all_history(limit=500)

    return templates.TemplateResponse(
        "admin_history.html",
        {
            "request": request,
            "username": user["username"],
            "records": records,
            "total": len(records),
        },
    )