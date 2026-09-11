import hashlib
import hmac
import secrets

from fastapi import APIRouter, Cookie, HTTPException, Response
from pydantic import BaseModel, Field

from app.db.sqlite import SQLiteDatabase

router = APIRouter(prefix="/api/auth", tags=["auth"])


def authenticated_user(airgap_session: str | None) -> dict[str, object]:
    user = SQLiteDatabase().get_user_by_session(airgap_session)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


class AuthPayload(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    email: str
    password: str = Field(min_length=6, max_length=128)


class LoginPayload(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=128)


def password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 180_000)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 180_000)
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(candidate.hex(), digest)


def issue_session(response: Response, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    SQLiteDatabase().create_session(token, user_id)
    response.set_cookie("airgap_session", token, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 30)
    return token


@router.post("/register", status_code=201)
async def register(payload: AuthPayload, response: Response) -> dict[str, object]:
    database = SQLiteDatabase()
    if database.get_user_by_email(payload.email.strip()):
        raise HTTPException(status_code=409, detail="Email is already registered")
    user_id = database.create_user(payload.name or payload.email.split("@")[0], payload.email.strip(), password_hash(payload.password))
    issue_session(response, user_id)
    return {"id": user_id, "name": payload.name, "email": payload.email}


@router.post("/login")
async def login(payload: LoginPayload, response: Response) -> dict[str, object]:
    user = SQLiteDatabase().get_user_by_email(payload.email.strip())
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    issue_session(response, int(user["id"]))
    return {"id": user["id"], "name": user["name"], "email": user["email"]}


@router.get("/me")
async def me(airgap_session: str | None = Cookie(default=None)) -> dict[str, object]:
    user = SQLiteDatabase().get_user_by_session(airgap_session)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.post("/logout")
async def logout(response: Response, airgap_session: str | None = Cookie(default=None)) -> dict[str, str]:
    if airgap_session:
        SQLiteDatabase().delete_session(airgap_session)
    response.delete_cookie("airgap_session")
    return {"status": "ok"}
