from app.models.lead import Lead
from app.repositories.base import TenantRepository


class LeadRepository(TenantRepository[Lead]):
    model = Lead
