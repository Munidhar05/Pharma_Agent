import pytest
from backend.app.main import health_check, root
from backend.app.config import settings

def test_health_endpoint(test_db):
    result = health_check(db=test_db)
    assert result["status"] == "online"
    assert result["database"] == "healthy"
    assert result["app_name"] == settings.APP_NAME
    assert result["freshness_period_days"] == 7

def test_root_endpoint():
    result = root()
    assert "Welcome" in result["message"]
    assert result["docs_url"] == "/docs"
    assert result["health_check"] == "/health"

def test_dashboard_endpoint():
    from backend.app.main import dashboard
    response = dashboard()
    assert response.status_code == 200
    assert "text/html" in response.media_type
