from fastapi import APIRouter
from app.api.v1.endpoints import (
    applications,
    auth,
    chat,
    citizens,
    departments,
    documents,
    grievances,
    health,
    notifications,
    services,
    users,
)

api_router = APIRouter()

# System & Authentication
api_router.include_router(health.router, tags=["Health & System"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Identity"])
api_router.include_router(users.router, prefix="/users", tags=["User Management"])

# Domain Catalogues & Profiles
api_router.include_router(departments.router, prefix="/departments", tags=["Departments"])
api_router.include_router(services.router, prefix="/services", tags=["Service Catalogue"])
api_router.include_router(citizens.router, prefix="/citizens", tags=["Citizen Profiles"])

# Workflow Engines
api_router.include_router(applications.router, prefix="/applications", tags=["Service Applications"])
api_router.include_router(grievances.router, prefix="/grievances", tags=["Grievance System"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notification Logs"])

# Knowledge Base & Grounded RAG
api_router.include_router(documents.router, prefix="/documents", tags=["Knowledge Documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["Civic Chatbot & RAG"])
