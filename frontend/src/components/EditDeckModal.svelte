<script lang="ts">
    import { onMount } from 'svelte';
    import { appState } from '../state.svelte';
    import type { Deck } from '../types';

    let { deck }: { deck: Deck } = $props();

    let name = $state(deck.name);
    let brandId = $derived(deck.brandId);
    let selectedModelIds = $state<string[]>([...deck.modelIds]);
    let selectedRegionIds = $state<string[]>([...deck.regionIds]);
    let selectedPromptIds = $state<string[]>([...deck.promptIds]);
    let frequency = $state(deck.frequency);
    let toExecute = $state(deck.toExecute);
    let loading = $state(false);

    const filteredPrompts = $derived(appState.allPrompts.filter(p => p.brandId === brandId));
    const totalMins = $derived(frequency * appState.cronInterval);

    function toggleSelection(list: string[], id: string) {
        const idx = list.indexOf(id);
        if (idx === -1) list.push(id);
        else list.splice(idx, 1);
        return list;
    }

    function formatTime(totalMins: number) {
        if (totalMins === 0) return 'Immediate';
        const minsPerDay = 1440;
        const minsPerWeek = 10080;
        const minsPerMonth = 43200;

        if (totalMins < 60) return `${totalMins}m`;
        if (totalMins < minsPerDay) {
            const h = Math.floor(totalMins / 60);
            const m = totalMins % 60;
            return m > 0 ? `${h}h ${m}m` : `${h}h`;
        }
        if (totalMins < minsPerDay * 7) {
            const d = Math.floor(totalMins / minsPerDay);
            const h = Math.floor((totalMins % minsPerDay) / 60);
            return h > 0 ? `${d}d ${h}h` : `${d}d`;
        }
        const w = Math.floor(totalMins / minsPerWeek);
        return `${w}w`;
    }

    async function handleUpdate() {
        if (!name || selectedModelIds.length === 0 || selectedPromptIds.length === 0) {
            appState.toast('Name, Models, and Prompts are required.');
            return;
        }

        loading = true;
        try {
            const payload = {
                name,
                model_ids: selectedModelIds,
                region_ids: selectedRegionIds,
                prompt_ids: selectedPromptIds,
                frequency,
                to_execute: toExecute
            };

            await appState.updateDeck(deck.id, payload);
            appState.closeEditDeck();
        } catch (e) {
            console.error(e);
        } finally {
            loading = false;
        }
    }
    
    function getBrandName(id: string) {
        return appState.brands.find(b => b.id === id)?.name || 'Unknown Brand';
    }
</script>

