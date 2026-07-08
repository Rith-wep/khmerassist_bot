from app.models.conversation import Conversation
from app.repositories.base import TenantRepository


class ConversationRepository(TenantRepository[Conversation]):
    model = Conversation

    def get_by_chat_id(self, customer_chat_id: int) -> Conversation | None:
        return (
            self._scoped_query()
            .filter(Conversation.customer_chat_id == customer_chat_id)
            .order_by(Conversation.started_at.desc())
            .first()
        )
