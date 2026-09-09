/**
 * Smart Store AI — Human-Crafted Retail Spatial Intelligence & Trajectory Studio
 * Pure Vanilla JavaScript, High-DPI Canvas Rendering, Smooth Animations & Theme Management
 */

document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------------------
    // 1. Theme Initialization & Toggle
    // -------------------------------------------------------------------------
    const themeToggleBtn = document.getElementById('theme-toggle');
    const savedTheme = localStorage.getItem('smartstore-theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);

    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('smartstore-theme', newTheme);
        renderCanvas();
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', toggleTheme);
    }

    // Export Dropdown Setup
    const exportDropdownBtn = document.getElementById('export-dropdown-btn');
    const exportDropdownWrapper = exportDropdownBtn ? exportDropdownBtn.closest('.dropdown-wrapper') : null;

    if (exportDropdownBtn && exportDropdownWrapper) {
        exportDropdownBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            exportDropdownWrapper.classList.toggle('open');
        });

        document.addEventListener('click', (e) => {
            if (!exportDropdownWrapper.contains(e.target)) {
                exportDropdownWrapper.classList.remove('open');
            }
        });
    }

    // -------------------------------------------------------------------------
    // 2. DOM Elements & State
    // -------------------------------------------------------------------------
    const kpiFootfall = document.getElementById('kpi-footfall');
    const kpiActive = document.getElementById('kpi-active');
    const kpiDwell = document.getElementById('kpi-dwell');
    const kpiAlerts = document.getElementById('kpi-alerts');
    const kpiSlaTag = document.getElementById('kpi-sla-tag');
    const slaHealthChip = document.getElementById('sla-health-chip');
    const queueOverallBadge = document.getElementById('queue-overall-badge');
    
    const zonesList = document.getElementById('zones-list');
    const alertsFeed = document.getElementById('alerts-feed');
    const tracksList = document.getElementById('tracks-list');
    const quickFrameCount = document.getElementById('quick-frame-count');
    
    const btnSimulate = document.getElementById('btn-simulate');
    const btnStreamAuto = document.getElementById('btn-stream-auto');
    const btnStreamText = document.getElementById('btn-stream-text');

    const toggleHeatmap = document.getElementById('toggle-heatmap');
    const toggleTrajectories = document.getElementById('toggle-trajectories');
    const toggleZones = document.getElementById('toggle-zones');
    const toggleFixtures = document.getElementById('toggle-fixtures');

    const canvas = document.getElementById('store-canvas');
    const ctx = canvas.getContext('2d');

    // State Variables
    let heatmapMatrix = null;
    let zonesData = [];
    let trajectoriesData = [];
    let hoveredZoneId = null;
    let selectedTrackId = null;
    let isAutoPlaying = false;
    let playIntervalId = null;
    let frameCounter = 120;

    // Display Layer States
    const layers = {
        heatmap: true,
        trajectories: true,
        zones: true,
        fixtures: true
    };

    // Store Architectural Fixtures (Shelves, Display Islands, Cashier Desks)
    const storeFixtures = [
        // Gondola Shelves (Electronics)
        { type: 'shelf', x: 780, y: 100, w: 180, h: 40, label: 'Shelf A1' },
        { type: 'shelf', x: 1000, y: 100, w: 180, h: 40, label: 'Shelf A2' },
        { type: 'shelf', x: 780, y: 220, w: 180, h: 40, label: 'Shelf B1' },
        { type: 'shelf', x: 1000, y: 220, w: 180, h: 40, label: 'Shelf B2' },
        // Promotional Feature Pods (Center)
        { type: 'island', x: 440, y: 260, r: 45, label: 'Feature Island 1' },
        { type: 'island', x: 600, y: 380, r: 45, label: 'Feature Island 2' },
        // Checkout Counters
        { type: 'counter', x: 860, y: 620, w: 120, h: 32, label: 'Register 1' },
        { type: 'counter', x: 1040, y: 620, w: 120, h: 32, label: 'Register 2' },
        // Turnstiles at Entrance
        { type: 'gate', x: 340, y: 120, w: 10, h: 80, label: 'Gates' }
    ];

    // Setup Layer Toggle Listeners
    function setupLayerToggle(button, layerKey) {
        if (!button) return;
        button.addEventListener('click', () => {
            layers[layerKey] = !layers[layerKey];
            button.classList.toggle('active', layers[layerKey]);
            renderCanvas();
        });
    }

    setupLayerToggle(toggleHeatmap, 'heatmap');
    setupLayerToggle(toggleTrajectories, 'trajectories');
    setupLayerToggle(toggleZones, 'zones');
    setupLayerToggle(toggleFixtures, 'fixtures');

    // -------------------------------------------------------------------------
    // 3. High-DPI Canvas Resolution Sizing
    // -------------------------------------------------------------------------
    function initCanvasResolution() {
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        
        // Base coordinate space
        canvas.width = 1280;
        canvas.height = 720;
        renderCanvas();
    }

    window.addEventListener('resize', initCanvasResolution);

    // -------------------------------------------------------------------------
    // 4. Data Fetching (API Integration)
    // -------------------------------------------------------------------------
    async function loadHeatmap() {
        try {
            const res = await fetch('/api/v1/heatmap');
            if (res.ok) {
                const data = await res.json();
                heatmapMatrix = data.matrix;
            }
        } catch (err) {
            console.warn('Heatmap load warning:', err);
        }
    }

    async function loadAnalytics() {
        try {
            const res = await fetch('/api/v1/analytics/stats');
            if (res.ok) {
                const data = await res.json();
                
                // Update Top KPIs
                if (kpiFootfall) kpiFootfall.textContent = data.total_footfall;
                if (kpiActive) kpiActive.textContent = data.active_shoppers;
                
                // Average Dwell Across Zones
                const totalDwell = data.zones.reduce((sum, z) => sum + z.avg_dwell_seconds, 0);
                const avgDwell = data.zones.length > 0 ? (totalDwell / data.zones.length).toFixed(1) : '0.0';
                if (kpiDwell) kpiDwell.textContent = avgDwell;

                // Queue Alerts & SLA Tag
                const alertCount = data.queue_alerts ? data.queue_alerts.length : 0;
                if (kpiAlerts) kpiAlerts.textContent = alertCount;
                
                if (alertCount > 0) {
                    if (kpiSlaTag) {
                        kpiSlaTag.textContent = 'Congestion Alert';
                        kpiSlaTag.className = 'kpi-tag negative';
                    }
                    if (slaHealthChip) {
                        slaHealthChip.textContent = 'Attention Needed';
                        slaHealthChip.className = 'chip-value text-danger';
                    }
                    if (queueOverallBadge) {
                        queueOverallBadge.textContent = 'SLA Breach Active';
                        queueOverallBadge.className = 'status-indicator-badge danger';
                    }
                } else {
                    if (kpiSlaTag) {
                        kpiSlaTag.textContent = 'Optimal (0 Alerts)';
                        kpiSlaTag.className = 'kpi-tag positive';
                    }
                    if (slaHealthChip) {
                        slaHealthChip.textContent = 'Healthy (100%)';
                        slaHealthChip.className = 'chip-value text-success';
                    }
                    if (queueOverallBadge) {
                        queueOverallBadge.textContent = 'All Queues Normal';
                        queueOverallBadge.className = 'status-indicator-badge success';
                    }
                }

                if (quickFrameCount) {
                    frameCounter = data.total_frames_processed || frameCounter;
                    quickFrameCount.textContent = `Frame ${frameCounter} / 120`;
                }

                zonesData = data.zones || [];
                trajectoriesData = data.trajectories || [];

                renderZonesList(zonesData);
                renderAlerts(data.queue_alerts || []);
                renderTracksList(trajectoriesData);
                renderCanvas();
            }
        } catch (err) {
            console.error('Analytics load error:', err);
        }
    }

    // -------------------------------------------------------------------------
    // 5. Sidebar Lists Rendering
    // -------------------------------------------------------------------------
    function renderZonesList(zones) {
        if (!zonesList) return;
        zonesList.innerHTML = '';
        
        zones.forEach(z => {
            const card = document.createElement('div');
            card.className = 'zone-row-card';
            card.setAttribute('data-zone-id', z.id);
            
            card.innerHTML = `
                <div class="zone-row-top">
                    <div class="zone-name-wrap">
                        <span class="zone-color-tag" style="background-color: ${z.color_hex};"></span>
                        <span class="zone-name">${z.name}</span>
                    </div>
                    <span class="zone-occupancy">${z.current_occupants} active</span>
                </div>
                <div class="zone-metrics-grid">
                    <span class="zone-stat">Total Visits: <strong>${z.total_visits}</strong></span>
                    <span class="zone-stat">Avg Dwell: <strong>${z.avg_dwell_seconds.toFixed(1)}s</strong></span>
                </div>
            `;

            card.addEventListener('mouseenter', () => {
                hoveredZoneId = z.id;
                renderCanvas();
            });

            card.addEventListener('mouseleave', () => {
                hoveredZoneId = null;
                renderCanvas();
            });

            zonesList.appendChild(card);
        });
    }

    function renderAlerts(alerts) {
        if (!alertsFeed) return;
        if (!alerts || alerts.length === 0) {
            alertsFeed.innerHTML = `
                <div class="empty-state">
                    Queue wait-times and occupancy are operating within standard SLA tolerances.
                </div>
            `;
            return;
        }

        alertsFeed.innerHTML = '';
        alerts.forEach(a => {
            const item = document.createElement('div');
            item.className = `alert-item ${a.severity}`;
            item.innerHTML = `
                <div class="alert-top">
                    <span class="alert-level">${a.severity} Violation</span>
                    <span class="alert-time">${a.timestamp || 'Just now'}</span>
                </div>
                <div class="alert-message">${a.recommendation}</div>
            `;
            alertsFeed.appendChild(item);
        });
    }

    function renderTracksList(trajectories) {
        if (!tracksList) return;
        tracksList.innerHTML = '';
        
        if (!trajectories || trajectories.length === 0) {
            tracksList.innerHTML = '<div class="empty-state">No live shopper tracks.</div>';
            return;
        }

        trajectories.forEach(t => {
            const row = document.createElement('div');
            row.className = 'track-row';
            const [cx, cy] = t.current_pos ? t.current_pos : [0, 0];
            
            row.innerHTML = `
                <span class="track-id-badge">Shopper #${t.track_id}</span>
                <span class="track-pos">(${Math.round(cx)}, ${Math.round(cy)})</span>
                <span class="track-status">Tracking</span>
            `;

            row.addEventListener('mouseenter', () => {
                selectedTrackId = t.track_id;
                renderCanvas();
            });

            row.addEventListener('mouseleave', () => {
                selectedTrackId = null;
                renderCanvas();
            });

            tracksList.appendChild(row);
        });
    }

    // -------------------------------------------------------------------------
    // 6. Architectural 2D Floorplan & Trajectory Canvas Engine
    // -------------------------------------------------------------------------
    function renderCanvas() {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        
        // Colors from theme
        const colorBg = isDark ? '#10131b' : '#fcfcfd';
        const colorGrid = isDark ? '#181c28' : '#f1f5f9';
        const colorWall = isDark ? '#333b4e' : '#cbd5e1';
        const colorWallFill = isDark ? '#161922' : '#f8fafc';
        const colorFixtureBg = isDark ? '#191d2a' : '#f1f5f9';
        const colorFixtureBorder = isDark ? '#272d3f' : '#e2e8f0';
        const colorFixtureText = isDark ? '#64748b' : '#94a3b8';

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // A. Background Fill
        ctx.fillStyle = colorBg;
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // B. Crisp Architectural Grid Lines (Every 40px)
        ctx.strokeStyle = colorGrid;
        ctx.lineWidth = 1;
        for (let x = 0; x <= canvas.width; x += 40) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, canvas.height);
            ctx.stroke();
        }
        for (let y = 0; y <= canvas.height; y += 40) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(canvas.width, y);
            ctx.stroke();
        }

        // C. Perimeter Store Walls & Entry/Exit Openings
        ctx.strokeStyle = colorWall;
        ctx.lineWidth = 4;
        ctx.strokeRect(30, 30, canvas.width - 60, canvas.height - 60);

        // Entrance Gate Indicator
        ctx.clearRect(30, 100, 4, 120);
        ctx.strokeStyle = '#0284c7';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(30, 100);
        ctx.lineTo(30, 220);
        ctx.stroke();
        
        ctx.fillStyle = '#0284c7';
        ctx.font = '600 11px Inter, sans-serif';
        ctx.fillText('MAIN STORE ENTRANCE →', 42, 165);

        // D. Architectural Fixtures & Shelving Units
        if (layers.fixtures) {
            storeFixtures.forEach(fix => {
                ctx.fillStyle = colorFixtureBg;
                ctx.strokeStyle = colorFixtureBorder;
                ctx.lineWidth = 1.5;

                if (fix.type === 'shelf' || fix.type === 'counter') {
                    // Rounded rectangle for retail shelving
                    drawRoundedRect(ctx, fix.x, fix.y, fix.w, fix.h, 4);
                    ctx.fill();
                    ctx.stroke();

                    // Fixture Sub-divisions
                    ctx.strokeStyle = colorFixtureBorder;
                    ctx.beginPath();
                    for (let lx = fix.x + 30; lx < fix.x + fix.w; lx += 30) {
                        ctx.moveTo(lx, fix.y + 4);
                        ctx.lineTo(lx, fix.y + fix.h - 4);
                    }
                    ctx.stroke();

                    // Label
                    ctx.fillStyle = colorFixtureText;
                    ctx.font = '500 10px JetBrains Mono, monospace';
                    ctx.fillText(fix.label, fix.x + 8, fix.y + fix.h / 2 + 3);
                } else if (fix.type === 'island') {
                    // Circular promotional display podium
                    ctx.beginPath();
                    ctx.arc(fix.x, fix.y, fix.r, 0, Math.PI * 2);
                    ctx.fill();
                    ctx.stroke();

                    // Center ring
                    ctx.beginPath();
                    ctx.arc(fix.x, fix.y, fix.r * 0.4, 0, Math.PI * 2);
                    ctx.stroke();

                    // Label
                    ctx.fillStyle = colorFixtureText;
                    ctx.font = '500 9px JetBrains Mono, monospace';
                    ctx.textAlign = 'center';
                    ctx.fillText(fix.label, fix.x, fix.y + 3);
                    ctx.textAlign = 'start';
                }
            });
        }

        // E. Spatial Heatmap Density Accumulator (Smooth Thermal Rendering)
        if (layers.heatmap && heatmapMatrix) {
            const gh = heatmapMatrix.length;
            const gw = heatmapMatrix[0].length;
            const cellW = canvas.width / gw;
            const cellH = canvas.height / gh;

            for (let r = 0; r < gh; r++) {
                for (let c = 0; c < gw; c++) {
                    const val = heatmapMatrix[r][c];
                    if (val > 0.04) {
                        // Human-crafted subtle thermal color mapping
                        const alpha = Math.min(val * 0.65, 0.7);
                        let fillColor = `rgba(239, 68, 68, ${alpha})`; // Coral red for hotspot
                        if (val < 0.25) {
                            fillColor = `rgba(59, 130, 246, ${alpha * 0.8})`; // Soft blue
                        } else if (val < 0.55) {
                            fillColor = `rgba(245, 158, 11, ${alpha * 0.9})`; // Warm amber
                        }

                        ctx.fillStyle = fillColor;
                        ctx.fillRect(c * cellW - 1, r * cellH - 1, cellW + 2, cellH + 2);
                    }
                }
            }
        }

        // F. Commercial Zones Boundaries (Clean, Professional Outlines)
        if (layers.zones) {
            const defaultPolygons = [
                { id: "zone_entrance", name: "Zone 1: Entrance & Foyer", polygon: [[50, 50], [350, 50], [350, 250], [50, 250]], stroke: isDark ? '#38bdf8' : '#0284c7', fill: isDark ? 'rgba(56, 189, 248, 0.08)' : 'rgba(2, 132, 199, 0.06)' },
                { id: "zone_promotions", name: "Zone 2: Promotions & Showcase", polygon: [[380, 200], [680, 200], [680, 480], [380, 480]], stroke: isDark ? '#a78bfa' : '#7c3aed', fill: isDark ? 'rgba(167, 139, 250, 0.08)' : 'rgba(124, 58, 237, 0.06)' },
                { id: "zone_electronics", name: "Zone 3: Electronics Wall", polygon: [[750, 50], [1200, 50], [1200, 350], [750, 350]], stroke: isDark ? '#34d399' : '#059669', fill: isDark ? 'rgba(52, 211, 153, 0.08)' : 'rgba(5, 150, 105, 0.06)' },
                { id: "zone_checkout", name: "Zone 4: Checkout & Service Queue", polygon: [[800, 420], [1220, 420], [1220, 680], [800, 680]], stroke: isDark ? '#fbbf24' : '#d97706', fill: isDark ? 'rgba(251, 191, 36, 0.08)' : 'rgba(217, 119, 6, 0.06)' },
            ];

            defaultPolygons.forEach(z => {
                const isHovered = hoveredZoneId === z.id;
                ctx.beginPath();
                ctx.moveTo(z.polygon[0][0], z.polygon[0][1]);
                for (let i = 1; i < z.polygon.length; i++) {
                    ctx.lineTo(z.polygon[i][0], z.polygon[i][1]);
                }
                ctx.closePath();

                // Fill with gentle highlight if hovered
                ctx.fillStyle = isHovered ? (isDark ? 'rgba(255, 255, 255, 0.12)' : 'rgba(0, 0, 0, 0.06)') : z.fill;
                ctx.fill();

                // 1.5px Crisp Architectural Outline
                ctx.strokeStyle = z.stroke;
                ctx.lineWidth = isHovered ? 2.5 : 1.5;
                ctx.setLineDash([6, 4]);
                ctx.stroke();
                ctx.setLineDash([]);

                // Zone Badge Label
                const labelX = z.polygon[0][0] + 14;
                const labelY = z.polygon[0][1] + 24;
                
                // Text background pill
                ctx.font = '600 12px Plus Jakarta Sans, sans-serif';
                const textWidth = ctx.measureText(z.name).width;
                
                ctx.fillStyle = isDark ? 'rgba(20, 23, 33, 0.85)' : 'rgba(255, 255, 255, 0.9)';
                drawRoundedRect(ctx, labelX - 6, labelY - 14, textWidth + 12, 20, 4);
                ctx.fill();
                ctx.strokeStyle = z.stroke;
                ctx.lineWidth = 1;
                ctx.stroke();

                ctx.fillStyle = z.stroke;
                ctx.fillText(z.name, labelX, labelY);
            });
        }

        // G. Customer Trajectory Trails & Shopper Avatars
        if (layers.trajectories) {
            trajectoriesData.forEach(t => {
                const isSelected = selectedTrackId === t.track_id;
                const trailColor = isSelected ? '#2563eb' : (isDark ? '#38bdf8' : '#0284c7');

                // 1. Smooth Trajectory Trail
                if (t.points && t.points.length > 1) {
                    ctx.beginPath();
                    ctx.moveTo(t.points[0][0], t.points[0][1]);
                    for (let i = 1; i < t.points.length; i++) {
                        ctx.lineTo(t.points[i][0], t.points[i][1]);
                    }
                    ctx.strokeStyle = isSelected ? '#2563eb' : (isDark ? 'rgba(56, 189, 248, 0.5)' : 'rgba(2, 132, 199, 0.5)');
                    ctx.lineWidth = isSelected ? 3 : 2;
                    ctx.stroke();

                    // Historical breadcrumb dots
                    t.points.forEach((pt, idx) => {
                        if (idx % 3 === 0) {
                            ctx.beginPath();
                            ctx.arc(pt[0], pt[1], 2, 0, Math.PI * 2);
                            ctx.fillStyle = isDark ? 'rgba(56, 189, 248, 0.6)' : 'rgba(2, 132, 199, 0.6)';
                            ctx.fill();
                        }
                    });
                }

                // 2. Current Position Avatar Pin
                if (t.current_pos) {
                    const [px, py] = t.current_pos;

                    // Outer Subtle Ring
                    ctx.beginPath();
                    ctx.arc(px, py, 11, 0, Math.PI * 2);
                    ctx.fillStyle = isSelected ? 'rgba(37, 99, 235, 0.25)' : (isDark ? 'rgba(56, 189, 248, 0.2)' : 'rgba(2, 132, 199, 0.15)');
                    ctx.fill();
                    ctx.strokeStyle = trailColor;
                    ctx.lineWidth = 1.5;
                    ctx.stroke();

                    // Center Solid Dot
                    ctx.beginPath();
                    ctx.arc(px, py, 4.5, 0, Math.PI * 2);
                    ctx.fillStyle = trailColor;
                    ctx.fill();

                    // Floating ID Pill
                    const idLabel = `ID #${t.track_id}`;
                    ctx.font = '600 11px JetBrains Mono, monospace';
                    const idWidth = ctx.measureText(idLabel).width;
                    
                    const tagX = px + 14;
                    const tagY = py - 6;

                    ctx.fillStyle = isDark ? '#1c202d' : '#ffffff';
                    ctx.strokeStyle = isSelected ? '#2563eb' : (isDark ? '#333b4e' : '#cbd5e1');
                    ctx.lineWidth = 1;
                    drawRoundedRect(ctx, tagX, tagY - 11, idWidth + 10, 18, 4);
                    ctx.fill();
                    ctx.stroke();

                    ctx.fillStyle = isDark ? '#f8fafc' : '#0f172a';
                    ctx.fillText(idLabel, tagX + 5, tagY + 2);
                }
            });
        }
    }

    // Helper: Draw Rounded Rectangle on Canvas
    function drawRoundedRect(c, x, y, width, height, radius) {
        c.beginPath();
        c.moveTo(x + radius, y);
        c.lineTo(x + width - radius, y);
        c.quadraticCurveTo(x + width, y, x + width, y + radius);
        c.lineTo(x + width, y + height - radius);
        c.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
        c.lineTo(x + radius, y + height);
        c.quadraticCurveTo(x, y + height, x, y + height - radius);
        c.lineTo(x, y + radius);
        c.quadraticCurveTo(x, y, x + radius, y);
        c.closePath();
    }

    // -------------------------------------------------------------------------
    // 7. Simulation Controls (Single Step & Auto Playback Loop)
    // -------------------------------------------------------------------------
    async function triggerSimulationStep() {
        if (btnSimulate) {
            btnSimulate.disabled = true;
        }
        try {
            await fetch('/api/v1/analytics/simulate', { method: 'POST' });
            await loadHeatmap();
            await loadAnalytics();
        } catch (err) {
            console.error('Simulation step error:', err);
        } finally {
            if (btnSimulate) {
                btnSimulate.disabled = false;
            }
        }
    }

    if (btnSimulate) {
        btnSimulate.addEventListener('click', triggerSimulationStep);
    }

    // Auto-Play Stream
    if (btnStreamAuto) {
        btnStreamAuto.addEventListener('click', () => {
            isAutoPlaying = !isAutoPlaying;
            if (isAutoPlaying) {
                btnStreamAuto.classList.add('active-playing');
                if (btnStreamText) btnStreamText.textContent = 'Pause Stream';
                playIntervalId = setInterval(triggerSimulationStep, 900);
            } else {
                btnStreamAuto.classList.remove('active-playing');
                if (btnStreamText) btnStreamText.textContent = 'Live Play';
                clearInterval(playIntervalId);
            }
        });
    }

    // -------------------------------------------------------------------------
    // 8. Initial Initialization
    // -------------------------------------------------------------------------
    initCanvasResolution();
    loadHeatmap();
    loadAnalytics();
});
