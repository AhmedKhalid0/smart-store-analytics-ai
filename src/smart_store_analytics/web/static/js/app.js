/**
 * Smart-Store-Analytics Interactive Vision & Spatial Dashboard Frontend
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const kpiFootfall = document.getElementById('kpi-footfall');
    const kpiActive = document.getElementById('kpi-active');
    const kpiDwell = document.getElementById('kpi-dwell');
    const kpiAlerts = document.getElementById('kpi-alerts');
    const kpiAlertStatus = document.getElementById('kpi-alert-status');
    const zonesList = document.getElementById('zones-list');
    const alertsFeed = document.getElementById('alerts-feed');
    const btnSimulate = document.getElementById('btn-simulate');
    const toggleHeatmap = document.getElementById('toggle-heatmap');
    const canvas = document.getElementById('store-canvas');
    const ctx = canvas.getContext('2d');

    // Dashboard State
    let heatmapMatrix = null;
    let zonesData = [];
    let trajectoriesData = [];

    // 1. Fetch Heatmap Density Matrix
    async function loadHeatmap() {
        try {
            const res = await fetch('/api/v1/heatmap');
            if (res.ok) {
                const data = await res.json();
                heatmapMatrix = data.matrix;
            }
        } catch (err) {
            console.error('Heatmap load error:', err);
        }
    }

    // 2. Fetch Live Analytics & KPIs
    async function loadAnalytics() {
        try {
            const res = await fetch('/api/v1/analytics/stats');
            if (res.ok) {
                const data = await res.json();
                
                // Update KPIs
                kpiFootfall.textContent = data.total_footfall;
                kpiActive.textContent = data.active_shoppers;
                
                // Calculate average dwell across all zones
                const totalDwell = data.zones.reduce((sum, z) => sum + z.avg_dwell_seconds, 0);
                const avgDwell = data.zones.length > 0 ? (totalDwell / data.zones.length).toFixed(1) : 0.0;
                kpiDwell.textContent = `${avgDwell}s`;

                // Update Queue Alerts
                kpiAlerts.textContent = data.queue_alerts.length;
                if (data.queue_alerts.length > 0) {
                    kpiAlertStatus.textContent = 'Action Required';
                    kpiAlertStatus.className = 'kpi-badge text-rose';
                } else {
                    kpiAlertStatus.textContent = 'Normal';
                    kpiAlertStatus.className = 'kpi-badge text-emerald';
                }

                zonesData = data.zones;
                trajectoriesData = data.trajectories;

                renderZonesList(data.zones);
                renderAlerts(data.queue_alerts);
                renderCanvas();
            }
        } catch (err) {
            console.error('Analytics load error:', err);
        }
    }

    // 3. Render Zone Breakdown
    function renderZonesList(zones) {
        zonesList.innerHTML = '';
        zones.forEach(z => {
            const item = document.createElement('div');
            item.className = 'zone-item';
            item.style.borderLeftColor = z.color_hex;
            item.innerHTML = `
                <div class="zone-item-header">
                    <span>${z.name}</span>
                    <span style="color: ${z.color_hex}">${z.current_occupants} active</span>
                </div>
                <div class="zone-item-metrics">
                    <span>Visits: <strong>${z.total_visits}</strong></span>
                    <span>Avg Dwell: <strong>${z.avg_dwell_seconds.toFixed(1)}s</strong></span>
                </div>
            `;
            zonesList.appendChild(item);
        });
    }

    // 4. Render Queue Alerts
    function renderAlerts(alerts) {
        if (!alerts || alerts.length === 0) {
            alertsFeed.innerHTML = '<div class="empty-alerts">No active bottleneck alerts. Queue SLA operating within normal limits.</div>';
            return;
        }

        alertsFeed.innerHTML = '';
        alerts.forEach(a => {
            const card = document.createElement('div');
            card.className = `alert-card ${a.severity}`;
            card.innerHTML = `
                <div class="alert-header">
                    <span class="${a.severity === 'CRITICAL' ? 'text-rose' : 'text-amber'}">${a.severity}: Queue SLA Breach</span>
                    <span class="text-dim">${a.timestamp}</span>
                </div>
                <div>${a.recommendation}</div>
            `;
            alertsFeed.appendChild(card);
        });
    }

    // 5. Draw 2D Floorplan Canvas
    function renderCanvas() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // A. Background Grid
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)';
        ctx.lineWidth = 1;
        for (let x = 0; x < canvas.width; x += 40) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, canvas.height);
            ctx.stroke();
        }
        for (let y = 0; y < canvas.height; y += 40) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(canvas.width, y);
            ctx.stroke();
        }

        // B. Draw Spatial Heatmap (if enabled)
        if (toggleHeatmap.checked && heatmapMatrix) {
            const gh = heatmapMatrix.length;
            const gw = heatmapMatrix[0].length;
            const cellW = canvas.width / gw;
            const cellH = canvas.height / gh;

            for (let r = 0; r < gh; r++) {
                for (let c = 0; c < gw; c++) {
                    const val = heatmapMatrix[r][c];
                    if (val > 0.05) {
                        ctx.fillStyle = `rgba(244, 63, 94, ${val * 0.45})`;
                        ctx.fillRect(c * cellW, r * cellH, cellW + 1, cellH + 1);
                    }
                }
            }
        }

        // C. Draw Commercial Zones
        const defaultZones = [
            { id: "zone_entrance", name: "Entrance & Foyer", polygon: [[50, 50], [350, 50], [350, 250], [50, 250]], color: "rgba(6, 182, 212, 0.18)", stroke: "#06b6d4" },
            { id: "zone_promotions", name: "Promotions & New Arrivals", polygon: [[380, 200], [680, 200], [680, 480], [380, 480]], color: "rgba(168, 85, 247, 0.18)", stroke: "#a855f7" },
            { id: "zone_electronics", name: "Electronics & Premium Wall", polygon: [[750, 50], [1200, 50], [1200, 350], [750, 350]], color: "rgba(16, 185, 129, 0.18)", stroke: "#10b981" },
            { id: "zone_checkout", name: "Checkout & Service Queue", polygon: [[800, 420], [1220, 420], [1220, 680], [800, 680]], color: "rgba(245, 158, 11, 0.18)", stroke: "#f59e0b" },
        ];

        defaultZones.forEach(z => {
            ctx.beginPath();
            ctx.moveTo(z.polygon[0][0], z.polygon[0][1]);
            for (let i = 1; i < z.polygon.length; i++) {
                ctx.lineTo(z.polygon[i][0], z.polygon[i][1]);
            }
            ctx.closePath();
            ctx.fillStyle = z.color;
            ctx.fill();
            ctx.strokeStyle = z.stroke;
            ctx.lineWidth = 2;
            ctx.stroke();

            // Label
            ctx.fillStyle = z.stroke;
            ctx.font = "bold 13px Inter, sans-serif";
            ctx.fillText(z.name, z.polygon[0][0] + 12, z.polygon[0][1] + 24);
        });

        // D. Draw Customer Trajectory Trails & Current Positions
        trajectoriesData.forEach(t => {
            if (t.points && t.points.length > 1) {
                ctx.beginPath();
                ctx.moveTo(t.points[0][0], t.points[0][1]);
                for (let i = 1; i < t.points.length; i++) {
                    ctx.lineTo(t.points[i][0], t.points[i][1]);
                }
                ctx.strokeStyle = "rgba(6, 182, 212, 0.5)";
                ctx.lineWidth = 3;
                ctx.setLineDash([4, 4]);
                ctx.stroke();
                ctx.setLineDash([]);
            }

            // Current Position Point & ID Tag
            if (t.current_pos) {
                const [px, py] = t.current_pos;
                // Outer glow
                ctx.beginPath();
                ctx.arc(px, py, 10, 0, 2 * Math.PI);
                ctx.fillStyle = "rgba(6, 182, 212, 0.3)";
                ctx.fill();

                // Center dot
                ctx.beginPath();
                ctx.arc(px, py, 5, 0, 2 * Math.PI);
                ctx.fillStyle = "#38bdf8";
                ctx.fill();

                // ID Tag
                ctx.fillStyle = "#ffffff";
                ctx.font = "11px JetBrains Mono, monospace";
                ctx.fillText(`ID #${t.track_id}`, px + 12, py + 4);
            }
        });
    }

    toggleHeatmap.addEventListener('change', renderCanvas);

    // 6. Trigger Simulation Stream
    btnSimulate.addEventListener('click', async () => {
        btnSimulate.disabled = true;
        btnSimulate.textContent = 'Simulating Stream...';
        try {
            await fetch('/api/v1/analytics/simulate', { method: 'POST' });
            await loadHeatmap();
            await loadAnalytics();
        } catch (err) {
            alert('Simulation failed: ' + err.message);
        } finally {
            btnSimulate.disabled = false;
            btnSimulate.textContent = '▶️ Run Simulation Stream';
        }
    });

    // Initial Load & Polling
    loadHeatmap();
    loadAnalytics();
});
