<script lang="ts">
    import { appState } from '../state.svelte';

    let searchQuery = $state('');
    let showCreate  = $state(false);

    // Create form
    let newContent  = $state('');
    let newNotes    = $state('');
    let newBrandId  = $state('');
    let saving      = $state(false);

    const filteredPrompts = $derived(
        appState.allPrompts.filter(p => 
            p.brandId === appState.activeBrandId && (
                p.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
                (p.notes ?? '').toLowerCase().includes(searchQuery.toLowerCase())
            )
        )
    );

    function getBrandName(brandId: string) {
        return appState.brands.find(b => b.id === brandId)?.name || 'Unknown Brand';
    }

    function openCreate() {
        if (!appState.activeBrandId) {
            appState.toast('Please select a brand first.');
            return;
        }
        newContent = '';
        newNotes   = '';
        newBrandId = appState.activeBrandId;
        showCreate = true;
    }

    async function submitCreate() {
        if (!newContent.trim() || !newBrandId) return;
        saving = true;
        await appState.createPrompt(newBrandId, { content: newContent.trim(), notes: newNotes.trim() || undefined });
        saving = false;
        showCreate = false;
    }

    async function handleDelete(e: MouseEvent, promptId: string) {
        e.stopPropagation();
        const ok = await appState.confirm('Delete Prompt', 'Delete this prompt? This cannot be undone.');
        if (!ok) return;
        await appState.deletePrompt(promptId);
    }

    // Dynamic avg length
    const avgLength = $derived(
        appState.allPrompts.length
            ? Math.round(appState.allPrompts.reduce((s, p) => s + p.content.length, 0) / appState.allPrompts.length)
            : 0
    );

    const todayCount = $derived(
        appState.allPrompts.filter(p => {
            try { return new Date(p.createdAt).toDateString() === new Date().toDateString(); } catch { return false; }
        }).length
    );
</script>

<!-- Stats bar -->
<div class="stats-grid">
    <div class="stat-card"><div class="stat-label">TOTAL PROMPTS</div><div class="stat-val">{appState.allPrompts.length}</div></div>
    <div class="stat-card"><div class="stat-label">BRANDS</div><div class="stat-val">{appState.brands.length}</div></div>
    <div class="stat-card"><div class="stat-label">CREATED TODAY</div><div class="stat-val p1">{todayCount}</div></div>
    <div class="stat-card"><div class="stat-label">AVG LENGTH</div><div class="stat-val">{avgLength} chars</div></div>
</div>

<!-- Toolbar -->
<div class="toolbar">
    <div style="display:flex;align-items:center;gap:8px">
        <span class="sec-title">All prompts</span>
    </div>
    <div style="display:flex;align-items:center;gap:8px">
        <input class="srch" placeholder="Search content…" bind:value={searchQuery}>
        <button class="new-btn" onclick={openCreate}>+ New Prompt</button>
    </div>
</div>

