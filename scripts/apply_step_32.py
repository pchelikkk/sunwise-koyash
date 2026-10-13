from pathlib import Path
import re

ROOT = Path(r"C:\Projects\sunwise-koyash")


def write_file(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip("\n"), encoding="utf-8")


def replace_function(relative_path: str, function_name: str, replacement: str) -> None:
    path = ROOT / relative_path
    text = path.read_text(encoding="utf-8")
    pattern = rf"function {re.escape(function_name)}\([^)]*\) \{{"
    match = re.search(pattern, text)
    if not match:
        raise RuntimeError(f"Function {function_name} not found in {relative_path}")

    start = match.start()
    i = match.end() - 1
    depth = 0
    end = None
    in_string = None
    escape = False
    in_line_comment = False
    in_block_comment = False

    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""

        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
        elif in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 1
        elif in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == in_string:
                in_string = None
        else:
            if ch == "/" and nxt == "/":
                in_line_comment = True
                i += 1
            elif ch == "/" and nxt == "*":
                in_block_comment = True
                i += 1
            elif ch in {'"', "'", "`"}:
                in_string = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break

        i += 1

    if end is None:
        raise RuntimeError(f"Function {function_name} end not found in {relative_path}")

    new_text = text[:start] + replacement.lstrip("\n").rstrip() + text[end:]
    path.write_text(new_text, encoding="utf-8")


def insert_after_function(relative_path: str, function_name: str, addition: str, marker: str) -> None:
    path = ROOT / relative_path
    text = path.read_text(encoding="utf-8")

    if marker in text:
        return

    pattern = rf"function {re.escape(function_name)}\([^)]*\) \{{"
    match = re.search(pattern, text)

    if not match:
        raise RuntimeError(f"Function {function_name} not found in {relative_path}")

    i = match.end() - 1
    depth = 0
    end = None
    in_string = None
    escape = False
    in_line_comment = False
    in_block_comment = False

    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""

        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
        elif in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 1
        elif in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == in_string:
                in_string = None
        else:
            if ch == "/" and nxt == "/":
                in_line_comment = True
                i += 1
            elif ch == "/" and nxt == "*":
                in_block_comment = True
                i += 1
            elif ch in {'"', "'", "`"}:
                in_string = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break

        i += 1

    if end is None:
        raise RuntimeError(f"Function {function_name} end not found in {relative_path}")

    new_text = text[:end] + "\n\n" + addition.lstrip("\n").rstrip() + text[end:]
    path.write_text(new_text, encoding="utf-8")


write_file("backend/app/schemas/user.py", r'''
from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    user_id: str
    email: EmailStr
    full_name: str | None = None
    anonymous_id: str | None = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    last_seen_at: datetime


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    anonymous_id: str | None = Field(default=None, max_length=120)


class QuestionnaireHistoryCreate(BaseModel):
    recommendation_id: str | None = Field(default=None, max_length=120)
    age: int | None = Field(default=None, ge=12, le=100)
    skin_type: str | None = None
    concerns: list[str] = Field(default_factory=list)
    budget: str | None = None
    excluded_ingredients: list[str] = Field(default_factory=list)
    custom_restrictions: list[str] = Field(default_factory=list)
    experience: str | None = None
    values: list[str] = Field(default_factory=list)
    total_price_rub: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class UserProfileResponse(BaseModel):
    profile_id: str
    user_id: str
    anonymous_id: str | None = None
    age: int | None = Field(default=None, ge=12, le=100)
    skin_type: str | None = None
    concerns: list[str] = Field(default_factory=list)
    budget: str | None = None
    excluded_ingredients: list[str] = Field(default_factory=list)
    custom_restrictions: list[str] = Field(default_factory=list)
    experience: str | None = None
    values: list[str] = Field(default_factory=list)
    questionnaire_history: list[dict[str, Any]] = Field(default_factory=list)
    feedback_history: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class UserProfileUpdate(BaseModel):
    age: int | None = Field(default=None, ge=12, le=100)
    skin_type: str | None = None
    concerns: list[str] | None = None
    budget: str | None = None
    excluded_ingredients: list[str] | None = None
    custom_restrictions: list[str] | None = None
    experience: str | None = None
    values: list[str] | None = None
''')


