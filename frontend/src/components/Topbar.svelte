<script lang="ts">
    import { appState } from '../state.svelte';
    import Logo from './Logo.svelte';
    let dropdownOpen = $state(false);

    function toggleDropdown() { dropdownOpen = !dropdownOpen; }
    function closeDropdown() { dropdownOpen = false; }
    function logout() { appState.logout(); }
    
    function getGreeting() {
        const h = new Date().getHours();
        if (h < 12) return 'Good morning,';
        if (h < 17) return 'Good afternoon,';
        return 'Good evening,';
    }
</script>

<div class="topbar" style="position: relative; display: flex; align-items: center; justify-content: space-between; padding: 0 1.25rem;">
    <!-- Left: Branding -->
    <div style="display: flex; align-items: center; gap: 12px; z-index: 1;">
        <Logo size={26} />
        <span style="font-family: 'Bebas Neue', sans-serif; font-size: 20px; color: #e8e6f0; letter-spacing: 0.05em; margin-left: 2px">AIVIS</span>
        <div class="topbar-divider" style="width: 1px; height: 16px; background: #2a2840; margin: 0 4px"></div>
        <div class="topbar-time mono" style="min-width: 100px; margin-left: 4px; font-size: 12px; color: #6b6882; font-weight: 500">{appState.currentTime}</div>
    </div>

    <!-- Center: Welcome (Absolutely Centered) -->
    <div class="topbar-welcome" style="position: absolute; left: 50%; transform: translateX(-50%); pointer-events: none; white-space: nowrap; display: flex; align-items: center; gap: 15px">
        <div style="opacity: 0.8">{getGreeting()} <span>{appState.user?.fullName}</span></div>
        <button class="top-sync-btn {appState.isInitialLoading ? 'spinning' : ''}" 
                onclick={() => appState.fetchAllData(true)} 
                title="Sync All Hub Data"
                style="pointer-events: auto">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 2v6h-6"/><path d="M3 12a9 9 0 0 1 15-6.7L21 8"/><path d="M3 22v-6h6"/><path d="M21 12a9 9 0 0 1-15 6.7L3 16"/></svg>
            <span>Sync Hub</span>
        </button>
    </div>

    <!-- Right: Brand Badge + Avatar -->
    <div class="topbar-right" style="display: flex; align-items: center; gap: 10px; z-index: 1;">
        {#if appState.activeBrandId}
             {@const activeBrand = appState.brands.find(b => b.id === appState.activeBrandId)}
             <div style="display: flex; align-items: center; gap: 8px; background: rgba(164, 126, 253, 0.08); padding: 4px 10px; border-radius: 6px; border: 1px solid rgba(164, 126, 253, 0.15)">
                <div style="width: 5px; height: 5px; border-radius: 50%; background: var(--primary-p3); box-shadow: 0 0 6px var(--primary-p3)"></div>
                <span style="font-size: 11px; font-weight: 700; color: var(--primary-p1); letter-spacing: 0.05em; text-transform: uppercase">
                    {activeBrand?.name || '...'}
                </span>
             </div>
        {/if}

        <div class="avatar" onclick={toggleDropdown} onkeydown={(e) => e.key === 'Enter' && toggleDropdown()} role="button" tabindex="0">{appState.user?.initials}</div>
        
        {#if dropdownOpen}
            <div class="dropdown open" style="display: block">
                <div class="dropdown-head">
                    <div class="dropdown-name">{appState.user?.fullName}</div>
                    <div class="dropdown-email">{appState.user?.email}</div>
                </div>
                <div class="dropdown-item" onclick={() => { appState.openTab('profile', 'profile', 'Profile'); closeDropdown(); }} onkeydown={(e) => e.key === 'Enter' && (appState.openTab('profile', 'profile', 'Profile') || closeDropdown())} role="button" tabindex="0">
                    <svg width="14" height="14" fill="none" viewBox="0 0 16 16"><circle cx="8" cy="5" r="3" stroke="#a09cc0" stroke-width="1.5"/><path d="M2 13c0-3 2.686-5 6-5s6 2 6 5" stroke="#a09cc0" stroke-width="1.5" stroke-linecap="round"/></svg>
                    Profile
                </div>
                <div class="dropdown-item danger" onclick={logout} onkeydown={(e) => e.key === 'Enter' && logout()} role="button" tabindex="0">
                    <svg width="14" height="14" fill="none" viewBox="0 0 16 16"><path d="M6 3H3v10h3M10 5l3 3-3 3M13 8H6" stroke="#f87171" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
                    Logout
                </div>
            </div>
        {/if}
    </div>
</div>

<style>
    .top-sync-btn {
        background: rgba(164, 126, 253, 0.05);
        border: 1px solid rgba(164, 126, 253, 0.1);
        border-radius: 20px;
        color: #a09cc0;
        padding: 4px 12px;
        font-size: 10px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: flex;
        align-items: center;
        gap: 6px;
        cursor: pointer;
        transition: all 0.2s;
    }
    .top-sync-btn:hover {
        background: rgba(164, 126, 253, 0.12);
        border-color: var(--primary-p3);
        color: #fff;
    }
    .top-sync-btn.spinning svg {
        animation: spin 1s linear infinite;
    }
    @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>
