<script lang="ts">
    import { appState } from '../state.svelte';
    import type { Brand } from '../types';
    
    const user = $derived(appState.user!);
    const brands = $derived(appState.brands);
    const activeBrand = $derived(brands.find(b => b.id === appState.activeBrandId) || null);

    let isEditing = $state(false);
    let isCreating = $state(false);
    let isEditingUser = $state(false);
    let brandForm = $state<Partial<Brand>>({ name: '', industry: '', domain: '', description: '' });
    let userForm = $state({ fullName: '', email: '' });
    let slackForm = $state({ slackId: '' });
    let isEditingSlack = $state(false);
    let isChangingPassword = $state(false);
    let passwordForm = $state({ current: '', new: '', confirm: '' });

    function formatDate(dateStr: string) {
        if (!dateStr) return 'N/A';
        return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
    }

    function handleConnectSlack() {
        slackForm = { slackId: user.slackId || '' };
        isEditingSlack = true;
    }

    async function saveSlackId() {
        if (!slackForm.slackId) {
            appState.toast('Slack ID is required. Use Disconnect if you want to remove it.');
            return;
        }
        await appState.updateUser(user.id, { slackId: slackForm.slackId });
        isEditingSlack = false;
    }

    async function handleLogout() {
        const ok = await appState.confirm('Sign Out', 'Are you sure you want to sign out of AIVIS?');
        if (ok) {
            appState.logout();
        }
    }

    function startEdit(brand: Brand) {
        brandForm = { ...brand };
        isEditing = true;
    }

    function startCreate() {
        brandForm = { name: '', industry: '', domain: '', description: '' };
        isCreating = true;
    }

    async function saveBrand() {
        if (!brandForm.name || !brandForm.industry || !brandForm.domain) {
            appState.toast('Name, Industry and Domain are required');
            return;
        }

        if (isCreating) {
            await appState.createBrand(brandForm);
            isCreating = false;
        } else if (brandForm.id) {
            await appState.updateBrand(brandForm.id, brandForm);
            isEditing = false;
        }
    }

    async function deleteBrand(id: string) {
        const ok = await appState.confirm('Delete Brand', 'Delete this brand permanently? All associated decks and prompts will be lost.');
        if (ok) {
            await appState.deleteBrand(id);
            if (appState.activeBrandId === id) {
                appState.activeBrandId = appState.brands.length > 0 ? appState.brands[0].id : null;
            }
        }
    }

    function startEditUser() {
        userForm = { fullName: user.fullName, email: user.email };
        isEditingUser = true;
    }

    async function saveUser() {
        if (!userForm.fullName || !userForm.email) {
            appState.toast('Name and email are required');
            return;
        }
        await appState.updateUser(user.id, userForm);
        isEditingUser = false;
    }

    function switchBrand(id: string) {
        appState.activeBrandId = id;
        appState.toast(`Switched to ${appState.brands.find(b=>b.id===id)?.name}`);
    }

    function startChangePassword() {
        passwordForm = { current: '', new: '', confirm: '' };
        isChangingPassword = true;
    }

    async function handlePasswordChange() {
        if (!passwordForm.current || !passwordForm.new || !passwordForm.confirm) {
            appState.toast('All fields are required');
            return;
        }
        if (passwordForm.new !== passwordForm.confirm) {
            appState.toast('New passwords do not match');
            return;
        }
        if (passwordForm.new.length < 6) {
            appState.toast('New password must be at least 6 characters');
            return;
        }

        const success = await appState.changePassword(passwordForm.current, passwordForm.new);
        if (success) {
            isChangingPassword = false;
        }
    }
</script>

