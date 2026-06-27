from routes.admin_routes import router as admin_router
from routes.auth_routes import router as auth_router
from routes.project_routes import router as project_router
from routes.file_routes import router as file_router
from routes.file_routes import file_router as direct_file_router
from routes.session_routes import router as session_router
from routes.chat_routes import router as chat_router
from routes.settings_routes import router as settings_router
from routes.workflow_routes import router as workflow_router

__all__ = [
    "auth_router",
    "admin_router",
    "project_router",
    "file_router",
    "direct_file_router",
    "session_router",
    "chat_router",
    "settings_router",
    "workflow_router",
]