write_file("backend/app/repositories/profile_repository.py", r'''
from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.core.time import utc_now


def _clean_profile(document: dict[str, Any]) -> dict[str, Any]:
    document["profile_id"] = str(document.pop("_id"))
    document.setdefault("age", None)
    document.setdefault("concerns", [])
    document.setdefault("excluded_ingredients", [])
    document.setdefault("custom_restrictions", [])
    document.setdefault("values", [])
    document.setdefault("questionnaire_history", [])
    document.setdefault("feedback_history", [])
    return document


class ProfileRepository:
    def __init__(self, database: AsyncDatabase[Any]) -> None:
        self.collection = database["user_profiles"]

    async def create_default_profile(
        self,
        user_id: str,
        anonymous_id: str | None = None,
    ) -> dict[str, Any]:
        now = utc_now()

        document = {
            "user_id": user_id,
            "anonymous_id": anonymous_id,
            "age": None,
            "skin_type": None,
            "concerns": [],
            "budget": None,
            "excluded_ingredients": [],
            "custom_restrictions": [],
            "experience": None,
            "values": [],
            "questionnaire_history": [],
            "feedback_history": [],
            "created_at": now,
            "updated_at": now,
        }

        result = await self.collection.insert_one(document)
        document["_id"] = result.inserted_id

        return _clean_profile(document)

    async def find_by_user_id(self, user_id: str) -> dict[str, Any] | None:
        document = await self.collection.find_one({"user_id": user_id})

        if document is None:
            return None

        return _clean_profile(document)

    async def ensure_profile(
        self,
        user_id: str,
        anonymous_id: str | None = None,
    ) -> dict[str, Any]:
        profile = await self.find_by_user_id(user_id)

        if profile is not None:
            return profile

        return await self.create_default_profile(
            user_id=user_id,
            anonymous_id=anonymous_id,
        )

    async def update_profile(
        self,
        user_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        allowed_fields = {
            "age",
            "skin_type",
            "concerns",
            "budget",
            "excluded_ingredients",
            "custom_restrictions",
            "experience",
            "values",
        }

        update = {
            key: value
            for key, value in payload.items()
            if key in allowed_fields and value is not None
        }

        update["updated_at"] = utc_now()

        await self.collection.update_one(
            {"user_id": user_id},
            {"$set": update},
        )

        return await self.find_by_user_id(user_id)

    async def append_questionnaire_history(
        self,
        user_id: str,
        entry: dict[str, Any],
    ) -> dict[str, Any] | None:
        now = utc_now()
        history_entry = {
            **entry,
            "created_at": now,
        }

        await self.collection.update_one(
            {"user_id": user_id},
            {
                "$push": {
                    "questionnaire_history": {
                        "$each": [history_entry],
                        "$slice": -20,
                    }
                },
                "$set": {"updated_at": now},
            },
        )

        return await self.find_by_user_id(user_id)

    async def sync_anonymous_id(
        self,
        user_id: str,
        anonymous_id: str | None,
    ) -> None:
        if anonymous_id is None:
            return

        await self.collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "anonymous_id": anonymous_id,
                    "updated_at": utc_now(),
                }
            },
        )
''')


write_file("backend/app/services/user_service.py", r'''
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    QuestionnaireHistoryCreate,
    UserProfileResponse,
    UserProfileUpdate,
    UserResponse,
    UserUpdate,
)


class UserService:
    def __init__(
        self,
        user_repository: UserRepository,
        profile_repository: ProfileRepository,
    ) -> None:
        self.user_repository = user_repository
        self.profile_repository = profile_repository

    async def get_me(self, user: dict) -> UserResponse:
        return UserResponse(**user)

    async def update_me(
        self,
        user: dict,
        payload: UserUpdate,
    ) -> UserResponse | None:
        updated = await self.user_repository.update_user(
            user_id=user["user_id"],
            full_name=payload.full_name,
            anonymous_id=payload.anonymous_id,
        )

        if updated is None:
            return None

        await self.profile_repository.sync_anonymous_id(
            user_id=updated["user_id"],
            anonymous_id=updated.get("anonymous_id"),
        )

        return UserResponse(**updated)

    async def get_my_profile(self, user: dict) -> UserProfileResponse:
        profile = await self.profile_repository.ensure_profile(
            user_id=user["user_id"],
            anonymous_id=user.get("anonymous_id"),
        )

        return UserProfileResponse(**profile)

    async def update_my_profile(
        self,
        user: dict,
        payload: UserProfileUpdate,
    ) -> UserProfileResponse | None:
        profile = await self.profile_repository.ensure_profile(
            user_id=user["user_id"],
            anonymous_id=user.get("anonymous_id"),
        )

        updated = await self.profile_repository.update_profile(
            user_id=profile["user_id"],
            payload=payload.model_dump(),
        )

        if updated is None:
            return None

        return UserProfileResponse(**updated)

    async def append_questionnaire_history(
        self,
        user: dict,
        payload: QuestionnaireHistoryCreate,
    ) -> UserProfileResponse | None:
        profile = await self.profile_repository.ensure_profile(
            user_id=user["user_id"],
            anonymous_id=user.get("anonymous_id"),
        )

        updated = await self.profile_repository.append_questionnaire_history(
            user_id=profile["user_id"],
            entry=payload.model_dump(),
        )

        if updated is None:
            return None

        return UserProfileResponse(**updated)
''')


