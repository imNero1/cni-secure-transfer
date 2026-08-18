import os
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import get_user_by_username

load_dotenv()

# Fallback prevents app crash if .env file is missing on local machine
JWT_SECRET = os.getenv("JWT_SECRET", "fallback_dev_secret_39f08123a4b56c7d8e9f0123")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

security = HTTPBearer()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(db: Session, username: str, password: str):
    """Returns the User object if credentials are valid, else None."""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_token(role: str, username: str | None = None) -> str:
    """Generates a JWT token for a given role (valid for 8 hours)."""
    payload = {
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=8)
    }
    if username:
        payload["sub"] = username
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def require_role(required_role: str):
    """Dependency that verifies incoming HTTP Bearer tokens for a specific role."""
    def dependency(credentials: HTTPAuthorizationCredentials = Security(security)):
        token = credentials.credentials
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
            role = payload.get("role")
            if role != required_role:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Access denied: Requires {required_role} role."
                )
            return role
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired.")
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid or tampered token signature.")
    return dependency