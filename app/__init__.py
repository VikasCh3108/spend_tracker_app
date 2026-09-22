import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import DEFAULT_SECRET_KEY, settings
from app.database import Base, engine
from app.errors import register_error_handlers
from app.models import Expense, User  # noqa: F401 — register models with Base.metadata
from app.routes import register_routes


def create_app() -> FastAPI:
    """Application factory: creates and configures the FastAPI app."""
    # Fail fast: refuse to start in production with the default secret key
    if not settings.debug and settings.secret_key == DEFAULT_SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY must be set to a non-default value in production. "
            "Set the SECRET_KEY environment variable or set DEBUG=True for development."
        )

    app = FastAPI(
        title=settings.app_name,
        description="Mini Spend Tracker API",
        version="1.0.0",
    )

    # Register routes and error handlers
    register_routes(app)
    register_error_handlers(app)

    # Create database tables
    Base.metadata.create_all(bind=engine)

    # Serve static frontend
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    if os.path.isdir(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")

        @app.get("/", include_in_schema=False)
        async def root():
            return FileResponse(os.path.join(static_dir, "index.html"))

    return app
