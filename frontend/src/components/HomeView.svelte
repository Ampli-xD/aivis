<script lang="ts">
    import { appState } from '../state.svelte';
    import Logo from './Logo.svelte';
</script>

<div class="home-container">
    <div class="home-layout">
        <!-- Left Section: Branding & Status -->
        <div class="hero-section">
            <div class="hero-content">
                <div class="hero-badge">
                    <div class="badge-dot"></div>
                    <span>SYSTEM ID: AVIS-CORE-01</span>
                </div>
                <h1>Welcome to AVIS</h1>
                <p>
                    The hyper-intelligence platform for your brand. Directing neural workflows 
                    across {appState.brands.length} brand workspaces with real-time 
                    validation and multi-region deployment capabilities.
                </p>
                <div class="hero-footer">
                    <div class="meta-item">
                        <span class="m-label">ACTIVE NODES</span>
                        <span class="m-val">{appState.models.length} API Providers</span>
                    </div>
                    <div class="meta-item">
                        <span class="m-label">BACKEND LATENCY</span>
                        <span class="m-val">{appState.backendLatency}ms</span>
                    </div>
                    <div class="meta-item">
                        <span class="m-label">DATABASE DEPTH</span>
                        <span class="m-val">{appState.dbLatency}ms</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Thin Divider -->
        <div class="divider"></div>

        <!-- Right Section: Navigation -->
        <div class="nav-section">
            <div class="qgrid">
                <button class="qbtn h-analytics" onclick={() => appState.openTab('analytics', 'analytics', 'Analytics')}>
                    <div class="qbtn-visual">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M18 20V10M12 20V4M6 20v-6"/>
                        </svg>
                    </div>
                    <div class="qbtn-text">
                        <div class="qbtn-label">Performance Analytics</div>
                        <div class="qbtn-sub">Neural effectiveness & diagnostics</div>
                    </div>
                    <span class="arrow">→</span>
                </button>

                <button class="qbtn h-decks" onclick={() => appState.openTab('decks', 'deck', 'Decks')}>
                    <div class="qbtn-visual">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
                            <rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/>
                        </svg>
                    </div>
                    <div class="qbtn-text">
                        <div class="qbtn-label">Intelligence Decks</div>
                        <div class="qbtn-sub">Manage clusters and execution logic</div>
                    </div>
                    <span class="arrow">→</span>
                </button>

                <button class="qbtn h-prompts" onclick={() => appState.openTab('all-prompts', 'prompts', 'All prompts')}>
                    <div class="qbtn-visual">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
                        </svg>
                    </div>
                    <div class="qbtn-text">
                        <div class="qbtn-label">Prompt Library</div>
                        <div class="qbtn-sub">Neural instruction set architecture</div>
                    </div>
                    <span class="arrow">→</span>
                </button>

                <button class="qbtn h-instances" onclick={() => appState.openTab('instances', 'instances', 'Instances')}>
                    <div class="qbtn-visual">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
                        </svg>
                    </div>
                    <div class="qbtn-text">
                        <div class="qbtn-label">Execution Archive</div>
                        <div class="qbtn-sub">Historical validation results</div>
                    </div>
                    <span class="arrow">→</span>
                </button>

                <button class="qbtn h-settings" onclick={() => appState.openTab('settings', 'settings', 'Settings')}>
                    <div class="qbtn-visual">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/>
                        </svg>
                    </div>
                    <div class="qbtn-text">
                        <div class="qbtn-label">System Control</div>
                        <div class="qbtn-sub">Global workspace parameters</div>
                    </div>
                    <span class="arrow">→</span>
                </button>
            </div>
        </div>
    </div>
</div>

