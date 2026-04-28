<script lang="ts">
    import { appState } from '../state.svelte';
    import Logo from './Logo.svelte';
    
    let email = $state('');
    let pass = $state('');
    let fullName = $state('');
    let isSignUp = $state(false);
    let loading = $state(false);
    let errorMsg = $state('');

    async function handleSubmit() {
        if (!email || !pass || (isSignUp && !fullName)) {
            errorMsg = 'Please fill in all fields';
            return;
        }
        
        loading = true;
        errorMsg = '';
        
        try {
            if (isSignUp) {
                const success = await appState.signup(email, pass, fullName);
                if (success) {
                    isSignUp = false; // Switch to login after successful signup
                }
            } else {
                await appState.login(email, pass);
            }
        } catch (e: any) {
            errorMsg = e.message || 'An error occurred';
        } finally {
            loading = false;
        }
    }

    function toggleMode() {
        isSignUp = !isSignUp;
        errorMsg = '';
    }
</script>

<div id="login-screen">
    <div class="bg-blur"></div>
    <div class="login-card">
        <div class="login-logo" style="flex-direction: column; align-items: flex-start; gap: 0">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 2px">
                <Logo size={28} />
                <span style="font-size:32px;font-weight:400;color:#e8e6f0;font-family: 'Bebas Neue', sans-serif; letter-spacing: 0.05em; line-height: 1">AVIS</span>
            </div>
            <span style="font-size:10px; color: #6b6882; font-weight: 500; letter-spacing: 0.1em; margin-left: 38px">BY DOPEST.IO</span>
        </div>
        
        <div class="login-title">{isSignUp ? 'Create account' : 'Welcome back'}</div>
        <div class="login-sub">{isSignUp ? 'Join the AIVIS workspace' : 'Sign in to your workspace'}</div>
        
        {#if isSignUp}
            <div style="margin-bottom:12px">
                <div class="field-label">FULL NAME</div>
                <input bind:value={fullName} class="login-input" type="text" placeholder="John Doe">
            </div>
        {/if}
        
        <div style="margin-bottom:12px">
            <div class="field-label">EMAIL</div>
            <input bind:value={email} class="login-input" type="email" placeholder="example@dopest.io">
        </div>
        
        <div style="margin-bottom:12px">
            <div class="field-label">PASSWORD</div>
            <input bind:value={pass} class="login-input" type="password" placeholder="••••••••" onkeydown={(e) => e.key === 'Enter' && handleSubmit()}>
        </div>
        
        {#if errorMsg}
            <div class="login-err" style="display: block; margin-bottom: 12px">{errorMsg}</div>
        {/if}
        
        <button class="login-btn" onclick={handleSubmit} disabled={loading}>
            {#if loading}
                <span class="loading-spinner"></span>
            {:else}
                {isSignUp ? 'Sign Up' : 'Sign In'}
            {/if}
        </button>
        
        <div style="text-align:center;margin-top:18px;font-size:13px;color:#8b88a1">
            {isSignUp ? 'Already have an account?' : "Don't have an account?"}
            <button class="text-btn" onclick={toggleMode} style="color: #6366f1; font-weight: 600; background: none; border: none; padding: 0; cursor: pointer; margin-left: 4px">
                {isSignUp ? 'Sign in' : 'Create one'}
            </button>
        </div>
    </div>
</div>

<style>
    #login-screen {
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
            radial-gradient(circle at 20% 20%, rgba(164, 126, 253, 0.15) 0%, transparent 40%),
            radial-gradient(circle at 80% 80%, rgba(2, 201, 205, 0.15) 0%, transparent 40%),
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
        max-width: 380px;
        /* Center content internally as well */
        display: flex;
        flex-direction: column;
    }
    .text-btn:hover {
        text-decoration: underline;
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
</style>