<div class="modal-overlay">
    <div class="modal-content deck-modal">
        <div class="modal-header">
            <h3>Edit Deck: {deck.name}</h3>
            <button class="close-x" onclick={() => appState.closeEditDeck()}>&times;</button>
        </div>

        <div class="modal-body scrollable">
            <div class="form-group">
                <label>DECK NAME</label>
                <input bind:value={name} class="modal-input">
            </div>

            <div class="form-group">
                <label>BRAND</label>
                <div class="brand-display">{getBrandName(brandId)}</div>
            </div>

            <div class="grid-2-col">
                <div class="form-group">
                    <label>MODELS (NODES) <span class="count-pill">{selectedModelIds.length}</span></label>
                    <div class="multi-select-box sm-box">
                        {#each appState.models as m}
                            <label class="item-wrap {selectedModelIds.includes(m.id) ? 'on' : ''}">
                                <input type="checkbox" checked={selectedModelIds.includes(m.id)} 
                                       onchange={() => selectedModelIds = toggleSelection(selectedModelIds, m.id)}>
                                <div class="txt">
                                    <div class="nm">{m.modelName}</div>
                                    <div class="sub">{m.provider}</div>
                                </div>
                            </label>
                        {/each}
                    </div>
                </div>

                <div class="form-group">
                    <label>REGIONS (GEO) <span class="count-pill">{selectedRegionIds.length}</span></label>
                    <div class="multi-select-box sm-box">
                        {#each appState.regions as r}
                            <label class="item-wrap {selectedRegionIds.includes(r.id) ? 'on' : ''}">
                                <input type="checkbox" checked={selectedRegionIds.includes(r.id)} 
                                       onchange={() => selectedRegionIds = toggleSelection(selectedRegionIds, r.id)}>
                                <div class="txt">
                                    <div class="nm">{r.name}</div>
                                    <div class="sub">{r.countryCode}</div>
                                </div>
                            </label>
                        {/each}
                    </div>
                </div>
            </div>

            <div class="form-group">
                <label>PROMPT SEQUENCES <span class="count-pill">{selectedPromptIds.length}</span></label>
                <div class="multi-select-box lg-box">
                    {#each filteredPrompts as p}
                        <label class="item-wrap {selectedPromptIds.includes(p.id) ? 'on' : ''}">
                            <input type="checkbox" checked={selectedPromptIds.includes(p.id)} 
                                   onchange={() => selectedPromptIds = toggleSelection(selectedPromptIds, p.id)}>
                            <div class="txt">
                                <div class="nm" style="white-space:normal; -webkit-line-clamp:3; display:-webkit-box; -webkit-box-orient:vertical; overflow:hidden;">{p.content}</div>
                                {#if p.notes}
                                    <div class="sub" style="color:var(--primary-p3)">Note: {p.notes}</div>
                                {/if}
                            </div>
                        </label>
                    {/each}
                </div>
            </div>

            <div class="form-group">
                <label>EXECUTION INTERVAL (SLOTS OF {appState.cronInterval} MIN)</label>
                <div style="display:flex;align-items:center;gap:12px">
                    <input type="number" bind:value={frequency} class="modal-input" style="width: 100px">
                    <div class="time-tip">
                        <span class="l">WAIT:</span>
                        <span class="v">{formatTime(totalMins)}</span>
                    </div>
                </div>
            </div>

            <div class="form-group">
                <label>CURRENT STATUS</label>
                <div style="display:flex;gap:8px">
                    <button class="st-btn {toExecute ? 'up' : ''}" onclick={() => toExecute = true}>Enabled</button>
                    <button class="st-btn {!toExecute ? 'dn' : ''}" onclick={() => toExecute = false}>Disabled</button>
                </div>
            </div>
        </div>

        <div class="modal-footer">
            <button class="cancel-btn" onclick={() => appState.closeEditDeck()}>Discard</button>
            <button class="save-btn" onclick={handleUpdate} disabled={loading}>
                {loading ? 'Saving Changes...' : 'Update Deck'}
            </button>
        </div>
    </div>
</div>

<style>
    .modal-overlay {
        position: fixed; inset: 0; background: rgba(0, 0, 0, 0.85); backdrop-filter: blur(12px);
        display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 20px;
    }
    .modal-content {
        background: #13121a; border: 1px solid rgba(42, 40, 64, 0.8); border-radius: 20px;
        padding: 32px; width: 100%; max-width: 680px; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.8);
        position: relative; max-height: 90vh; display: flex; flex-direction: column;
    }
    .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
    .modal-header h3 { margin: 0; font-family: 'Bebas Neue', sans-serif; font-size: 24px; letter-spacing: 0.05em; color: #e8e6f0; }
    .close-x { background: none; border: none; color: #6b6882; font-size: 24px; cursor: pointer; }
    .modal-body { flex: 1; overflow-y: auto; padding-right: 10px; }
    .scrollable::-webkit-scrollbar { width: 4px; }
    .scrollable::-webkit-scrollbar-thumb { background: #2a2840; border-radius: 10px; }
    .form-group { margin-bottom: 20px; }
    .form-group label { display: flex; justify-content: space-between; align-items: center; font-size: 10px; font-weight: 700; color: #3d3b52; letter-spacing: 0.1em; margin-bottom: 8px; }
    .count-pill { background: #1e1c2a; color: var(--primary-p3); padding: 2px 6px; border-radius: 10px; font-size: 9px; }
    .modal-input {
        width: 100%; background: #0f0e16; border: 1px solid #1e1c2a; border-radius: 8px;
        padding: 12px; color: #e8e6f0; font-size: 14px; outline: none; box-sizing: border-box;
    }
    .brand-display { background: #0f0e16; border: 1px solid #1e1c2a; border-radius: 8px; padding: 12px; color: #5a5672; font-size: 14px; font-weight: 500; }
    .grid-2-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
    .multi-select-box { background: #0f0e16; border: 1px solid #1e1c2a; border-radius: 8px; overflow-y: auto; padding: 6px; }
    .sm-box { height: 160px; }
    .lg-box { height: 280px; }
    .item-wrap { display: flex; align-items: flex-start; gap: 10px; padding: 12px; border-radius: 8px; cursor: pointer; transition: 0.2s; margin-bottom: 4px; border: 1px solid transparent; }
    .item-wrap:hover { background: rgba(255,255,255,0.02); border-color: #1e1c2a; }
    .item-wrap.on { background: rgba(164, 126, 253, 0.04); border-color: rgba(164, 126, 253, 0.2); }
    .item-wrap input { margin: 0; margin-top: 3px; flex-shrink: 0; width: 14px; height: 14px; }
    .txt { flex: 1; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
    .nm { font-size: 13px; color: #e8e6f0; font-weight: 500; overflow: hidden; text-overflow: ellipsis; }
    .sub { font-size: 10px; color: #5a5672; text-transform: uppercase; letter-spacing: 0.05em; }
    .time-tip { display: flex; align-items: center; gap: 8px; background: #171522; padding: 8px 16px; border-radius: 8px; border: 1px solid #1e1c2a; }
    .time-tip .l { font-size: 9px; font-weight: 700; color: #3d3b52; letter-spacing: 0.08em; }
    .time-tip .v { font-size: 13px; font-weight: 600; color: #4ade80; }
    .modal-footer { display: flex; justify-content: flex-end; gap: 15px; margin-top: 25px; padding-top: 20px; border-top: 1px solid #1e1c2a; }
    .cancel-btn { background: transparent; border: none; color: #6b6882; font-weight: 600; cursor: pointer; font-size: 13px; }
    .save-btn { background: var(--primary-p3); color: #fff; border: none; padding: 12px 24px; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 13px; transition: 0.2s; }
    .save-btn:hover { opacity: 0.9; transform: translateY(-1px); }
    .save-btn:disabled { opacity: 0.4; cursor: not-allowed; }
    .st-btn { background: #0f0e16; border: 1px solid #1e1c2a; border-radius: 8px; padding: 8px 16px; color: #5a5672; font-size: 12px; font-weight: 600; cursor: pointer; transition: 0.2s; }
    .st-btn.up { background: rgba(74, 222, 128, 0.1); border-color: #4ade80; color: #4ade80; }
    .st-btn.dn { background: rgba(248, 113, 113, 0.1); border-color: #f87171; color: #f87171; }
</style>