write_file("backend/app/api/v1/endpoints/users.py", r'''
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.dependencies import get_current_user
from app.db.mongodb import get_database
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    QuestionnaireHistoryCreate,
    UserProfileResponse,
    UserProfileUpdate,
    UserResponse,
    UserUpdate,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(database=Depends(get_database)) -> UserService:
    return UserService(
        user_repository=UserRepository(database),
        profile_repository=ProfileRepository(database),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await service.get_me(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    payload: UserUpdate,
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    result = await service.update_me(
        user=current_user,
        payload=payload,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return result


@router.get("/me/profile", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserProfileResponse:
    return await service.get_my_profile(current_user)


@router.patch("/me/profile", response_model=UserProfileResponse)
async def update_my_profile(
    payload: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserProfileResponse:
    result = await service.update_my_profile(
        user=current_user,
        payload=payload,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    return result


@router.post("/me/profile/questionnaire-history", response_model=UserProfileResponse)
async def append_questionnaire_history(
    payload: QuestionnaireHistoryCreate,
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserProfileResponse:
    result = await service.append_questionnaire_history(
        user=current_user,
        payload=payload,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    return result
''')


write_file("frontend/src/api.js", r'''
// KOYASH API client.
// Base URL comes from VITE_API_BASE_URL at build time.
// In Docker, nginx serves the SPA and reverse-proxies /api to backend.

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || "/api/v1").replace(
  /\/$/,
  "",
);

const TOKEN_KEY = "koyash_token";
const ANON_KEY = "koyash_anon_id";

let token = null;
try {
  token = localStorage.getItem(TOKEN_KEY);
} catch {
  token = null;
}

export function setToken(value) {
  token = value || null;
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* ignore storage errors */
  }
}

export function getToken() {
  return token;
}

export function logout() {
  setToken(null);
}

export function getAnonymousId() {
  let value = null;
  try {
    value = localStorage.getItem(ANON_KEY);
  } catch {
    value = null;
  }

  if (!value) {
    value =
      "anon-" +
      Math.random().toString(36).slice(2) +
      "-" +
      Date.now().toString(36);

    try {
      localStorage.setItem(ANON_KEY, value);
    } catch {
      /* ignore storage errors */
    }
  }

  return value;
}

export class ApiError extends Error {
  constructor(status, message, detail) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

function humanizeDetail(detail, status) {
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        const loc = Array.isArray(item.loc) ? item.loc.join(".") : "field";
        return loc + ": " + (item.msg || "invalid value");
      })
      .join("; ");
  }

  if (typeof detail === "string" && detail) return detail;

  if (status === 401) return "Нужно войти в аккаунт.";
  if (status === 403) return "Недостаточно прав.";
  if (status === 404) return "Запись не найдена.";
  if (status === 409) return "Такая запись уже существует.";
  if (status === 422) return "Проверьте заполнение полей.";

  return "Запрос не выполнен (" + status + ")";
}

async function request(path, options = {}) {
  const { method = "GET", body, auth = false } = options;
  const headers = {};
  let payload;

  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  if (auth) {
    if (!token) throw new ApiError(401, "Нужно войти в аккаунт.", null);
    headers["Authorization"] = "Bearer " + token;
  }

  let res;
  try {
    res = await fetch(BASE_URL + path, { method, headers, body: payload });
  } catch (networkError) {
    throw new ApiError(
      0,
      "Не удалось связаться с сервером. Проверьте соединение.",
      networkError,
    );
  }

  if (res.status === 204) return null;

  let data = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!res.ok) {
    const detail = data && typeof data === "object" ? data.detail : data;
    throw new ApiError(res.status, humanizeDetail(detail, res.status), detail);
  }

  return data;
}

export const getQuestionnaire = () => request("/questionnaire");

export const getRestrictionSuggestions = () =>
  request("/restrictions/suggestions");

export const createRecommendation = (payload) =>
  request("/recommendations", {
    method: "POST",
    body: { ...payload, anonymous_id: getAnonymousId() },
  });

export const getRecommendation = (recommendationId) =>
  request("/recommendations/" + encodeURIComponent(recommendationId));

export const submitFeedback = (recommendationId, payload) =>
  request(
    "/recommendations/" + encodeURIComponent(recommendationId) + "/feedback",
    {
      method: "POST",
      body: { ...payload, anonymous_id: getAnonymousId() },
    },
  );

export const listReplacements = (recommendationId) =>
  request(
    "/recommendations/" +
      encodeURIComponent(recommendationId) +
      "/replacements",
  );

export const selectReplacement = (
  recommendationId,
  sessionId,
  productExternalId,
) =>
  request(
    "/recommendations/" +
      encodeURIComponent(recommendationId) +
      "/replacements/" +
      encodeURIComponent(sessionId) +
      "/select",
    { method: "POST", body: { product_external_id: productExternalId } },
  );

export const register = (payload) =>
  request("/auth/register", {
    method: "POST",
    body: { ...payload, anonymous_id: getAnonymousId() },
  });

export const login = (email, password) =>
  request("/auth/login", {
    method: "POST",
    body: { email: email.trim().toLowerCase(), password },
  });

export const getMe = () => request("/users/me", { auth: true });

export const updateMe = (payload) =>
  request("/users/me", { method: "PATCH", body: payload, auth: true });

export const getMyProfile = () => request("/users/me/profile", { auth: true });

export const updateMyProfile = (payload) =>
  request("/users/me/profile", {
    method: "PATCH",
    body: payload,
    auth: true,
  });

export const appendQuestionnaireHistory = (payload) =>
  request("/users/me/profile/questionnaire-history", {
    method: "POST",
    body: payload,
    auth: true,
  });

export async function loadAuthState() {
  if (!getToken()) return null;

  try {
    const [user, profile] = await Promise.all([getMe(), getMyProfile()]);
    return { user, profile };
  } catch (error) {
    if (error && error.status === 401) setToken(null);
    throw error;
  }
}
''')


