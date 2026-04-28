<script lang="ts">
    import { appState } from '../state.svelte';
    import Logo from './Logo.svelte';

    let name = $state('');
    let domain = $state('');
    let industry = $state('');
    let description = $state('');
    let loading = $state(false);
    let errorMsg = $state('');

    async function handleCreateBrand() {
        if (!name || !industry || !domain) {
            errorMsg = 'Name, Industry, and Domain are required';
            return;
        }

        loading = true;
        errorMsg = '';

        try {
            await appState.createBrand({
                name,
                domain,
                industry,
                description
            });
        } catch (e: any) {
            errorMsg = e.message || 'Failed to create brand';
        } finally {
            loading = false;
        }
    }
</script>

<div id="onboarding-screen">
    <div class="bg-blur"></div>
    <div class="login-card">
        <div class="login-logo" style="flex-direction: column; align-items: flex-start; gap: 0">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 2px">
                <Logo size={28} />
                <span style="font-size:32px;font-weight:400;color:#e8e6f0;font-family: 'Bebas Neue', sans-serif; letter-spacing: 0.05em; line-height: 1">AVIS</span>
            </div>
            <span style="font-size:10px; color: #6b6882; font-weight: 500; letter-spacing: 0.1em; margin-left: 38px">BY DOPEST.IO</span>
        </div>
        
        <div class="login-title">Set up your brand</div>
        <div class="login-sub">Tell us about the intelligence you're building</div>
        
        <div style="margin-bottom:12px">
            <div class="field-label">BRAND NAME</div>
            <input bind:value={name} class="login-input" type="text" placeholder="e.g. Acme Corp">
        </div>
        
        <div style="margin-bottom:12px">
            <div class="field-label">INDUSTRY</div>
            <input bind:value={industry} class="login-input" type="text" placeholder="e.g. SaaS, eCommerce">
        </div>

        <div style="margin-bottom:12px">
            <div class="field-label">DOMAIN</div>
            <input bind:value={domain} class="login-input" type="text" placeholder="e.g. acme.com">
        </div>

        <div style="margin-bottom:16px">
            <div class="field-label">DESCRIPTION (OPTIONAL)</div>
            <textarea bind:value={description} class="login-input" placeholder="Briefly describe your brand's mission" rows="2" style="resize: none;"></textarea>
        </div>
        
        {#if errorMsg}
            <div class="login-err" style="display: block; margin-bottom: 12px">{errorMsg}</div>
        {/if}
        
        <button class="login-btn" onclick={handleCreateBrand} disabled={loading}>
            {#if loading}
                <span class="loading-spinner"></span>
            {:else}
                Launch Brand
            {/if}
        </button>

        <div style="text-align:center;margin-top:18px;font-size:11px;color:#3d3b52">
            You can add more brands later in settings
            <div style="margin-top: 12px;">
                <button onclick={() => appState.logout()} class="switch-account-btn">Switch Account</button>
            </div>
        </div>
    </div>
</div>

<style>
    #onboarding-screen {
        position: fixed;
        inset: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        background: #000;
        z-index: 50;
        padding: 1.5rem;
    }
    .bg-blur {
        position: absolute;
        top: -10%;
        left: -10%;
        width: 120%;
        height: 120%;
        background: 
            radial-gradient(circle at 80% 20%, rgba(164, 126, 253, 0.15) 0%, transparent 40%),
            radial-gradient(circle at 20% 80%, rgba(2, 201, 205, 0.15) 0%, transparent 40%),
            radial-gradient(circle at 50% 50%, rgba(50, 79, 198, 0.1) 0%, transparent 50%);
        filter: blur(80px);
        z-index: 1;
        animation: pulse 15s ease-in-out infinite alternate;
    }
    @keyframes pulse {
        0% { transform: scale(1) rotate(0deg); }
        100% { transform: scale(1.1) rotate(5deg); }
    }
    .login-card {
        position: relative;
        z-index: 2;
        backdrop-filter: blur(16px);
        background: rgba(19, 18, 26, 0.85);
        border: 1px solid rgba(42, 40, 64, 0.6);
        border-radius: 16px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        padding: 2.5rem 2rem;
        width: 100%;
        max-width: 400px;
        display: flex;
        flex-direction: column;
    }
    textarea.login-input {
        line-height: 1.5;
    }
    .loading-spinner {
        display: inline-block;
        width: 16px;
        height: 16px;
        border: 2px solid rgba(255,255,255,0.3);
        border-radius: 50%;
        border-top-color: #fff;
        animation: spin 0.8s linear infinite;
    }
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    .login-btn:disabled {
        opacity: 0.7;
        cursor: not-allowed;
    }
    .switch-account-btn {
        background: none;
        border: none;
        color: #a47efd;
        font-size: 11px;
        cursor: pointer;
        text-decoration: none;
        font-family: inherit;
        transition: color 0.2s;
    }
    .switch-account-btn:hover {
        color: #c8adff;
        text-decoration: underline;
    }
</style>
