from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import Cookie
from pathlib import Path
from fastapi.templating import Jinja2Templates
from fastapi import Request

from .database import init_db
from .auth import get_user_by_session
from .routers import analyze
from .routers import auth_router

app = FastAPI()

init_db()

app.include_router(auth_router.router)
app.include_router(analyze.router)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

templates = Jinja2Templates(directory=str(FRONTEND_DIR))


@app.get("/", response_class=HTMLResponse)
async def root(request: Request, session_id: str = Cookie(default=None)):
    user = get_user_by_session(session_id)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "username": user["username"],
            "role": user.get("role", "user"),
        },
    )