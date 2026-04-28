<script lang="ts">
    import { appState } from '../state.svelte';
    import AnalyticsDashboard from './AnalyticsDashboard.svelte';
    
    // Filters
    let selectedDeckId = $state('all');
    let selectedPromptId = $state('all');
    let selectedModelId = $state('all');
    let selectedRegionId = $state('all');
    let startDate = $state('');
    let endDate = $state('');
    let isAnalyzing = $state(false);
    let viewMode = $state('dashboard'); // 'dashboard', 'cards' or 'table'

    // Derived filtered list of instances that HAVE metrics
    const analyzedInstances = $derived(
        appState.instances.filter(i => {
            // Only show those with metrics for analytics view
            const hasMetrics = i.metrics && Object.keys(i.metrics).length > 0;
            if (!hasMetrics) return false;

            const matchesBrand = i.brandId === appState.activeBrandId;
            const matchesDeck = selectedDeckId === 'all' || i.deckId === selectedDeckId;
            const matchesPrompt = selectedPromptId === 'all' || i.promptId === selectedPromptId;
            const matchesModel = selectedModelId === 'all' || i.modelId === selectedModelId;
            const matchesRegion = selectedRegionId === 'all' || i.regionId === selectedRegionId;
            
            // Simplified date check
            let matchesDate = true;
            if (startDate || endDate) {
                const iDate = new Date(i.timeBucket).getTime();
                if (startDate && iDate < new Date(startDate).getTime()) matchesDate = false;
                if (endDate && iDate > new Date(endDate).getTime()) matchesDate = false;
            }

            return matchesBrand && matchesDeck && matchesPrompt && matchesModel && matchesRegion && matchesDate;
        })
    );

    // Filter options from current brand
    const brandDecks = $derived(appState.decks.filter(d => d.brandId === appState.activeBrandId));
    const brandPrompts = $derived(appState.allPrompts.filter(p => p.brandId === appState.activeBrandId));

    const unprocessedCount = $derived(
        appState.instances.filter(i => {
           const noMetrics = !i.metrics || Object.keys(i.metrics).length === 0;
           return i.brandId === appState.activeBrandId && noMetrics;
        }).length
    );

    async function triggerAnalysis() {
        isAnalyzing = true;
        // Process up to 100 at a time
        await appState.runAnalytics(100, appState.activeBrandId ?? undefined);
        isAnalyzing = false;
    }

    // Sorting
    let sortKey = $state('date');
    let sortDir = $state<'asc' | 'desc'>('desc');

    function toggleSort(key: string) {
        if (sortKey === key) {
            sortDir = sortDir === 'asc' ? 'desc' : 'asc';
        } else {
            sortKey = key;
            sortDir = 'desc';
        }
    }

    const sortedInstances = $derived(() => {
        return [...analyzedInstances].sort((a, b) => {
            let valA: any, valB: any;
            if (sortKey === 'date') {
                valA = new Date(a.timeBucket).getTime();
                valB = new Date(b.timeBucket).getTime();
            } else if (sortKey === 'deck') {
                valA = a.deckName || '';
                valB = b.deckName || '';
            } else if (sortKey === 'model') {
                valA = a.modelName || '';
                valB = b.modelName || '';
            } else if (sortKey === 'status') {
                valA = a.metrics.brand_mentioned ? 1 : 0;
                valB = b.metrics.brand_mentioned ? 1 : 0;
            } else if (sortKey === 'sentiment') {
                valA = a.metrics.sentiment_score ?? -2;
                valB = b.metrics.sentiment_score ?? -2;
            } else if (sortKey === 'position') {
                valA = a.metrics.brand_position ?? 100;
                valB = b.metrics.brand_position ?? 100;
            } else {
                valA = (a as any)[sortKey];
                valB = (b as any)[sortKey];
            }

            if (valA < valB) return sortDir === 'asc' ? -1 : 1;
            if (valA > valB) return sortDir === 'asc' ? 1 : -1;
            return 0;
        });
    });

    function downloadCSV() {
        if (analyzedInstances.length === 0) return;

        const headers = [
            'Instance ID', 'Time', 'Brand', 'Deck', 'Model', 'Region', 'Prompt', 'Mentioned', 
            'Narrative', 'Intent', 'Position', 'Sentiment', 'Density', 'Response'
        ];
        
        const rows = analyzedInstances.map(i => {
            return [
                i.id,
                new Date(i.timeBucket).toISOString(),
                `"${(i.brandName || '-').replace(/"/g, '""')}"`,
                `"${(i.deckName || '-').replace(/"/g, '""')}"`,
                `"${(i.modelName || '-').replace(/"/g, '""')}"`,
                `"${(i.regionName || '-').replace(/"/g, '""')}"`,
                `"${(i.promptContent || '').replace(/"/g, '""')}"`,
                i.metrics.brand_mentioned ? 'Yes' : 'No',
                i.metrics.narrative_mention ? 'Yes' : 'No',
                i.metrics.mention_intent || '-',
                i.metrics.brand_position || '-',
                i.metrics.sentiment_score ?? '-',
                i.metrics.brand_mention_density ?? '-',
                `"${JSON.stringify(i.responseData).replace(/"/g, '""')}"`
            ].join(',');
        });

        const csvContent = [headers.join(','), ...rows].join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', `aivis_raw_export_${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
</script>

<div class="analytics-container">
    <div class="filter-bar">
        <div class="filter-group">
            <label for="deckFilter">Deck</label>
            <select id="deckFilter" bind:value={selectedDeckId}>
                <option value="all">All Decks</option>
                {#each brandDecks as d}
                    <option value={d.id}>{d.name}</option>
                {/each}
            </select>
        </div>

        <div class="filter-group">
            <label for="promptFilter">Prompt</label>
            <select id="promptFilter" bind:value={selectedPromptId}>
                <option value="all">All Prompts</option>
                {#each brandPrompts as p}
                    <option value={p.id}>{p.content.substring(0, 30)}...</option>
                {/each}
            </select>
        </div>

        <div class="filter-group">
            <label for="modelFilter">Model</label>
            <select id="modelFilter" bind:value={selectedModelId}>
                <option value="all">All Models</option>
                {#each appState.models as m}
                    <option value={m.id}>{m.modelName}</option>
                {/each}
            </select>
        </div>

        <div class="filter-group">
            <label for="regionFilter">Region</label>
            <select id="regionFilter" bind:value={selectedRegionId}>
                <option value="all">All Regions</option>
                {#each appState.regions as r}
                    <option value={r.id}>{r.name}</option>
                {/each}
            </select>
        </div>

        <div class="filter-group">
            <label for="startDate">Start date</label>
            <input id="startDate" type="date" bind:value={startDate} />
        </div>

        <div class="filter-group">
            <label for="endDate">End date</label>
            <input id="endDate" type="date" bind:value={endDate} />
        </div>

        <button class="run-btn" onclick={triggerAnalysis} disabled={isAnalyzing}>
            {#if isAnalyzing}
                Analyzing...
            {:else}
                Run Analysis {unprocessedCount > 0 ? `(${unprocessedCount})` : ''}
            {/if}
        </button>
    </div>

    <div class="stats-overview">
        <div class="stat-card">
            <div class="stat-label">ANALYZED RESPONSES</div>
            <div class="stat-val">{analyzedInstances.length}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">BRAND MENTIONED</div>
            <div class="stat-val g">
                {Math.round((analyzedInstances.filter(i => i.metrics.brand_mentioned).length / (analyzedInstances.length || 1)) * 100)}%
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-label">NARRATIVE MENTION</div>
            <div class="stat-val" style="color:var(--primary-p3)">
                {analyzedInstances.filter(i => i.metrics.narrative_mention).length}
            </div>
        </div>
    </div>

    <div class="view-header">
        <div class="view-controls">
            <button class="view-tab {viewMode === 'dashboard' ? 'active' : ''}" onclick={() => viewMode = 'dashboard'}>Dashboard</button>
            <button class="view-tab {viewMode === 'cards' ? 'active' : ''}" onclick={() => viewMode = 'cards'}>Full Feed</button>
            <button class="view-tab {viewMode === 'table' ? 'active' : ''}" onclick={() => viewMode = 'table'}>Metric Table</button>
        </div>
        <button class="export-csv-btn" onclick={downloadCSV} disabled={analyzedInstances.length === 0}>
            Export to CSV
        </button>
    </div>

    {#if analyzedInstances.length === 0}
        <div class="empty-state">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M3 3v18h18M7 16l4-4 4 4 6-6" />
            </svg>
            <p>No analyzed data found for the current filters.</p>
            <button onclick={triggerAnalysis}>Run Initial Analysis</button>
        </div>
    {:else if viewMode === 'dashboard'}
        <AnalyticsDashboard 
            instances={analyzedInstances} 
            models={appState.models} 
            prompts={brandPrompts} 
        />
    {:else if viewMode === 'cards'}
        <div class="analytics-grid">
            {#each analyzedInstances as i (i.id)}
                <div class="analysis-card" onclick={() => appState.openTab(i.id, 'instance', 'Instance: ' + i.id.split('-')[1])} onkeydown={(e) => e.key === 'Enter' && appState.openTab(i.id, 'instance', 'Instance: ' + i.id.split('-')[1])} role="button" tabindex="0">
                    <div class="card-header">
                        <div class="brand-tag {i.metrics.brand_mentioned ? 'mentioned' : 'missing'}">
                            {i.metrics.brand_mentioned ? 'Mentioned' : 'Not Mentioned'}
                        </div>
                        <div class="timestamp">{new Date(i.timeBucket).toLocaleDateString()}</div>
                    </div>
                    
                    <div class="deck-info">{i.deckName}</div>
                    <div class="prompt-snippet">{i.promptContent}</div>
                    
                    <div class="metrics-row">
                        <div class="metric">
                            <span class="m-label">Intent</span>
                            <span class="m-val">{i.metrics.mention_intent || 'None'}</span>
                        </div>
                        <div class="metric">
                            <span class="m-label">Position</span>
                            <span class="m-val">#{i.metrics.brand_position || '-'}</span>
                        </div>
                        <div class="metric">
                            <span class="m-label">Density</span>
                            <span class="m-val">{i.metrics.brand_mention_density ? (i.metrics.brand_mention_density * 100).toFixed(1) + '%' : '-'}</span>
                        </div>
                    </div>

                    <div class="source-list">
                        {#if (i.metrics.mention_sources || []).length > 0}
                            <div class="source-label">Mention Sources:</div>
                            <div class="sources">
                                {#each i.metrics.mention_sources.slice(0, 3) as s}
                                    <div class="source-link" title={s.url}>{s.source}</div>
                                {/each}
                                {#if i.metrics.mention_sources.length > 3}
                                    <div class="source-more">+{i.metrics.mention_sources.length - 3} more</div>
                                {/if}
                            </div>
                        {:else}
                            <div class="no-sources">No mentions linked to sources</div>
                        {/if}
                    </div>
                </div>
            {/each}
        </div>
    {:else}
        <div class="table-wrap">
            <table class="analytics-table">
                <thead>
                    <tr>
                        <th style="width: 100px" class="sortable" onclick={() => toggleSort('status')}>
                            Status {sortKey === 'status' ? (sortDir === 'asc' ? '↑' : '↓') : ''}
                        </th>
                        <th class="sortable" onclick={() => toggleSort('deck')}>
                            Deck {sortKey === 'deck' ? (sortDir === 'asc' ? '↑' : '↓') : ''}
                        </th>
                        <th class="sortable" onclick={() => toggleSort('model')}>
                            Model {sortKey === 'model' ? (sortDir === 'asc' ? '↑' : '↓') : ''}
                        </th>
                        <th class="sortable" onclick={() => toggleSort('date')}>
                            Date {sortKey === 'date' ? (sortDir === 'asc' ? '↑' : '↓') : ''}
                        </th>
                        <th>Intent</th>
                        <th class="sortable" onclick={() => toggleSort('position')}>
                            Pos {sortKey === 'position' ? (sortDir === 'asc' ? '↑' : '↓') : ''}
                        </th>
                        <th>Density</th>
                        <th class="sortable" onclick={() => toggleSort('sentiment')}>
                            Sentiment {sortKey === 'sentiment' ? (sortDir === 'asc' ? '↑' : '↓') : ''}
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {#each sortedInstances as i (i.id)}
                        <tr onclick={() => appState.openTab(i.id, 'instance', 'Instance: ' + i.id.split('-')[1])}>
                            <td>
                                <span class="dot {i.metrics.brand_mentioned ? 'mentioned' : 'missing'}"></span>
                                {i.metrics.brand_mentioned ? 'Mentioned' : 'Missing'}
                            </td>
                            <td>{i.deckName}</td>
                            <td>{i.modelName}</td>
                            <td>{new Date(i.timeBucket).toLocaleDateString()}</td>
                            <td><span class="intent-pill">{i.metrics.mention_intent || '-'}</span></td>
                            <td class="num">{i.metrics.brand_position || '-'}</td>
                            <td class="num">{i.metrics.brand_mention_density ? (i.metrics.brand_mention_density * 100).toFixed(1) + '%' : '-'}</td>
                            <td class="num">
                                {#if i.metrics.sentiment_score !== null}
                                    <span class="sent {i.metrics.sentiment_score > 0 ? 'pos' : (i.metrics.sentiment_score < 0 ? 'neg' : 'neu')}">
                                        {i.metrics.sentiment_score.toFixed(2)}
                                    </span>
                                {:else}
                                    -
                                {/if}
                            </td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    {/if}
</div>

<style>
    .analytics-container {
        padding: 24px;
        height: 100%;
        overflow-y: auto;
    }

    .filter-bar {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        background: rgba(16, 14, 27, 0.4);
        padding: 16px;
        border-radius: 12px;
        border: 1px solid rgba(164, 126, 253, 0.1);
        align-items: flex-end;
        margin-bottom: 24px;
    }

    .filter-group {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }

    .filter-group label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 10px;
        text-transform: uppercase;
        color: #6b6882;
        letter-spacing: 0.05em;
    }

    .filter-group select, .filter-group input {
        background: #0d0c16;
        border: 1px solid #3d3b52;
        color: #fff;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 12px;
        outline: none;
        min-width: 140px;
    }

    .filter-group select:focus, .filter-group input:focus {
        border-color: var(--primary-p3);
    }

    .run-btn {
        background: var(--primary-p3);
        color: #fff;
        border: none;
        padding: 9px 20px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
        height: 35px;
    }

    .run-btn:hover:not(:disabled) {
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(164, 126, 253, 0.3);
    }

    .run-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    .stats-overview {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
    }

    .stat-card {
        background: rgba(16, 14, 27, 0.4);
        border: 1px solid rgba(164, 126, 253, 0.08);
        padding: 20px;
        border-radius: 12px;
    }

    .stat-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        color: #6b6882;
        margin-bottom: 8px;
    }

    .stat-val {
        font-size: 28px;
        font-weight: 700;
        font-family: 'Outfit', sans-serif;
    }

    .stat-val.g { color: #a47efd; }

    .analytics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 20px;
    }

    .analysis-card {
        background: rgba(16, 14, 27, 0.4);
        border: 1px solid rgba(164, 126, 253, 0.08);
        padding: 20px;
        border-radius: 12px;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .analysis-card:hover {
        border-color: rgba(164, 126, 253, 0.3);
        background: rgba(22, 19, 38, 0.6);
        transform: translateY(-2px);
    }

    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }

    .brand-tag {
        font-size: 10px;
        text-transform: uppercase;
        font-weight: 700;
        padding: 4px 8px;
        border-radius: 4px;
        letter-spacing: 0.05em;
    }

    .brand-tag.mentioned {
        background: rgba(164, 126, 253, 0.2);
        color: var(--primary-p3);
    }

    .brand-tag.missing {
        background: rgba(235, 87, 87, 0.1);
        color: #eb5757;
    }

    .timestamp {
        font-size: 11px;
        color: #3d3b52;
    }

    .deck-info {
        font-size: 11px;
        font-family: 'JetBrains Mono', monospace;
        color: var(--primary-p2);
        margin-bottom: 4px;
    }

    .prompt-snippet {
        font-size: 14px;
        color: #fff;
        line-height: 1.4;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        margin-bottom: 16px;
    }

    .metrics-row {
        display: flex;
        gap: 24px;
        padding: 12px 0;
        border-top: 1px solid rgba(164, 126, 253, 0.1);
        border-bottom: 1px solid rgba(164, 126, 253, 0.1);
        margin-bottom: 12px;
    }

    .metric {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .m-label {
        font-size: 9px;
        color: #6b6882;
        text-transform: uppercase;
    }

    .m-val {
        font-size: 12px;
        font-weight: 600;
        color: #fff;
    }

    .source-list {
        margin-top: 8px;
    }

    .source-label {
        font-size: 10px;
        color: #6b6882;
        margin-bottom: 6px;
    }

    .sources {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }

    .source-link {
        font-size: 11px;
        background: #0d0c16;
        padding: 2px 8px;
        border-radius: 4px;
        border: 1px solid #3d3b52;
        color: #a3a1b5;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 120px;
    }

    .source-more {
        font-size: 11px;
        color: #3d3b52;
    }

    .no-sources {
        font-size: 11px;
        font-style: italic;
        color: #3d3b52;
    }

    .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 60px;
        background: rgba(16, 14, 27, 0.2);
        border: 1px dashed rgba(164, 126, 253, 0.2);
        border-radius: 12px;
        color: #6b6882;
        text-align: center;
    }

    .empty-state svg {
        margin-bottom: 16px;
        opacity: 0.5;
    }

    .empty-state p {
        margin-bottom: 20px;
    }

    .empty-state button {
        background: #0d0c16;
        border: 1px solid var(--primary-p3);
        color: var(--primary-p3);
        padding: 8px 16px;
        border-radius: 6px;
        cursor: pointer;
    }

    /* Table & View Mode Styling */
    .view-controls {
        display: flex;
        gap: 8px;
        margin-bottom: 16px;
    }

    .view-tab {
        background: rgba(16, 14, 27, 0.4);
        border: 1px solid rgba(164, 126, 253, 0.1);
        color: #6b6882;
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 11px;
        font-family: 'JetBrains Mono', monospace;
        cursor: pointer;
        transition: all 0.2s;
    }

    .view-tab.active {
        background: rgba(164, 126, 253, 0.1);
        color: var(--primary-p3);
        border-color: var(--primary-p3);
    }

    .view-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
    }

    .export-csv-btn {
        background: transparent;
        border: 1px solid rgba(164, 126, 253, 0.3);
        color: var(--primary-p3);
        padding: 6px 14px;
        border-radius: 6px;
        font-size: 11px;
        cursor: pointer;
        transition: all 0.2s;
    }

    .export-csv-btn:hover:not(:disabled) {
        background: rgba(164, 126, 253, 0.1);
        border-color: var(--primary-p3);
    }

    .export-csv-btn:disabled {
        opacity: 0.3;
        cursor: not-allowed;
    }

    .table-wrap {
        background: rgba(16, 14, 27, 0.4);
        border: 1px solid rgba(164, 126, 253, 0.1);
        border-radius: 12px;
        overflow: hidden;
    }
/* ... */
    .sent.neu { color: #94a3b8; background: rgba(148, 163, 184, 0.1); }

    .sortable {
        cursor: pointer;
        user-select: none;
    }
    .sortable:hover {
        color: var(--primary-p3) !important;
        background: rgba(164, 126, 253, 0.1) !important;
    }

    .analytics-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        color: #a3a1b5;
    }

    .analytics-table th {
        text-align: left;
        padding: 12px 16px;
        background: rgba(22, 19, 38, 0.6);
        font-family: 'JetBrains Mono', monospace;
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #6b6882;
        border-bottom: 1px solid rgba(164, 126, 253, 0.1);
    }

    .analytics-table tr {
        border-bottom: 1px solid rgba(164, 126, 253, 0.05);
        cursor: pointer;
        transition: background 0.2s;
    }

    .analytics-table tr:hover {
        background: rgba(164, 126, 253, 0.05);
    }

    .analytics-table td {
        padding: 12px 16px;
        vertical-align: middle;
    }

    .dot {
        display: inline-block;
        width: 6px;
        height: 6px;
        border-radius: 50%;
        margin-right: 8px;
    }

    .dot.mentioned { background: #a47efd; box-shadow: 0 0 8px rgba(164, 126, 253, 0.6); }
    .dot.missing { background: #eb5757; }

    .intent-pill {
        font-size: 10px;
        background: #0d0c16;
        padding: 2px 6px;
        border-radius: 4px;
        border: 1px solid #3d3b52;
        text-transform: capitalize;
    }

    .num {
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
    }

    .sent {
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 11px;
    }
    .sent.pos { color: #4ade80; background: rgba(74, 222, 128, 0.1); }
    .sent.neg { color: #f87171; background: rgba(248, 113, 113, 0.1); }
    .sent.neu { color: #94a3b8; background: rgba(148, 163, 184, 0.1); }
</style>
