from fastapi import APIRouter, FastAPI

api_router = APIRouter(prefix="/api/v1")


def register_routes(app: FastAPI) -> None:
    """Include all route modules into the app.

    Each route module is imported and its router included here.
    New route modules can be added without touching existing code (OCP).
    """
    from app.routes.auth import router as auth_router
    from app.routes.expenses import router as expenses_router
    from app.routes.insights import router as insights_router
    from app.routes.summary import router as summary_router

    api_router.include_router(auth_router, tags=["auth"])
    api_router.include_router(expenses_router, tags=["expenses"])
    api_router.include_router(summary_router, tags=["summary"])
    api_router.include_router(insights_router, tags=["insights"])
    app.include_router(api_router)
