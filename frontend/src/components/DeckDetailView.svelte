<script lang="ts">
    import { appState } from '../state.svelte';
    
    interface Props {
        deckId: string;
    }
    let { deckId }: Props = $props();

    let activeView = $state('prompts'); // 'prompts' or 'instances'

    const deck = $derived(appState.decks.find(d => d.id === deckId));
    const prompts = $derived(appState.allPrompts.filter(p => deck?.promptIds.includes(p.id)));
    const instances = $derived(appState.instances.filter(i => i.deckId === deckId));
    const totalInstancesCount = $derived((deck?.promptIds.length || 0) * (deck?.regionIds.length || 0) * (deck?.modelIds.length || 0));

    function getModelNames() {
        return deck?.modelIds.map(id => appState.models.find(m => m.id === id)?.modelName).join(', ') || 'None';
    }

    function getRegionNames() {
        return deck?.regionIds.map(id => appState.regions.find(r => r.id === id)?.countryCode).join(', ') || 'None';
    }

    function getBrandName() {
        return appState.brands.find(b => b.id === deck?.brandId)?.name || 'Unknown Brand';
    }

    function formatTime(slots: number) {
        let totalMins = slots * appState.cronInterval;
        if (totalMins === 0) return 'Immediate';
        const minsPerDay = 1440;
        const minsPerWeek = 10080;
        if (totalMins < 60) return `${totalMins}m`;
        if (totalMins < minsPerDay) {
            const h = Math.floor(totalMins / 60);
            const m = totalMins % 60;
            return m > 0 ? `${h}h ${m}m` : `${h}h`;
        }
        if (totalMins < minsPerWeek) {
            const d = Math.floor(totalMins / minsPerDay);
            const h = Math.floor((totalMins % minsPerDay) / 60);
            return h > 0 ? `${d}d ${h}h` : `${d}d`;
        }
        return `${Math.floor(totalMins / minsPerWeek)}w`;
    }

    function getLastExecution() {
        if (instances.length === 0) return 'Never';
        const last = instances[0]; // Already sorted DESC
        return new Date(last.initiatedAt).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' });
    }

    async function toggleStatus() {
        if (!deck) return;
        await appState.updateDeck(deckId, { to_execute: !deck.toExecute });
    }
</script>

