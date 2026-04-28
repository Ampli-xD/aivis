<script lang="ts">
    import { appState } from '../state.svelte';
    
    let searchQuery = $state('');

    const filteredInstances = $derived(
        appState.instances.filter(i => {
            const matchesBrand = i.brandId === appState.activeBrandId;
            const matchesSearch = i.promptContent.toLowerCase().includes(searchQuery.toLowerCase()) || i.id.toLowerCase().includes(searchQuery.toLowerCase());
            return matchesBrand && matchesSearch;
        })
    );
</script>

<div class="stats-grid">
    <div class="stat-card"><div class="stat-label">TOTAL INSTANCES</div><div class="stat-val">{appState.instances.length}</div></div>
    <div class="stat-card"><div class="stat-label">AVG LATENCY</div><div class="stat-val g">1.1s</div></div>
    <div class="stat-card"><div class="stat-label">TOKENS PROCESSED</div><div class="stat-val" style="color:var(--primary-p3)">18.4k</div></div>
    <div class="stat-card"><div class="stat-label">REGIONS COVERED</div><div class="stat-val">{appState.regions.length}</div></div>
</div>

<div class="toolbar">
    <div style="display:flex;align-items:center;gap:8px">
        <span class="sec-title">Execution History</span>
    </div>
    <input class="srch" placeholder="Search prompts/IDs…" bind:value={searchQuery}>
</div>

<div class="grid2">
    {#each filteredInstances as i (i.id)}
        <div class="card" onclick={() => appState.openTab(i.id, 'instance', 'Instance: ' + i.id.split('-')[1])} onkeydown={(e) => e.key === 'Enter' && appState.openTab(i.id, 'instance', 'Instance: ' + i.id.split('-')[1])} role="button" tabindex="0">
            <div class="card-top">
                <div>
                    <div class="card-name" style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--primary-p2)">{i.id}</div>
                    <div class="card-id">{i.deckName}</div>
                </div>
                <div style="font-size: 10px; color: #3d3b52; font-weight: 500">HISTORY</div>
            </div>
            <div class="divl"></div>
            <div class="prev" style="-webkit-line-clamp: 2; font-size: 12px; color: #6b6882; margin: 10px 0; line-height: 1.5">
                {i.promptContent}
            </div>
            <div class="mrow">
                <span class="mi"><span class="ml">Model </span>{i.modelName}</span>
                <span class="mi"><span class="ml">Region </span>{i.regionName}</span>
            </div>
            <div class="card-foot">
                <div class="pmeta">
                    <span class="mi"><span class="ml">Started </span>{i.initiatedAt}</span>
                    {#if i.metrics?.latency}
                        <span class="mi"><span class="ml">Latency </span>{i.metrics.latency}s</span>
                    {/if}
                </div>
            </div>
        </div>
    {/each}
</div>

<style>
    /* Styling for p1 is unused now, but keeping clean */
</style>
