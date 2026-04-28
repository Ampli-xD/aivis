<script lang="ts">
    import Toggle from './Toggle.svelte';
    
    let showInactive = $state(true);
    let autoArchive = $state(false);
    let defaultGrid = $state(true);
    
    let emailNotify = $state(true);
    let lowUsageAlert = $state(false);
    let weeklyDigest = $state(true);
</script>

<div class="stats-grid">
    <div class="stat-card"><div class="stat-label">DECK LIMIT</div><div class="stat-val">50</div></div>
    <div class="stat-card"><div class="stat-label">PROMPT LIMIT</div><div class="stat-val">500</div></div>
    <div class="stat-card"><div class="stat-label">ACTIVE USERS</div><div class="stat-val">12</div></div>
    <div class="stat-card">
        <div class="stat-label">API CALLS</div>
        <div class="stat-val">4.2k</div>
        <div class="stat-sub">last 30 days</div>
    </div>
</div>

<div class="card" style="cursor:default;margin-bottom:10px">
    <div style="font-size:10px;color:#3d3b52;margin-bottom:10px;letter-spacing:.06em;font-weight:500">DISPLAY</div>
    <Toggle label="Show inactive items" checked={showInactive} onToggle={() => showInactive = !showInactive} />
    <Toggle label="Auto-archive after inactivity" checked={autoArchive} onToggle={() => autoArchive = !autoArchive} />
    <Toggle label="Grid view by default" checked={defaultGrid} onToggle={() => defaultGrid = !defaultGrid} />
</div>

<div class="card" style="cursor:default;margin-bottom:10px">
    <div style="font-size:10px;color:#3d3b52;margin-bottom:10px;letter-spacing:.06em;font-weight:500">NOTIFICATIONS</div>
    <Toggle label="Email on new deck" checked={emailNotify} onToggle={() => emailNotify = !emailNotify} />
    <Toggle label="Alert on low usage prompts" checked={lowUsageAlert} onToggle={() => lowUsageAlert = !lowUsageAlert} />
    <Toggle label="Weekly digest" checked={weeklyDigest} onToggle={() => weeklyDigest = !weeklyDigest} />
</div>

<div class="card" style="cursor:default">
    <div style="font-size:10px;color:#3d3b52;margin-bottom:10px;letter-spacing:.06em;font-weight:500">DANGER ZONE</div>
    <div style="display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid #1a1826">
        <span style="font-size:12px;color:#a09cc0">Export all data</span>
        <button class="new-btn" style="font-size:11px;padding:4px 10px;background:none;border-color:#2a2840;color:#a09cc0">Export CSV</button>
    </div>
    <div style="display:flex;justify-content:space-between;align-items:center;padding:7px 0">
        <span style="font-size:12px;color:#a09cc0">Clear inactive items</span>
        <button class="new-btn" style="font-size:11px;padding:4px 10px;background:#2a1a1a;border-color:#f87171;color:#f87171">Clear inactive</button>
    </div>
</div>