insert_after_function("frontend/src/main.jsx", "buildRecommendationRequest", r'''
// STEP 3.2 PROFILE_SYNC_HELPERS
function profilePayloadFromAnswers(answers) {
  const request = buildRecommendationRequest(answers);

  return {
    age: request.age,
    skin_type: request.skin_type || null,
    concerns: request.concerns || [],
    budget: request.budget || null,
    excluded_ingredients: request.excluded_ingredients || [],
    custom_restrictions: request.custom_restrictions || [],
    experience: request.experience || null,
    values: request.values || [],
  };
}

function historyPayloadFromAnswers(answers, recommendation) {
  return {
    ...profilePayloadFromAnswers(answers),
    recommendation_id: recommendation ? recommendation.recommendation_id : null,
    total_price_rub: recommendation ? recommendation.total_price_rub : null,
    metadata: {
      source: "frontend",
      algorithm_version: recommendation ? recommendation.algorithm_version : null,
    },
  };
}

function normalizeEmail(value) {
  return value.trim().toLowerCase();
}

function authErrorMessage(error) {
  if (!error) return null;
  if (error.status === 401) return "Неверная почта или пароль.";
  if (error.status === 409) return "Пользователь с такой почтой уже есть.";
  if (error.status === 422) return "Проверь почту и пароль.";
  return error.message || "Не удалось выполнить действие.";
}

function profileLabel(value) {
  if (Array.isArray(value)) return value.length ? value.join(", ") : "—";
  return value || "—";
}
''', "STEP 3.2 PROFILE_SYNC_HELPERS")


replace_function("frontend/src/main.jsx", "Login", r'''
function Login({ go, onAuth }) {
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState(null);

  const submit = () => {
    const normalizedEmail = normalizeEmail(email);
    if (!normalizedEmail || !password) {
      setError("Заполни почту и пароль.");
      return;
    }

    setBusy(true);
    setError(null);

    api
      .login(normalizedEmail, password)
      .then((res) => {
        api.setToken(res.access_token);
        onAuth({ user: res.user, profile: res.profile });
        go("account");
      })
      .catch((e) => setError(authErrorMessage(e)))
      .finally(() => setBusy(false));
  };

  return (
    <div className="quizPage authPage">
      <header className="topbar" style={{ padding: "4px 0 0" }}>
        <Logo onClick={() => go("home")} />
        <div style={{ flex: 1 }} />
      </header>
      <div className="authCard">
        <h1>Вход</h1>
        <div className="field">
          <label>Почта</label>
          <input
            type="email"
            autoComplete="email"
            placeholder="user@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") submit();
            }}
          />
        </div>
        <div className="field">
          <label>Пароль</label>
          <input
            type="password"
            autoComplete="current-password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") submit();
            }}
          />
        </div>
        <ErrorNote message={error} />
        <button
          className="btn solid"
          style={{ width: "100%" }}
          onClick={submit}
          disabled={busy || !email || !password}
        >
          {busy ? "Входим…" : "Войти"}
        </button>
        <div className="authLinks">
          <button className="linkBtn" onClick={() => go("reset")}>
            Забыли пароль?
          </button>
          <button className="linkBtn" onClick={() => go("register")}>
            Регистрация
          </button>
        </div>
      </div>
    </div>
  );
}
''')


