/**
 * Xennials Portfolio Interactive Engine
 * 1. Live Sandbox / Interactive Telegram Bot & Mini AI Agent
 * 2. Performance Audit "Before & After" Dynamic State Toggles
 * 3. Edge AI & Hardware Integration Interactive Viewers
 */

document.addEventListener('DOMContentLoaded', () => {
    initTelegramSandbox();
    initPerformanceAuditToggles();
    initEdgeAITabs();
});

/* ==========================================================================
   1. LIVE SANDBOX & INTERACTIVE TELEGRAM BOT STATE
   ========================================================================== */

function initTelegramSandbox() {
    const chatContainer = document.getElementById('tg-chat-history');
    const inputField = document.getElementById('tg-chat-input');
    const sendBtn = document.getElementById('tg-send-btn');
    const telemetryJson = document.getElementById('tg-telemetry-json');
    const latencyBadge = document.getElementById('tg-latency-badge');
    const tokenBadge = document.getElementById('tg-token-badge');
    const clearBtn = document.getElementById('tg-clear-btn');
    const copyLogBtn = document.getElementById('tg-copy-log-btn');

    if (!chatContainer || !inputField || !sendBtn) return;

    // Knowledge base for mini AI responses
    const botResponses = {
        audit: {
            text: `📊 **Full-Stack Performance Audit Initialized**\n\nTarget: \`https://client-demo.preview.xennials.tech\`\n\n• **Lighthouse Score:** 99/100 (Previously 42)\n• **Largest Contentful Paint (LCP):** 0.78s (Previously 4.6s)\n• **Cumulative Layout Shift (CLS):** 0.000\n• **Edge Cache Hit Ratio:** 99.4% via Redis Edge\n\n*Outcome: +128% booking conversions across client suites.*`,
            event: "audit_triggered",
            tokens: 146,
            latency: 28
        },
        deploy_agent: {
            text: `🤖 **Autonomous Agent Dispatch Initiated**\n\n• **Engine:** Nous Hermes 3 (Llama 3.1 70B Quant)\n• **AST Index:** CodeGraph AST active (57% token reduction)\n• **Sandbox Environment:** Isolated Docker GPU container\n• **Status:** Subagent spawned and awaiting execution plan.\n\n*Ready to ingest tasks via WebSocket on port 9119.*`,
            event: "subagent_spawned",
            tokens: 182,
            latency: 34
        },
        model_status: {
            text: `⚡ **Multi-Model Neural Gateway Health**\n\n• **Gemini 2.5 Pro (Cloud):** 🟢 Online • 310ms\n• **DeepSeek-R1 (Hybrid):** 🟢 Online • 420ms\n• **Nous Hermes 70B (On-Prem):** 🟢 Online • 14ms (Local RTX 4090)\n• **Ollama Local Daemon:** 🟢 Listening on 127.0.0.1:11434\n\n*All routing policies passing 99.98% SLA.*`,
            event: "neural_gateway_probe",
            tokens: 164,
            latency: 19
        },
        quote: {
            text: `💼 **Instant Project Scope & Estimate**\n\n• **Tier 1 - AI Automation & n8n Webhook:** $90 - $290 (2-3 days)\n• **Tier 2 - Full-Stack React 19 Booking System:** $380 - $950 (4-7 days)\n• **Tier 3 - On-Premises Local GPU Swarm / Hermes Agent:** $750 - $1,500 (5-10 days)\n\n*Every tier includes documentation, unit tests, and verified ID compliance.*`,
            event: "quote_calculated",
            tokens: 155,
            latency: 22
        }
    };

    function appendMessage(text, isUser = false) {
        const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const msgDiv = document.createElement('div');
        msgDiv.className = `flex gap-3 max-w-[85%] ${isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'}`;

        if (!isUser) {
            msgDiv.innerHTML = `
                <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white text-xs font-bold shrink-0 shadow-md">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="space-y-1">
                    <div class="bg-slate-800/90 border border-slate-700/80 rounded-2xl rounded-tl-none p-3.5 text-xs text-gray-200 leading-relaxed shadow-lg">
                        ${formatMarkdown(text)}
                    </div>
                    <span class="text-[10px] text-gray-500 font-mono px-1">${timeStr} • Delivered</span>
                </div>
            `;
        } else {
            msgDiv.innerHTML = `
                <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-pink-500 to-indigo-600 flex items-center justify-center text-white text-xs font-bold shrink-0 shadow-md">
                    <i class="fas fa-user"></i>
                </div>
                <div class="space-y-1 text-right">
                    <div class="bg-indigo-600 text-white rounded-2xl rounded-tr-none p-3.5 text-xs leading-relaxed shadow-lg">
                        ${escapeHtml(text)}
                    </div>
                    <span class="text-[10px] text-gray-500 font-mono px-1">${timeStr} • Sent</span>
                </div>
            `;
        }

        chatContainer.appendChild(msgDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.id = 'tg-typing-indicator';
        typingDiv.className = 'flex gap-3 max-w-[85%] mr-auto';
        typingDiv.innerHTML = `
            <div class="w-8 h-8 rounded-full bg-cyan-900/60 border border-cyan-500/40 flex items-center justify-center text-cyan-300 text-xs shrink-0">
                <i class="fas fa-ellipsis-h animate-pulse"></i>
            </div>
            <div class="bg-slate-800/80 border border-slate-700/60 rounded-2xl rounded-tl-none px-4 py-3 flex items-center gap-1.5">
                <span class="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce"></span>
                <span class="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce [animation-delay:0.2s]"></span>
                <span class="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce [animation-delay:0.4s]"></span>
            </div>
        `;
        chatContainer.appendChild(typingDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function removeTypingIndicator() {
        const typingDiv = document.getElementById('tg-typing-indicator');
        if (typingDiv) typingDiv.remove();
    }

    function updateTelemetry(payload, latency, tokens) {
        if (telemetryJson) {
            telemetryJson.textContent = JSON.stringify(payload, null, 2);
        }
        if (latencyBadge) {
            latencyBadge.textContent = `${latency}ms`;
        }
        if (tokenBadge) {
            tokenBadge.textContent = `${tokens} tok`;
        }
    }

    function handleUserInput(query) {
        if (!query || !query.trim()) return;
        const cleanQuery = query.trim();
        appendMessage(cleanQuery, true);
        inputField.value = '';

        showTypingIndicator();

        // Check for specific command pills
        const lower = cleanQuery.toLowerCase();
        let matchedKey = null;

        if (lower.includes('/audit') || lower.includes('audit') || lower.includes('performance') || lower.includes('lighthouse')) {
            matchedKey = 'audit';
        } else if (lower.includes('/deploy_agent') || lower.includes('agent') || lower.includes('hermes') || lower.includes('codegraph')) {
            matchedKey = 'deploy_agent';
        } else if (lower.includes('/model_status') || lower.includes('models') || lower.includes('status') || lower.includes('latency')) {
            matchedKey = 'model_status';
        } else if (lower.includes('/quote') || lower.includes('price') || lower.includes('pricing') || lower.includes('hire') || lower.includes('fiverr')) {
            matchedKey = 'quote';
        }

        setTimeout(() => {
            removeTypingIndicator();

            let responseData;
            if (matchedKey && botResponses[matchedKey]) {
                responseData = botResponses[matchedKey];
            } else {
                responseData = {
                    text: `🧠 **Xennials AI Gateway Dispatch**\n\nI processed your query: *"${escapeHtml(cleanQuery)}"*\n\nOur architecture supports:\n• **Multi-Model Orchestration:** Seamless fallback between Cloud (Gemini, Claude) and On-Premises GPU nodes (Nous Hermes, DeepSeek).\n• **Hardware & Edge Deployments:** Docker Compose GPU passthrough & SlimBOXtv firmware automation.\n• **High-Conversion Web Platforms:** React 19, Next.js 15, sub-second LCP.\n\n*Try clicking any command pill below or ask about specific stack details!*`,
                    event: "custom_nl_query",
                    tokens: Math.floor(100 + Math.random() * 80),
                    latency: Math.floor(20 + Math.random() * 25)
                };
            }

            appendMessage(responseData.text, false);

            const telemetryPayload = {
                event: responseData.event,
                timestamp: new Date().toISOString(),
                protocol: "WSS / HTTPS Webhook",
                client_id: "tg_guest_" + Math.random().toString(36).substring(2, 7),
                route: "/api/v1/bot/webhook",
                status: 200,
                latency_ms: responseData.latency,
                tokens_consumed: responseData.tokens,
                runtime: "Nous Hermes + FastAPI Bridge",
                edge_verified: true
            };

            updateTelemetry(telemetryPayload, responseData.latency, responseData.tokens);
        }, 650);
    }

    sendBtn.addEventListener('click', () => {
        handleUserInput(inputField.value);
    });

    inputField.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleUserInput(inputField.value);
        }
    });

    // Handle command pills
    document.querySelectorAll('.tg-command-pill').forEach(pill => {
        pill.addEventListener('click', () => {
            const cmd = pill.getAttribute('data-cmd');
            if (cmd) {
                handleUserInput(cmd);
            }
        });
    });

    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            chatContainer.innerHTML = '';
            appendMessage(`👋 **Interactive Sandbox Reset**\n\nWelcome to the Xennials Neural Workflow Sandbox! Visitors can trigger live automated workflows directly from this interface.\n\n*Choose a quick trigger below or type any question:*`, false);
        });
    }

    if (copyLogBtn && telemetryJson) {
        copyLogBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(telemetryJson.textContent).then(() => {
                const originalText = copyLogBtn.innerHTML;
                copyLogBtn.innerHTML = '<i class="fas fa-check text-emerald-400"></i> Copied';
                setTimeout(() => {
                    copyLogBtn.innerHTML = originalText;
                }, 1800);
            });
        });
    }
}

