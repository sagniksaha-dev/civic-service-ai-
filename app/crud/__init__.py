from app.crud.user import user_crud
from app.crud.department import department_crud
from app.crud.service import service_crud
from app.crud.citizen import citizen_crud
from app.crud.service_application import service_application_crud
from app.crud.grievance import grievance_crud
from app.crud.knowledge_document import knowledge_document_crud
from app.crud.chat import chat_crud
from app.crud.notification import notification_crud

__all__ = [
    "user_crud",
    "department_crud",
    "service_crud",
    "citizen_crud",
    "service_application_crud",
    "grievance_crud",
    "knowledge_document_crud",
    "chat_crud",
    "notification_crud",
]