replace_function("frontend/src/main.jsx", "Register", r'''
function Register({ go, onAuth }) {
  const [fullName, setFullName] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [password2, setPassword2] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState(null);

  const submit = () => {
    const normalizedEmail = normalizeEmail(email);

    if (!normalizedEmail) {
      setError("Укажи почту.");
      return;
    }
    if (password.length < 8) {
      setError("Пароль должен быть не короче 8 символов.");
      return;
    }
    if (password !== password2) {
      setError("Пароли не совпадают.");
      return;
    }

    setBusy(true);
    setError(null);

    api
      .register({
        email: normalizedEmail,
        password,
        full_name: fullName.trim() || null,
      })
      .then((res) => {
        api.setToken(res.access_token);
        onAuth({ user: res.user, profile: res.profile });
        go("account");
      })
      .catch((e) => setError(authErrorMessage(e)))
      .finally(() => setBusy(false));
  };

  return (
    <div className="quizPage authPage">
      <header className="topbar" style={{ padding: "4px 0 0" }}>
        <Logo onClick={() => go("home")} />
        <div style={{ flex: 1 }} />
      </header>
      <div className="authCard">
        <h1>Регистрация</h1>
        <div className="field">
          <label>Имя</label>
          <input
            type="text"
            autoComplete="name"
            placeholder="Как тебя зовут?"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
        </div>
        <div className="field">
          <label>Почта</label>
          <input
            type="email"
            autoComplete="email"
            placeholder="user@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="field">
          <label>Пароль</label>
          <input
            type="password"
            autoComplete="new-password"
            placeholder="минимум 8 символов"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <div className="field">
          <label>Повторите пароль</label>
          <input
            type="password"
            autoComplete="new-password"
            placeholder="••••••••"
            value={password2}
            onChange={(e) => setPassword2(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") submit();
            }}
          />
        </div>
        <ErrorNote message={error} />
        <button
          className="btn solid"
          style={{ width: "100%" }}
          onClick={submit}
          disabled={busy || !email || !password || !password2}
        >
          {busy ? "Создаём…" : "Создать аккаунт"}
        </button>
        <div className="authLinks">
          <button className="linkBtn" onClick={() => go("login")}>
            Уже есть аккаунт? Войти
          </button>
          <button className="linkBtn" onClick={() => go("quiz")}>
            Собрать подбор
          </button>
        </div>
      </div>
    </div>
  );
}
''')


replace_function("frontend/src/main.jsx", "Loading", r'''
function Loading({ go, answers, setRecommendation, auth, setAuth }) {
  const steps = [
    "Анализируем тип кожи",
    "Сопоставляем составы средств",
    "Учитываем бюджет и ограничения",
    "Формируем объяснения",
  ];
  const [done, setDone] = React.useState(0);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    let alive = true;
    const payload = buildRecommendationRequest(answers);

    if (!payload.skin_type) {
      setError("Сначала ответьте на вопросы анкеты.");
      return;
    }

    api
      .createRecommendation(payload)
      .then(async (rec) => {
        if (!alive) return;

        setRecommendation(rec);

        if (api.getToken()) {
          try {
            const updatedProfile = await api.updateMyProfile(
              profilePayloadFromAnswers(answers),
            );

            await api.appendQuestionnaireHistory(
              historyPayloadFromAnswers(answers, rec),
            );

            if (alive) {
              setAuth((current) => ({
                ...(current || auth || {}),
                profile: updatedProfile,
              }));
            }
          } catch {
            // Не блокируем показ результата, если профиль временно не сохранился.
          }
        }

        setTimeout(() => {
          if (alive) go("results");
        }, 400);
      })
      .catch((e) => {
        if (alive) setError(e.message || "Не удалось собрать подбор.");
      });

    return () => {
      alive = false;
    };
  }, []);

  React.useEffect(() => {
    if (done >= steps.length) return;
    const t = setTimeout(() => setDone((d) => d + 1), 600);
    return () => clearTimeout(t);
  }, [done]);

  if (error) {
    return (
      <CenterInfo
        title="Не удалось собрать подбор"
        text={error}
        action={{ label: "Попробовать снова", on: () => go("review") }}
      />
    );
  }

  return (
    <div className="quizPage">
      <div className="quizMain wide">
        <h1>Собираем твою косметичку…</h1>
        <p className="qsub">Это займёт пару секунд.</p>
        <div className="loadList">
          {steps.map((s, idx) => (
            <div className={"loadRow" + (idx < done ? " ok" : "")} key={s}>
              <span className="loadMark">
                {idx < done ? "✓" : <span className="spin" />}
              </span>
              {s}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
''')