/* ==========================================================================
   2. PERFORMANCE AUDIT "BEFORE & AFTER" STATES
   ========================================================================== */

const AUDIT_DATA = {
    "modern-styles": {
        title: "Modern Styles Business Suites — Salon Booking Platform",
        before: {
            score: 42,
            scoreColor: "text-rose-500",
            strokeDash: "105, 251", // ~42%
            badgeText: "Critical Optimization Required",
            badgeClass: "bg-rose-950/80 border-rose-600/50 text-rose-300",
            lcp: "4.6s",
            lcpStatus: "Poor",
            lcpColor: "text-rose-400",
            cls: "0.320",
            clsStatus: "Poor",
            clsColor: "text-rose-400",
            inp: "410ms",
            inpStatus: "Poor",
            inpColor: "text-rose-400",
            weight: "5.4 MB",
            requests: "68 reqs",
            conversion: "2.1%",
            bounceRate: "68%",
            summary: "Heavy uncompressed PNG banners (4MB+), render-blocking third-party appointment widgets, non-cached API requests, and layout shifting during responsive render.",
            bottlenecks: [
                "4.1 MB unoptimized hero carousel images blocking FCP",
                "Monolithic synchronous bundle script execution",
                "Excessive DOM re-renders during time-slot picker interaction",
                "Uncached database queries on every calendar date change"
            ]
        },
        after: {
            score: 99,
            scoreColor: "text-emerald-400",
            strokeDash: "248, 251", // ~99%
            badgeText: "High-Performance Certified",
            badgeClass: "bg-emerald-950/80 border-emerald-500/50 text-emerald-300",
            lcp: "0.78s",
            lcpStatus: "Good",
            lcpColor: "text-emerald-400",
            cls: "0.000",
            clsStatus: "Good",
            clsColor: "text-emerald-400",
            inp: "32ms",
            inpStatus: "Good",
            inpColor: "text-emerald-400",
            weight: "340 KB",
            requests: "14 reqs",
            conversion: "4.8%",
            bounceRate: "24%",
            summary: "Re-engineered with Next.js 15 Server Components, modern AVIF/WebP image pipeline, critical CSS inlining, Redis edge caching, and zero cumulative layout shifts.",
            bottlenecks: [
                "AVIF/WebP responsive srcset reduction: 5.4MB → 340KB (-94%)",
                "Edge-rendered calendar slots with stale-while-revalidate Redis caching",
                "Debounced state transitions with pure Tailwind v4 styling",
                "Verified 100/100 Mobile Accessibility and SEO ratings"
            ]
        }
    },
    "winnertainment": {
        title: "Winnertainment Arcade Hub — Multimedia & Merch Experience",
        before: {
            score: 38,
            scoreColor: "text-rose-500",
            strokeDash: "95, 251", // ~38%
            badgeText: "Severely Degraded Multimedia",
            badgeClass: "bg-rose-950/80 border-rose-600/50 text-rose-300",
            lcp: "5.2s",
            lcpStatus: "Poor",
            lcpColor: "text-rose-400",
            cls: "0.284",
            clsStatus: "Poor",
            clsColor: "text-rose-400",
            inp: "480ms",
            inpStatus: "Poor",
            inpColor: "text-rose-400",
            weight: "8.9 MB",
            requests: "92 reqs",
            conversion: "1.6%",
            bounceRate: "73%",
            summary: "Synchronous audio asset decoding, un-throttled canvas rendering loop, blocking Google Fonts, and non-responsive apparel imagery causing massive frame drops.",
            bottlenecks: [
                "Synchronous decoding of full audio WAV tracks on page load",
                "Canvas animation loop causing 100% CPU lock on mobile",
                "Unbounded DOM mutation during vinyl turntable rotation",
                "No media streaming buffer management or cache headers"
            ]
        },
        after: {
            score: 98,
            scoreColor: "text-emerald-400",
            strokeDash: "245, 251", // ~98%
            badgeText: "Ultra-Fast Arcade Experience",
            badgeClass: "bg-emerald-950/80 border-emerald-500/50 text-emerald-300",
            lcp: "0.85s",
            lcpStatus: "Good",
            lcpColor: "text-emerald-400",
            cls: "0.002",
            clsStatus: "Good",
            clsColor: "text-emerald-400",
            inp: "28ms",
            inpStatus: "Good",
            inpColor: "text-emerald-400",
            weight: "620 KB",
            requests: "18 reqs",
            conversion: "4.2%",
            bounceRate: "28%",
            summary: "Migrated to Web Audio API chunked streaming, requestAnimationFrame hardware-accelerated canvas loops, self-hosted preloaded fonts, and service worker caching.",
            bottlenecks: [
                "Chunked audio streaming buffer with instant 180ms playback start",
                "GPU-accelerated CSS transforms replacing JavaScript DOM ticks",
                "Service Worker pre-caching arcade sound effects and vinyl assets",
                "Session duration increased by +74% and apparel sales boosted"
            ]
        }
    }
};

