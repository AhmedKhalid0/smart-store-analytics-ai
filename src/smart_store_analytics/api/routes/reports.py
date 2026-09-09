"""Executive reporting and CSV data export API routes."""

from fastapi import APIRouter, Query, Request, Response
from fastapi.responses import HTMLResponse

from smart_store_analytics.core.reporter import ReportGenerator

router = APIRouter(prefix="/api/v1/reports", tags=["Executive Reports & Data Export"])


@router.get("/executive", response_class=HTMLResponse)
async def get_executive_report(
    request: Request,
    store_name: str = Query("Smart Store AI — Flagship Commercial Venue", description="Custom Store Name"),
    period: str = Query("Today (Live Operational Window)", description="Reporting Period"),
) -> HTMLResponse:
    """Generates an executive-ready, print-optimized performance summary document."""
    processor = request.app.state.processor
    reporter = ReportGenerator(processor)
    html_content = reporter.generate_executive_html(store_name=store_name, period_label=period)
    return HTMLResponse(content=html_content)


@router.get("/export/dwell-csv")
async def export_dwell_csv(request: Request) -> Response:
    """Exports raw commercial zone engagement and dwell-time metrics as CSV."""
    processor = request.app.state.processor
    reporter = ReportGenerator(processor)
    csv_data = reporter.export_dwell_csv()

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=store_dwell_telemetry.csv",
        },
    )


@router.get("/export/queue-csv")
async def export_queue_csv(request: Request) -> Response:
    """Exports checkout queue SLA anomaly log as CSV."""
    processor = request.app.state.processor
    reporter = ReportGenerator(processor)
    csv_data = reporter.export_queue_csv()

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=queue_sla_violations.csv",
        },
    )
