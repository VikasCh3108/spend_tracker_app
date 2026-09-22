"""Test that create_app() fails fast when SECRET_KEY is default in production mode."""

import os
from unittest import mock

import pytest


class TestSecretKeyFailFast:
    def test_create_app_raises_with_default_key_in_production(self):
        """create_app() should raise RuntimeError if SECRET_KEY is default and DEBUG=False."""
        # Temporarily override env vars to simulate production
        with mock.patch.dict(
            os.environ,
            {"SECRET_KEY": "dev-secret-key-change-in-production", "DEBUG": "False"},
        ):
            # Force re-import of app.config to pick up new env values
            import importlib

            import app.config
            importlib.reload(app.config)
            import app
            importlib.reload(app)

            with pytest.raises(RuntimeError, match="SECRET_KEY must be set"):
                app.create_app()

    def test_create_app_works_with_custom_key_in_production(self):
        """create_app() should succeed if SECRET_KEY is non-default and DEBUG=False."""
        with mock.patch.dict(
            os.environ,
            {"SECRET_KEY": "a-real-production-secret-key", "DEBUG": "False"},
        ):
            import importlib

            import app.config
            importlib.reload(app.config)
            import app
            importlib.reload(app)

            # Should not raise
            app_instance = app.create_app()
            assert app_instance is not None

    def test_create_app_works_with_default_key_in_debug(self):
        """create_app() should succeed if SECRET_KEY is default but DEBUG=True."""
        with mock.patch.dict(
            os.environ,
            {"SECRET_KEY": "dev-secret-key-change-in-production", "DEBUG": "True"},
        ):
            import importlib

            import app.config
            importlib.reload(app.config)
            import app
            importlib.reload(app)

            # Should not raise
            app_instance = app.create_app()
            assert app_instance is not None
