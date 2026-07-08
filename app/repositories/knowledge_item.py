from app.models.knowledge_item import KnowledgeItem
from app.repositories.base import TenantRepository


class KnowledgeItemRepository(TenantRepository[KnowledgeItem]):
    model = KnowledgeItem

    def list_ordered(self) -> list[KnowledgeItem]:
        return self._scoped_query().order_by(KnowledgeItem.sort_order).all()
