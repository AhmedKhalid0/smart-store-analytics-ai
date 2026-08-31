"""Rich interactive Command Line Interface for Smart-Store-Analytics."""

import sys
from pathlib import Path
from typing import Optional
import typer
import uvicorn
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Force UTF-8 on Windows stdout/stderr
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from smart_store_analytics import __version__
from smart_store_analytics.core.heatmap_generator import SpatialHeatmapGenerator
from smart_store_analytics.core.spatial_analytics import SpatialAnalyticsEngine
from smart_store_analytics.core.video_processor import VideoProcessor
from smart_store_analytics.utils.config import get_settings

app = typer.Typer(
    name="smart-store-analytics",
    help="Smart-Store-Analytics: Computer Vision & Retail Spatial Intelligence Engine CLI",
    add_completion=False,
)
console = Console(force_terminal=True)


@app.command("stats")
def show_stats():
    """Displays vision hardware parameters, configured store zones, and tracking algorithms."""
    settings = get_settings()
    spatial_engine = SpatialAnalyticsEngine()

    table = Table(title="Smart-Store-Analytics System Telemetry", show_header=True, header_style="bold cyan")
    table.add_column("Telemetry Parameter", style="dim", width=28)
    table.add_column("Configured Value", style="bold white")

    table.add_row("Version", __version__)
    table.add_row("Object Detector", settings.detector_model)
    table.add_row("Detection Confidence", f"{settings.detection_confidence_threshold * 100:.0f}%")
    table.add_row("MOT Algorithm", "ByteTrack / Centroid Proximity")
    table.add_row("Tracking IoU Threshold", str(settings.tracking_iou_threshold))
    table.add_row("Max Queue SLA Threshold", f"{settings.max_queue_length_threshold} shoppers / {settings.max_queue_wait_seconds}s")
    table.add_row("Configured Store Zones", f"{len(spatial_engine.zones)} active commercial polygons")

    console.print(table)


@app.command("heatmap")
def export_heatmap(
    output_path: Path = typer.Option(Path("./outputs/heatmap.ppm"), "--output", "-o", help="Output path for heatmap image"),
    frames: int = typer.Option(100, "--frames", "-f", help="Number of simulated video frames"),
):
    """Generates and exports a 2D spatial customer traffic heatmap."""
    processor = VideoProcessor()
    with console.status(f"[bold cyan]Simulating {frames} video frames and accumulating Gaussian density..."):
        processor.process_synthetic_simulation(num_frames=frames)
        output_file = processor.heatmap_gen.export_ppm_image(output_path)

    console.print(f"[bold green][OK] Heatmap generated and saved:[/bold green] [cyan]{output_file}[/cyan]")


@app.command("process")
def process_stream(
    frames: int = typer.Option(100, "--frames", "-f", help="Number of frames to process"),
):
    """Processes video stream, tracking individuals, zone visits, and queue bottlenecks."""
    processor = VideoProcessor()

    with console.status(f"[bold purple]Processing {frames} video stream frames..."):
        summary = processor.process_synthetic_simulation(num_frames=frames)

    # Zones Table
    table = Table(title=f"Zone Engagement Summary (Total Footfall: {summary.total_footfall})", show_header=True, header_style="bold purple")
    table.add_column("Zone Name", style="cyan", width=26)
    table.add_column("Category", style="yellow", width=14)
    table.add_column("Total Visits", style="white", width=14)
    table.add_column("Avg Dwell Time", style="green", width=16)

    for z in summary.zone_metrics.values():
        table.add_row(z["name"], z["category"], str(z["total_visits"]), f"{z['avg_dwell_seconds']:.1f}s")

    console.print(table)

    if summary.queue_alerts:
        console.print(f"\n[bold red]⚠️ Queue Bottlenecks Detected ({len(summary.queue_alerts)}):[/bold red]")
        for a in summary.queue_alerts:
            console.print(f"  [{a.severity}] [yellow]{a.timestamp}[/yellow]: {a.recommendation}")
    else:
        console.print("\n[bold green][OK] Queue operating within SLA limits.[/bold green]")


@app.command("serve")
def start_server(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Bind host address"),
    port: int = typer.Option(8095, "--port", "-p", help="Bind TCP port"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload"),
):
    """Starts the FastAPI Retail Analytics Web Dashboard."""
    console.print(f"[bold purple]Starting Smart-Store-Analytics Dashboard at http://{host}:{port}[/bold purple]")
    uvicorn.run("smart_store_analytics.api.app:create_app", host=host, port=port, reload=reload, factory=True)


@app.command("demo")
def run_demo():
    """Runs a complete self-contained computer vision retail intelligence demonstration."""
    console.print("[bold purple]Running Smart-Store-Analytics Autonomous Vision Demo...[/bold purple]\n")
    process_stream(frames=120)
    console.print("\n[bold green][OK] Retail spatial intelligence demo completed successfully![/bold green]")


if __name__ == "__main__":
    app()