replace_function("frontend/src/main.jsx", "Account", r'''
function Account({ go, auth, setAuth }) {
  const [profile, setProfile] = React.useState(
    auth && auth.profile ? auth.profile : null,
  );
  const [user, setUser] = React.useState(auth && auth.user ? auth.user : null);
  const [loading, setLoading] = React.useState(false);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState(null);
  const [saved, setSaved] = React.useState(false);
  const [form, setForm] = React.useState({
    full_name: user && user.full_name ? user.full_name : "",
    age: profile && profile.age ? String(profile.age) : "",
    skin_type: profile && profile.skin_type ? profile.skin_type : "",
    budget: profile && profile.budget ? profile.budget : "",
    experience: profile && profile.experience ? profile.experience : "",
    concerns:
      profile && profile.concerns && profile.concerns.length
        ? profile.concerns.join(", ")
        : "",
    values:
      profile && profile.values && profile.values.length
        ? profile.values.join(", ")
        : "",
  });

  React.useEffect(() => {
    if (!api.getToken()) return;

    setLoading(true);
    setError(null);

    api
      .loadAuthState()
      .then((state) => {
        if (!state) return;

        setAuth(state);
        setUser(state.user);
        setProfile(state.profile);
        setForm({
          full_name: state.user && state.user.full_name ? state.user.full_name : "",
          age: state.profile && state.profile.age ? String(state.profile.age) : "",
          skin_type:
            state.profile && state.profile.skin_type ? state.profile.skin_type : "",
          budget: state.profile && state.profile.budget ? state.profile.budget : "",
          experience:
            state.profile && state.profile.experience
              ? state.profile.experience
              : "",
          concerns:
            state.profile && state.profile.concerns
              ? state.profile.concerns.join(", ")
              : "",
          values:
            state.profile && state.profile.values
              ? state.profile.values.join(", ")
              : "",
        });
      })
      .catch((e) => setError(authErrorMessage(e)))
      .finally(() => setLoading(false));
  }, []);

  const logout = () => {
    api.logout();
    setAuth(null);
    go("home");
  };

  const parseList = (value) =>
    value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);

  const save = () => {
    setSaving(true);
    setSaved(false);
    setError(null);

    const age = form.age ? Number.parseInt(form.age, 10) : null;

    if (form.age && (!Number.isFinite(age) || age < 12 || age > 100)) {
      setError("Возраст должен быть числом от 12 до 100.");
      setSaving(false);
      return;
    }

    Promise.all([
      api.updateMe({ full_name: form.full_name.trim() || null }),
      api.updateMyProfile({
        age,
        skin_type: form.skin_type || null,
        budget: form.budget || null,
        experience: form.experience || null,
        concerns: parseList(form.concerns),
        values: parseList(form.values),
      }),
    ])
      .then(([updatedUser, updatedProfile]) => {
        const nextAuth = { user: updatedUser, profile: updatedProfile };
        setUser(updatedUser);
        setProfile(updatedProfile);
        setAuth(nextAuth);
        setSaved(true);
      })
      .catch((e) => setError(authErrorMessage(e)))
      .finally(() => setSaving(false));
  };

  if (!api.getToken()) {
    return (
      <CenterInfo
        title="Нужен вход"
        text="Войдите, чтобы увидеть личный кабинет."
        action={{ label: "Войти", on: () => go("login") }}
      />
    );
  }

  const name = (user && (user.full_name || user.email)) || "друг";
  const historyCount =
    profile && profile.questionnaire_history
      ? profile.questionnaire_history.length
      : 0;

  return (
    <div className="quizPage">
      <header className="topbar" style={{ padding: "4px 0 0" }}>
        <Logo onClick={() => go("home")} />
        <div style={{ flex: 1 }} />
        <button className="btn ghost xs" onClick={logout}>
          выйти
        </button>
      </header>
      <div className="quizMain wide">
        <h1>Личный кабинет</h1>
        <p className="qsub">
          Привет, {name}! Здесь хранятся профиль кожи и история подборов.
        </p>
        {loading ? <p className="qsub">Загружаем профиль…</p> : null}
        <ErrorNote message={error} />
        {saved ? <div className="okNote">Профиль сохранён.</div> : null}

        <div className="reviewGrid">
          <div className="reviewCard">
            <b>Возраст</b>
            <span>{profile && profile.age ? profile.age + " лет" : "—"}</span>
          </div>
          <div className="reviewCard">
            <b>Тип кожи</b>
            <span>{profileLabel(profile && profile.skin_type)}</span>
          </div>
          <div className="reviewCard">
            <b>Задачи ухода</b>
            <span>{profileLabel(profile && profile.concerns)}</span>
          </div>
          <div className="reviewCard">
            <b>Подборов в истории</b>
            <span>{historyCount}</span>
          </div>
        </div>

        <div className="accountForm">
          <div className="field">
            <label>Имя</label>
            <input
              type="text"
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              placeholder="Как тебя зовут?"
            />
          </div>
          <div className="field">
            <label>Возраст</label>
            <input
              type="number"
              min="12"
              max="100"
              value={form.age}
              onChange={(e) => setForm({ ...form, age: e.target.value })}
              placeholder="например 19"
            />
          </div>
          <div className="field">
            <label>Тип кожи</label>
            <select
              value={form.skin_type}
              onChange={(e) => setForm({ ...form, skin_type: e.target.value })}
            >
              <option value="">Не указано</option>
              <option value="oily">Жирная</option>
              <option value="dry">Сухая</option>
              <option value="combination">Комбинированная</option>
              <option value="sensitive">Чувствительная</option>
            </select>
          </div>
          <div className="field">
            <label>Бюджет</label>
            <select
              value={form.budget}
              onChange={(e) => setForm({ ...form, budget: e.target.value })}
            >
              <option value="">Не указано</option>
              <option value="minimum">Бюджет</option>
              <option value="balanced">Баланс</option>
              <option value="premium">Люкс</option>
            </select>
          </div>
          <div className="field">
            <label>Формат ухода</label>
            <select
              value={form.experience}
              onChange={(e) => setForm({ ...form, experience: e.target.value })}
            >
              <option value="">Не указано</option>
              <option value="minimal">Минимально</option>
              <option value="basic">Знаю базовый уход</option>
              <option value="advanced">Продвинутые знания</option>
              <option value="guided">Хочу заботливый шаговый уход</option>
            </select>
          </div>
          <div className="field">
            <label>Задачи ухода через запятую</label>
            <input
              type="text"
              value={form.concerns}
              onChange={(e) => setForm({ ...form, concerns: e.target.value })}
              placeholder="acne, sebum"
            />
          </div>
          <div className="field">
            <label>Приоритеты через запятую</label>
            <input
              type="text"
              value={form.values}
              onChange={(e) => setForm({ ...form, values: e.target.value })}
              placeholder="comfort, price_quality"
            />
          </div>
        </div>

        <div className="accountLinks">
          <button className="btn solid" onClick={save} disabled={saving}>
            {saving ? "Сохраняем…" : "Сохранить профиль"}
          </button>
          <button className="btn ghost" onClick={() => go("history")}>
            История подборов
          </button>
          <button className="btn ghost" onClick={() => go("quiz")}>
            Новый подбор
          </button>
        </div>
      </div>
    </div>
  );
}
''')


