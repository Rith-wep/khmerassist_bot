from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/signin")

_INVALID_TOKEN = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired token",
    headers={"WWW-Authenticate": "Bearer"},
)


class CurrentUser:
    def __init__(self, user_id: int, business_id: int):
        self.user_id = user_id
        self.business_id = business_id


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> CurrentUser:
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
        business_id = int(payload["business_id"])
    except Exception:
        raise _INVALID_TOKEN

    # Re-checked against the DB every request (not just trusted from the token)
    # so a deleted user or business reassignment can't still act as this user.
    user = db.get(User, user_id)
    if user is None or user.business_id != business_id:
        raise _INVALID_TOKEN

    return CurrentUser(user_id=user.id, business_id=user.business_id)