let currentAuditProject = "modern-styles";
let currentAuditState = "after"; // default to showcase the 'After' or toggle to 'Before'

function initPerformanceAuditToggles() {
    const projectSelectBtns = document.querySelectorAll('.audit-project-btn');
    const stateToggleBtns = document.querySelectorAll('.audit-state-toggle-btn');

    function renderAuditView() {
        const data = AUDIT_DATA[currentAuditProject];
        if (!data) return;
        const stateData = data[currentAuditState];

        // Update Project Title
        const titleEl = document.getElementById('audit-project-title');
        if (titleEl) titleEl.textContent = data.title;

        // Score Dial
        const scoreValEl = document.getElementById('audit-score-value');
        const scoreCircleEl = document.getElementById('audit-score-circle');
        const badgeEl = document.getElementById('audit-badge');

        if (scoreValEl) {
            scoreValEl.textContent = stateData.score;
            scoreValEl.className = `text-5xl font-extrabold font-mono ${stateData.scoreColor} transition-colors duration-500`;
        }
        if (scoreCircleEl) {
            scoreCircleEl.setAttribute('stroke-dasharray', stateData.strokeDash);
            scoreCircleEl.setAttribute('stroke', currentAuditState === 'after' ? '#10b981' : '#f43f5e');
        }
        if (badgeEl) {
            badgeEl.textContent = stateData.badgeText;
            badgeEl.className = `px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider font-mono border ${stateData.badgeClass} transition-all`;
        }

        // Metrics
        setTextAndColor('audit-lcp-val', stateData.lcp, stateData.lcpColor);
        setText('audit-lcp-status', stateData.lcpStatus);

        setTextAndColor('audit-cls-val', stateData.cls, stateData.clsColor);
        setText('audit-cls-status', stateData.clsStatus);

        setTextAndColor('audit-inp-val', stateData.inp, stateData.inpColor);
        setText('audit-inp-status', stateData.inpStatus);

        setText('audit-weight-val', stateData.weight);
        setText('audit-requests-val', stateData.requests);
        setText('audit-conversion-val', stateData.conversion);
        setText('audit-bounce-val', stateData.bounceRate);

        // Summary
        const summaryEl = document.getElementById('audit-summary-desc');
        if (summaryEl) summaryEl.textContent = stateData.summary;

        // Bottlenecks / Fixes list
        const listEl = document.getElementById('audit-points-list');
        if (listEl) {
            listEl.innerHTML = stateData.bottlenecks.map(point => {
                const icon = currentAuditState === 'after'
                    ? '<i class="fas fa-check-circle text-emerald-400 mt-0.5"></i>'
                    : '<i class="fas fa-exclamation-triangle text-rose-400 mt-0.5"></i>';
                return `<li class="flex items-start gap-2.5 text-xs text-gray-300">${icon}<span>${escapeHtml(point)}</span></li>`;
            }).join('');
        }

        // Active State Button visual updates
        stateToggleBtns.forEach(btn => {
            const btnState = btn.getAttribute('data-state');
            if (btnState === currentAuditState) {
                btn.className = `audit-state-toggle-btn px-5 py-2 rounded-xl text-xs font-bold transition-all shadow-md ${
                    currentAuditState === 'after'
                        ? 'bg-gradient-to-r from-emerald-500 to-teal-600 text-white shadow-emerald-500/20'
                        : 'bg-gradient-to-r from-rose-600 to-pink-600 text-white shadow-rose-600/20'
                }`;
            } else {
                btn.className = 'audit-state-toggle-btn px-5 py-2 rounded-xl text-xs font-semibold text-gray-400 hover:text-white bg-slate-800/80 border border-slate-700/60 transition-all';
            }
        });
    }

    projectSelectBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            projectSelectBtns.forEach(b => {
                b.classList.remove('bg-indigo-600', 'text-white', 'border-transparent');
                b.classList.add('bg-slate-800', 'text-gray-300', 'border-slate-700');
            });
            btn.classList.add('bg-indigo-600', 'text-white', 'border-transparent');
            btn.classList.remove('bg-slate-800', 'text-gray-300', 'border-slate-700');

            currentAuditProject = btn.getAttribute('data-project') || 'modern-styles';
            renderAuditView();
        });
    });

    stateToggleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            currentAuditState = btn.getAttribute('data-state') || 'after';
            renderAuditView();
        });
    });

    renderAuditView();
}