replace_function("frontend/src/main.jsx", "HistoryPage", r'''
function HistoryPage({ go, auth, setAuth }) {
  const [profile, setProfile] = React.useState(
    auth && auth.profile ? auth.profile : null,
  );
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    if (!api.getToken()) return;

    setLoading(true);

    api
      .getMyProfile()
      .then((prof) => {
        setProfile(prof);
        setAuth((current) => ({ ...(current || auth || {}), profile: prof }));
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const history = (profile && profile.questionnaire_history) || [];

  return (
    <div className="quizPage">
      <header className="topbar" style={{ padding: "4px 0 0" }}>
        <Logo onClick={() => go("home")} />
        <div style={{ flex: 1 }} />
        <button className="btn ghost xs" onClick={() => go("account")}>
          кабинет
        </button>
      </header>
      <div className="quizMain wide">
        <h1>История подборов</h1>
        {loading ? <p className="qsub">Обновляем историю…</p> : null}

        {history.length ? (
          <div className="histList">
            {[...history].reverse().map((it, idx) => (
              <div className="histRow" key={idx}>
                <div>
                  <b>{it.skin_type || "Подбор"}</b>
                  <span>
                    {it.created_at ? String(it.created_at).slice(0, 10) : ""}
                    {it.age ? " · " + it.age + " лет" : ""}
                  </span>
                  <span>
                    {(it.concerns || []).length
                      ? "Запросы: " + it.concerns.join(", ")
                      : ""}
                  </span>
                </div>
                <div style={{ textAlign: "right" }}>
                  <span>
                    {it.total_price_rub ? it.total_price_rub + " ₽" : ""}
                  </span>
                  {it.recommendation_id ? (
                    <span>{String(it.recommendation_id).slice(0, 8)}…</span>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="qsub">Пока нет сохранённых подборов.</p>
        )}

        <button className="btn ghost" onClick={() => go("account")}>
          Назад в кабинет
        </button>
      </div>
    </div>
  );
}
''')


main_path = ROOT / "frontend/src/main.jsx"
main_text = main_path.read_text(encoding="utf-8")

main_text = main_text.replace(
    '''      api
        .getMe()
        .then((user) => setAuth((a) => ({ ...(a || {}), user })))
        .catch(() => api.setToken(null));''',
    '''      api
        .loadAuthState()
        .then(setAuth)
        .catch(() => {
          api.setToken(null);
          setAuth(null);
        });'''
)

main_text = main_text.replace(
    '''        <Loading
          go={go}
          answers={answers}
          setRecommendation={setRecommendation}
        />''',
    '''        <Loading
          go={go}
          answers={answers}
          setRecommendation={setRecommendation}
          auth={auth}
          setAuth={setAuth}
        />'''
)

main_text = main_text.replace(
    '''{page === "history" && <HistoryPage go={go} auth={auth} />}''',
    '''{page === "history" && <HistoryPage go={go} auth={auth} setAuth={setAuth} />}'''
)

main_path.write_text(main_text, encoding="utf-8")


styles_path = ROOT / "frontend/src/styles.css"
styles_text = styles_path.read_text(encoding="utf-8")

if ".accountForm" not in styles_text:
    styles_text += r'''

.accountForm {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin: 22px 0;
}

.accountForm .field {
  margin: 0;
}

.accountForm select {
  width: 100%;
  border: 2px solid var(--line);
  border-radius: 14px;
  padding: 12px 14px;
  background: #fff;
  color: var(--text);
  font: inherit;
  outline: none;
}

.histRow span {
  display: block;
}

@media (max-width: 760px) {
  .accountForm {
    grid-template-columns: 1fr;
  }
}
'''