{#if deck}
    <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:1.25rem;flex-wrap:wrap;gap:10px">
        <div>
            <div style="font-size:17px;font-weight:600;color:#e8e6f0">{deck.name}</div>
            <div style="font-size:11px;color:#3d3b52;margin-top:3px;font-family:JetBrains Mono,monospace">{getBrandName()}</div>
        </div>
        <div style="display:flex;gap:8px;align-items:center">
            <span class="pill {deck.toExecute ? 'a' : 'i'}">{deck.toExecute ? 'active' : 'inactive'}</span>
            <button class="action-btn" onclick={toggleStatus} style="font-size:11px;padding:4px 10px; color: {deck.toExecute ? '#f87171' : '#4ade80'}">
                {deck.toExecute ? 'Disable Deck' : 'Enable Deck'}
            </button>
            <button class="action-btn" onclick={() => appState.editingDeck = deck} style="font-size:11px;padding:4px 10px">Edit</button>
            <button class="del-btn" onclick={() => appState.deleteDeck(deckId)} style="font-size:11px;padding:4px 10px">Delete</button>
        </div>
    </div>

    <!-- Configuration Grid -->
    <div class="card" style="margin-bottom: 20px; cursor: default">
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px">
            <div>
                <div class="mb-label">MODELS IN HUB</div>
                <div style="font-size: 13px; color: #e8e6f0; margin-top: 4px">{getModelNames()}</div>
            </div>
            <div>
                <div class="mb-label">GEO REGIONS</div>
                <div style="font-size: 13px; color: #e8e6f0; margin-top: 4px">{getRegionNames()}</div>
            </div>
            <div>
                <div class="mb-label">EXECTUION CYCLE (TOTAL)</div>
                <div style="font-size: 20px; font-weight: 600; color: var(--primary-p2); margin-top: 4px">
                    {instances.length} <span style="font-size: 11px; color: #3d3b52; font-weight: 400">/ max {totalInstancesCount}</span>
                </div>
            </div>
        </div>
    </div>

    <div class="meta-grid3">
        <div class="mb"><div class="mb-label">PROMPT SEQUENCES</div><div class="mb-val">{deck.promptIds.length}</div></div>
        <div class="mb"><div class="mb-label">LAST EXECUTION</div><div class="mb-val" style="color:#4ade80">{getLastExecution()}</div></div>
        <div class="mb"><div class="mb-label">LIVE FREQUENCY</div><div class="mb-val">{formatTime(deck.frequency)}</div></div>
    </div>
    
    <div style="font-size:12px;color:#6b6882;margin-bottom:1.25rem;line-height:1.7">{deck.name} was initialized on {new Date(deck.createdAt).toLocaleDateString()}. Runs every {formatTime(deck.frequency)}.</div>
    
    
    <div class="divl" style="margin-bottom:1rem"></div>

    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px">
        <div class="filter-wrap" style="margin: 0">
            <button class="fb {activeView === 'prompts' ? 'on' : ''}" onclick={() => activeView = 'prompts'}>Prompts ({prompts.length})</button>
            <button class="fb {activeView === 'instances' ? 'on' : ''}" onclick={() => activeView = 'instances'}>Executed Instances ({instances.length})</button>
        </div>
    </div>

    {#if activeView === 'prompts'}
        <div class="plist">
            {#each prompts as p (p.id)}
                <div class="pc" onclick={() => appState.openTab(p.id, 'prompt', 'Prompt: ' + p.id.split('-')[1])} onkeydown={(e) => e.key === 'Enter' && appState.openTab(p.id, 'prompt', 'Prompt: ' + p.id.split('-')[1])} role="button" tabindex="0">
                    <div class="pc-top">
                        <div class="pc-name" style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--primary-p2)">{p.id}</div>
                        <span class="pill a">ready</span>
                    </div>
                    <div class="prev" style="-webkit-line-clamp: 4; margin-top: 8px">{p.content}</div>
                </div>
            {:else}
                <div style="text-align:center;padding:2rem;color:#3d3b52;font-size:13px">No prompts yet.</div>
            {/each}
        </div>
    {:else}
        <div class="grid2">
            {#each instances as i (i.id)}
                <div class="card" onclick={() => appState.openTab(i.id, 'instance', 'Instance: ' + i.id.split('-')[1])} onkeydown={(e) => e.key === 'Enter' && appState.openTab(i.id, 'instance', 'Instance: ' + i.id.split('-')[1])} role="button" tabindex="0">
                    <div class="card-top">
                        <div class="card-name" style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--primary-p2)">{i.id}</div>
                        <div style="font-size: 10px; color: #3d3b52; font-weight: 500">HISTORY</div>
                    </div>
                    <div class="prev" style="-webkit-line-clamp: 2; font-size: 12px; color: #6b6882; margin: 10px 0; line-height: 1.5">
                        {i.promptContent}
                    </div>
                    <div class="mrow">
                        <span class="mi"><span class="ml">Model </span>{i.modelName}</span>
                        <span class="mi"><span class="ml">Region </span>{i.regionName}</span>
                    </div>
                    <div class="card-foot">
                        <span class="ts">Started {i.initiatedAt}</span>
                    </div>
                </div>
            {:else}
                <div style="text-align:center;padding:2rem;color:#3d3b52;font-size:13px">No instances executed yet.</div>
            {/each}
        </div>
    {/if}

{:else}
    <div style="text-align:center;padding:2rem;color:#3d3b52;font-size:13px">Deck not found.</div>
{/if}

<style>
    .mb-label { font-size: 10px; color: #3d3b52; font-weight: 600; letter-spacing: 0.05em; margin-bottom: 2px; }

    .action-btn {
        background: transparent; border: 1px solid #2c293d; border-radius: 6px;
        color: #9b96b0; font-family: inherit; font-size: 12px;
        cursor: pointer; transition: all 0.15s;
    }
    .action-btn:hover { border-color: #a47efd; }

    .del-btn {
        background: transparent; border: 1px solid #2c293d; border-radius: 6px;
        color: #5a5672; font-family: inherit; font-size: 12px;
        cursor: pointer; transition: all 0.15s;
    }
    .del-btn:hover { border-color: #f87171; color: #f87171; background: rgba(248,113,113,0.06); }
</style>
