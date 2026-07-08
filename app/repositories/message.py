from app.models.message import Message
from app.repositories.base import TenantRepository


class MessageRepository(TenantRepository[Message]):
    model = Message

    def list_for_conversation(self, conversation_id: int) -> list[Message]:
        return (
            self._scoped_query()
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .all()
        )
