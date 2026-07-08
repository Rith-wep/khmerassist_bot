from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.repositories.business import BusinessRepository
from app.repositories.user import UserRepository, get_user_by_email
from app.schemas.auth import SigninRequest, SignupRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> TokenResponse:
    if get_user_by_email(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered"
        )

    business = BusinessRepository(db).create(
        name=payload.business_name,
        business_type=payload.business_type,
        default_language="km",
        plan="trial",
        status="active",
    )
    db.flush()

    user = UserRepository(db, business.id).create(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="owner",
    )
    db.flush()

    # Token creation before commit: if it fails, nothing is persisted — no
    # orphaned business/user left behind with no way to get a token for it.
    token = create_access_token(user_id=user.id, business_id=business.id)
    db.commit()
    return TokenResponse(access_token=token, business_id=business.id, business_name=business.name)


@router.post("/signin", response_model=TokenResponse)
def signin(payload: SigninRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = get_user_by_email(db, payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
        )

    business = BusinessRepository(db).get(user.business_id)
    token = create_access_token(user_id=user.id, business_id=user.business_id)
    return TokenResponse(access_token=token, business_id=business.id, business_name=business.name)
