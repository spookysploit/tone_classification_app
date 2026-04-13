from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import Cookie
from pathlib import Path

from .database import init_db
from .auth import get_user_by_session
from .routers import analyze
from .routers import auth_router

app = FastAPI()

# Инициализируем БД при старте
init_db()

app.include_router(auth_router.router)
app.include_router(analyze.router)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
async def root(session_id: str = Cookie(default=None)):
    # Если пользователь не авторизован — редирект на логин
    user = get_user_by_session(session_id)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    index_file = FRONTEND_DIR / "index.html"
    html = index_file.read_text(encoding="utf-8")
    # Подставляем имя пользователя (простая замена плейсхолдера)
    html = html.replace("{{username}}", user["username"])
    return HTMLResponse(content=html)