<!-- Prompt cards -->
<div class="grid2">
    {#each filteredPrompts as p (p.id)}
        <div class="card"
            onclick={() => appState.openTab(p.id, 'prompt', 'Prompt: ' + p.content.slice(0, 20))}
            onkeydown={(e) => e.key === 'Enter' && appState.openTab(p.id, 'prompt', 'Prompt: ' + p.content.slice(0, 20))}
            role="button" tabindex="0"
        >
            <div class="card-top">
                <div>
                    <div class="card-id" style="font-size:10px;color:#3d3b52">{p.createdAt ? new Date(p.createdAt).toLocaleDateString() : '—'}</div>
                </div>
                <div style="display:flex;align-items:center;gap:6px">
                    <span class="pill a">ready</span>
                    <button class="del-btn" title="Delete prompt"
                        onclick={(e) => handleDelete(e, p.id)}
                        onkeydown={(e) => e.key === 'Enter' && handleDelete(e as any, p.id)}
                    >✕</button>
                </div>
            </div>
            <div class="divl"></div>
            <div class="prev" style="-webkit-line-clamp:5;font-size:15px;color:#e8e6f0;margin:14px 0;line-height:1.6;font-weight:500">
                {p.content}
            </div>
            {#if p.notes}
                <div style="font-size:10px;color:#3d3b52;margin-bottom:8px;font-style:italic;opacity:0.7">{p.notes}</div>
            {/if}
            <div class="card-foot">
                <div class="tags"><span class="tag">system</span></div>
                <span class="ts">{p.id.slice(0, 8)}…</span>
            </div>
        </div>
    {/each}

    {#if filteredPrompts.length === 0}
        <div style="grid-column:1/-1;text-align:center;padding:3rem;color:#3d3b52">
            {searchQuery ? 'No prompts match your search.' : 'No prompts yet — create your first one.'}
        </div>
    {/if}
</div>

<!-- Create modal -->
{#if showCreate}
    <!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
    <div class="modal-overlay" onclick={(e) => { if (e.target === e.currentTarget) showCreate = false; }}>
        <div class="modal">
            <div class="modal-header">
                <span>New Prompt</span>
                <button class="close-btn" onclick={() => showCreate = false}>✕</button>
            </div>

            <div class="field">
                <label for="promptBrand">Brand</label>
                <div id="promptBrand" class="brand-display">{getBrandName(appState.activeBrandId || '')}</div>
            </div>

            <div class="field">
                <label for="promptContent">Content <span class="req">*</span></label>
                <textarea
                    id="promptContent"
                    bind:value={newContent}
                    placeholder="Enter your prompt content…"
                    rows="6"
                ></textarea>
                <div class="char-count">{newContent.length} chars</div>
            </div>

            <div class="field">
                <label for="promptNotes">Notes <span class="opt">(optional)</span></label>
                <input id="promptNotes" type="text" bind:value={newNotes} placeholder="Internal notes about this prompt…">
            </div>

            <div class="modal-footer">
                <button class="cancel-btn" onclick={() => showCreate = false}>Cancel</button>
                <button class="save-btn" onclick={submitCreate} disabled={saving || !newContent.trim()}>
                    {saving ? 'Saving…' : 'Create Prompt'}
                </button>
            </div>
        </div>
    </div>
{/if}

<style>
    .p1 { color: var(--primary-p1); }

    .del-btn {
        background: transparent;
        border: 1px solid transparent;
        color: #3d3b52;
        font-size: 11px;
        cursor: pointer;
        padding: 2px 6px;
        border-radius: 4px;
        line-height: 1;
        transition: all 0.15s;
    }
    .del-btn:hover { border-color: #f87171; color: #f87171; background: rgba(248,113,113,0.08); }

    /* Modal */
    .modal-overlay {
        position: fixed; inset: 0;
        background: rgba(0,0,0,0.6);
        backdrop-filter: blur(6px);
        z-index: 1000;
        display: flex; align-items: center; justify-content: center;
    }
    .modal {
        background: #0f0e16;
        border: 1px solid #1e1c29;
        border-radius: 12px;
        padding: 24px;
        width: min(540px, 92vw);
        display: flex; flex-direction: column; gap: 16px;
        box-shadow: 0 24px 60px rgba(0,0,0,0.6);
    }
    .modal-header {
        display: flex; justify-content: space-between; align-items: center;
        font-family: 'Bebas Neue', sans-serif;
        font-size: 20px; color: #e8e6f0; letter-spacing: 0.05em;
    }
    .close-btn {
        background: transparent; border: none; color: #3d3b52;
        font-size: 14px; cursor: pointer; padding: 4px 8px;
        border-radius: 4px; transition: color 0.15s;
    }
    .close-btn:hover { color: #c8c3d8; }

    .field { display: flex; flex-direction: column; gap: 6px; }
    .field label { font-size: 11px; color: #5a5672; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; }
    .req { color: #f87171; }
    .opt { color: #3d3a52; font-weight: 400; text-transform: none; }

    .field input, .field textarea {
        background: #171522; border: 1px solid #2c293d;
        border-radius: 8px; padding: 10px 12px;
        color: #c8c3d8; font-family: inherit; font-size: 13px;
        outline: none; resize: vertical;
    }
    .field input:focus, .field textarea:focus {
        border-color: #a47efd; box-shadow: 0 0 0 3px rgba(164,126,253,0.1);
    }

    .brand-display {
        background: #171522; border: 1px solid #2c293d;
        border-radius: 8px; padding: 10px 12px;
        color: #5a5672; font-size: 13px; font-weight: 500;
        cursor: not-allowed;
    }
    .char-count { font-size: 10px; color: #3d3a52; text-align: right; margin-top: 2px; }

    .modal-footer { display: flex; justify-content: flex-end; gap: 8px; margin-top: 4px; }
    .cancel-btn {
        background: transparent; border: 1px solid #2c293d; border-radius: 8px;
        padding: 9px 18px; color: #5a5672; font-family: inherit; font-size: 13px;
        cursor: pointer; transition: all 0.15s;
    }
    .cancel-btn:hover { border-color: #5a5672; color: #c8c3d8; }
    .save-btn {
        background: linear-gradient(135deg, #7c5cfc, #a47efd); border: none;
        border-radius: 8px; padding: 9px 20px; color: #fff;
        font-family: inherit; font-size: 13px; cursor: pointer; transition: opacity 0.2s;
    }
    .save-btn:hover { opacity: 0.85; }
    .save-btn:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
