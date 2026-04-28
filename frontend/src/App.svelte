<script lang="ts">
    import { appState } from './state.svelte';
    import Login from './components/Login.svelte';
    import BrandOnboarding from './components/BrandOnboarding.svelte';
    import Topbar from './components/Topbar.svelte';
    import TabBar from './components/TabBar.svelte';
    import ContentArea from './components/ContentArea.svelte';
    import CreateDeckModal from './components/CreateDeckModal.svelte';
    import EditDeckModal from './components/EditDeckModal.svelte';
    import AdminConsole from './components/AdminConsole.svelte';
    import ConfirmModal from './components/ConfirmModal.svelte';

    // --- Admin Console (Ctrl+Shift+A) ---
    // Completely isolated — does not touch appState
    let showAdmin = $state(false);

    function onKeyDown(e: KeyboardEvent) {
        if (e.ctrlKey && e.shiftKey && e.key === 'A') {
            e.preventDefault();
            showAdmin = !showAdmin;
        }
    }
</script>

<svelte:window onkeydown={onKeyDown} />

{#if !appState.isLoggedIn}
    <Login />
{:else if appState.isInitialLoading}
    <div id="loading-screen">
        <div class="loader-content">
            <div class="spinner"></div>
            <div class="loading-text">Synchronizing Global Hub...</div>
        </div>
    </div>
{:else if appState.brands.length === 0}
    <BrandOnboarding />
{:else}
    <div id="app" style="display: flex; flex-direction: column; height: 100vh; overflow: hidden; position: relative">
        <Topbar />
        <TabBar />
        <ContentArea />
        {#if appState.showCreateDeckModal}
            <CreateDeckModal />
        {/if}
        {#if appState.editingDeck}
            <EditDeckModal deck={appState.editingDeck} />
        {/if}
    </div>
{/if}

<div id="toast" class={appState.showToast ? 'show' : ''}>{appState.toastMsg}</div>

{#if showAdmin}
    <AdminConsole on:close={() => showAdmin = false} />
{/if}

<ConfirmModal />

<style>
    #loading-screen {
        position: fixed;
        inset: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: #000;
        z-index: 100;
    }
    .loader-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 20px;
    }
    .spinner {
        width: 32px;
        height: 32px;
        border: 2px solid rgba(164, 126, 253, 0.2);
        border-radius: 50%;
        border-top-color: var(--primary-p3);
        animation: spin 0.8s linear infinite;
    }
    .loading-text {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        color: #6b6882;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
</style>
