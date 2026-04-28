<script lang="ts">
    // ── COMPLETELY ISOLATED FROM appState ──────────────────────────────
    import { createEventDispatcher } from 'svelte';
    const dispatch = createEventDispatcher();
    const close = () => dispatch('close');

    const API = `${(import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')}/admin`;
    let adminKey   = $state('');
    let isVerified = $state(false);
    let verifyError = $state('');
    let isVerifying = $state(false);

    type LineType = 'out'|'in'|'ok'|'err'|'info'|'sep'|'tbl'|'hdr';
    type Line = { type: LineType; text?: string; rows?: Record<string,string>[]; cols?: string[] };

    let lines    = $state<Line[]>([]);
    let input    = $state('');
    let inputEl: HTMLInputElement;
    let termEl:  HTMLDivElement;
    let cmdHistory: string[] = [];
    let histIdx  = -1;

    // pending multi-step wizard
    let wizard = $state<any>(null);

    // cached data (refreshed per command)
    let cache = { models:[], regions:[], users:[], brands:[], decks:[], prompts:[], instances:[] } as any;

    // ── helpers ────────────────────────────────────────────────────────
    const p    = (text='', type: LineType='out') => { lines = [...lines, { type, text }]; tick(); };
    const ok   = (t='') => p(t, 'ok');
    const err  = (t='') => p(t, 'err');
    const info = (t='') => p(t, 'info');
    const sep  = ()     => p('', 'sep');
    const tbl  = (rows: Record<string,string>[], cols: string[]) => { lines = [...lines, { type:'tbl', rows, cols }]; tick(); };
    const hdr  = (t='') => p(t, 'hdr');
    const tick = ()     => setTimeout(() => { if (termEl) termEl.scrollTop = termEl.scrollHeight; }, 20);

    const H = () => ({ 'X-Admin-Key': adminKey, 'Content-Type': 'application/json' });

    async function api(path: string, opts: RequestInit = {}) {
        const r = await fetch(`${API}${path}`, { ...opts, headers: { ...H(), ...(opts.headers||{}) } });
        if (!r.ok) { const e = await r.json().catch(()=>({})); throw new Error(e.detail || `HTTP ${r.status}`); }
        return r.json();
    }

    const short = (id='') => id.slice(0,8)+'…';

    // ── verify ─────────────────────────────────────────────────────────
    async function verify() {
        if (!adminKey.trim()) return;
        isVerifying = true; verifyError = '';
        try {
            const r = await fetch(`${API}/verify`, { method:'POST', headers: H() });
            if (!r.ok) throw 0;
            isVerified = true;
            const d = await api('/overview');
            Object.assign(cache, d);
            boot(d.counts);
        } catch { verifyError = 'Access denied — wrong key.'; }
        finally  { isVerifying = false; }
    }

    function boot(c: any) {
        const msgs: [string, LineType, number][] = [
            ['╔══════════════════════════════════════════╗','info',0],
            ['║     AIVIS  ADMIN  CONSOLE  v2.0      ║','info',50],
            ['╚══════════════════════════════════════════╝','info',100],
            [`  ${c.models}m · ${c.regions}r · ${c.users}u · ${c.brands}b · ${c.decks}d (${c.active_decks} active) · ${c.prompts}p · ${c.instances}i`,'out',200],
            ['','out',300],
            ["  Type 'help' for commands.",'info',350],
        ];
        msgs.forEach(([t, type, delay]) => setTimeout(() => p(t, type), delay));
    }

    // ── command router ─────────────────────────────────────────────────
    async function run(raw: string) {
        const cmd = raw.trim();
        if (!cmd) return;
        cmdHistory = [cmd, ...cmdHistory].slice(0,100);
        histIdx = -1;
        p(`❯ ${cmd}`, 'in');
        input = '';

        if (wizard) { await handleWizard(cmd); return; }

        const [base, sub='', ...rest] = cmd.split(/\s+/);
        const arg = rest.join(' ');

        try {
            switch(base.toLowerCase()) {
                case 'help':      showHelp(); break;
                case 'clear':     lines = []; break;
                case 'exit':      close(); break;
                case 'overview':  await cmdOverview(); break;
                case 'models':    await handleModels(sub, arg); break;
                case 'regions':   await handleRegions(sub, arg); break;
                case 'users':     await handleUsers(sub, arg); break;
                case 'brands':    await handleBrands(sub, arg); break;
                case 'decks':     await handleDecks(sub, arg); break;
                case 'prompts':   await handlePrompts(sub, arg); break;
                case 'instances': await handleInstances(sub, arg); break;
                default: err(`Unknown: '${base}'. Type 'help'.`);
            }
        } catch(e:any) { err(`Error: ${e.message}`); }
    }

    // ── help (compact grouped) ─────────────────────────────────────────
    function showHelp() {
        sep();
        const groups: [string, [string,string][]][] = [
            ['SYSTEM', [
                ['overview',                    'all counts + cached data snapshot'],
                ['clear / exit',                'clear screen / close console'],
            ]],
            ['MODELS', [
                ['models list',                 'list models + pricing'],
                ['models add',                  'wizard: add model'],
                ['models pricing <id>',         'update pricing'],
                ['models delete <id>',          'delete model'],
            ]],
            ['REGIONS', [
                ['regions list',                'list regions'],
                ['regions add',                 'wizard: add region'],
                ['regions delete <id>',         'delete region'],
            ]],
            ['BRANDS', [
                ['brands list',                 'all brands (all users)'],
                ['brands get <id>',             'brand detail'],
                ['brands update <id>',          'wizard: update brand'],
                ['brands delete <id>',          'delete brand + cascade'],
            ]],
            ['DECKS', [
                ['decks list',                  'all decks'],
                ['decks get <id>',              'deck detail'],
                ['decks toggle <id>',           'toggle active/inactive'],
                ['decks delete <id>',           'delete deck'],
            ]],
            ['PROMPTS', [
                ['prompts list [brand-id]',     'all prompts or by brand'],
                ['prompts get <id>',            'prompt content'],
                ['prompts delete <id>',         'delete prompt'],
            ]],
            ['INSTANCES', [
                ['instances list [deck-id]',    'recent instances (max 20)'],
                ['instances get <id>',          'full instance detail'],
            ]],
            ['USERS', [
                ['users list',                  'all registered users'],
                ['users get <id>',              'user detail'],
                ['users update <id>',           'wizard: update user'],
                ['users delete <id>',           'delete user'],
            ]],
        ];
        groups.forEach(([g, cmds]) => {
            hdr(`  ─── ${g} ${'─'.repeat(Math.max(0, 34 - g.length))}`);
            cmds.forEach(([c, d]) => p(`  ${c.padEnd(28)} ${d}`));
        });
        sep();
    }

    // ── overview ───────────────────────────────────────────────────────
    async function cmdOverview() {
        const d = await api('/overview');
        Object.assign(cache, d);
        const c = d.counts;
        sep();
        [
            ['Models',  c.models],  ['Regions', c.regions],
            ['Users',   c.users],   ['Brands',  c.brands],
            ['Decks',   `${c.decks} (${c.active_decks} active)`],
            ['Prompts', c.prompts], ['Instances', c.instances],
        ].forEach(([k, v]) => p(`  ${String(k).padEnd(12)} ${v}`));
        sep();
    }

    // ── models ─────────────────────────────────────────────────────────
    async function handleModels(sub: string, arg: string) {
        switch(sub || 'list') {
            case 'list': {
                const ms = await api('/models');
                cache.models = ms;
                if (!ms.length) { info('No models.'); return; }
                tbl(ms.map((m:any) => ({
                    'ID': m.id, 'Name': m.model_name, 'Provider': m.provider,
                    'External ID': m.external_id,
                    '$/1M in': String(m.pricing?.input ?? '—'),
                    '$/1M out': String(m.pricing?.output ?? '—'),
                })), ['ID','Name','Provider','External ID','$/1M in','$/1M out']);
                break;
            }
            case 'add':
                wizard = { type:'model_add', step:'provider', buf:{} };
                info('Provider (openai / anthropic / google / perplexity):');
                break;
            case 'pricing':
                if (!arg) { err('Usage: models pricing <id>'); return; }
                wizard = { type:'model_pricing', step:'input', id:arg, buf:{} };
                info(`Pricing for ${short(arg)} — input $/1M:`);
                break;
            case 'delete': {
                if (!arg) { err('Usage: models delete <id>'); return; }
                await api(`/models/${arg}`, { method:'DELETE' });
                ok(`Model ${short(arg)} deleted.`);
                break;
            }
            default: err(`models: unknown sub-command '${sub}'.`);
        }
    }

    // ── regions ────────────────────────────────────────────────────────
    async function handleRegions(sub: string, arg: string) {
        switch(sub || 'list') {
            case 'list': {
                const rs = await api('/regions');
                cache.regions = rs;
                if (!rs.length) { info('No regions.'); return; }
                tbl(rs.map((r:any) => ({
                    'ID': r.id, 'Name': r.name, 'Country': r.country_code,
                    'Region': r.region||'—', 'City': r.city||'—',
                })), ['ID','Name','Country','Region','City']);
                break;
            }
            case 'add':
                wizard = { type:'region_add', step:'name', buf:{} };
                info('Display name (e.g. California, USA):');
                break;
            case 'delete': {
                if (!arg) { err('Usage: regions delete <id>'); return; }
                await api(`/regions/${arg}`, { method:'DELETE' });
                ok(`Region ${short(arg)} deleted.`);
                break;
            }
            default: err(`regions: unknown sub-command '${sub}'.`);
        }
    }

    // ── brands ─────────────────────────────────────────────────────────
    async function handleBrands(sub: string, arg: string) {
        switch(sub || 'list') {
            case 'list': {
                const bs = await api('/brands');
                cache.brands = bs;
                if (!bs.length) { info('No brands.'); return; }
                tbl(bs.map((b:any) => ({
                    'ID': b.id, 'Name': b.name, 'Industry': b.industry||'—',
                    'Domain': b.domain||'—', 'User': b.user_id,
                })), ['ID','Name','Industry','Domain','User']);
                break;
            }
            case 'get': {
                if (!arg) { err('Usage: brands get <id>'); return; }
                const b = await api(`/brands/${arg}`);
                sep();
                Object.entries(b).forEach(([k,v]) => p(`  ${k.padEnd(16)} ${v}`));
                sep();
                break;
            }
            case 'update': {
                if (!arg) { err('Usage: brands update <id>'); return; }
                wizard = { type:'brand_update', step:'name', id:arg, buf:{} };
                info('New name (blank to skip):');
                break;
            }
            case 'delete': {
                if (!arg) { err('Usage: brands delete <id>'); return; }
                wizard = { type:'confirm_delete', target:'brands', id:arg };
                err(`⚠ Delete brand ${short(arg)} + all its decks/prompts? (yes/no)`);
                break;
            }
            default: err(`brands: unknown sub-command '${sub}'.`);
        }
    }

    // ── decks ──────────────────────────────────────────────────────────
    async function handleDecks(sub: string, arg: string) {
        switch(sub || 'list') {
            case 'list': {
                const ds = await api('/decks');
                cache.decks = ds;
                if (!ds.length) { info('No decks.'); return; }
                tbl(ds.map((d:any) => ({
                    'ID': d.id, 'Name': d.name,
                    'Active': d.to_execute ? '✓' : '✗',
                    'Freq': `${d.frequency}s`, 'Prompts': String((d.prompt_ids||[]).length),
                })), ['ID','Name','Active','Freq','Prompts']);
                break;
            }
            case 'get': {
                if (!arg) { err('Usage: decks get <id>'); return; }
                const d = await api(`/decks/${arg}`);
                sep();
                Object.entries(d).forEach(([k,v]) => p(`  ${k.padEnd(16)} ${JSON.stringify(v)}`));
                sep();
                break;
            }
            case 'toggle': {
                if (!arg) { err('Usage: decks toggle <id>'); return; }
                const d = await api(`/decks/${arg}`);
                const updated = await api(`/decks/${arg}`, { method:'PATCH', body: JSON.stringify({ to_execute: !d.to_execute }) });
                ok(`Deck '${updated.name}' is now ${updated.to_execute ? 'ACTIVE' : 'PAUSED'}.`);
                break;
            }
            case 'delete': {
                if (!arg) { err('Usage: decks delete <id>'); return; }
                wizard = { type:'confirm_delete', target:'decks', id:arg };
                err(`⚠ Delete deck ${short(arg)}? (yes/no)`);
                break;
            }
            default: err(`decks: unknown sub-command '${sub}'.`);
        }
    }

    // ── prompts ────────────────────────────────────────────────────────
    async function handlePrompts(sub: string, arg: string) {
        switch(sub || 'list') {
            case 'list': {
                const ps = await api(`/prompts${arg ? `?brand_id=${arg}` : ''}`);
                cache.prompts = ps;
                if (!ps.length) { info('No prompts.'); return; }
                tbl(ps.map((p:any) => ({
                    'ID': p.id,
                    'Brand': p.brand_id,
                    'Content': p.content.slice(0,50) + (p.content.length > 50 ? '…' : ''),
                    'Notes': p.notes||'—',
                })), ['ID','Brand','Content','Notes']);
                break;
            }
            case 'get': {
                if (!arg) { err('Usage: prompts get <id>'); return; }
                const pr = await api(`/prompts/${arg}`);
                sep();
                p(`  ID:      ${pr.id}`);
                p(`  Brand:   ${pr.brand_id}`);
                p(`  Notes:   ${pr.notes||'—'}`);
                p('  Content:');
                pr.content.match(/.{1,70}/g)?.forEach((l:string) => p(`    ${l}`));
                sep();
                break;
            }
            case 'delete': {
                if (!arg) { err('Usage: prompts delete <id>'); return; }
                wizard = { type:'confirm_delete', target:'prompts', id:arg };
                err(`⚠ Delete prompt ${short(arg)}? (yes/no)`);
                break;
            }
            default: err(`prompts: unknown sub-command '${sub}'.`);
        }
    }

    // ── instances ──────────────────────────────────────────────────────
    async function handleInstances(sub: string, arg: string) {
        switch(sub || 'list') {
            case 'list': {
                const url = arg ? `/instances?deck_id=${arg}` : '/instances';
                const ins = await api(url);
                const slice = ins.slice(0, 20);
                if (!slice.length) { info('No instances.'); return; }
                tbl(slice.map((i:any) => ({
                    'ID': i.id,
                    'Model': i.model_name||'—',
                    'Region': i.region_name||'Global',
                    'Prompt': (i.prompt_content||'').slice(0,30)+'…',
                    'At': i.initiated_at ? new Date(i.initiated_at).toLocaleTimeString() : '—',
                })), ['ID','Model','Region','Prompt','At']);
                if (ins.length > 20) info(`Showing 20 of ${ins.length}.`);
                break;
            }
            case 'get': {
                if (!arg) { err('Usage: instances get <id>'); return; }
                const i = await api(`/instances/${arg}`);
                sep();
                const fields = ['id','model_name','region_name','brand_name','deck_name','initiated_at','completed_at'];
                fields.forEach(f => p(`  ${f.padEnd(16)} ${i[f]||'—'}`));
                p('  response_data:');
                JSON.stringify(i.response_data, null, 2).split('\n').slice(0,20).forEach(l => p(`    ${l}`));
                sep();
                break;
            }
            default: err(`instances: unknown sub-command '${sub}'.`);
        }
    }

    // ── users ──────────────────────────────────────────────────────────
    async function handleUsers(sub: string, arg: string) {
        switch(sub || 'list') {
            case 'list': {
                const us = await api('/users');
                cache.users = us;
                if (!us.length) { info('No users.'); return; }
                tbl(us.map((u:any) => ({
                    'ID': u.id, 'Email': u.email,
                    'Name': u.full_name||'—',
                    'Created': new Date(u.created_at).toLocaleDateString(),
                })), ['ID','Email','Name','Created']);
                break;
            }
            case 'get': {
                if (!arg) { err('Usage: users get <id>'); return; }
                const u = await api(`/users/${arg}`);
                sep();
                Object.entries(u).forEach(([k,v]) => p(`  ${k.padEnd(18)} ${v}`));
                sep();
                break;
            }
            case 'update': {
                if (!arg) { err('Usage: users update <id>'); return; }
                wizard = { type:'user_update', step:'email', id:arg, buf:{} };
                info('New email (blank to skip):');
                break;
            }
            case 'delete': {
                if (!arg) { err('Usage: users delete <id>'); return; }
                wizard = { type:'confirm_delete', target:'users', id:arg };
                err(`⚠ Delete user ${short(arg)}? (yes/no)`);
                break;
            }
            default: err(`users: unknown sub-command '${sub}'.`);
        }
    }

    // ── wizard handler ─────────────────────────────────────────────────
    async function handleWizard(val: string) {
        const w = wizard;
        try {
            // Generic confirm delete
            if (w.type === 'confirm_delete') {
                wizard = null;
                if (val.toLowerCase() === 'yes') {
                    await api(`/${w.target}/${w.id}`, { method:'DELETE' });
                    ok(`Deleted ${short(w.id)}.`);
                } else { info('Cancelled.'); }
                return;
            }

            // Model add
            if (w.type === 'model_add') {
                if (w.step === 'provider')      { w.buf.provider    = val; w.step = 'name';         info('Display name (e.g. GPT-4o Mini):'); }
                else if (w.step === 'name')     { w.buf.model_name  = val; w.step = 'ext_id';       info('External ID (e.g. gpt-4o-mini):'); }
                else if (w.step === 'ext_id')   { w.buf.external_id = val; w.step = 'input';        info('Input cost $/1M (e.g. 0.15):'); }
                else if (w.step === 'input')    { w.buf.input       = +val; w.step = 'cached_input'; info('Cached input $/1M (e.g. 0.075):'); }
                else if (w.step === 'cached_input') { w.buf.cached_input = +val; w.step = 'output'; info('Output $/1M (e.g. 0.60):'); }
                else if (w.step === 'output') {
                    w.buf.output = +val; wizard = null;
                    const m = await api('/models', { method:'POST', body: JSON.stringify({ provider: w.buf.provider, model_name: w.buf.model_name, external_id: w.buf.external_id, pricing: { input: w.buf.input, cached_input: w.buf.cached_input, output: w.buf.output } }) });
                    ok(`✓ Model '${m.model_name}' created (${short(m.id)})`);
                }
                return;
            }

            // Model pricing
            if (w.type === 'model_pricing') {
                if (w.step === 'input')             { w.buf.input = +val; w.step = 'cached_input'; info('Cached input $/1M:'); }
                else if (w.step === 'cached_input') { w.buf.cached_input = +val; w.step = 'output'; info('Output $/1M:'); }
                else if (w.step === 'output') {
                    w.buf.output = +val; wizard = null;
                    const m = await api(`/models/${w.id}`, { method:'PATCH', body: JSON.stringify({ pricing: w.buf }) });
                    ok(`✓ Pricing updated for ${m.model_name}`);
                }
                return;
            }

            // Region add
            if (w.type === 'region_add') {
                if (w.step === 'name')         { w.buf.name = val; w.step = 'code'; info('Country code (ISO 2-letter, e.g. US):'); }
                else if (w.step === 'code')    { w.buf.country_code = val.toUpperCase(); w.step = 'region'; info('Sub-region/state (blank to skip):'); }
                else if (w.step === 'region')  { w.buf.region = val||null; w.step = 'city'; info('City (blank to skip):'); }
                else if (w.step === 'city') {
                    w.buf.city = val||null; wizard = null;
                    const r = await api('/regions', { method:'POST', body: JSON.stringify(w.buf) });
                    ok(`✓ Region '${r.name}' created (${short(r.id)})`);
                }
                return;
            }

            // Brand update
            if (w.type === 'brand_update') {
                if (w.step === 'name')    { if (val) w.buf.name = val; w.step = 'domain'; info('New domain (blank to skip):'); }
                else if (w.step === 'domain')   { if (val) w.buf.domain = val; w.step = 'industry'; info('New industry (blank to skip):'); }
                else if (w.step === 'industry') {
                    if (val) w.buf.industry = val; wizard = null;
                    if (!Object.keys(w.buf).length) { info('No changes.'); return; }
                    const b = await api(`/brands/${w.id}`, { method:'PATCH', body: JSON.stringify(w.buf) });
                    ok(`✓ Brand '${b.name}' updated.`);
                }
                return;
            }

            // User update
            if (w.type === 'user_update') {
                if (w.step === 'email')    { if (val) w.buf.email = val; w.step = 'name'; info('New full name (blank to skip):'); }
                else if (w.step === 'name') { if (val) w.buf.full_name = val; w.step = 'slack'; info('New Slack ID (blank to skip):'); }
                else if (w.step === 'slack') {
                    if (val) w.buf.slack_user_id = val; wizard = null;
                    if (!Object.keys(w.buf).length) { info('No changes.'); return; }
                    const u = await api(`/users/${w.id}`, { method:'PATCH', body: JSON.stringify(w.buf) });
                    ok(`✓ User ${u.email} updated.`);
                }
                return;
            }

        } catch(e: any) { wizard = null; err(`Error: ${e.message}`); }
    }

    // ── keyboard ───────────────────────────────────────────────────────
    function onKey(e: KeyboardEvent) {
        if (e.key === 'Enter')     { run(input); }
        else if (e.key === 'ArrowUp')   { e.preventDefault(); histIdx = Math.min(histIdx+1, cmdHistory.length-1); input = cmdHistory[histIdx]??''; }
        else if (e.key === 'ArrowDown') { e.preventDefault(); histIdx = Math.max(histIdx-1, -1); input = histIdx===-1 ? '' : cmdHistory[histIdx]; }
        else if (e.key === 'Escape')    { close(); }
    }
