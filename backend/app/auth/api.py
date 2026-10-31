"""Registration, login, and current-user endpoints."""
import re

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.auth.service import (
    DUMMY_HASH, create_access_token, decode_access_token, hash_password,
    normalize_email, verify_password,
)
from app.database import get_db_session
from app.models import User

router = APIRouter(prefix="/auth", tags=["authentication"])
bearer = HTTPBearer(auto_error=False)
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def user_response(user: User) -> UserResponse:
    return UserResponse(id=user.id, email=user.email)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        user_id = decode_access_token(credentials.credentials)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = await session.scalar(select(User).where(User.id == user_id, User.is_active.is_(True)))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account unavailable")
    return user


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, session: AsyncSession = Depends(get_db_session)):
    email = normalize_email(payload.email)
    if not EMAIL_PATTERN.fullmatch(email):
        raise HTTPException(status_code=422, detail="Enter a valid email address")
    if await session.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(email=email, password_hash=hash_password(payload.password))
    session.add(user)
    try:
        await session.commit()
        await session.refresh(user)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    return TokenResponse(access_token=create_access_token(user.id), user=user_response(user))


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_db_session)):
    email = normalize_email(payload.email)
    user = await session.scalar(select(User).where(User.email == email))
    hashed = user.password_hash if user is not None else DUMMY_HASH
    valid = verify_password(payload.password, hashed)
    if user is None or not valid or not user.is_active:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return TokenResponse(access_token=create_access_token(user.id), user=user_response(user))


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user_response(user)
