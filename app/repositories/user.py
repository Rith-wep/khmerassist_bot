from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base import TenantRepository


class UserRepository(TenantRepository[User]):
    model = User


def get_user_by_email(db: Session, email: str) -> User | None:
    """The one sanctioned cross-tenant lookup: login happens before business_id is known."""
    return db.query(User).filter(User.email == email).first()