/* ==========================================================================
   3. EDGE AI & HARDWARE INTEGRATION PROFILES
   ========================================================================== */

function initEdgeAITabs() {
    const tabBtns = document.querySelectorAll('.edge-tab-btn');
    const tabPanels = document.querySelectorAll('.edge-tab-panel');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');

            tabBtns.forEach(b => {
                b.classList.remove('border-cyan-500', 'text-cyan-400', 'bg-cyan-950/40');
                b.classList.add('border-slate-700', 'text-gray-400', 'bg-slate-800/50');
            });
            btn.classList.add('border-cyan-500', 'text-cyan-400', 'bg-cyan-950/40');
            btn.classList.remove('border-slate-700', 'text-gray-400', 'bg-slate-800/50');

            tabPanels.forEach(panel => {
                if (panel.id === targetId) {
                    panel.classList.remove('hidden');
                } else {
                    panel.classList.add('hidden');
                }
            });
        });
    });

    // Copy code button for Docker Compose
    const copyDockerBtn = document.getElementById('copy-docker-compose-btn');
    const dockerCodeEl = document.getElementById('docker-compose-code');
    if (copyDockerBtn && dockerCodeEl) {
        copyDockerBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(dockerCodeEl.textContent).then(() => {
                const orig = copyDockerBtn.innerHTML;
                copyDockerBtn.innerHTML = '<i class="fas fa-check text-emerald-400"></i> Copied';
                setTimeout(() => { copyDockerBtn.innerHTML = orig; }, 1800);
            });
        });
    }
}

/* ==========================================================================
   HELPER UTILITIES
   ========================================================================== */

function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

function setTextAndColor(id, text, colorClass) {
    const el = document.getElementById(id);
    if (el) {
        el.textContent = text;
        el.className = `text-xl font-bold font-mono ${colorClass} transition-colors`;
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>"']/g, m => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    }[m]));
}

function formatMarkdown(text) {
    if (!text) return '';
    let html = escapeHtml(text);
    // Bold **text**
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Italic *text*
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    // Inline code `code`
    html = html.replace(/`(.*?)`/g, '<code class="bg-black/60 px-1.5 py-0.5 rounded text-cyan-300 font-mono text-[11px]">$1</code>');
    // Linebreaks
    html = html.replace(/\n/g, '<br/>');
    return html;
}