styles_path.write_text(styles_text, encoding="utf-8")


write_file("backend/tests/test_auth_users.py", r'''
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def _unique_email() -> str:
    return f"test-{uuid4().hex}@example.com"


def _register_user(client: TestClient) -> tuple[str, dict]:
    email = _unique_email()

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": "Test User",
            "anonymous_id": "auth-test-anon",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    return payload["access_token"], payload


def test_user_can_register() -> None:
    with TestClient(app) as client:
        _, payload = _register_user(client)

    assert payload["token_type"] == "bearer"
    assert payload["user"]["email"]
    assert payload["user"]["full_name"] == "Test User"
    assert payload["user"]["anonymous_id"] == "auth-test-anon"
    assert payload["profile"]["user_id"] == payload["user"]["user_id"]
    assert payload["profile"]["questionnaire_history"] == []


def test_duplicate_registration_returns_409() -> None:
    email = _unique_email()

    with TestClient(app) as client:
        first = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "StrongPassword123!",
                "full_name": "First User",
                "anonymous_id": "dup-anon",
            },
        )
        second = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "StrongPassword123!",
                "full_name": "Second User",
                "anonymous_id": "dup-anon-2",
            },
        )

    assert first.status_code == 201
    assert second.status_code == 409


def test_user_can_login() -> None:
    email = _unique_email()
    password = "StrongPassword123!"

    with TestClient(app) as client:
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Login User",
                "anonymous_id": "login-anon",
            },
        )
        assert register_response.status_code == 201

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

    assert login_response.status_code == 200
    payload = login_response.json()
    assert payload["access_token"]
    assert payload["user"]["email"] == email
    assert payload["profile"]["user_id"] == payload["user"]["user_id"]


def test_swagger_oauth_token_endpoint_accepts_form_login() -> None:
    email = _unique_email()
    password = "StrongPassword123!"

    with TestClient(app) as client:
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Swagger OAuth User",
                "anonymous_id": "swagger-oauth-anon",
            },
        )
        assert register_response.status_code == 201

        token_response = client.post(
            "/api/v1/auth/token",
            data={
                "username": email,
                "password": password,
            },
        )

    assert token_response.status_code == 200
    payload = token_response.json()
    assert payload["access_token"]
    assert payload["token_type"] == "bearer"
    assert payload["user"]["email"] == email


def test_login_with_wrong_password_returns_401() -> None:
    email = _unique_email()

    with TestClient(app) as client:
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "StrongPassword123!",
                "full_name": "Wrong Password User",
                "anonymous_id": "wrong-password-anon",
            },
        )
        assert register_response.status_code == 201

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": "WrongPassword123!",
            },
        )

    assert login_response.status_code == 401


def test_get_me_requires_valid_token() -> None:
    with TestClient(app) as client:
        token, register_payload = _register_user(client)

        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == register_payload["user"]["user_id"]


def test_get_me_without_token_returns_401() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/users/me")

    assert response.status_code == 401


def test_user_can_update_profile() -> None:
    with TestClient(app) as client:
        token, _ = _register_user(client)

        response = client.patch(
            "/api/v1/users/me/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "age": 19,
                "skin_type": "combination",
                "concerns": ["acne", "sebum"],
                "budget": "balanced",
                "excluded_ingredients": ["fragrance"],
                "custom_restrictions": ["alcohol"],
                "experience": "guided",
                "values": ["comfort", "price_quality"],
            },
        )

    assert response.status_code == 200
    payload = response.json()

    assert payload["age"] == 19
    assert payload["skin_type"] == "combination"
    assert "acne" in payload["concerns"]
    assert payload["budget"] == "balanced"
    assert "fragrance" in payload["excluded_ingredients"]


def test_user_can_append_questionnaire_history() -> None:
    with TestClient(app) as client:
        token, _ = _register_user(client)

        response = client.post(
            "/api/v1/users/me/profile/questionnaire-history",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "recommendation_id": "rec-test-123",
                "age": 19,
                "skin_type": "combination",
                "concerns": ["acne", "sebum"],
                "budget": "balanced",
                "excluded_ingredients": ["fragrance"],
                "custom_restrictions": [],
                "experience": "guided",
                "values": ["comfort", "price_quality"],
                "total_price_rub": 3440,
                "metadata": {"source": "test"},
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["questionnaire_history"]) == 1
    assert payload["questionnaire_history"][0]["recommendation_id"] == "rec-test-123"
    assert payload["questionnaire_history"][0]["age"] == 19


def test_user_can_update_basic_info() -> None:
    with TestClient(app) as client:
        token, _ = _register_user(client)

        response = client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "full_name": "Updated User",
                "anonymous_id": "updated-anon",
            },
        )

    assert response.status_code == 200
    payload = response.json()

    assert payload["full_name"] == "Updated User"
    assert payload["anonymous_id"] == "updated-anon"
''')

print("Step 3.2 auth and profile frontend integration written successfully.")