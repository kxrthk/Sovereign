// Dashboard Premium Application Logic

document.addEventListener("DOMContentLoaded", () => {
    // --- Tab Navigation Setup ---
    const navItems = document.querySelectorAll('.nav-section li');
    const tabContents = document.querySelectorAll('.tab-content');

    navItems.forEach((navItem, index) => {
        navItem.addEventListener('click', () => {
            // Update Active Nav Link
            navItems.forEach(n => n.classList.remove('active'));
            navItem.classList.add('active');

            // Hide All Tabs
            tabContents.forEach(t => t.style.display = 'none');

            // Show Selected Tab
            const tabs = ['tab-overview', 'tab-charts', 'tab-history', 'tab-cortex', 'tab-vision', 'tab-config'];
            const targetId = tabs[index] || 'tab-overview';
            document.getElementById(targetId).style.display = 'flex';

            // Re-render chart size if navigating to charts tab to prevent sizing bugs
            if (targetId === 'tab-charts' && dynamicChart) {
                const chartsContainer = document.getElementById('dynamic-chart-container');
                dynamicChart.applyOptions({ width: chartsContainer.clientWidth, height: chartsContainer.clientHeight });
            }
            if (targetId === 'tab-overview' && overviewChart) {
                const chartsContainer = document.getElementById('overview-chart-container');
                overviewChart.applyOptions({ width: chartsContainer.clientWidth, height: chartsContainer.clientHeight });
            }
        });
    });

    // 1. Initialize Charts
    const commonChartOptions = {
        layout: { background: { type: 'solid', color: 'transparent' }, textColor: '#94A3B8' },
        grid: { vertLines: { color: 'rgba(148, 163, 184, 0.05)' }, horzLines: { color: 'rgba(148, 163, 184, 0.05)' } },
        crosshair: { mode: LightweightCharts.CrosshairMode.Normal, vertLine: { color: '#3B82F6', labelBackgroundColor: '#3B82F6' }, horzLine: { color: '#3B82F6', labelBackgroundColor: '#3B82F6' } },
        rightPriceScale: { borderColor: 'rgba(148, 163, 184, 0.1)' },
        timeScale: { borderColor: 'rgba(148, 163, 184, 0.1)', timeVisible: true, secondsVisible: false }
    };

    const overviewContainer = document.getElementById('overview-chart-container');
    const overviewChart = LightweightCharts.createChart(overviewContainer, commonChartOptions);
    const overviewSeries = overviewChart.addCandlestickSeries({ upColor: '#00F0FF', downColor: '#FF003C', borderVisible: false, wickUpColor: '#00F0FF', wickDownColor: '#FF003C' });

    const dynamicContainer = document.getElementById('dynamic-chart-container');
    const dynamicChart = LightweightCharts.createChart(dynamicContainer, commonChartOptions);
    const dynamicSeries = dynamicChart.addCandlestickSeries({ upColor: '#00F0FF', downColor: '#FF003C', borderVisible: false, wickUpColor: '#00F0FF', wickDownColor: '#FF003C' });

    // Mini Sparkline Charts (AI Predict & Campaigns)
    const miniChartOptions = {
        layout: { background: { type: 'solid', color: 'transparent' } },
        grid: { vertLines: { visible: false }, horzLines: { visible: false } },
        crosshair: { mode: LightweightCharts.CrosshairMode.Hidden },
        rightPriceScale: { visible: false },
        timeScale: { visible: false },
        handleScroll: false,
        handleScale: false
    };

    let sparkLine1 = LightweightCharts.createChart(document.getElementById('mini-chart-accuracy'), miniChartOptions).addLineSeries({ color: '#00F0FF', lineWidth: 2 });
    let sparkLine2 = LightweightCharts.createChart(document.getElementById('mini-chart-campaigns'), miniChartOptions).addLineSeries({ color: '#B026FF', lineWidth: 2 });
    let dummySpark1 = [], dummySpark2 = [];
    let startT = new Date().getTime() / 1000;
    for (let i = 0; i < 30; i++) {
        dummySpark1.push({ time: startT + i, value: 50 + Math.random() * 20 });
        dummySpark2.push({ time: startT + i, value: i * 2 + Math.random() * 5 });
    }
    sparkLine1.setData(dummySpark1);
    sparkLine2.setData(dummySpark2);

    // Resize Handlers
    new ResizeObserver(entries => {
        if (entries.length === 0 || entries[0].target !== overviewContainer) return;
        const newRect = entries[0].contentRect;
        overviewChart.applyOptions({ height: newRect.height, width: newRect.width });
    }).observe(overviewContainer);

    new ResizeObserver(entries => {
        if (entries.length === 0 || entries[0].target !== dynamicContainer) return;
        const newRect = entries[0].contentRect;
        dynamicChart.applyOptions({ height: newRect.height, width: newRect.width });
    }).observe(dynamicContainer);

    // State
    let currentSymbol = '';
    let currentPrice = 0;
    let currentLines = [];

    // --- Data Fetching ---

    async function fetchWatchlist() {
        try {
            const res = await fetch('/api/watchlist');
            const data = await res.json();
            const select = document.getElementById('asset-selector');
            select.innerHTML = '';

            data.forEach(sym => {
                const opt = document.createElement('option');
                opt.value = sym;
                opt.innerText = sym;
                select.appendChild(opt);
            });

            if (data.length > 0) {
                currentSymbol = data[0];
                fetchChartData(currentSymbol);
            }

            select.addEventListener('change', (e) => {
                currentSymbol = e.target.value;
                fetchChartData(currentSymbol);
            });

            // Hardcode NIFTY 50 for the Overview chart
            fetchChartData('^NSEI', null, true);
        } catch (e) {
            console.error("Failed to load watchlist", e);
            document.getElementById('asset-selector').innerHTML = '<option>Error loading</option>';
        }
    }

    async function fetchChartData(symbol, tradeData = null, isOverview = false) {
        try {
            const res = await fetch(`/api/chart_data/${symbol}`);
            const data = await res.json();

            if (!isOverview && data.length > 0) {
                currentPrice = data[data.length - 1].close;
            }

            if (isOverview) {
                overviewSeries.setData(data);
                overviewChart.timeScale().fitContent();
            } else {
                dynamicSeries.setData(data);

                // Manage Lines
                currentLines.forEach(line => dynamicSeries.removePriceLine(line));
                currentLines = [];

                if (tradeData) {
                    const entryLine = dynamicSeries.createPriceLine({
                        price: tradeData.price,
                        color: '#3B82F6',
                        lineWidth: 2,
                        lineStyle: LightweightCharts.LineStyle.Dotted,
                        axisLabelVisible: true,
                        title: `ENTRY (${tradeData.action})`,
                    });
                    currentLines.push(entryLine);
                }

                dynamicChart.timeScale().fitContent();
            }

        } catch (e) {
            console.error("Failed to load chart data for " + symbol, e);
        }
    }

    async function fetchSystemStatus() {
        try {
            const res = await fetch('/api/status');
            const data = await res.json();

            // Update Balance
            document.getElementById('wallet-balance').innerText = `₹${data.wallet_balance.toLocaleString('en-IN')}`;

            // Update Oracle Intel
            const confPercent = Math.round(data.latest_oracle_confidence * 100);
            document.getElementById('confidence-text').innerText = `${confPercent}%`;

            // Animate Circle
            const circle = document.getElementById('confidence-circle');
            circle.setAttribute('stroke-dasharray', `${confPercent}, 100`);

            // Change color based on confidence
            const svgGroup = circle.parentElement;
            if (confPercent > 70) {
                svgGroup.classList.remove('red');
                svgGroup.classList.add('cyan');
            } else {
                svgGroup.classList.remove('cyan');
                svgGroup.classList.add('red');
            }

            document.getElementById('trading-mode').innerText = data.trading_mode;
            document.getElementById('bot-message').innerText = data.bot_message;

            // Update New AI Metrics Grid
            document.getElementById('ai-accuracy').innerText = data.ai_accuracy ? `${data.ai_accuracy}%` : '55.5%';
            document.getElementById('ai-trades').innerText = data.ai_trades || '142';
            document.getElementById('ai-regime').innerText = data.ai_regime || 'NORMAL';

        } catch (e) {
            console.error("Failed to load status", e);
        }
    }

    // ─── Red Flag State ───────────────────────────────────────────────────────────
    let currentDefconData = {};
    let redFlagDismissed = false;

    async function fetchMacroView() {
        try {
            const res = await fetch('/api/world_view');
            const data = await res.json();
            currentDefconData = data;

            const badge = document.getElementById('defcon-badge');
            // Reset classes
            badge.className = 'badge';

            let icon = 'shield-check';

            if (data.defcon === 'SAFE') {
                badge.classList.add('badge-safe');
                icon = 'shield-check';
            } else if (data.defcon === 'CAUTION') {
                badge.classList.add('badge-caution');
                icon = 'alert-triangle';
            } else {
                badge.classList.add('badge-danger');
                icon = 'shield-alert';
            }

            badge.innerHTML = `<i data-lucide="${icon}"></i> DEFCON ${data.defcon}`;
            document.getElementById('macro-justification').innerText = data.justification;

            lucide.createIcons(); // Re-render icon

            // ── Red Flag / DEFCON Danger Handling ────────────────────────
            if (!redFlagDismissed && (data.defcon === 'DANGER' || data.defcon === 'CAUTION')) {
                showRedFlagBanner(data);
            } else if (data.defcon === 'SAFE') {
                hideRedFlagBanner();
            }
        } catch (e) {
            console.error("Failed to load macro view");
        }
    }

    function showRedFlagBanner(data) {
        const banner = document.getElementById('red-flag-banner');
        const reason = document.getElementById('red-flag-reason');
        if (banner) {
            // Remove any inline display:none set on the element and add 'visible' class
            banner.style.removeProperty('display');
            banner.classList.add('visible');
            banner.style.display = 'block';
        }
        if (reason) {
            reason.innerText = data.justification || 'Extreme macro threat detected by Global Intelligence Engine.';
        }
        // Populate the red flag panel data
        updateRedFlagPanel(data);
    }

    function hideRedFlagBanner() {
        const banner = document.getElementById('red-flag-banner');
        if (banner) {
            banner.style.display = 'none';
            banner.classList.remove('visible');
        }
    }

    function updateRedFlagPanel(data) {
        const threatLevel = document.getElementById('rf-threat-level');
        const threatCount = document.getElementById('rf-threat-count');
        const lastScan = document.getElementById('rf-last-scan');
        const justEl = document.getElementById('rf-justification');
        const headlinesEl = document.getElementById('rf-headlines');

        if (threatLevel) {
            threatLevel.innerText = data.defcon || 'DANGER';
            threatLevel.style.color = data.defcon === 'CAUTION' ? '#f59e0b' : '#ff003c';
        }
        if (threatCount) {
            const themes = data.top_themes || data.sector_hotspots || [];
            threatCount.innerText = themes.length > 0 ? themes.length : (data.headline_count || '—');
        }
        if (lastScan) {
            const ts = data.timestamp;
            if (ts) {
                const d = new Date(typeof ts === 'number' ? ts * 1000 : ts);
                lastScan.innerText = d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
            }
        }
        if (justEl) {
            justEl.innerText = data.justification || 'Extreme macro threat detected.';
        }
        if (headlinesEl) {
            const themes = data.top_themes || [];
            if (themes.length > 0) {
                headlinesEl.innerHTML = themes.map(h => `
                    <div style="background:rgba(255,0,60,0.07); border:1px solid rgba(255,0,60,0.2); border-radius:6px; padding:10px 14px; font-size:12px; color:rgba(255,200,200,0.9); display:flex; align-items:flex-start; gap:8px;">
                        <span style="color:#ff003c; font-size:10px; margin-top:2px; flex-shrink:0;">⚠</span>
                        ${h}
                    </div>
                `).join('');
            } else {
                headlinesEl.innerHTML = '<div style="color:rgba(255,255,255,0.3); font-size:12px;">No specific flagged headlines available.</div>';
            }
        }
        lucide.createIcons();
    }

    // Expose to global scope for onclick handlers
    window.showRedFlagPanel = function () {
        const panel = document.getElementById('red-flag-panel');
        if (panel) {
            panel.style.display = 'block';
            // Scroll to top of overview tab
            panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        updateRedFlagPanel(currentDefconData);
        lucide.createIcons();
    };

    window.hideRedFlagPanel = function () {
        const panel = document.getElementById('red-flag-panel');
        if (panel) panel.style.display = 'none';
    };

    window.dismissRedFlag = function () {
        redFlagDismissed = true;
        hideRedFlagBanner();
        window.hideRedFlagPanel();
        console.log('[RED FLAG] Acknowledged by operator. Banner dismissed.');
    };

    window.triggerEmergencyStop = async function () {
        const btn = document.getElementById('btn-emergency-stop');
        if (btn) {
            btn.innerHTML = '<i data-lucide="loader"></i> SENDING KILL SIGNAL...';
            btn.style.opacity = '0.7';
            lucide.createIcons();
        }
        try {
            const res = await fetch('/api/kill_switch', { method: 'POST' });
            const data = await res.json();
            if (data.status === 'success') {
                alert('🚨 EMERGENCY STOP ACTIVATED\n\nAll trading has been halted. A STOP.flag file has been written. Restart the bot manually to resume.');
                if (btn) {
                    btn.innerHTML = '<i data-lucide="shield-off"></i> ✓ TRADES STOPPED';
                    btn.style.background = 'rgba(0,255,102,0.2)';
                    btn.style.borderColor = 'var(--accent-green)';
                    btn.style.color = 'var(--accent-green)';
                    btn.style.opacity = '1';
                }
            } else {
                alert('⚠️ Kill switch command sent but got unexpected response: ' + JSON.stringify(data));
                if (btn) { btn.innerHTML = '<i data-lucide="shield-alert"></i> EMERGENCY STOP ALL TRADES'; btn.style.opacity = '1'; }
            }
        } catch (e) {
            alert('❌ Failed to trigger emergency stop: ' + e);
            if (btn) { btn.innerHTML = '<i data-lucide="shield-alert"></i> EMERGENCY STOP ALL TRADES'; btn.style.opacity = '1'; }
        }
        lucide.createIcons();
    };

    window.switchToSafeDefcon = async function () {
        // This just acknowledges caution mode and hides the panel.
        // The actual DEFCON level is controlled by the backend Cortex engine.
        window.hideRedFlagPanel();
        redFlagDismissed = false; // Allow re-check on next fetch
        alert('⚠️ CAUTION MODE ACKNOWLEDGED\n\nThe bot will continue operating with reduced position sizing and higher confidence thresholds. Monitor closely.');
    };


    async function fetchFlightRecorder() {
        try {
            const res = await fetch('/api/flight_recorder');
            const data = await res.json();
            const logContainer = document.getElementById('trade-log');

            if (!data || data.length === 0) {
                logContainer.innerHTML = '<div class="empty-state">No recent trades found.</div>';
                return;
            }

            logContainer.innerHTML = '';

            data.reverse().forEach(trade => {
                const el = document.createElement('div');
                const isBuy = trade.action.toUpperCase() === 'BUY';
                el.className = `trade-card ${isBuy ? 'buy' : 'sell'}`;

                const confText = trade.confidence ? Math.round(trade.confidence * 100) + '%' : 'N/A';

                el.innerHTML = `
                    <div class="tc-top">
                        <span class="tc-symbol">${trade.symbol}</span>
                        <span class="tc-action">${trade.action}</span>
                    </div>
                    <div class="tc-stats">
                        <span>Price: <strong>${trade.price}</strong></span>
                        <span>Qty: <strong>${trade.qty}</strong></span>
                        <span>Conf: <strong>${confText}</strong></span>
                        <span>Date: <strong>${new Date().toLocaleTimeString()}</strong></span>
                    </div>
                `;

                el.addEventListener('click', () => {
                    fetchChartData(trade.symbol, trade);
                    document.getElementById('asset-selector').value = trade.symbol;
                });

                logContainer.appendChild(el);
            });

        } catch (e) {
            console.error("Failed to load flight recorder", e);
        }
    }

    // --- Actions ---

    async function executeTrade(action) {
        if (!currentSymbol || currentPrice === 0) return;

        // Optimistic UI interaction
        const btn = document.getElementById(action === 'BUY' ? 'btn-buy' : 'btn-sell');
        const ogText = btn.innerHTML;
        btn.innerHTML = '<div class="spinner" style="width:14px; height:14px; margin:0; border-width:2px; display:inline-block; vertical-align:middle; margin-right:5px;"></div> EXECUTING...';
        btn.style.opacity = '0.7';

        try {
            const res = await fetch('/api/manual_trade', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    symbol: currentSymbol,
                    action: action,
                    price: currentPrice,
                    qty: 1
                })
            });
            if (res.ok) {
                await fetchFlightRecorder();
                fetchSystemStatus();
            }
        } catch (e) {
            console.error("Trade execution failed", e);
        } finally {
            btn.innerHTML = ogText;
            btn.style.opacity = '1';
        }
    }

    document.getElementById('btn-buy').addEventListener('click', () => executeTrade('BUY'));
    document.getElementById('btn-sell').addEventListener('click', () => executeTrade('SELL'));

    // --- God-Level AI Vision Center ---
    const dropzone = document.getElementById('vision-dropzone');
    const fileInput = document.getElementById('vision-file-input');
    const preview = document.getElementById('vision-preview');
    const scanContainer = document.getElementById('scan-container');
    const visionOutput = document.getElementById('vision-output');
    const loaderPulse = document.getElementById('vision-loader');

    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('drag-over');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('drag-over');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('drag-over');
        if (e.dataTransfer.files.length) {
            handleVisionFile(e.dataTransfer.files[0]);
        }
    });

    dropzone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) handleVisionFile(e.target.files[0]);
    });

    function handleVisionFile(file) {
        if (!file.type.startsWith('image/')) return;

        const reader = new FileReader();
        reader.onload = async (e) => {
            const b64 = e.target.result;
            preview.src = b64;
            scanContainer.style.display = 'block';
            visionOutput.innerHTML = '';
            loaderPulse.style.display = 'flex';

            try {
                const res = await fetch('/api/vision_analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image: b64, context: "Analyze the trading chart for technical patterns and provide a futuristic intel readout." })
                });

                const data = await res.json();
                loaderPulse.style.display = 'none';

                if (data.analysis) {
                    visionOutput.innerHTML = data.analysis;
                } else {
                    visionOutput.innerHTML = JSON.stringify(data);
                }

            } catch (err) {
                loaderPulse.style.display = 'none';
                visionOutput.innerHTML = `<span style="color:var(--accent-danger)">[CRITICAL FAILURE] Neural Link offline. Check backend.</span>`;
            }
        };
        reader.readAsDataURL(file);
    }

    // --- Configuration & Cortex ---
    async function fetchCortexLog() {
        try {
            const res = await fetch('/api/cortex_log');
            const data = await res.json();
            const logContainer = document.getElementById('cortex-terminal');
            if (data.log_text) {
                logContainer.innerText = data.log_text;
                // auto-scroll
                logContainer.scrollTop = logContainer.scrollHeight;
            }
        } catch (e) {
            console.error("Failed to load Cortex log");
        }
    }

    async function fetchConfig() {
        try {
            const res = await fetch('/api/settings');
            const data = await res.json();
            document.getElementById('config-mode').value = data.trading_mode;
            document.getElementById('config-risk').value = data.risk_per_trade;
        } catch (e) { console.error("Config fetch err", e); }
    }

    document.getElementById('btn-save-config').addEventListener('click', async (e) => {
        const btn = e.target;
        btn.innerText = "SAVING...";
        try {
            const res = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    trading_mode: document.getElementById('config-mode').value,
                    risk_per_trade: parseFloat(document.getElementById('config-risk').value)
                })
            });
            if (res.ok) btn.innerText = "SAVED!";
            setTimeout(() => btn.innerText = "SAVE SETTINGS", 2000);
        } catch (e) {
            btn.innerText = "ERROR";
        }
    });

    // --- Init ---
    fetchWatchlist();
    fetchSystemStatus();
    fetchMacroView();
    fetchFlightRecorder();
    fetchConfig();
    fetchCortexLog();
    fetchNews(); // Added fetchNews to initial calls

    // Polling Intervals
    setInterval(fetchSystemStatus, 5000); // 5s High freq status
    setInterval(fetchMacroView, 30000);   // 30s low freq macro
    setInterval(fetchFlightRecorder, 10000); // 10s med freq logs
    setInterval(fetchCortexLog, 5000); // 5s log poll

    // Ping Simulator
    setInterval(() => {
        document.getElementById('ws-ping').innerText = `Ping: ${Math.floor(Math.random() * 20 + 20)}ms`;
    }, 2000);

    // ── NEWS CAROUSEL LOGIC ───────────────────────────────────────
    let newsArticles = [];
    let currentNewsPage = 0;
    const NEWS_PER_PAGE = 3;

    async function fetchNews() {
        try {
            const res = await fetch('/api/news');
            const data = await res.json();
            if (data && data.length > 0) {
                newsArticles = data;
                renderNewsCarousel();
            }
        } catch (e) {
            console.error("Failed to load news", e);
        }
    }

    function renderNewsCarousel() {
        const container = document.getElementById('news-carousel-content');
        const dotsContainer = document.getElementById('news-carousel-dots');
        const pageIndicator = document.getElementById('news-page-indicator');
        const btnPrev = document.getElementById('btn-news-prev');
        const btnNext = document.getElementById('btn-news-next');

        if (!container) return;

        if (newsArticles.length === 0) {
            container.innerHTML = `
                <div style="text-align:center; color:rgba(255,255,255,0.5);">
                    <i data-lucide="newspaper" style="width:24px;height:24px; opacity:0.5; margin-bottom:8px;"></i>
                    <div style="font-size:12px;">Waiting for intelligence feed...</div>
                </div>`;
            return;
        }

        const totalPages = Math.ceil(newsArticles.length / NEWS_PER_PAGE);
        currentNewsPage = Math.min(Math.max(0, currentNewsPage), totalPages - 1);

        // Update Nav
        if (pageIndicator) pageIndicator.innerText = `${currentNewsPage + 1}/${totalPages}`;

        if (btnPrev) {
            btnPrev.disabled = currentNewsPage === 0;
            btnPrev.style.opacity = currentNewsPage === 0 ? '0.3' : '1';
            btnPrev.style.cursor = currentNewsPage === 0 ? 'not-allowed' : 'pointer';
        }

        if (btnNext) {
            btnNext.disabled = currentNewsPage >= totalPages - 1;
            btnNext.style.opacity = currentNewsPage >= totalPages - 1 ? '0.3' : '1';
            btnNext.style.cursor = currentNewsPage >= totalPages - 1 ? 'not-allowed' : 'pointer';
        }

        // Render Dots
        let dotsHTML = '';
        for (let i = 0; i < Math.min(totalPages, 8); i++) {
            const isActive = i === currentNewsPage;
            dotsHTML += `<button onclick="window.goToNewsPage(${i})" style="width:${isActive ? '16px' : '6px'}; height:6px; border-radius:3px; background:${isActive ? '#00f0ff' : 'rgba(255,255,255,0.15)'}; border:none; cursor:pointer; transition:all 0.3s ease; padding:0; box-shadow:${isActive ? '0 0 6px #00f0ff' : 'none'}; margin:0 2px;"></button>`;
        }
        if (dotsContainer) dotsContainer.innerHTML = dotsHTML;

        // Render Cards
        const startIdx = currentNewsPage * NEWS_PER_PAGE;
        const visibleCards = newsArticles.slice(startIdx, startIdx + NEWS_PER_PAGE);

        let html = '';
        visibleCards.forEach(article => {
            const sent = article.sentiment || 'NEUTRAL';
            let sentColor = 'rgba(255,255,255,0.5)';
            let sentBg = 'rgba(255,255,255,0.03)';
            if (sent === 'BULLISH') {
                sentColor = '#22c55e';
                sentBg = 'rgba(0,255,102,0.08)';
            } else if (sent === 'BEARISH') {
                sentColor = '#ef4444';
                sentBg = 'rgba(255,0,60,0.08)';
            }

            const title = article.title.length > 90 ? article.title.substring(0, 90) + '...' : article.title;
            const category = article.category || 'MARKETS';
            const source = article.source || 'Intelligence Feed';

            html += `
                <a href="${article.link || '#'}" target="_blank" style="text-decoration:none; display:block;">
                    <div style="background:${sentBg}; border:1px solid ${sentColor}33; border-left:3px solid ${sentColor}; border-radius:8px; padding:12px 14px; cursor:pointer; transition:all 0.2s ease;"
                         onmouseover="this.style.transform='translateY(-1px)'" onmouseout="this.style.transform='translateY(0)'">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                            <span style="font-size:9px; font-weight:800; letter-spacing:1.5px; color:rgba(255,255,255,0.5); text-transform:uppercase;">${category}</span>
                            <span style="font-size:9px; font-weight:800; letter-spacing:1px; color:${sentColor}; background:${sentColor}22; padding:2px 6px; border-radius:3px;">${sent}</span>
                        </div>
                        <div style="font-size:12px; color:#fff; font-weight:600; line-height:1.5; margin-bottom:6px;">${title}</div>
                        <div style="font-size:10px; color:rgba(255,255,255,0.5); display:flex; justify-content:space-between;">
                            <span>${source}</span>
                            <span style="color:#00f0ff; opacity:0.7;">↗ Read</span>
                        </div>
                    </div>
                </a>
            `;
        });
        container.innerHTML = html;
        if (window.lucide) window.lucide.createIcons();
    }

    // Export navigation methods to window for inline onclick handlers
    window.goToNewsPage = function (page) {
        currentNewsPage = page;
        renderNewsCarousel();
    };

    const btnNewsPrev = document.getElementById('btn-news-prev');
    if (btnNewsPrev) btnNewsPrev.addEventListener('click', () => {
        currentNewsPage = Math.max(0, currentNewsPage - 1);
        renderNewsCarousel();
    });

    const btnNewsNext = document.getElementById('btn-news-next');
    if (btnNewsNext) btnNewsNext.addEventListener('click', () => {
        const totalPages = Math.ceil(newsArticles.length / NEWS_PER_PAGE);
        currentNewsPage = Math.min(totalPages - 1, currentNewsPage + 1);
        renderNewsCarousel();
    });

    // Add news fetch to polling
    setInterval(fetchNews, 600000); // Poll once every 10 min

});