</script>

<!-- svelte-ignore a11y-click-events-have-key-events -->
<!-- svelte-ignore a11y-no-static-element-interactions -->
<div id="ao" onclick={(e) => { if (e.target === e.currentTarget) close(); }}>
    <div id="ac">
        <div id="bar">
            <div id="dots">
                <span class="d r" onclick={close}></span>
                <span class="d y"></span>
                <span class="d g"></span>
            </div>
            <span id="ttl">AIVIS Admin Console</span>
            <span id="lock">{isVerified ? '🔓 Authenticated' : '🔐 Locked'}</span>
        </div>

        {#if !isVerified}
            <div id="gate">
                <div id="gate-icon">⬡</div>
                <div id="gate-title">Admin Access Required</div>
                {#if verifyError}<div id="gate-err">{verifyError}</div>{/if}
                <input id="gate-in" type="password" placeholder="Enter admin key…"
                    bind:value={adminKey} onkeydown={(e)=>e.key==='Enter'&&verify()} autofocus />
                <button id="gate-btn" onclick={verify} disabled={isVerifying}>
                    {isVerifying ? 'Verifying…' : 'Enter →'}
                </button>
            </div>
        {:else}
            <div id="term" bind:this={termEl} onclick={() => inputEl?.focus()}>
                {#each lines as line}
                    {#if line.type === 'sep'}
                        <div class="sep"></div>
                    {:else if line.type === 'tbl' && line.rows}
                        <div class="tw">
                            <table>
                                <thead><tr>{#each line.cols||[] as c}<th>{c}</th>{/each}</tr></thead>
                                <tbody>{#each line.rows as row}<tr>{#each line.cols||[] as c}<td>{row[c]}</td>{/each}</tr>{/each}</tbody>
                            </table>
                        </div>
                    {:else}
                        <div class="l {line.type}">{line.text}</div>
                    {/if}
                {/each}
                <div id="iline">
                    <span id="ps">{wizard ? '┃' : '❯'}</span>
                    <input id="ci" bind:this={inputEl} bind:value={input}
                        onkeydown={onKey} spellcheck="false" autocomplete="off" autofocus
                        placeholder={wizard ? 'enter value…' : 'type a command'} />
                </div>
            </div>
        {/if}
    </div>
</div>

<style>
    #ao {
        position: fixed; inset: 0;
        background: rgba(0,0,0,.78);
        backdrop-filter: blur(10px);
        z-index: 9999;
        display: flex; align-items: center; justify-content: center;
        animation: fi .18s ease;
    }
    @keyframes fi { from { opacity:0 } to { opacity:1 } }

    #ac {
        width: min(900px, 96vw); height: min(660px, 93vh);
        background: #0c0b10; border: 1px solid #222030;
        border-radius: 12px;
        box-shadow: 0 36px 90px rgba(0,0,0,.75), 0 0 0 1px rgba(164,126,253,.07);
        display: flex; flex-direction: column; overflow: hidden;
        animation: su .22s cubic-bezier(.16,1,.3,1);
    }
    @keyframes su { from { transform:translateY(18px); opacity:0 } to { transform:none; opacity:1 } }

    #bar {
        display: flex; align-items: center; gap: 10px;
        padding: 11px 16px; background: #100f16;
        border-bottom: 1px solid #1c1a27; flex-shrink: 0;
    }
    #dots { display:flex; gap:6px; }
    .d { width:12px; height:12px; border-radius:50%; cursor:pointer; }
    .d.r { background:#ff5f57; } .d.y { background:#febc2e; } .d.g { background:#28c840; }
    #ttl { flex:1; text-align:center; font-family:'JetBrains Mono',monospace; font-size:11px; color:#3d3a52; letter-spacing:.1em; }
    #lock { font-family:'JetBrains Mono',monospace; font-size:10px; color:#2e2b3e; }

    #gate {
        flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:14px;
    }
    #gate-icon { font-size:44px; opacity:.35; }
    #gate-title { font-family:'JetBrains Mono',monospace; font-size:16px; color:#b8b3c8; }
    #gate-err { font-family:'JetBrains Mono',monospace; font-size:11px; color:#f87171; background:rgba(248,113,113,.08); padding:7px 14px; border-radius:6px; border:1px solid rgba(248,113,113,.18); }
    #gate-in { width:260px; background:#171522; border:1px solid #2c293d; border-radius:8px; padding:11px 14px; color:#c8c3d8; font-family:'JetBrains Mono',monospace; font-size:13px; outline:none; text-align:center; letter-spacing:.12em; }
    #gate-in:focus { border-color:#a47efd; box-shadow:0 0 0 3px rgba(164,126,253,.1); }
    #gate-btn { background:linear-gradient(135deg,#7c5cfc,#a47efd); border:none; border-radius:8px; padding:10px 26px; color:#fff; font-family:'JetBrains Mono',monospace; font-size:12px; cursor:pointer; transition:opacity .2s; }
    #gate-btn:hover { opacity:.85; } #gate-btn:disabled { opacity:.4; cursor:not-allowed; }

    #term { flex:1; overflow-y:auto; padding:14px 18px; font-family:'JetBrains Mono',monospace; font-size:12px; line-height:1.6; cursor:text; }
    #term::-webkit-scrollbar { width:3px; }
    #term::-webkit-scrollbar-thumb { background:#2a2738; border-radius:2px; }

    .l { white-space:pre-wrap; word-break:break-all; }
    .l.out  { color:#888299; }
    .l.in   { color:#a47efd; }
    .l.ok   { color:#4ade80; }
    .l.err  { color:#f87171; }
    .l.info { color:#60a5fa; }
    .l.hdr  { color:#6b5fa0; font-weight:600; margin-top:4px; }
    .sep { height:1px; background:#1a1825; margin:5px 0; }

    .tw { overflow-x:auto; margin:5px 0; }
    table { border-collapse:collapse; font-size:11px; }
    th { color:#4a4660; text-align:left; padding:2px 14px 2px 0; border-bottom:1px solid #1c1a27; font-weight:600; }
    td { color:#888299; padding:2px 14px 2px 0; }
    tr:hover td { color:#c0bbcf; }

    #iline { display:flex; align-items:center; gap:7px; margin-top:3px; }
    #ps { color:#a47efd; font-size:12px; }
    #ci { flex:1; background:transparent; border:none; outline:none; color:#ddd8ee; font-family:'JetBrains Mono',monospace; font-size:12px; caret-color:#a47efd; }
    #ci::placeholder { color:#2a2738; }
</style>
