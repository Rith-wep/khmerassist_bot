from typing import Generic, TypeVar

from sqlalchemy.orm import Session

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class TenantRepository(Generic[ModelT]):
    """Base for repositories over tables that carry a business_id column.

    Every instance is bound to one business_id at construction time and every
    query method filters by it — there is no method that accepts business_id
    as an argument, so a caller cannot accidentally query across tenants.
    """

    model: type[ModelT]

    def __init__(self, db: Session, business_id: int):
        if not business_id:
            raise ValueError("business_id is required to construct a TenantRepository")
        self.db = db
        self.business_id = business_id

    def _scoped_query(self):
        return self.db.query(self.model).filter(self.model.business_id == self.business_id)

    def list(self) -> list[ModelT]:
        return self._scoped_query().all()

    def get(self, id_: int) -> ModelT | None:
        return self._scoped_query().filter(self.model.id == id_).first()

    def create(self, **fields) -> ModelT:
        fields["business_id"] = self.business_id
        obj = self.model(**fields)
        self.db.add(obj)
        self.db.flush()
        return obj

    def delete(self, id_: int) -> bool:
        obj = self.get(id_)
        if obj is None:
            return False
        self.db.delete(obj)
        self.db.flush()
        return True
