<script lang="ts">
    import { appState } from '../state.svelte';
    
    interface Props {
        instanceId: string;
    }
    let { instanceId }: Props = $props();

    const instance = $derived(appState.instances.find(i => i.id === instanceId));
</script>

{#if instance}
    <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:1.5rem">
        <div>
            <div style="font-family: 'Bebas Neue', sans-serif; font-size: 24px; color: #e8e6f0; letter-spacing: 0.05em">{instance.id}</div>
            <div style="font-size: 11px; color: #3d3b52; margin-top: 4px">Generated {instance.initiatedAt} · Reference Archive</div>
        </div>
        <div style="display:flex; gap: 8px">
            <button class="new-btn">Export Result</button>
        </div>
    </div>

    <!-- Triple dimensions -->
    <div class="card" style="margin-bottom: 1.5rem; cursor: default">
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px">
            <div>
                <div class="mb-label">DECK</div>
                <div style="font-size: 14px; color: #e8e6f0; margin-top: 4px">{instance.deckName}</div>
            </div>
            <div>
                <div class="mb-label">MODEL</div>
                <div style="font-size: 14px; color: #e8e6f0; margin-top: 4px">{instance.modelName}</div>
            </div>
            <div>
                <div class="mb-label">REGION</div>
                <div style="font-size: 14px; color: #e8e6f0; margin-top: 4px">{instance.regionName}</div>
            </div>
        </div>
    </div>

    <!-- Prompt Content (Single Line) -->
    <div class="card" style="margin-bottom: 1.5rem; cursor: default; background: #050505; padding: 12px 20px">
        <div style="display: flex; align-items: center; gap: 15px">
            <div class="mb-label" style="margin-bottom: 0; white-space: nowrap">PROMPT</div>
            <div style="font-size: 12px; color: #6b6882; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1">
                {instance.promptContent}
            </div>
        </div>
    </div>

    <!-- Visibility Analytics Section -->
    {#if instance.metrics && instance.metrics.brand_mentioned !== undefined}
        <div style="margin-bottom: 1.5rem">
            <div class="mb-label" style="margin-bottom: 12px">VISIBILITY ANALYTICS</div>
            <div class="stats-grid" style="margin-bottom: 20px">
                <div class="stat-card">
                    <div class="stat-label">BRAND MENTIONED</div>
                    <div class="stat-val {instance.metrics.brand_mentioned ? 'g' : ''}">
                        {instance.metrics.brand_mentioned ? 'YES' : 'NO'}
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">NARRATIVE MENTION</div>
                    <div class="stat-val" style="color:var(--primary-p3)">
                        {instance.metrics.narrative_mention ? 'YES' : 'NO'}
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">SENTIMENT</div>
                    <div class="stat-val {instance.metrics.sentiment_score > 0 ? 'g' : (instance.metrics.sentiment_score < 0 ? 'r' : '')}">
                        {instance.metrics.sentiment_score !== null ? instance.metrics.sentiment_score.toFixed(2) : '-'}
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">MENTION DENSITY</div>
                    <div class="stat-val" style="color: #6b6882">
                        {instance.metrics.brand_mention_density ? (instance.metrics.brand_mention_density * 100).toFixed(1) + '%' : '-'}
                    </div>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem">
                <!-- Detailed Analytics -->
                <div class="card" style="cursor: default">
                    <div class="mb-label">MENTION DETAILS</div>
                    <div class="detail-row">
                        <span>Intent:</span>
                        <span class="detail-val">{instance.metrics.mention_intent || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span>Position:</span>
                        <span class="detail-val">{instance.metrics.brand_position ? '#' + instance.metrics.brand_position : 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span>Mention Count:</span>
                        <span class="detail-val">{instance.metrics.mention_count || 0}</span>
                    </div>
                    <div class="detail-row">
                        <span>Total Brands in Resp:</span>
                        <span class="detail-val">{instance.metrics.total_brands_mentioned || 0}</span>
                    </div>
                    <div class="detail-row" style="margin-top: 15px; border-top: 1px solid rgba(42, 40, 64, 0.3); padding-top: 10px">
                        <span>Context:</span>
                        <span class="detail-val italic" style="font-size: 11px; color: #a3a1b5">
                            "{instance.metrics.mention_context || 'No specific context snippet'}"
                        </span>
                    </div>
                </div>

                <!-- Competitors -->
                <div class="card" style="cursor: default">
                    <div class="mb-label">COMPETITIVE PRESENCE</div>
                    {#if (instance.metrics.competitors_mentioned || []).length > 0}
                        <div class="competitor-list" style="margin-top: 10px">
                            {#each instance.metrics.competitors_mentioned as c}
                                <div class="comp-item">
                                    <div class="comp-main">
                                        <span class="comp-name">{c.name}</span>
                                        {#if c.narrative}<span class="mini-pill">Narrative</span>{/if}
                                    </div>
                                    <div class="comp-stats">
                                        <span>#{c.position || '?'}</span>
                                        <span class="sep">|</span>
                                        <span>{c.mention_count} hits</span>
                                        <span class="sep">|</span>
                                        <span class={c.sentiment_score > 0 ? 'g' : (c.sentiment_score < 0 ? 'r' : '')}>
                                            {c.sentiment_score?.toFixed(1) || '0.0'}
                                        </span>
                                    </div>
                                </div>
                            {/each}
                        </div>
                    {:else}
                        <div style="font-size: 11px; color: #3d3b52; margin-top: 12px">No competitors identified in response.</div>
                    {/if}
                </div>
            </div>

            <!-- Full Source List -->
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-top: 1.5rem">
                <div class="card" style="cursor: default">
                    <div class="mb-label">BRAND SPECIFIC SOURCES</div>
                    {#if (instance.metrics.mention_sources || []).length > 0}
                        <div class="sources-list" style="margin-top: 10px">
                            {#each instance.metrics.mention_sources as s}
                                <div class="source-item">
                                    <div class="source-name">{s.source}</div>
                                    <div class="source-tier {s.authority_tier}">{s.authority_tier}</div>
                                    <a href={s.url} target="_blank" class="source-link">Link</a>
                                </div>
                            {/each}
                        </div>
                    {:else}
                        <div style="font-size: 11px; color: #3d3b52; margin-top: 12px">No specific sources cited for the brand.</div>
                    {/if}
                </div>

                <div class="card" style="cursor: default">
                    <div class="mb-label">ALL CITED SOURCES</div>
                    {#if (instance.metrics.all_sources || []).length > 0}
                        <div class="sources-list" style="margin-top: 10px">
                            {#each instance.metrics.all_sources as s}
                                <div class="source-item">
                                    <div class="source-name">{s.source}</div>
                                    <div class="source-tier {s.authority_tier || 'low'}">{s.authority_tier || 'N/A'}</div>
                                    {#if s.url}<a href={s.url} target="_blank" class="source-link">Link</a>{/if}
                                </div>
                            {/each}
                        </div>
                    {:else}
                        <div style="font-size: 11px; color: #3d3b52; margin-top: 12px">No citations found in response.</div>
                    {/if}
                </div>
            </div>
        </div>
    {/if}

    <!-- Raw Performance Metrics -->
    {#if instance.metrics && (instance.metrics.latency || instance.metrics.tokens_in)}
        <div style="margin-bottom: 2rem">
            <div class="mb-label" style="margin-bottom: 12px">PERFORMANCE METRICS</div>
            <div class="stats-grid">
                <div class="stat-card"><div class="stat-label">LATENCY</div><div class="stat-val">{instance.metrics.latency ? instance.metrics.latency + 's' : '-'}</div></div>
                <div class="stat-card"><div class="stat-label">TOKENS IN</div><div class="stat-val">{instance.metrics.tokens_in || '-'}</div></div>
                <div class="stat-card"><div class="stat-label">TOKENS OUT</div><div class="stat-val">{instance.metrics.tokens_out || '-'}</div></div>
                <div class="stat-card"><div class="stat-label">TIME BUCKET</div><div class="stat-val" style="font-size: 12px; color: #3d3b52">{instance.timeBucket.split('T')[0]}</div></div>
            </div>
        </div>
    {/if}

    <!-- Raw Response JSON -->
    <div class="card" style="cursor: default; background: #050505; border-color: rgba(164, 126, 253, 0.1); margin-bottom: 2rem">
        <div class="mb-label" style="color: var(--primary-p3); margin-bottom: 12px">RAW RESPONSE JSON</div>
        <div style="font-size: 12px; color: #a3a1b5; line-height: 1.6; font-family: 'JetBrains Mono', monospace; white-space: pre; overflow-x: auto; background: #000; padding: 15px; border-radius: 8px; max-height: 400px">
            {JSON.stringify(instance.responseData, null, 2)}
        </div>
    </div>
{:else}
    <div style="text-align:center;padding:2rem;color:#3d3b52">Instance not found.</div>
{/if}

<style>
    .mb-label { font-size: 10px; color: #3d3b52; font-weight: 600; letter-spacing: 0.05em; }
    .detail-row {
        display: flex;
        justify-content: space-between;
        margin-top: 10px;
        font-size: 12px;
        color: #6b6882;
    }
    .detail-val { color: #e8e6f0; }
    .detail-val.italic { font-style: italic; text-align: right; max-width: 200px; }

    .source-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 0;
        border-bottom: 1px solid rgba(164, 126, 253, 0.05);
    }
    .source-name {
        flex: 1;
        font-size: 12px;
        color: #e8e6f0;
    }
    .source-tier {
        font-size: 8px;
        text-transform: uppercase;
        padding: 2px 6px;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
    }
    .source-tier.high { background: rgba(164, 126, 253, 0.2); color: var(--primary-p3); }
    .source-tier.medium { background: rgba(50, 79, 198, 0.2); color: #82aaff; }
    .source-tier.low { background: rgba(61, 59, 82, 0.2); color: #6b6882; }

    .source-link {
        font-size: 11px;
        color: #a47efd;
        text-decoration: none;
    }
    .source-link:hover { text-decoration: underline; }

    .comp-item {
        padding: 10px 0;
        border-bottom: 1px solid rgba(164, 126, 253, 0.05);
    }
    .comp-item:last-child { border-bottom: none; }
    .comp-main { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
    .comp-name { font-size: 13px; font-weight: 600; color: #e8e6f0; }
    .mini-pill { font-size: 8px; background: rgba(164, 126, 253, 0.1); color: var(--primary-p3); padding: 1px 4px; border-radius: 3px; text-transform: uppercase; font-weight: 700; }
    .comp-stats { display: flex; align-items: center; gap: 6px; font-size: 10px; color: #5a5672; font-family: 'JetBrains Mono', monospace; }
    .comp-stats .sep { color: #2c293d; }

    .stat-val.g { color: #4ade80 !important; }
    .stat-val.r { color: #f87171 !important; }
</style>