<div class="profile-layout">
    <div class="sidebar">
        <!-- User Header -->
        <div class="user-header">
            <div class="avatar">{user.initials}</div>
            <div class="user-meta">
                <div class="user-name-row" style="display:flex;align-items:center;gap:8px">
                    <div class="user-name">{user.fullName}</div>
                    <button class="edit-profile-btn" onclick={startEditUser} title="Edit Profile" style="background:none;border:none;color:#6b6882;cursor:pointer;padding:0;display:flex">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                    </button>
                </div>
                <div class="user-email">{user.email}</div>
            </div>
        </div>

        <!-- Account Details -->
        <div class="card section-card">
            <div class="section-tag">ACCOUNT ENTITY</div>
            <div class="detail-row"><span class="label">User ID</span><span class="val mono">{user.id}</span></div>
            <div class="detail-row"><span class="label">Joined</span><span class="val">{formatDate(user.createdAt)}</span></div>
            <div class="detail-row" style="border-bottom:none"><span class="label">Rank</span><span class="val">Workspace Admin</span></div>
        </div>

        <!-- Security -->
        <div class="card section-card">
            <div class="section-tag">SECURITY</div>
            <div class="password-row" style="display:flex;justify-content:space-between;align-items:center">
                <div style="display:flex;align-items:center;gap:8px">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6b6882" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
                    <span style="font-size:12px;color:#a09cc0">Password</span>
                </div>
                <button class="connect-btn mini" onclick={startChangePassword} style="font-size: 9px; padding: 3px 8px; background: rgba(164, 126, 253, 0.1); color: var(--primary-p3); border: 1px solid rgba(164, 126, 253, 0.2)">Update</button>
            </div>
        </div>

        <!-- Slack Integration -->
        <div class="card section-card">
            <div class="section-tag">INTEGRATIONS</div>
            <div class="slack-row">
                <div class="slack-info">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M6 15C6 16.6569 4.65685 18 3 18C1.34315 18 0 16.6569 0 15C0 13.3431 1.34315 12 3 12H6V15Z" fill="#E01E5A"/><path d="M7.5 15C7.5 13.3431 8.84315 12 10.5 12C12.1569 12 13.5 13.3431 13.5 15V21C13.5 22.6569 12.1569 24 10.5 24C8.84315 24 7.5 22.6569 7.5 21V15Z" fill="#E01E5A"/><path d="M9 6C7.34315 6 6 4.65685 6 3C6 1.34315 7.34315 0 9 0C10.6569 0 12 1.34315 12 3V6H9Z" fill="#36C5F0"/><path d="M9 7.5C10.6569 7.5 12 8.84315 12 10.5C12 12.1569 10.6569 13.5 9 13.5H3C1.34315 13.5 0 12.1569 0 10.5C0 8.84315 1.34315 7.5 3 7.5H9Z" fill="#36C5F0"/><path d="M18 9C18 7.34315 19.3431 6 21 6C22.6569 6 24 7.34315 24 9C24 10.6569 22.6569 12 21 12H18V9Z" fill="#2EB67D"/><path d="M16.5 9C16.5 10.6569 15.1569 12 13.5 12C11.8431 12 10.5 10.6569 10.5 9V3C10.5 1.34315 11.8431 0 13.5 0C15.1569 0 16.5 1.34315 16.5 3V9Z" fill="#2EB67D"/><path d="M15 18C16.6569 18 18 19.3431 18 21C18 22.6569 16.6569 24 15 24C13.3431 24 12 22.6569 12 21H15V18Z" fill="#ECB22E"/><path d="M15 16.5C13.3431 16.5 12 15.1569 12 13.5C12 11.8431 13.3431 10.5 15 10.5H21C22.6569 10.5 24 11.8431 24 13.5C24 15.1569 22.6569 16.5 21 16.5H15Z" fill="#ECB22E"/></svg>
                    <span>Slack Service</span>
                </div>
                {#if user.slackId}
                    <div class="slack-status-wrap" style="display:flex;flex-direction:column;align-items:flex-end;gap:4px">
                        <div class="status-linked">SLACK CONNECTED</div>
                        <button class="connect-btn mini" onclick={handleConnectSlack} style="font-size: 9px; padding: 3px 8px; background: rgba(164, 126, 253, 0.1); color: var(--primary-p3); border: 1px solid rgba(164, 126, 253, 0.2)">Connect New ID</button>
                    </div>
                {:else}
                    <button class="connect-btn" onclick={handleConnectSlack}>Connect</button>
                {/if}
            </div>
        </div>

        <button class="logout-btn" onclick={handleLogout}>Sign Out</button>
    </div>

    <div class="main-content">
        <div class="header-row">
            <div class="title-wrap">
                <h2>Manage Brands</h2>
                <div class="sub-h">Switch between or modify your brand identities</div>
            </div>
            <button class="add-brand-btn" onclick={startCreate}>+ New Brand</button>
        </div>

        <div class="brand-grid">
            {#each brands as b (b.id)}
                <div class="brand-item {appState.activeBrandId === b.id ? 'active' : ''}" onclick={() => switchBrand(b.id)} style="cursor:pointer" role="button" tabindex="0" onkeydown={(e) => e.key === 'Enter' && switchBrand(b.id)}>
                    <div class="brand-info">
                        <div class="brand-name-row">
                            <span class="bn">{b.name}</span>
                            {#if appState.activeBrandId === b.id}
                                <span class="active-dot">Current</span>
                            {/if}
                        </div>
                        <div class="brand-sub">{b.industry} • {b.domain}</div>
                    </div>
                    <div 
                        class="brand-actions" 
                        onclick={(e) => e.stopPropagation()}
                        onkeydown={(e) => e.key === 'Enter' && e.stopPropagation()}
                        role="button"
                        tabindex="0"
                    >
                        <button class="icon-btn" title="Edit" onclick={() => startEdit(b)}>
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                        </button>
                        <button class="icon-btn del" title="Delete" onclick={() => deleteBrand(b.id)}>
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
                        </button>
                    </div>
                </div>
            {/each}
        </div>
    </div>
</div>

<!-- Modal Overlays -->
{#if isEditing || isCreating}
    <div class="modal-overlay">
        <div class="modal-content">
            <h3>{isCreating ? 'Create Brand' : 'Edit Brand'}</h3>
            <div class="input-set">
                <div class="f-box">
                    <label for="brandName">NAME</label>
                    <input id="brandName" bind:value={brandForm.name} placeholder="Acme Inc">
                </div>
                <div class="f-box">
                    <label for="brandIndustry">INDUSTRY</label>
                    <input id="brandIndustry" bind:value={brandForm.industry} placeholder="Tech, Marketing...">
                </div>
                <div class="f-box">
                    <label for="brandDomain">DOMAIN</label>
                    <input id="brandDomain" bind:value={brandForm.domain} placeholder="acme.com">
                </div>
                <div class="f-box">
                    <label for="brandDesc">DESCRIPTION (OPTIONAL)</label>
                    <textarea id="brandDesc" bind:value={brandForm.description} placeholder="Brand purpose..." rows="3"></textarea>
                </div>
            </div>
            <div class="modal-foot">
                <button class="cancel-btn" onclick={() => {isEditing = false; isCreating = false;}}>Cancel</button>
                <button class="save-btn" onclick={saveBrand}>{isCreating ? 'Create Brand' : 'Save Changes'}</button>
            </div>
        </div>
    </div>
{/if}

<!-- User Edit Modal -->
{#if isEditingUser}
    <div class="modal-overlay">
        <div class="modal-content">
            <h3>Edit Platform Profile</h3>
            <div class="input-set">
                <div class="f-box">
                    <label for="userFullName">FULL NAME</label>
                    <input id="userFullName" bind:value={userForm.fullName} placeholder="Jane Doe">
                </div>
                <div class="f-box">
                    <label for="userEmail">EMAIL ADDRESS</label>
                    <input id="userEmail" bind:value={userForm.email} placeholder="jane@example.com" type="email">
                </div>
            </div>
            <div class="modal-foot">
                <button class="cancel-btn" onclick={() => isEditingUser = false}>Cancel</button>
                <button class="save-btn" onclick={saveUser}>Save Profile</button>
            </div>
        </div>
    </div>
{/if}

<!-- Slack Edit Modal -->
{#if isEditingSlack}
    <div class="modal-overlay">
        <div class="modal-content">
            <h3>Connect Slack Account</h3>
            <p style="font-size: 12px; color: #6b6882; margin-bottom: 20px;">
                Enter your Slack Member ID (e.g., U12345678) to allow AIVIS to send direct messages to your account.
            </p>
            <div class="input-set">
                <div class="f-box">
                    <label for="slackId">SLACK MEMBER ID</label>
                    <input id="slackId" bind:value={slackForm.slackId} placeholder="UXXXXXXX">
                </div>
            </div>
            <div class="modal-foot">
                <button class="cancel-btn" onclick={() => isEditingSlack = false}>Cancel</button>
                <button class="save-btn" onclick={saveSlackId}>Save Slack ID</button>
            </div>
        </div>
    </div>
{/if}

<!-- Password Change Modal -->
{#if isChangingPassword}
    <div class="modal-overlay">
        <div class="modal-content">
            <h3>Update Login Password</h3>
            <div class="input-set">
                <div class="f-box">
                    <label for="currentPass">CURRENT PASSWORD</label>
                    <input id="currentPass" type="password" bind:value={passwordForm.current} placeholder="••••••••">
                </div>
                <div class="f-box">
                    <label for="newPass">NEW PASSWORD</label>
                    <input id="newPass" type="password" bind:value={passwordForm.new} placeholder="••••••••">
                </div>
                <div class="f-box">
                    <label for="confirmPass">CONFIRM NEW PASSWORD</label>
                    <input id="confirmPass" type="password" bind:value={passwordForm.confirm} placeholder="••••••••">
                </div>
            </div>
            <div class="modal-foot">
                <button class="cancel-btn" onclick={() => isChangingPassword = false}>Cancel</button>
                <button class="save-btn" onclick={handlePasswordChange}>Update Password</button>
            </div>
        </div>
    </div>
{/if}


<style>
    .profile-layout {
        display: flex;
        gap: 40px;
        padding: 10px;
        max-width: 1000px;
    }

    .sidebar { width: 320px; flex-shrink: 0; }
    .main-content { flex: 1; }

    .user-header { display: flex; align-items: center; gap: 16px; margin-bottom: 30px; }
    .avatar { width: 60px; height: 60px; border-radius: 50%; background: var(--primary-gradient); display: flex; align-items: center; justify-content: center; font-size: 22px; font-weight: 600; color: #fff; box-shadow: 0 4px 15px rgba(164, 126, 253, 0.3); }
    .user-name { font-size: 18px; font-weight: 600; color: #e8e6f0; }
    .user-email { font-size: 13px; color: #6b6882; }

    .section-card { padding: 20px; border-radius: 12px; border-color: rgba(42, 40, 64, 0.6); margin-bottom: 16px; background: rgba(19, 18, 26, 0.4); }
    .section-tag { font-size: 10px; color: #3d3b52; margin-bottom: 14px; letter-spacing: .1em; font-weight: 700; }
    
    .detail-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #1a1826; }
    .label { font-size: 12px; color: #6b6882; }
    .val { font-size: 12px; color: #e8e6f0; }
    .mono { font-family: 'JetBrains Mono', monospace; font-size: 10px; }

    .slack-row { display: flex; justify-content: space-between; align-items: center; }
    .slack-info { display: flex; align-items: center; gap: 10px; font-size: 13px; color: #e8e6f0; font-weight: 500; }
    .connect-btn { background: var(--primary-p3); color: #fff; border: none; padding: 5px 12px; border-radius: 6px; font-size: 11px; font-weight: 600; cursor: pointer; }
    .status-linked { font-size: 10px; color: #10b981; font-weight: 700; }

    .logout-btn { width: 100%; padding: 12px; background: transparent; border: 1px solid #2a2840; color: #6b6882; border-radius: 10px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s; }
    .logout-btn:hover { background: rgba(239, 68, 68, 0.1); border-color: rgba(239, 68, 68, 0.2); color: #ef4444; }

    /* Main Content Area */
    .header-row { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 24px; }
    h2 { font-size: 24px; font-weight: 600; color: #e8e6f0; margin: 0; }
    .sub-h { font-size: 13px; color: #6b6882; margin-top: 4px; }
    .add-brand-btn { background: #1a1826; color: #e8e6f0; border: 1px solid #2a2840; padding: 7px 14px; border-radius: 6px; font-size: 11px; font-weight: 600; cursor: pointer; transition: 0.2s; }
    .add-brand-btn:hover { background: #2a2840; border-color: #3d3b52; }

    .brand-grid { display: flex; flex-direction: column; gap: 12px; }
    .brand-item { display: flex; justify-content: space-between; align-items: center; padding: 20px; background: rgba(19, 18, 26, 0.4); border: 1px solid #1e1c2a; border-radius: 12px; transition: 0.2s; }
    .brand-item:hover { border-color: #2a2840; background: rgba(19, 18, 26, 0.6); }
    .brand-item.active { border-color: var(--primary-p3); background: rgba(164, 126, 253, 0.05); }

    .brand-name-row { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
    .bn { font-size: 16px; font-weight: 600; color: #e8e6f0; }
    .active-dot { background: var(--primary-p3); color: #fff; font-size: 9px; padding: 2px 6px; border-radius: 4px; font-weight: 700; text-transform: uppercase; }
    .brand-sub { font-size: 12px; color: #6b6882; }

    .brand-actions { display: flex; gap: 8px; }
    .icon-btn { width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; background: #1a1826; border: 1px solid #1e1c2a; color: #6b6882; border-radius: 6px; cursor: pointer; transition: 0.2s; }
    .icon-btn:hover { border-color: #3d3b52; color: #e8e6f0; }
    .icon-btn.del:hover { background: #ef4444; color: #fff; border-color: #ef4444; }

    /* Modals */
    .modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.8); backdrop-filter: blur(8px); display: flex; align-items: center; justify-content: center; z-index: 200; }
    .modal-content { width: 100%; max-width: 480px; background: #13121a; border: 1px solid #2a2840; border-radius: 16px; padding: 30px; }
    .modal-content h3 { font-size: 20px; color: #e8e6f0; margin: 0 0 24px 0; font-family: 'Bebas Neue', sans-serif; letter-spacing: 0.05em; }
    
    .input-set { display: flex; flex-direction: column; gap: 16px; margin-bottom: 24px; }
    .f-box { display: flex; flex-direction: column; gap: 6px; }
    .f-box label { font-size: 10px; font-weight: 700; color: #3d3b52; letter-spacing: 0.1em; }
    .f-box input, .f-box textarea { background: #0f0e16; border: 1px solid #1e1c2a; border-radius: 8px; padding: 12px; color: #e8e6f0; font-size: 14px; outline: none; }
    .f-box input:focus, .f-box textarea:focus { border-color: var(--primary-p3); }

    .modal-foot { display: flex; justify-content: flex-end; gap: 12px; }
    .cancel-btn { background: transparent; border: none; color: #6b6882; font-weight: 600; cursor: pointer; }
    .save-btn { background: var(--primary-p3); color: #fff; border: none; padding: 10px 18px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; transition: 0.2s; }
    .save-btn:hover { opacity: 0.9; }
</style>
