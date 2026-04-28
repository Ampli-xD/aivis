<script lang="ts">
    import { appState } from '../state.svelte';
    
    let filter = $state('all');
    let searchQuery = $state('');

    const filteredDecks = $derived(
        appState.decks.filter(d => {
            const matchesBrand = d.brandId === appState.activeBrandId;
            const matchesFilter = filter === 'all' || (filter === 'active' ? d.toExecute : !d.toExecute);
            const matchesSearch = d.name.toLowerCase().includes(searchQuery.toLowerCase());
            return matchesBrand && matchesFilter && matchesSearch;
        })
    );

    const activeCount = $derived(filteredDecks.filter(d => d.toExecute).length);
    const totalCount = $derived(filteredDecks.length);
    const inactiveCount = $derived(totalCount - activeCount);

    function getBrandName(brandId: string) {
        return appState.brands.find(b => b.id === brandId)?.name || 'Unknown Brand';
    }

    function getLastRun(deckId: string) {
        const instances = appState.instances.filter(i => i.deckId === deckId);
        if (instances.length === 0) return 'Never';
        // Instances are already sorted DESC in state
        const last = instances[0];
        const date = new Date(last.initiatedAt);
        return date.toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    }
</script>

<div class="stats-grid">
    <div class="stat-card"><div class="stat-label">TOTAL DECKS</div><div class="stat-val">{totalCount}</div></div>
    <div class="stat-card"><div class="stat-label">ACTIVE</div><div class="stat-val g">{activeCount}</div></div>
    <div class="stat-card"><div class="stat-label">INACTIVE</div><div class="stat-val r">{inactiveCount}</div></div>
    <div class="stat-card"><div class="stat-label">AVG PROMPTS</div><div class="stat-val">2.5</div></div>
</div>

<div class="toolbar">
    <div style="display:flex;align-items:center;gap:8px">
        <span class="sec-title">All decks</span>
        <div class="filter-wrap">
            <button class="fb {filter === 'all' ? 'on' : ''}" onclick={() => filter = 'all'}>All</button>
            <button class="fb {filter === 'active' ? 'on' : ''}" onclick={() => filter = 'active'}>Active</button>
            <button class="fb {filter === 'inactive' ? 'on' : ''}" onclick={() => filter = 'inactive'}>Inactive</button>
        </div>
    </div>
    <div style="display:flex;gap:6px">
        <input class="srch" placeholder="Search decks…" bind:value={searchQuery}>
        <button class="new-btn" onclick={() => appState.showCreateDeckModal = true}>+ New deck</button>
    </div>
</div>

<div class="grid2">
    {#each filteredDecks as d (d.id)}
        <div class="card" onclick={() => appState.openTab(d.id, 'deck', d.name)} onkeydown={(e) => e.key === 'Enter' && appState.openTab(d.id, 'deck', d.name)} role="button" tabindex="0">
            <div class="card-top">
                <div>
                    <div class="card-name">{d.name}</div>
                    <div class="card-id" style="font-family: inherit; font-size: 11px; color: #3d3b52">{getBrandName(d.brandId)}</div>
                </div>
                <span class="pill {d.toExecute ? 'a' : 'i'}">{d.toExecute ? 'active' : 'inactive'}</span>
            </div>
            <div class="divl"></div>
            <div class="mrow" style="margin-top: 4px; gap: 8px">
                <span class="mi" style="font-size: 9px"><span class="ml">PROMPTS </span>{d.promptIds.length}</span>
                <span class="mi" style="font-size: 9px"><span class="ml">NEXT </span>{d.nextExecutionTime ? new Date(d.nextExecutionTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit'}) : 'PAUSED'}</span>
            </div>
            <div class="card-foot" style="margin-top: 10px; flex-wrap: nowrap;">
                <div class="tags"><span class="tag" style="font-size: 8px; padding: 1px 5px">System</span></div>
                <div style="display: flex; align-items: center; gap: 3px; color: #4ade80; font-size: 9px; font-weight: 600; font-family: 'JetBrains Mono', monospace; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                    <span style="color: #3d3b52; font-size: 8px; letter-spacing: 0.05em">LAST </span>
                    <span style="overflow: hidden; text-overflow: ellipsis;">{getLastRun(d.id)}</span>
                </div>
            </div>
            <div class="bar-bg" style="margin-top: 10px; height: 3px; width: 100%; overflow: hidden; position: relative">
                <div class="bar {d.toExecute ? 'g' : 'r'}" style="height: 100%; position: absolute; left: 0; top: 0; max-width: 100%; width:{Math.min(100, (appState.instances.filter(i => i.deckId === d.id).length / Math.max(1, (d.promptIds.length || 0) * (d.regionIds.length || 0) * (d.modelIds.length || 0)) * 100))}%"></div>
            </div>
        </div>
    {/each}
</div>
