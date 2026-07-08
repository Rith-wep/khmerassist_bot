from sqlalchemy.orm import Session

from app.models.business import Business


class BusinessRepository:
    """Not tenant-scoped: businesses ARE the tenants, not tenant-owned data."""

    def __init__(self, db: Session):
        self.db = db

    def get(self, id_: int) -> Business | None:
        return self.db.query(Business).filter(Business.id == id_).first()

    def list_all(self) -> list[Business]:
        return self.db.query(Business).all()

    def create(self, **fields) -> Business:
        obj = Business(**fields)
        self.db.add(obj)
        self.db.flush()
        return obj
