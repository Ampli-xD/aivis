<script lang="ts">
    import { appState } from '../state.svelte';
    let quickMenuOpen = $state(false);
    let draggingIndex = $state<number | null>(null);

    function toggleQuickMenu() { quickMenuOpen = !quickMenuOpen; }
    function closeQuickMenu() { quickMenuOpen = false; }

    function onDragStart(index: number) {
        draggingIndex = index;
    }

    function onDragOver(e: DragEvent, index: number) {
        e.preventDefault();
        if (draggingIndex === null || draggingIndex === index) return;
        
        appState.moveTab(draggingIndex, index);
        draggingIndex = index;
    }

    function onDragEnd() {
        draggingIndex = null;
    }
</script>

<div class="tabbar-wrap" style="position:relative">
    <div class="tabbar">
        {#each appState.openTabs as t, i (t.id)}
            <div 
                class="tab-item {appState.activeTabId === t.id ? 'active' : ''} {draggingIndex === i ? 'dragging' : ''}" 
                draggable="true"
                ondragstart={() => onDragStart(i)}
                ondragover={(e) => onDragOver(e, i)}
                ondragend={onDragEnd}
                onclick={() => appState.activeTabId = t.id}
                onkeydown={(e) => e.key === 'Enter' && (appState.activeTabId = t.id)}
                role="button"
                tabindex="0"
            >
                {#if t.type === 'pinned'}
                    <svg width="12" height="12" fill="none" viewBox="0 0 16 16">
                        <rect x="2" y="2" width="5" height="5" rx="1" fill="currentColor" opacity=".7"/>
                        <rect x="9" y="2" width="5" height="5" rx="1" fill="currentColor" opacity=".7"/>
                        <rect x="2" y="9" width="5" height="5" rx="1" fill="currentColor" opacity=".7"/>
                        <rect x="9" y="9" width="5" height="5" rx="1" fill="currentColor" opacity=".4"/>
                    </svg>
                    <span>{t.label}</span>
                {:else}
                    {@const dotClass = t.type === 'prompts' ? 'prompts' : (t.type === 'settings' || t.type === 'profile' ? 'settings' : (t.type === 'instances' ? 'instances' : (t.type === 'analytics' ? 'analytics' : (t.type === 'prompt' ? 'prompt' : 'deck'))))}
                    <span class="tab-dot {dotClass}"></span>
                    <span>{t.label}</span>
                    <button class="tab-close" onclick={(e) => { e.stopPropagation(); appState.closeTab(t.id); }}>×</button>
                {/if}
            </div>
        {/each}
    </div>
    <button class="tab-add" onclick={toggleQuickMenu} title="Open new tab">+</button>
    <div class="tab-count">{appState.openTabs.length}/10</div>

    {#if quickMenuOpen}
        <div id="quick-menu" style="display:block">
            <div class="qm-section">OPEN</div>
            <div class="qm-item" onclick={() => { appState.openTab('decks', 'deck', 'Decks'); closeQuickMenu(); }}>Decks</div>
            <div class="qm-item" onclick={() => { appState.openTab('all-prompts', 'prompts', 'All prompts'); closeQuickMenu(); }}>All prompts</div>
            <div class="qm-item" onclick={() => { appState.openTab('instances', 'instances', 'Instances'); closeQuickMenu(); }}>Instances</div>
            <div class="qm-item" onclick={() => { appState.openTab('analytics', 'analytics', 'Analytics'); closeQuickMenu(); }}>Analytics</div>
            <div class="qm-item" onclick={() => { appState.openTab('settings', 'settings', 'Settings'); closeQuickMenu(); }}>Settings</div>
            <div class="qm-section" style="margin-top:2px">DECK DETAIL</div>
            {#each appState.decks.filter(d => d.brandId === appState.activeBrandId) as d (d.id)}
                <div class="qm-item" onclick={() => { appState.openTab(d.id, 'deck', d.name); closeQuickMenu(); }}>{d.name}</div>
            {/each}
        </div>
    {/if}
</div>

<style>
    .tab-item.dragging {
        opacity: 0.5;
        background: rgba(164, 126, 253, 0.1);
        border: 1px dashed var(--primary-p1);
    }
    
    .tab-item {
        user-select: none;
        cursor: grab;
    }
    
    .tab-item:active {
        cursor: grabbing;
    }

    .tab-dot.prompt {
        background: var(--primary-p2);
    }
</style>
