<script lang="ts">
    import { appState } from '../state.svelte';

    interface Props { promptId: string; }
    let { promptId }: Props = $props();

    const prompt    = $derived(appState.allPrompts.find(p => p.id === promptId));
    const instances = $derived(appState.instances.filter(i => i.promptId === promptId));

    function getBrandName(brandId: string) {
        return appState.brands.find(b => b.id === brandId)?.name || 'Unknown';
    }

    // Edit mode
    let editing     = $state(false);
    let editContent = $state('');
    let editNotes   = $state('');
    let saving      = $state(false);

    function startEdit() {
        if (!prompt) return;
        editContent = prompt.content;
        editNotes   = prompt.notes ?? '';
        editing     = true;
    }

    function cancelEdit() { editing = false; }

    async function saveEdit() {
        if (!prompt || !editContent.trim()) return;
        saving = true;
        await appState.updatePrompt(prompt.id, {
            content: editContent.trim(),
            notes:   editNotes.trim() || undefined
        });
        saving  = false;
        editing = false;
    }

    async function handleDelete() {
        if (!prompt) return;
        const ok = await appState.confirm('Delete Prompt', 'Delete this prompt? This cannot be undone.');
        if (!ok) return;
        await appState.deletePrompt(prompt.id);
        appState.closeTab(promptId);
    }
</script>

{#if prompt}
    <!-- Header -->
    <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:1.5rem">
        <div>
            <div style="font-family:'Bebas Neue',sans-serif;font-size:24px;color:#e8e6f0;letter-spacing:0.05em">
                {prompt.content.slice(0, 40)}{prompt.content.length > 40 ? '…' : ''}
            </div>
            <div style="font-size:11px;color:#3d3b52;margin-top:4px">
                Created {prompt.createdAt ? new Date(prompt.createdAt).toLocaleDateString() : '—'}
            </div>
        </div>
        <div style="display:flex;gap:8px">
            {#if !editing}
                <button class="action-btn" onclick={startEdit}>Edit</button>
                <button class="del-btn" onclick={handleDelete}>Delete</button>
            {:else}
                <button class="cancel-btn" onclick={cancelEdit}>Cancel</button>
                <button class="save-btn" onclick={saveEdit} disabled={saving || !editContent.trim()}>
                    {saving ? 'Saving…' : 'Save'}
                </button>
            {/if}
        </div>
    </div>

    <!-- Content card -->
    <div class="card" style="margin-bottom:2rem;cursor:default;background:#050505">
        <div class="mb-label">CONTENT</div>
        {#if editing}
            <textarea
                class="edit-area"
                bind:value={editContent}
                rows="8"
            ></textarea>
            <div style="margin-top:12px">
                <div class="mb-label" style="margin-bottom:6px">NOTES</div>
                <input class="edit-input" type="text" bind:value={editNotes} placeholder="Internal notes…">
            </div>
            <div style="font-size:10px;color:#3d3a52;margin-top:6px;text-align:right">{editContent.length} chars</div>
        {:else}
            <div style="font-size:14px;color:#e8e6f0;line-height:1.6;margin-top:10px;white-space:pre-wrap">{prompt.content}</div>
            {#if prompt.notes}
                <div style="margin-top:12px;padding-top:12px;border-top:1px solid #1e1c29;font-size:12px;color:#5a5672;font-style:italic">{prompt.notes}</div>
            {/if}
        {/if}
    </div>

    <!-- Instances -->
    <div class="sec-title" style="margin-bottom:20px">Instances of this prompt ({instances.length})</div>
    <div class="grid2">
        {#each instances as i (i.id)}
            <div class="card"
                onclick={() => appState.openTab(i.id, 'instance', 'Instance: ' + i.id.slice(0, 8))}
                onkeydown={(e) => e.key === 'Enter' && appState.openTab(i.id, 'instance', 'Instance: ' + i.id.slice(0, 8))}
                role="button" tabindex="0"
            >
                <div class="card-top">
                    <div>
                        <div class="card-name" style="font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--primary-p2)">{i.id}</div>
                        <div class="card-id">{i.deckName}</div>
                    </div>
                    <div style="font-size:10px;color:#3d3b52;font-weight:500">HISTORY</div>
                </div>
                <div class="mrow">
                    <span class="mi"><span class="ml">Model </span>{i.modelName}</span>
                    <span class="mi"><span class="ml">Region </span>{i.regionName}</span>
                    <span class="mi"><span class="ml">Latency </span>{i.metrics?.latency ?? '—'}s</span>
                </div>
                <div class="card-foot">
                    <span class="ts">Started {i.initiatedAt}</span>
                </div>
            </div>
        {/each}

        {#if instances.length === 0}
            <div style="grid-column:1/-1;text-align:center;padding:2rem;color:#3d3b52">No instances for this prompt yet.</div>
        {/if}
    </div>
{:else}
    <div style="text-align:center;padding:2rem;color:#3d3b52">Prompt not found.</div>
{/if}

<style>
    .mb-label { font-size:10px; color:#3d3b52; font-weight:600; letter-spacing:0.05em; }

    .action-btn {
        background: transparent; border: 1px solid #2c293d; border-radius: 8px;
        padding: 7px 16px; color: #9b96b0; font-family: inherit; font-size: 12px;
        cursor: pointer; transition: all 0.15s;
    }
    .action-btn:hover { border-color: #a47efd; color: #a47efd; }

    .del-btn {
        background: transparent; border: 1px solid #2c293d; border-radius: 8px;
        padding: 7px 16px; color: #5a5672; font-family: inherit; font-size: 12px;
        cursor: pointer; transition: all 0.15s;
    }
    .del-btn:hover { border-color: #f87171; color: #f87171; background: rgba(248,113,113,0.06); }

    .cancel-btn {
        background: transparent; border: 1px solid #2c293d; border-radius: 8px;
        padding: 7px 16px; color: #5a5672; font-family: inherit; font-size: 12px; cursor: pointer;
    }
    .save-btn {
        background: linear-gradient(135deg, #7c5cfc, #a47efd); border: none;
        border-radius: 8px; padding: 7px 18px; color: #fff;
        font-family: inherit; font-size: 12px; cursor: pointer; transition: opacity 0.2s;
    }
    .save-btn:hover { opacity: 0.85; }
    .save-btn:disabled { opacity: 0.4; cursor: not-allowed; }

    .edit-area {
        width: 100%; background: #0a0912; border: 1px solid #2c293d; border-radius: 8px;
        padding: 12px; color: #e8e6f0; font-family: inherit; font-size: 14px;
        line-height: 1.6; resize: vertical; outline: none; margin-top: 10px; box-sizing: border-box;
    }
    .edit-area:focus { border-color: #a47efd; }

    .edit-input {
        width: 100%; background: #0a0912; border: 1px solid #2c293d; border-radius: 8px;
        padding: 10px 12px; color: #c8c3d8; font-family: inherit; font-size: 13px;
        outline: none; box-sizing: border-box;
    }
    .edit-input:focus { border-color: #a47efd; }
</style>
