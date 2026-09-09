"""API routes for Webhook and Telegram alert notification configuration and testing."""

from pathlib import Path
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from smart_store_analytics.core.notifier import (
    AlertDispatcher,
    AlertEvent,
    NotificationConfig,
)
from smart_store_analytics.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/notifications", tags=["Alert Notifications"])


class TestWebhookRequest(BaseModel):
    """Payload to test external webhook endpoint."""

    webhook_url: str = Field(..., description="Target Webhook URL")


class TestTelegramRequest(BaseModel):
    """Payload to test Telegram bot message delivery."""

    bot_token: str = Field(..., description="Telegram Bot Token")
    chat_id: str = Field(..., description="Target Chat or Channel ID")


def get_dispatcher(request: Request) -> AlertDispatcher:
    """Safely retrieves or lazily instantiates the AlertDispatcher."""
    if not hasattr(request.app.state, "alert_dispatcher") or request.app.state.alert_dispatcher is None:
        settings = getattr(request.app.state, "settings", None)
        cfg_path = (settings.data_dir / "notifications_config.json") if settings else Path("data/notifications_config.json")
        request.app.state.alert_dispatcher = AlertDispatcher(config_path=cfg_path)
    return request.app.state.alert_dispatcher


@router.get("/config", response_model=NotificationConfig, status_code=status.HTTP_200_OK)
async def get_notification_config(request: Request) -> NotificationConfig:
    """Returns the current webhook and Telegram alert configuration."""
    dispatcher = get_dispatcher(request)
    return dispatcher.get_config()


@router.put("/config", response_model=NotificationConfig, status_code=status.HTTP_200_OK)
async def update_notification_config(
    payload: NotificationConfig,
    request: Request,
) -> NotificationConfig:
    """Updates and persists webhook URL, Telegram tokens, and alert filtering preferences."""
    dispatcher = get_dispatcher(request)
    return dispatcher.save_config(payload)


@router.post("/test-webhook", status_code=status.HTTP_200_OK)
async def test_webhook_connection(
    payload: TestWebhookRequest,
    request: Request,
) -> Dict[str, Any]:
    """Transmits a live verification ping to the specified webhook endpoint."""
    dispatcher = get_dispatcher(request)
    result = await dispatcher.test_webhook(payload.webhook_url)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook test failed: {result['message']}",
        )
    return result


@router.post("/test-telegram", status_code=status.HTTP_200_OK)
async def test_telegram_connection(
    payload: TestTelegramRequest,
    request: Request,
) -> Dict[str, Any]:
    """Transmits a verification alert to the specified Telegram bot and chat ID."""
    dispatcher = get_dispatcher(request)
    result = await dispatcher.test_telegram(payload.bot_token, payload.chat_id)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Telegram test failed: {result['message']}",
        )
    return result


@router.post("/dispatch-sample", status_code=status.HTTP_200_OK)
async def dispatch_sample_alert(request: Request) -> Dict[str, Any]:
    """Simulates an urgent queue SLA breach and dispatches it through configured active channels."""
    dispatcher = get_dispatcher(request)
    sample_alert = AlertEvent(
        alert_id="sample_sla_001",
        event_type="queue_sla_breached",
        severity="critical",
        zone_id="zone_checkout",
        zone_name="Checkout & Service Queue",
        metric_value=7.0,
        threshold_value=5.0,
        message="Simulated SLA alert: 7 customers queued with wait time of 210s exceeding 180s threshold",
        recommendation="Open backup cashier register 02 immediately",
    )
    return await dispatcher.dispatch_alert(sample_alert)
