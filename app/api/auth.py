from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

from app.config import settings
from app.database.connection import get_connection


password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(user_id: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": user_id,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def authenticate_user(user_id: str, password: str) -> bool:
    connection = get_connection()

    try:
        user = connection.execute(
            """
            SELECT password_hash
            FROM customer_credentials
            WHERE user_id = ? AND active = 1
            """,
            (user_id,),
        ).fetchone()

        if not user:
            return False

        return verify_password(password, user["password_hash"])

    finally:
        connection.close()


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou sessão expirada.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        user_id = payload.get("sub")

        if not user_id or not isinstance(user_id, str):
            raise credentials_exception

        connection = get_connection()

        try:
            user = connection.execute(
                """
                SELECT user_id
                FROM customer_credentials
                WHERE user_id = ? AND active = 1
                """,
                (user_id,),
            ).fetchone()
        finally:
            connection.close()

        if not user:
            raise credentials_exception

        return user_id

    except jwt.InvalidTokenError:
        raise credentials_exception