from django.conf import settings


def test_settings_loaded():
    assert settings.SECRET_KEY is not None
    assert settings.INSTALLED_APPS is not None
    assert "metrics" in settings.INSTALLED_APPS