<style>
    .home-container {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: calc(100vh - 120px);
        padding: 40px;
        background: radial-gradient(circle at 10% 10%, rgba(164, 126, 253, 0.05), transparent 50%);
    }

    .home-layout {
        display: flex;
        align-items: center;
        gap: 80px;
        width: 100%;
        max-width: 1100px;
    }

    /* Left Section */
    .hero-section {
        flex: 1.2;
        animation: slideRight 0.8s cubic-bezier(0.16, 1, 0.3, 1);
    }

    @keyframes slideRight {
        from { opacity: 0; transform: translateX(-30px); }
        to { opacity: 1; transform: translateX(0); }
    }

    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 12px;
        background: rgba(164, 126, 253, 0.05);
        border: 1px solid rgba(164, 126, 253, 0.15);
        border-radius: 4px;
        margin-bottom: 24px;
    }

    .badge-dot {
        width: 5px;
        height: 5px;
        border-radius: 50%;
        background: var(--primary-p2);
        box-shadow: 0 0 8px var(--primary-p2);
    }

    .hero-badge span {
        font-size: 9px;
        font-weight: 700;
        color: var(--primary-p1);
        letter-spacing: 0.15em;
    }

    h1 {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 82px;
        line-height: 0.9;
        color: #e8e6f0;
        letter-spacing: 0.02em;
        margin: 0 0 24px 0;
        background: linear-gradient(to bottom, #fff, #a09cc0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    p {
        font-size: 16px;
        color: #6b6882;
        line-height: 1.7;
        margin-bottom: 40px;
        max-width: 480px;
    }

    .hero-footer {
        display: flex;
        gap: 40px;
    }

    .meta-item {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .m-label {
        font-size: 10px;
        color: #3d3b52;
        font-weight: 600;
        letter-spacing: 0.1em;
    }

    .m-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        color: var(--primary-p2);
    }

    /* Divider */
    .divider {
        width: 1px;
        height: 380px;
        background: linear-gradient(to bottom, transparent, #1e1c2a, transparent);
    }

    /* Right Section */
    .nav-section {
        flex: 1;
        animation: slideLeft 0.8s cubic-bezier(0.16, 1, 0.3, 1) 0.1s both;
    }

    @keyframes slideLeft {
        from { opacity: 0; transform: translateX(30px); }
        to { opacity: 1; transform: translateX(0); }
    }

    .qgrid {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }

    .qbtn {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 20px;
        background: rgba(15, 14, 22, 0.4);
        border: 1px solid #1e1c2a;
        border-radius: 12px;
        text-align: left;
        cursor: pointer;
        transition: all 0.3s ease;
        position: relative;
        backdrop-filter: blur(5px);
    }

    .qbtn:hover {
        background: #14131f;
        border-color: #2a2840;
        transform: translateX(6px);
    }

    .qbtn-visual {
        width: 40px;
        height: 40px;
        border-radius: 8px;
        background: #1a1826;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #6b6882;
        transition: all 0.3s ease;
        flex-shrink: 0;
    }

    .qbtn-label {
        font-size: 14px;
        font-weight: 600;
        color: #e8e6f0;
        margin-bottom: 2px;
    }

    .qbtn-sub {
        font-size: 12px;
        color: #3d3b52;
    }

    .arrow {
        margin-left: auto;
        font-size: 18px;
        color: #3d3b52;
        transition: all 0.3s ease;
        opacity: 0;
        transform: translateX(-10px);
    }

    .qbtn:hover .arrow {
        opacity: 1;
        transform: translateX(0);
        color: var(--primary-p2);
    }

    .qbtn:hover .qbtn-visual {
        background: var(--primary-p3);
        color: #fff;
    }

    .h-analytics:hover .qbtn-visual { background: var(--primary-p3); }
    .h-prompts:hover .qbtn-visual { background: var(--primary-p1); }
    .h-instances:hover .qbtn-visual { background: var(--primary-p2); }
    .h-decks:hover .qbtn-visual { background: #10b981; }

    @media (max-width: 900px) {
        .home-layout {
            flex-direction: column;
            gap: 40px;
            align-items: flex-start;
        }
        .divider {
            width: 100%;
            height: 1px;
            background: linear-gradient(to right, transparent, #1e1c2a, transparent);
        }
        h1 { font-size: 56px; }
    }
</style>
