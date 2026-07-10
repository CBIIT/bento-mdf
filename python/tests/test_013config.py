"""Tests for bento_mdf.config module."""

import os
import importlib
import logging
import pytest


class TestSettingsWithStsUrl:
    """Test Settings when STS_URL is properly configured."""

    def test_settings_from_env_var(self, monkeypatch):
        monkeypatch.setenv("STS_URL", "http://example.com/v2")
        import bento_mdf.config as config_mod

        reloaded = importlib.reload(config_mod)
        assert reloaded.settings.sts_url == "http://example.com/v2"

    def test_settings_case_insensitive(self, monkeypatch):
        monkeypatch.setenv("STS_URL", "http://case-test.com/v2")
        import bento_mdf.config as config_mod

        reloaded = importlib.reload(config_mod)
        assert reloaded.settings.sts_url == "http://case-test.com/v2"


class TestSettingsWithoutStsUrl:
    """Test fallback behavior when STS_URL is not set."""

    def test_defaults_to_localhost_when_sts_url_missing(self, monkeypatch):
        monkeypatch.delenv("STS_URL", raising=False)
        monkeypatch.setenv("ENV_FILE", "/dev/null")
        # Ensure no .env file is picked up
        monkeypatch.chdir("/tmp")
        import bento_mdf.config as config_mod

        reloaded = importlib.reload(config_mod)
        assert reloaded.settings.sts_url == "http://localhost:8000/v2"

    def test_logs_warning_when_sts_url_missing(self, monkeypatch, caplog):
        monkeypatch.delenv("STS_URL", raising=False)
        monkeypatch.chdir("/tmp")
        import bento_mdf.config as config_mod

        with caplog.at_level(logging.WARN, logger="bento_mdf.config"):
            importlib.reload(config_mod)
        assert "STS_URL env not set" in caplog.text

    def test_sets_env_var_as_fallback(self, monkeypatch):
        monkeypatch.delenv("STS_URL", raising=False)
        monkeypatch.chdir("/tmp")
        import bento_mdf.config as config_mod

        importlib.reload(config_mod)
        assert os.environ["STS_URL"] == "http://localhost:8000/v2"


class TestSettingsValidationError:
    """Test that non-STS_URL validation errors are re-raised."""

    def test_non_sts_validation_error_propagates(self, monkeypatch):
        from pydantic import ValidationError
        from unittest.mock import patch

        monkeypatch.setenv("STS_URL", "http://example.com/v2")

        # Simulate a ValidationError whose message does NOT mention STS_URL
        def raise_other_error(**kwargs):
            from pydantic import BaseModel

            class Strict(BaseModel):
                required_field: int

            Strict.model_validate({})

        with patch(
            "pydantic_settings.BaseSettings.__init__", side_effect=raise_other_error
        ):
            import bento_mdf.config as config_mod

            with pytest.raises(ValidationError):
                importlib.reload(config_mod)
