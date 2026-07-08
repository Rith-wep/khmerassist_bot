from app.models.bot_config import BotConfig
from app.repositories.base import TenantRepository


class BotConfigRepository(TenantRepository[BotConfig]):
    model = BotConfig

    def get_for_business(self) -> BotConfig | None:
        return self._scoped_query().first()
