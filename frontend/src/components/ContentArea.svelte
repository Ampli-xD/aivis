<script lang="ts">
    import { appState } from '../state.svelte';
    import HomeView from './HomeView.svelte';
    import DecksView from './DecksView.svelte';
    import PromptsView from './PromptsView.svelte';
    import SettingsView from './SettingsView.svelte';
    import ProfileView from './ProfileView.svelte';
    import DeckDetailView from './DeckDetailView.svelte';
    import InstancesView from './InstancesView.svelte';
    import PromptDetailView from './PromptDetailView.svelte';
    import InstanceDetailView from './InstanceDetailView.svelte';
    import AnalyticsView from './AnalyticsView.svelte';

    // This acts as a simple router based on activeTabId
</script>

<div class="content-area">
    <div class="panel {appState.activeTabId === 'home' ? 'active' : ''}">
        <HomeView />
    </div>

    {#if appState.openTabs.find(t => t.id === 'decks')}
        <div class="panel {appState.activeTabId === 'decks' ? 'active' : ''}">
            <DecksView />
        </div>
    {/if}

    {#if appState.openTabs.find(t => t.id === 'all-prompts')}
        <div class="panel {appState.activeTabId === 'all-prompts' ? 'active' : ''}">
            <PromptsView />
        </div>
    {/if}

    {#if appState.openTabs.find(t => t.id === 'instances')}
        <div class="panel {appState.activeTabId === 'instances' ? 'active' : ''}">
            <InstancesView />
        </div>
    {/if}

    {#if appState.openTabs.find(t => t.id === 'settings')}
        <div class="panel {appState.activeTabId === 'settings' ? 'active' : ''}">
            <SettingsView />
        </div>
    {/if}

    {#if appState.openTabs.find(t => t.id === 'analytics')}
        <div class="panel {appState.activeTabId === 'analytics' ? 'active' : ''}">
            <AnalyticsView />
        </div>
    {/if}

    {#if appState.openTabs.find(t => t.id === 'profile')}
        <div class="panel {appState.activeTabId === 'profile' ? 'active' : ''}">
            <ProfileView />
        </div>
    {/if}

    {#each appState.openTabs.filter(t => t.type === 'deck') as t (t.id)}
        {#if !['decks'].includes(t.id)}
            <div class="panel {appState.activeTabId === t.id ? 'active' : ''}">
                <DeckDetailView deckId={t.id} />
            </div>
        {/if}
    {/each}

    {#each appState.openTabs.filter(t => t.type === 'prompt') as t (t.id)}
        <div class="panel {appState.activeTabId === t.id ? 'active' : ''}">
            <PromptDetailView promptId={t.id} />
        </div>
    {/each}

    {#each appState.openTabs.filter(t => t.type === 'instance') as t (t.id)}
        <div class="panel {appState.activeTabId === t.id ? 'active' : ''}">
            <InstanceDetailView instanceId={t.id} />
        </div>
    {/each}
</div>

<style>
    .panel {
        display: none;
    }
    .panel.active {
        display: block;
    }
</style>
