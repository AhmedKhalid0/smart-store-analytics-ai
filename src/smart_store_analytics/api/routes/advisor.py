"""AI Retail Copilot recommendations and layout optimization API routes."""

from fastapi import APIRouter, Request, status

from smart_store_analytics.core.advisor import CopilotAnalysisResult, RetailCopilotAdvisor
from smart_store_analytics.core.video_processor import VideoProcessor

router = APIRouter(prefix="/api/v1/advisor", tags=["AI Retail Copilot"])


@router.get("/insights", response_model=CopilotAnalysisResult, status_code=status.HTTP_200_OK)
async def get_copilot_insights(request: Request) -> CopilotAnalysisResult:
    """Evaluates spatial zone dwell-times, footfall patterns, and queue telemetry to generate AI recommendations."""
    processor: VideoProcessor = request.app.state.processor

    # Ensure baseline simulation has run
    if processor.spatial_engine.total_footfall == 0:
        processor.process_synthetic_simulation(num_frames=60)

    advisor = RetailCopilotAdvisor(processor)
    return advisor.analyze()
