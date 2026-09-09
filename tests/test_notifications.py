"""Test suite for Webhook & Telegram Notification Engine & API Endpoints."""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from smart_store_analytics.api.app import create_app
from smart_store_analytics.core.notifier import (
    AlertDispatcher,
    AlertEvent,
    NotificationConfig,
)


class TestAlertDispatcher:
    """Unit tests for AlertDispatcher."""

    def test_default_config(self):
        dispatcher = AlertDispatcher()
        cfg = dispatcher.get_config()
        assert isinstance(cfg, NotificationConfig)
        assert cfg.webhook_enabled is False
        assert cfg.telegram_enabled is False
        assert cfg.min_severity_level == "warning"

    def test_save_and_reload_config(self):
        import shutil
        import tempfile
        temp_dir = Path(tempfile.mkdtemp(prefix="test_notif_cfg_"))
        try:
            cfg_path = temp_dir / "notif.json"
            dispatcher = AlertDispatcher(config_path=cfg_path)
            new_cfg = NotificationConfig(
                webhook_url="https://hooks.slack.com/services/test/123",
                webhook_enabled=True,
                telegram_bot_token="123456:ABC-DEF",
                telegram_chat_id="-100987654321",
                telegram_enabled=True,
                min_severity_level="critical",
                cooldown_seconds=30,
            )
            saved = dispatcher.save_config(new_cfg)
            assert saved.webhook_enabled is True
            assert saved.cooldown_seconds == 30

            # Reload
            reloaded = AlertDispatcher(config_path=cfg_path)
            assert reloaded.config.webhook_url == "https://hooks.slack.com/services/test/123"
            assert reloaded.config.telegram_enabled is True
            assert reloaded.config.min_severity_level == "critical"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.anyio
    async def test_cooldown_suppression(self):
        dispatcher = AlertDispatcher()
        dispatcher.config.cooldown_seconds = 100
        event = AlertEvent(
            alert_id="test_sla_1",
            event_type="queue_sla_breached",
            severity="critical",
            zone_id="zone_checkout",
            zone_name="Checkout Desk",
            metric_value=8.0,
            threshold_value=5.0,
            message="Test bottleneck",
            recommendation="Open register",
        )
        res1 = await dispatcher.dispatch_alert(event)
        # Second immediate dispatch should be throttled
        res2 = await dispatcher.dispatch_alert(event)
        assert res2["status"] == "throttled"

    @pytest.mark.anyio
    async def test_mock_test_webhook(self):
        dispatcher = AlertDispatcher()
        res = await dispatcher.test_webhook("https://mock.webhook.local/alerts")
        assert res["success"] is True
        assert res["status_code"] == 200

    @pytest.mark.anyio
    async def test_mock_test_telegram(self):
        dispatcher = AlertDispatcher()
        res = await dispatcher.test_telegram("mock_bot_token", "12345678")
        assert res["success"] is True
        assert res["status_code"] == 200


class TestNotificationsAPI:
    """Integration tests for /api/v1/notifications HTTP endpoints."""

    @pytest.fixture
    def client(self):
        import shutil
        import tempfile
        temp_dir = Path(tempfile.mkdtemp(prefix="test_notif_api_"))
        try:
            cfg_path = temp_dir / "notif.json"
            dispatcher = AlertDispatcher(config_path=cfg_path)
            app = create_app()
            app.state.alert_dispatcher = dispatcher
            c = TestClient(app)
            yield c
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_get_config_endpoint(self, client: TestClient):
        res = client.get("/api/v1/notifications/config")
        assert res.status_code == 200
        data = res.json()
        assert "webhook_enabled" in data
        assert "telegram_enabled" in data

    def test_update_config_endpoint(self, client: TestClient):
        payload = {
            "webhook_url": "https://example.com/webhook",
            "webhook_enabled": True,
            "telegram_bot_token": "token123",
            "telegram_chat_id": "chat456",
            "telegram_enabled": False,
            "min_severity_level": "info",
            "cooldown_seconds": 120,
        }
        res = client.put("/api/v1/notifications/config", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["webhook_url"] == "https://example.com/webhook"
        assert data["webhook_enabled"] is True
        assert data["cooldown_seconds"] == 120

    def test_test_webhook_endpoint(self, client: TestClient):
        res = client.post(
            "/api/v1/notifications/test-webhook",
            json={"webhook_url": "https://mock.service.local/webhook"},
        )
        assert res.status_code == 200
        assert res.json()["success"] is True

    def test_test_telegram_endpoint(self, client: TestClient):
        res = client.post(
            "/api/v1/notifications/test-telegram",
            json={"bot_token": "mock_token", "chat_id": "999"},
        )
        assert res.status_code == 200
        assert res.json()["success"] is True

    def test_dispatch_sample_endpoint(self, client: TestClient):
        res = client.post("/api/v1/notifications/dispatch-sample")
        assert res.status_code == 200
