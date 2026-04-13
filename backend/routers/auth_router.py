from fastapi import APIRouter, Form, Request, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from ..auth import (
    create_user,
    get_user_by_username,
    verify_password,
    create_session,
    delete_session,
)

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "../frontend"
templates = Jinja2Templates(directory=str(FRONTEND_DIR))


# ---------------------------------------------------------------------------
# Регистрация
# ---------------------------------------------------------------------------

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})


@router.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    password2: str = Form(...),
):
    if password != password2:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Пароли не совпадают."},
        )

    if len(username) < 3:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Логин должен содержать не менее 3 символов."},
        )

    if len(password) < 6:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Пароль должен содержать не менее 6 символов."},
        )

    success = create_user(username, password)
    if not success:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Пользователь с таким логином уже существует."},
        )

    return RedirectResponse(url="/login?registered=1", status_code=303)


# ---------------------------------------------------------------------------
# Вход
# ---------------------------------------------------------------------------

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, registered: str = None):
    success_msg = "Регистрация прошла успешно. Войдите в систему." if registered else None
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None, "success": success_msg},
    )


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    user = get_user_by_username(username)
    if not user or not verify_password(password, user["password"]):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Неверный логин или пароль.", "success": None},
        )

    session_id = create_session(user["id"])
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 дней
    )
    return response


# ---------------------------------------------------------------------------
# Выход
# ---------------------------------------------------------------------------

@router.get("/logout")
async def logout(session_id: str = Cookie(default=None)):
    if session_id:
        delete_session(session_id)
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session_id")
    return response