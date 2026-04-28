<script lang="ts">
    import { onMount } from 'svelte';
    import { computePromptMetrics, getWeeklyBuckets } from '../lib/analytics_utils';
    import type { Instance, Model, Prompt } from '../types';

    interface Props {
        instances: Instance[];
        models: Model[];
        prompts: Prompt[];
    }
    let { instances, models, prompts }: Props = $props();

    // --- Filters ---
    let selectedRange = $state<'7d' | '30d' | '90d' | 'all'>('30d');
    let selectedModels = $state<string[]>([]);
    $effect(() => {
        if (selectedModels.length === 0 && models.length > 0) {
            selectedModels = models.map(m => m.id);
        }
    });

    let searchQuery = $state('');

    const filteredInstances = $derived(() => {
        const now = new Date();
        const cutoff: Record<string, number> = { '7d': 7, '30d': 30, '90d': 90 };
        let result = instances;

        if (selectedRange !== 'all') {
            const days = cutoff[selectedRange];
            const cutoffDate = new Date(now.getTime() - days * 86400000);
            result = result.filter(i => new Date(i.time_bucket || i.timeBucket) >= cutoffDate);
        }

        if (selectedModels.length < models.length) {
            result = result.filter(i => selectedModels.includes(i.modelId));
        }

        if (searchQuery) {
            const q = searchQuery.toLowerCase();
            result = result.filter(i => 
                (i.promptContent?.toLowerCase().includes(q) || i.promptId.toLowerCase().includes(q)) ||
                (i.modelName?.toLowerCase().includes(q)) ||
                (i.deckName?.toLowerCase().includes(q))
            );
        }

        return result;
    });

    function toggleModel(id: string) {
        if (selectedModels.includes(id)) {
            if (selectedModels.length > 1) selectedModels = selectedModels.filter(m => m !== id);
        } else {
            selectedModels = [...selectedModels, id];
        }
    }

    // --- KPI Summary ---
    const kpis = $derived(() => {
        const fi = filteredInstances();
        if (!fi.length) return null;

        const atg = fi.length;
        const gbm = fi.filter(i => i.metrics?.brand_mentioned).length;
        const gnbm = fi.filter(i => i.metrics?.narrative_mention).length;
        const oasr = gbm / atg;
        const oaair = gnbm / atg;

        const mentioned = fi.filter(i => i.metrics?.brand_mentioned && i.metrics?.brand_position != null);
        const amp = mentioned.length > 0
            ? mentioned.reduce((a, b) => a + (b.metrics?.brand_position || 0), 0) / mentioned.length
            : null;

        const modelCounts: Record<string, number> = {};
        selectedModels.forEach(mid => {
            const sub = fi.filter(i => i.modelId === mid);
            modelCounts[mid] = sub.length > 0
                ? sub.filter(i => i.metrics?.brand_mentioned).length / sub.length
                : 0;
        });
        const topModelId = Object.entries(modelCounts).sort((a, b) => b[1] - a[1])[0]?.[0];
        const topModel = models.find(m => m.id === topModelId)?.modelName ?? '—';

        // week-over-week OASR delta
        const weekly = getWeeklyBuckets(fi);
        const weekKeys = Object.keys(weekly).sort();
        let oasrDelta: number | null = null;
        if (weekKeys.length >= 2) {
            const prev = weekly[weekKeys[weekKeys.length - 2]];
            const curr = weekly[weekKeys[weekKeys.length - 1]];
            const prevRate = prev.filter((i: Instance) => i.metrics?.brand_mentioned).length / (prev.length || 1);
            const currRate = curr.filter((i: Instance) => i.metrics?.brand_mentioned).length / (curr.length || 1);
            oasrDelta = currRate - prevRate;
        }

        // Weak prompts — UASR < 0.3
        const weakPrompts = prompts.filter(p => {
            const sub = fi.filter(i => i.promptId === p.id);
            if (!sub.length) return false;
            return sub.filter(i => i.metrics?.brand_mentioned).length / sub.length < 0.3;
        }).length;

        return { oasr, oaair, amp, topModel, oasrDelta, atg, gbm, gnbm, weakPrompts };
    });

    // --- Insight Generator ---
    function getInsight(type: string, data: any): string {
        if (!data) return '';
        switch (type) {
            case 'hero':
                if (data.oasr < 0.2) return `Low overall visibility — brand appears in only ${(data.oasr * 100).toFixed(0)}% of responses. Focus on Tier 1 prompt diagnostics.`;
                if (data.oaair / data.oasr < 0.5) return `Mentions are mostly superficial — narrative inclusion is less than half of signal rate. Improve content depth.`;
                return `Visibility is healthy. Gap between OASR and OAAIR is ${((data.oasr - data.oaair) * 100).toFixed(0)}% — these are source-only mentions worth converting to narrative.`;
            case 'heatmap':
                return `Red cells indicate prompt-model combinations where brand visibility is low. Prioritise content for these specific combinations.`;
            case 'scatter':
                return `Bottom-right quadrant (high signal, low narrative) are quick wins — brand is mentioned but not featured. Improving these prompts has highest ROI.`;
            case 'amp':
                if (data.some((d: any) => d.val > 6)) return `Some prompts have AMP > 6 — brand is buried. Earlier mentions correlate with higher user engagement.`;
                return `Mention positions are healthy. Keep monitoring as competitors improve.`;
            case 'sov':
                return `C-SOV lower than S-SOV means competitors have better narrative quality despite fewer mentions. Focus on narrative depth.`;
            case 'mpr':
                return `Bubbles below position 3 with MPR > 1 are your strongest prompts. Large bubbles = crowded competitive space.`;
            case 'sar':
                return `SAR below 1 means competitors have better sentiment. Review what AI is saying about your brand in those prompts.`;
            case 'sa':
                return `Declining sentiment lines need immediate attention — AI may be picking up negative coverage or outdated information.`;
            case 'usds':
                return `Low-authority source stacks mean brand is cited by low-quality sites. PR and backlink strategy can shift this.`;
            default: return '';
        }
    }

    // --- CSV Export ---
    function downloadCSV() {
        const data = filteredInstances();
        if (!data.length) return;

        const headers = [
            'Instance ID', 'Time', 'Brand', 'Deck', 'Model', 'Region', 'Prompt', 'Brand Mentioned', 
            'Narrative Mention', 'Mention Position', 'Sentiment Score', 'Mention Intent', 
            'Source Diversity', 'Response'
        ];
        
        const csvRows = [
            headers.join(','),
            ...data.map(i => [
                i.id,
                new Date(i.time_bucket || i.timeBucket).toLocaleString(),
                `"${(i.brandName || '').replace(/"/g, '""')}"`,
                `"${(i.deckName || '').replace(/"/g, '""')}"`,
                `"${(i.modelName || '').replace(/"/g, '""')}"`,
                `"${(i.regionName || '').replace(/"/g, '""')}"`,
                `"${(i.promptContent || '').replace(/"/g, '""')}"`,
                i.metrics?.brand_mentioned ? 'Yes' : 'No',
                i.metrics?.narrative_mention ? 'Yes' : 'No',
                i.metrics?.brand_position ?? '-',
                i.metrics?.sentiment_score ?? '-',
                `"${(i.metrics?.mention_intent || '-').replace(/"/g, '""')}"`,
                i.metrics?.source_diversity ?? '-',
                `"${JSON.stringify(i.responseData).replace(/"/g, '""')}"`
            ].join(','))
        ];

        const csvString = csvRows.join('\n');
        const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `aivis_export_${new Date().toISOString().slice(0, 10)}.csv`);
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    // --- Chart Action ---
    function chartAction(node: HTMLElement, config: any) {
        // @ts-ignore
        const chart = echarts.init(node, 'dark', { renderer: 'canvas' });
        chart.setOption(config);
        const resize = () => chart.resize();
        window.addEventListener('resize', resize);
        return {
            update(newConfig: any) { chart.setOption(newConfig, true); },
            destroy() { window.removeEventListener('resize', resize); chart.dispose(); }
        };
    }

    // --- Derived Chart Data ---
    const metrics = $derived(() => {
        const fi = filteredInstances();
        if (!fi.length) return null;

        const weekly = getWeeklyBuckets(fi);
        const dates = Object.keys(weekly).sort();

        // 1. OASR + OAAIR
        const oasrLine = dates.map(d => {
            const b = weekly[d];
            return +(b.filter((i: Instance) => i.metrics?.brand_mentioned).length / (b.length || 1)).toFixed(3);
        });
        const oaairLine = dates.map(d => {
            const b = weekly[d];
            return +(b.filter((i: Instance) => i.metrics?.narrative_mention).length / (b.length || 1)).toFixed(3);
        });

        // 2. Heatmap
        const activeModels = models.filter(m => selectedModels.includes(m.id));
        const promptNodes = prompts.map(p => p.content.slice(0, 35) + (p.content.length > 35 ? '…' : ''));
        const modelNodes = activeModels.map(m => m.modelName);
        const heatmapData = prompts.flatMap((p, pi) =>
            activeModels.map((m, mi) => {
                const sub = fi.filter(i => i.promptId === p.id && i.modelId === m.id);
                const score = sub.length > 0 ? +(sub.filter(i => i.metrics?.brand_mentioned).length / sub.length).toFixed(2) : 0;
                return [mi, pi, score];
            })
        );

        // 3. Scatter
        const scatterData = prompts.map(p => {
            const sub = fi.filter(i => i.promptId === p.id);
            const m = computePromptMetrics(sub);
            return [+m.uasr.toFixed(3), +m.uaair.toFixed(3), p.content.slice(0, 50), sub.length];
        });

        // 4. AMP Bar
        const ampData = prompts.map(p => {
            const sub = fi.filter(i => i.promptId === p.id);
            const m = computePromptMetrics(sub);
            return { prompt: p.content.slice(0, 20), full: p.content, val: +(m.amp || 10).toFixed(1) };
        }).sort((a, b) => a.val - b.val);

        // 5. SOV
        const allComps = [...new Set(fi.flatMap(i => (i.metrics?.competitors_mentioned || []).map((c: any) => c.name)))].slice(0, 4);
        const entities = ['Your Brand', ...allComps];
        const totalGbm = fi.filter(i => i.metrics?.brand_mentioned).length +
            fi.flatMap(i => i.metrics?.competitors_mentioned || []).length;
        const totalGnbm = fi.filter(i => i.metrics?.narrative_mention).length +
            fi.flatMap(i => i.metrics?.competitors_mentioned || []).filter((c: any) => c.narrative).length;

        const s_sov = entities.map(name => {
            const count = name === 'Your Brand'
                ? fi.filter(i => i.metrics?.brand_mentioned).length
                : fi.filter(i => (i.metrics?.competitors_mentioned || []).some((c: any) => c.name === name)).length;
            return +((count / (totalGbm || 1)) * 100).toFixed(1);
        });
        const c_sov = entities.map(name => {
            const count = name === 'Your Brand'
                ? fi.filter(i => i.metrics?.narrative_mention).length
                : fi.filter(i => (i.metrics?.competitors_mentioned || []).some((c: any) => c.name === name && c.narrative)).length;
            return +((count / (totalGnbm || 1)) * 100).toFixed(1);
        });

        // 6. MPR Bubble
        const bubbleData = prompts.map(p => {
            const pin = fi.filter(i => i.promptId === p.id);
            const brandAmp = computePromptMetrics(pin).amp || 10;
            const compPositions = pin.flatMap(i => i.metrics?.competitors_mentioned || []).map((c: any) => c.position || 10);
            const avgCompAmp = compPositions.length > 0
                ? compPositions.reduce((a: number, b: number) => a + b, 0) / compPositions.length
                : 10;
            const mpr = +(avgCompAmp / brandAmp).toFixed(2);
            const compCount = [...new Set(pin.flatMap(i => (i.metrics?.competitors_mentioned || []).map((c: any) => c.name)))].length;
            return { label: p.content.slice(0, 18), brandAmp: +brandAmp.toFixed(1), compCount, mpr };
        });

        // 7. Radar
        const radarSeries = activeModels.map(m => {
            const sub = fi.filter(i => i.modelId === m.id);
            const met = computePromptMetrics(sub);
            const ampScore = Math.max(0, 1 - ((met.amp || 10) / 10));
            const sentNorm = ((met.sentimentAuthority || 0) + 1) / 2;
            return {
                name: m.modelName,
                value: [
                    +met.uasr.toFixed(3),
                    +met.uaair.toFixed(3),
                    +ampScore.toFixed(3),
                    +sentNorm.toFixed(3),
                    +(met.sourceDiversity || 0).toFixed(3)
                ]
            };
        });

        // 8. SAR
        const sarLine = dates.map(d => {
            const buck = weekly[d];
            const brandSa = computePromptMetrics(buck).sentimentAuthority || 0.01;
            const compScores = buck.flatMap((i: Instance) => i.metrics?.competitors_mentioned || []).map((c: any) => c.sentiment_score || 0);
            const compAvg = compScores.length > 0 ? compScores.reduce((a: number, b: number) => a + b, 0) / compScores.length : 0.01;
            return +(brandSa / (compAvg || 0.01)).toFixed(2);
        });

        // 9. USDS
        const usdsData = prompts.slice(0, 10).map(p => {
            const pin = fi.filter(i => i.promptId === p.id);
            const srcs = pin.flatMap(i => i.metrics?.mention_sources || []);
            const high = srcs.filter((s: any) => s.authority_tier === 'high').length;
            const med = srcs.filter((s: any) => s.authority_tier === 'medium').length;
            const low = srcs.filter((s: any) => s.authority_tier === 'low').length;
            const total = (high + med + low) || 1;
            const uniqueSrcs = new Set(srcs.map((s: any) => s.source)).size;
            const usds = +(uniqueSrcs / (srcs.length || 1)).toFixed(2);
            return {
                name: p.content.slice(0, 18),
                full: p.content,
                high: +((high / total) * 100).toFixed(1),
                med: +((med / total) * 100).toFixed(1),
                low: +((low / total) * 100).toFixed(1),
                usds
            };
        });

        // 10. SA per prompt over time
        const promptSaData = prompts.slice(0, 5).map(p => {
            const pWeekly = getWeeklyBuckets(fi.filter(i => i.promptId === p.id));
            return {
                name: p.content.slice(0, 18),
                data: dates.map(d => {
                    const buck = pWeekly[d] || [];
                    const narr = buck.filter((i: Instance) => i.metrics?.narrative_mention);
                    if (!narr.length) return null;
                    return +(narr.reduce((a: number, b: Instance) => a + (b.metrics?.sentiment_score || 0), 0) / narr.length).toFixed(2);
                })
            };
        });

        return { dates, oasrLine, oaairLine, heatmapData, modelNodes, promptNodes, scatterData, ampData, entities, s_sov, c_sov, bubbleData, radarSeries, sarLine, usdsData, promptSaData };
    });

    // --- Empty state check ---
    const hasData = $derived(() => filteredInstances().length > 0);

    // ---- Chart Options ----

    const heroOpt = $derived(() => {
        const m = metrics();
        if (!m) return {};
        return {
            backgroundColor: 'transparent',
            tooltip: { trigger: 'axis', backgroundColor: '#1a1625', borderColor: '#2d2540', textStyle: { color: '#c4b5fd', fontSize: 11 } },
            legend: { data: ['OASR — Signal Rate', 'OAAIR — Narrative Inclusion'], textStyle: { color: '#7c6fa0', fontSize: 11 }, top: 0 },
            grid: { left: '50px', right: '30px', bottom: '40px', top: '44px', containLabel: true },
            xAxis: { type: 'category', data: m.dates, boundaryGap: false, axisLabel: { fontSize: 10, color: '#4a4060' }, axisLine: { lineStyle: { color: '#2c2540' } }, splitLine: { show: false } },
            yAxis: { type: 'value', min: 0, max: 1, axisLabel: { fontSize: 10, color: '#4a4060', formatter: (v: number) => (v * 100).toFixed(0) + '%' }, splitLine: { lineStyle: { color: 'rgba(124,92,252,0.06)' } } },
            series: [
                {
                    name: 'OASR — Signal Rate',
                    type: 'line', data: m.oasrLine, smooth: true,
                    lineStyle: { width: 2.5, color: '#7c5cfc' },
                    symbol: 'circle', symbolSize: 5,
                    areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(124,92,252,0.18)' }, { offset: 1, color: 'rgba(124,92,252,0)' }] } }
                },
                {
                    name: 'OAAIR — Narrative Inclusion',
                    type: 'line', data: m.oaairLine, smooth: true,
                    lineStyle: { color: '#a47efd', type: 'dashed', width: 2 },
                    symbol: 'circle', symbolSize: 4,
                    areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(164,126,253,0.08)' }, { offset: 1, color: 'rgba(164,126,253,0)' }] } }
                }
            ]
        };
    });

    const heatmapOpt = $derived(() => {
        const m = metrics();
        if (!m) return {};
        return {
            backgroundColor: 'transparent',
            tooltip: {
                position: 'top',
                backgroundColor: '#1a1625',
                borderColor: '#2d2540',
                formatter: (p: any) => {
                    const prompt = m.promptNodes[p.value[1]];
                    const model = m.modelNodes[p.value[0]];
                    return `<div style="font-size:11px;color:#c4b5fd"><b>${model}</b><br/>${prompt}<br/>UASR: <b>${(p.value[2] * 100).toFixed(0)}%</b></div>`;
                }
            },
            grid: { left: '10px', right: '60px', bottom: '60px', top: '10px', containLabel: true },
            xAxis: { type: 'category', data: m.modelNodes, axisLabel: { fontSize: 10, color: '#7c6fa0', rotate: 30 }, axisLine: { lineStyle: { color: '#2c2540' } } },
            yAxis: { type: 'category', data: m.promptNodes, axisLabel: { fontSize: 10, color: '#7c6fa0', width: 140, overflow: 'truncate' } },
            visualMap: { min: 0, max: 1, orient: 'horizontal', left: 'center', bottom: 0, textStyle: { fontSize: 9, color: '#7c6fa0' }, inRange: { color: ['#3d1515', '#eb5757', '#e2b93b', '#27ae60'] } },
            series: [{ name: 'UASR', type: 'heatmap', data: m.heatmapData, label: { show: true, fontSize: 10, color: '#fff', formatter: (p: any) => (p.value[2] * 100).toFixed(0) + '%' }, emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(124,92,252,0.5)' } } }]
        };
    });

    const radarOpt = $derived(() => {
        const m = metrics();
        if (!m) return {};
        const colors = ['#7c5cfc', '#27ae60', '#e2b93b', '#eb5757'];
        return {
            backgroundColor: 'transparent',
            legend: { bottom: 0, textStyle: { color: '#7c6fa0', fontSize: 10 }, itemWidth: 12, itemHeight: 8 },
            tooltip: { backgroundColor: '#1a1625', borderColor: '#2d2540', textStyle: { color: '#c4b5fd', fontSize: 11 } },
            radar: {
                radius: '62%', center: ['50%', '48%'],
                indicator: [
                    { name: 'UASR', max: 1 },
                    { name: 'UAAIR', max: 1 },
                    { name: 'Position', max: 1 },
                    { name: 'Sentiment', max: 1 },
                    { name: 'Sources', max: 1 }
                ],
                axisName: { fontSize: 10, color: '#7c6fa0' },
                splitLine: { lineStyle: { color: 'rgba(124,92,252,0.1)' } },
                splitArea: { areaStyle: { color: ['rgba(124,92,252,0.02)', 'rgba(124,92,252,0.04)'] } }
            },
            series: [{
                type: 'radar',
                data: m.radarSeries.map((s, i) => ({
                    ...s,
                    lineStyle: { color: colors[i % colors.length], width: 2 },
                    itemStyle: { color: colors[i % colors.length] },
                    areaStyle: { color: colors[i % colors.length], opacity: 0.07 }
                })),
                symbol: 'circle', symbolSize: 4
            }]
        };
    });

    const scatterOpt = $derived(() => {
        const m = metrics();
        if (!m) return {};
        return {
            backgroundColor: 'transparent',
            tooltip: {
                backgroundColor: '#1a1625', borderColor: '#2d2540',
                formatter: (p: any) => `<div style="font-size:11px;color:#c4b5fd">${p.data[2]}<br/>UASR: <b>${(p.data[0]*100).toFixed(0)}%</b> · UAAIR: <b>${(p.data[1]*100).toFixed(0)}%</b><br/>Runs: ${p.data[3]}</div>`
            },
            grid: { left: '50px', right: '30px', bottom: '50px', top: '30px', containLabel: true },
            xAxis: { name: 'UASR →', nameTextStyle: { fontSize: 10, color: '#4a4060' }, min: 0, max: 1, axisLabel: { fontSize: 10, color: '#4a4060', formatter: (v: number) => (v*100).toFixed(0)+'%' }, splitLine: { lineStyle: { color: 'rgba(124,92,252,0.06)' } } },
            yAxis: { name: 'UAAIR →', nameTextStyle: { fontSize: 10, color: '#4a4060' }, min: 0, max: 1, axisLabel: { fontSize: 10, color: '#4a4060', formatter: (v: number) => (v*100).toFixed(0)+'%' }, splitLine: { lineStyle: { color: 'rgba(124,92,252,0.06)' } } },
            series: [{
                type: 'scatter',
                data: m.scatterData,
                symbolSize: (d: any) => Math.max(10, Math.sqrt(d[3]) * 8),
                itemStyle: { color: (p: any) => {
                    const [x, y] = p.data;
                    if (x >= 0.5 && y >= 0.5) return '#27ae60';
                    if (x < 0.5 && y >= 0.5) return '#7c5cfc';
                    if (x >= 0.5 && y < 0.5) return '#e2b93b';
                    return '#eb5757';
                }, opacity: 0.85 },
                markLine: {
                    silent: true,
                    symbol: 'none',
                    lineStyle: { type: 'dashed', color: 'rgba(124,92,252,0.2)', width: 1 },
                    label: { show: false },
                    data: [{ xAxis: 0.5 }, { yAxis: 0.5 }]
                },
                markArea: {
                    silent: true,
                    data: [
                        [{ coord: [0.5, 0.5], itemStyle: { color: 'rgba(39,174,96,0.04)' }, label: { show: true, position: 'insideTopRight', formatter: 'Star Prompts ★', fontSize: 10, color: 'rgba(39,174,96,0.5)' } }, { coord: [1, 1] }],
                        [{ coord: [0, 0.5], itemStyle: { color: 'rgba(124,92,252,0.03)' }, label: { show: true, position: 'insideTopLeft', formatter: 'Niche Quality', fontSize: 10, color: 'rgba(124,92,252,0.4)' } }, { coord: [0.5, 1] }],
                        [{ coord: [0.5, 0], itemStyle: { color: 'rgba(226,185,59,0.03)' }, label: { show: true, position: 'insideBottomRight', formatter: 'Weak Narrative', fontSize: 10, color: 'rgba(226,185,59,0.4)' } }, { coord: [1, 0.5] }],
                        [{ coord: [0, 0], itemStyle: { color: 'rgba(235,87,87,0.04)' }, label: { show: true, position: 'insideBottomLeft', formatter: 'Dead Prompts', fontSize: 10, color: 'rgba(235,87,87,0.4)' } }, { coord: [0.5, 0.5] }]
                    ]
                }
            }]
        };
    });

    const ampOpt = $derived(() => {
        const m = metrics();
        if (!m) return {};
        return {
            backgroundColor: 'transparent',
            tooltip: {
                backgroundColor: '#1a1625', borderColor: '#2d2540',
                formatter: (p: any) => `<div style="font-size:11px;color:#c4b5fd">${m.ampData[p.dataIndex]?.full || p.name}<br/>AMP: <b>${p.value}</b> (${p.value < 3 ? 'Excellent' : p.value < 6 ? 'Average' : 'Buried'})</div>`
            },
            grid: { left: '10px', right: '40px', bottom: '10px', top: '10px', containLabel: true },
            xAxis: { type: 'value', max: 12, axisLabel: { fontSize: 10, color: '#4a4060' }, splitLine: { lineStyle: { color: 'rgba(124,92,252,0.06)' } } },
            yAxis: { type: 'category', data: m.ampData.map(d => d.prompt), axisLabel: { fontSize: 10, color: '#7c6fa0', width: 100, overflow: 'truncate' } },
            series: [{
                type: 'bar',
                data: m.ampData.map(d => d.val),
                barMaxWidth: 28,
                itemStyle: { color: (p: any) => p.data < 3 ? '#27ae60' : p.data < 6 ? '#e2b93b' : '#eb5757', borderRadius: [0, 4, 4, 0] },
                label: { show: true, position: 'right', fontSize: 10, color: '#7c6fa0', formatter: (p: any) => `${p.value}` }
            }]
        };
    });

    const sovOpt = $derived(() => {
        const m = metrics();
        if (!m) return {};
        return {
            backgroundColor: 'transparent',
            tooltip: {
                trigger: 'axis', backgroundColor: '#1a1625', borderColor: '#2d2540',
                textStyle: { color: '#c4b5fd', fontSize: 11 },
                formatter: (params: any[]) => `<div style="font-size:11px;color:#c4b5fd"><b>${params[0].axisValue}</b><br/>${params.map(p => `${p.marker} ${p.seriesName}: <b>${p.value}%</b>`).join('<br/>')}</div>`
            },
            legend: { top: 0, textStyle: { color: '#7c6fa0', fontSize: 10 } },
            grid: { left: '10px', right: '20px', bottom: '50px', top: '36px', containLabel: true },
            xAxis: { type: 'category', data: m.entities, axisLabel: { fontSize: 10, color: '#7c6fa0', rotate: 20, interval: 0 }, axisLine: { lineStyle: { color: '#2c2540' } } },
            yAxis: { type: 'value', axisLabel: { fontSize: 10, color: '#4a4060', formatter: (v: number) => v + '%' }, splitLine: { lineStyle: { color: 'rgba(124,92,252,0.06)' } } },
            series: [
                { name: 'S-SOV', type: 'bar', data: m.s_sov, itemStyle: { color: '#7c5cfc', borderRadius: [4, 4, 0, 0] }, barGap: '10%' },
                { name: 'C-SOV', type: 'bar', data: m.c_sov, itemStyle: { color: '#a47efd', opacity: 0.7, borderRadius: [4, 4, 0, 0] } }
            ]
        };
    });

    const bubbleOpt = $derived(() => {
        const m = metrics();
        if (!m) return {};
        return {
            backgroundColor: 'transparent',
            tooltip: {
                backgroundColor: '#1a1625', borderColor: '#2d2540',
                formatter: (p: any) => {
                    const d = m.bubbleData[p.dataIndex];
                    if (!d) return '';
                    return `<div style="font-size:11px;color:#c4b5fd"><b>${d.label}</b><br/>Brand AMP: <b>${d.brandAmp}</b><br/>Competitors: ${d.compCount}<br/>MPR: <b>${d.mpr}</b> ${d.mpr > 1 ? '✓ ahead' : '✗ behind'}</div>`;
                }
            },
            grid: { left: '40px', right: '30px', bottom: '60px', top: '10px', containLabel: true },
            xAxis: { type: 'category', data: m.bubbleData.map(d => d.label), axisLabel: { fontSize: 9, color: '#7c6fa0', rotate: 25, interval: 0 }, axisLine: { lineStyle: { color: '#2c2540' } } },
            yAxis: { name: '← Better', nameTextStyle: { fontSize: 9, color: '#4a4060' }, inverse: true, min: 1, max: 12, axisLabel: { fontSize: 10, color: '#4a4060' }, splitLine: { lineStyle: { color: 'rgba(124,92,252,0.06)' } } },
            series: [{
                type: 'scatter',
                data: m.bubbleData.map(d => [d.label, d.brandAmp, d.compCount]),
                symbolSize: (d: any) => Math.max(14, d[2] * 10),
                itemStyle: { color: (p: any) => m.bubbleData[p.dataIndex]?.mpr > 1 ? '#27ae60' : m.bubbleData[p.dataIndex]?.mpr > 0.7 ? '#e2b93b' : '#eb5757', opacity: 0.85 }
            }]
        };
    });

    const sarOpt = $derived(() => {
        const m = metrics();
        if (!m) return {};
        return {
            backgroundColor: 'transparent',
            tooltip: {
                trigger: 'axis', backgroundColor: '#1a1625', borderColor: '#2d2540',
                formatter: (params: any[]) => `<div style="font-size:11px;color:#c4b5fd">${params[0].axisValue}<br/>SAR: <b>${params[0].value}</b> ${params[0].value >= 1 ? '↑ above competitors' : '↓ below competitors'}</div>`
            },
            grid: { left: '50px', right: '30px', bottom: '40px', top: '20px', containLabel: true },
            xAxis: { type: 'category', data: m.dates, axisLabel: { fontSize: 10, color: '#4a4060' }, axisLine: { lineStyle: { color: '#2c2540' } } },
            yAxis: { name: 'SAR', nameTextStyle: { fontSize: 9, color: '#4a4060' }, axisLabel: { fontSize: 10, color: '#4a4060' }, splitLine: { lineStyle: { color: 'rgba(124,92,252,0.06)' } } },
            series: [{
                type: 'line', data: m.sarLine, smooth: true,
                lineStyle: { color: '#7c5cfc', width: 2 },
                symbol: 'circle', symbolSize: 5,
                areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(124,92,252,0.15)' }, { offset: 1, color: 'rgba(124,92,252,0)' }] } },
                markLine: {
                    silent: true, symbol: 'none',
                    data: [{ yAxis: 1, label: { formatter: 'Parity', fontSize: 9, color: '#4a4060' }, lineStyle: { color: '#3d3b52', type: 'dashed' } }]
                }
            }]
        };
    });

    const saOpt = $derived(() => {
        const m = metrics();
        if (!m) return {};
        const colors = ['#7c5cfc', '#27ae60', '#e2b93b', '#eb5757', '#a47efd'];
        return {
            backgroundColor: 'transparent',
            tooltip: { trigger: 'axis', backgroundColor: '#1a1625', borderColor: '#2d2540', textStyle: { color: '#c4b5fd', fontSize: 11 } },
            legend: { data: m.promptSaData.map(d => d.name), bottom: 0, textStyle: { color: '#7c6fa0', fontSize: 9 }, itemWidth: 12, itemHeight: 8 },
            grid: { left: '50px', right: '20px', bottom: '70px', top: '10px', containLabel: true },
            xAxis: { type: 'category', data: m.dates, axisLabel: { fontSize: 10, color: '#4a4060' }, axisLine: { lineStyle: { color: '#2c2540' } } },
            yAxis: { min: -1, max: 1, axisLabel: { fontSize: 10, color: '#4a4060' }, splitLine: { lineStyle: { color: 'rgba(124,92,252,0.06)' } } },
            series: m.promptSaData.map((d, i) => ({
                name: d.name, type: 'line', data: d.data, smooth: true,
                lineStyle: { color: colors[i % colors.length], width: 2 },
                symbol: 'circle', symbolSize: 4,
                connectNulls: false,
                markLine: { silent: true, symbol: 'none', data: [{ yAxis: 0, lineStyle: { color: '#3d3b52', type: 'dashed' }, label: { show: false } }] }
            }))
        };
    });

    const usdsOpt = $derived(() => {
        const m = metrics();
        if (!m) return {};
        return {
            backgroundColor: 'transparent',
            tooltip: {
                trigger: 'axis', axisPointer: { type: 'shadow' },
                backgroundColor: '#1a1625', borderColor: '#2d2540',
                formatter: (params: any[]) => {
                    const idx = params[0].dataIndex;
                    const d = m.usdsData[idx];
                    return `<div style="font-size:11px;color:#c4b5fd"><b>${d.full}</b><br/>USDS: <b>${d.usds}</b><br/>${params.map(p => `${p.marker} ${p.seriesName}: <b>${p.value}%</b>`).join('<br/>')}</div>`;
                }
            },
            legend: { top: 0, textStyle: { color: '#7c6fa0', fontSize: 10 } },
            grid: { left: '10px', right: '30px', bottom: '60px', top: '36px', containLabel: true },
            xAxis: { type: 'category', data: m.usdsData.map(d => d.name), axisLabel: { fontSize: 10, color: '#7c6fa0', rotate: 25, interval: 0 }, axisLine: { lineStyle: { color: '#2c2540' } } },
            yAxis: { max: 100, axisLabel: { fontSize: 10, color: '#4a4060', formatter: (v: number) => v + '%' }, splitLine: { lineStyle: { color: 'rgba(124,92,252,0.06)' } } },
            series: [
                { name: 'High Authority', type: 'bar', stack: 'a', data: m.usdsData.map(d => d.high), itemStyle: { color: '#27ae60' } },
                { name: 'Medium', type: 'bar', stack: 'a', data: m.usdsData.map(d => d.med), itemStyle: { color: '#e2b93b' } },
                { name: 'Low', type: 'bar', stack: 'a', data: m.usdsData.map(d => d.low), itemStyle: { color: '#eb5757', borderRadius: [4, 4, 0, 0] } }
            ]
        };
    });
</script>

<!-- Filters Bar -->
<div class="filter-bar">
    <div class="filter-group">
        <span class="filter-label">Period</span>
        {#each (['7d', '30d', '90d', 'all'] as const) as range}
            <button
                class="filter-btn"
                class:active={selectedRange === range}
                onclick={() => selectedRange = range}
            >
                {range === 'all' ? 'All time' : range === '7d' ? '7 days' : range === '30d' ? '30 days' : '90 days'}
            </button>
        {/each}
    </div>
    <div class="filter-group">
        <span class="filter-label">Models</span>
        {#each models as model}
            <button
                class="filter-btn model-btn"
                class:active={selectedModels.includes(model.id)}
                onclick={() => toggleModel(model.id)}
            >
                {model.modelName}
            </button>
        {/each}
    </div>
    <div class="filter-group search-group">
        <div class="search-input-wrap">
            <span class="search-icon">⌕</span>
            <input 
                type="text" 
                placeholder="Search results..." 
                bind:value={searchQuery}
                class="search-input"
            />
        </div>
    </div>
    <div class="filter-group ml-auto">
        <button class="download-btn" onclick={downloadCSV} disabled={!hasData()}>
            <span class="btn-icon">↓</span>
            Download CSV
        </button>
    </div>
</div>

<!-- KPI Summary Row -->
{#if kpis()}
    {@const k = kpis()!}
    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-label">Overall Signal Rate</div>
            <div class="kpi-value">{(k.oasr * 100).toFixed(1)}%</div>
            <div class="kpi-sub">
                {#if k.oasrDelta !== null}
                    <span class:up={k.oasrDelta >= 0} class:down={k.oasrDelta < 0}>
                        {k.oasrDelta >= 0 ? '↑' : '↓'} {Math.abs(k.oasrDelta * 100).toFixed(1)}% WoW
                    </span>
                {:else}
                    OASR · {k.gbm}/{k.atg} runs
                {/if}
            </div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Narrative Inclusion</div>
            <div class="kpi-value">{(k.oaair * 100).toFixed(1)}%</div>
            <div class="kpi-sub">OAAIR · {k.gnbm}/{k.atg} runs</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Avg Mention Position</div>
            <div class="kpi-value" class:good={k.amp !== null && k.amp < 3} class:warn={k.amp !== null && k.amp >= 3 && k.amp < 6} class:bad={k.amp !== null && k.amp >= 6}>
                {k.amp !== null ? k.amp.toFixed(1) : '—'}
            </div>
            <div class="kpi-sub">AMP · lower is better</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Strongest Model</div>
            <div class="kpi-value model-val">{k.topModel}</div>
            <div class="kpi-sub">by UASR signal rate</div>
        </div>
        <div class="kpi-card" class:alert={k.weakPrompts > 0}>
            <div class="kpi-label">Weak Prompts</div>
            <div class="kpi-value" class:bad={k.weakPrompts > 0} class:good={k.weakPrompts === 0}>
                {k.weakPrompts}
            </div>
            <div class="kpi-sub">UASR below 30%</div>
        </div>
    </div>
{/if}

<!-- Empty State -->
{#if !hasData()}
    <div class="empty-state">
        <div class="empty-icon">◎</div>
        <div class="empty-title">No data for this filter</div>
        <div class="empty-sub">Try a wider date range or enable more models</div>
    </div>
{:else}
    <div class="analytics-dash">

        <!-- Hero -->
        <div class="full-row dash-card hero-card">
            <div class="card-head">
                <div>
                    <div class="chart-title">Portfolio Visibility Trend</div>
                    <div class="chart-formula">OASR = GBM / ATG &nbsp;·&nbsp; OAAIR = GNBM / ATG</div>
                </div>
            </div>
            <div class="chart-container" style="height: 320px" use:chartAction={heroOpt()}></div>
            <div class="insight">{getInsight('hero', kpis())}</div>
        </div>

        <!-- Row 2 -->
        <div class="split-row">
            <div class="dash-card flex-1-5">
                <div class="card-head">
                    <div>
                        <div class="chart-title">Signal Rate Heatmap</div>
                        <div class="chart-formula">UASR = GBM(prompt, model) / ATG(prompt, model)</div>
                    </div>
                </div>
                <div class="chart-container" style="height: 420px" use:chartAction={heatmapOpt()}></div>
                <div class="insight">{getInsight('heatmap', null)}</div>
            </div>
            <div class="dash-card flex-1">
                <div class="card-head">
                    <div>
                        <div class="chart-title">Model Performance Radar</div>
                        <div class="chart-formula">Normalised: UASR · UAAIR · Position · Sentiment · Sources</div>
                    </div>
                </div>
                <div class="chart-container" style="height: 420px" use:chartAction={radarOpt()}></div>
            </div>
        </div>

        <!-- Row 3 -->
        <div class="split-row">
            <div class="dash-card">
                <div class="card-head">
                    <div>
                        <div class="chart-title">Efficiency Quadrant Scan</div>
                        <div class="chart-formula">UASR (x) vs UAAIR (y) per prompt</div>
                    </div>
                </div>
                <div class="chart-container" style="height: 380px" use:chartAction={scatterOpt()}></div>
                <div class="insight">{getInsight('scatter', null)}</div>
            </div>
            <div class="dash-card">
                <div class="card-head">
                    <div>
                        <div class="chart-title">Average Mention Position</div>
                        <div class="chart-formula">AMP = Σ brand_position / GBM &nbsp;·&nbsp; lower = better</div>
                    </div>
                </div>
                <div class="chart-container" style="height: 380px" use:chartAction={ampOpt()}></div>
                <div class="insight">{getInsight('amp', metrics()?.ampData)}</div>
            </div>
        </div>

        <!-- Row 4 -->
        <div class="split-row">
            <div class="dash-card">
                <div class="card-head">
                    <div>
                        <div class="chart-title">Competitive Share of Voice</div>
                        <div class="chart-formula">S-SOV = GBM(brand) / GBM(all) &nbsp;·&nbsp; C-SOV = GNBM(brand) / GNBM(all)</div>
                    </div>
                </div>
                <div class="chart-container" style="height: 380px" use:chartAction={sovOpt()}></div>
                <div class="insight">{getInsight('sov', null)}</div>
            </div>
            <div class="dash-card">
                <div class="card-head">
                    <div>
                        <div class="chart-title">Mention Position Ratio</div>
                        <div class="chart-formula">MPR = AMP(competitors avg) / AMP(brand) &nbsp;·&nbsp; >1 = ahead</div>
                    </div>
                </div>
                <div class="chart-container" style="height: 380px" use:chartAction={bubbleOpt()}></div>
                <div class="insight">{getInsight('mpr', null)}</div>
            </div>
        </div>

        <!-- Row 5 -->
        <div class="split-row">
            <div class="dash-card">
                <div class="card-head">
                    <div>
                        <div class="chart-title">Sentiment Authority Ratio</div>
                        <div class="chart-formula">SAR = SA(brand) / SA(competitors avg) &nbsp;·&nbsp; >1 = winning</div>
                    </div>
                </div>
                <div class="chart-container" style="height: 380px" use:chartAction={sarOpt()}></div>
                <div class="insight">{getInsight('sar', null)}</div>
            </div>
            <div class="dash-card">
                <div class="card-head">
                    <div>
                        <div class="chart-title">Prompt Sentiment Trend</div>
                        <div class="chart-formula">SA = Σ sentiment(narrative mentions) / GNBM</div>
                    </div>
                </div>
                <div class="chart-container" style="height: 380px" use:chartAction={saOpt()}></div>
                <div class="insight">{getInsight('sa', null)}</div>
            </div>
        </div>

        <!-- Row 6 -->
        <div class="full-row dash-card">
            <div class="card-head">
                <div>
                    <div class="chart-title">Source Diversity by Prompt</div>
                    <div class="chart-formula">USDS = Unique Authoritative Sources / Total Sources &nbsp;·&nbsp; shown as % authority tier</div>
                </div>
            </div>
            <div class="chart-container" style="height: 360px" use:chartAction={usdsOpt()}></div>
            <div class="insight">{getInsight('usds', null)}</div>
        </div>

    </div>
{/if}

<style>
    /* --- Filter Bar --- */
    .filter-bar {
        display: flex;
        gap: 24px;
        align-items: center;
        flex-wrap: wrap;
        padding: 14px 20px;
        background: rgba(16, 14, 27, 0.6);
        border: 1px solid rgba(124, 92, 252, 0.08);
        border-radius: 12px;
        margin-bottom: 20px;
    }
    .filter-group { display: flex; align-items: center; gap: 8px; }
    .filter-label { font-size: 11px; color: #4a4060; text-transform: uppercase; letter-spacing: 0.08em; margin-right: 4px; }
    .filter-btn {
        padding: 5px 12px;
        border-radius: 6px;
        border: 1px solid rgba(124, 92, 252, 0.15);
        background: transparent;
        color: #7c6fa0;
        font-size: 11px;
        cursor: pointer;
        transition: all 0.15s;
    }
    .filter-btn:hover { border-color: rgba(124, 92, 252, 0.4); color: #a47efd; }
    .filter-btn.active { background: rgba(124, 92, 252, 0.15); border-color: rgba(124, 92, 252, 0.4); color: #c4b5fd; }

    .search-group { flex: 1; min-width: 200px; }
    .search-input-wrap {
        position: relative;
        width: 100%;
    }
    .search-icon {
        position: absolute;
        left: 10px;
        top: 50%;
        transform: translateY(-50%);
        color: #4a4060;
        font-size: 14px;
        pointer-events: none;
    }
    .search-input {
        width: 100%;
        background: rgba(13, 12, 22, 0.8);
        border: 1px solid rgba(124, 92, 252, 0.15);
        border-radius: 6px;
        padding: 5px 12px 5px 32px;
        color: #c4b5fd;
        font-size: 11px;
        outline: none;
        transition: border-color 0.15s;
    }
    .search-input:focus {
        border-color: rgba(124, 92, 252, 0.5);
        background: rgba(13, 12, 22, 1);
    }
    .search-input::placeholder { color: #3d3455; }

    .ml-auto { margin-left: auto; }
    .download-btn {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 5px 14px;
        background: rgba(124, 92, 252, 0.1);
        border: 1px solid rgba(124, 92, 252, 0.2);
        border-radius: 6px;
        color: #a47efd;
        font-size: 11px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
    }
    .download-btn:hover:not(:disabled) {
        background: rgba(124, 92, 252, 0.2);
        border-color: rgba(124, 92, 252, 0.4);
        color: #c4b5fd;
        transform: translateY(-1px);
    }
    .download-btn:disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }
    .btn-icon { font-size: 14px; font-weight: 700; line-height: 1; margin-top: -2px; }

    /* --- KPI Row --- */
    .kpi-row {
        display: flex;
        gap: 16px;
        margin-bottom: 20px;
        flex-wrap: wrap;
    }
    .kpi-card {
        flex: 1;
        min-width: 140px;
        background: rgba(16, 14, 27, 0.6);
        border: 1px solid rgba(124, 92, 252, 0.08);
        border-radius: 12px;
        padding: 16px 20px;
        transition: border-color 0.2s;
    }
    .kpi-card:hover { border-color: rgba(124, 92, 252, 0.25); }
    .kpi-card.alert { border-color: rgba(235, 87, 87, 0.25); }
    .kpi-label { font-size: 10px; color: #4a4060; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; }
    .kpi-value { font-size: 28px; font-weight: 600; color: #c4b5fd; line-height: 1; margin-bottom: 6px; }
    .kpi-value.good { color: #27ae60; }
    .kpi-value.warn { color: #e2b93b; }
    .kpi-value.bad  { color: #eb5757; }
    .kpi-value.model-val { font-size: 18px; padding-top: 4px; }
    .kpi-sub { font-size: 11px; color: #4a4060; }
    .kpi-sub .up   { color: #27ae60; }
    .kpi-sub .down { color: #eb5757; }

    /* --- Dashboard Layout --- */
    .analytics-dash { display: flex; flex-direction: column; gap: 20px; padding-bottom: 40px; }
    .dash-card {
        background: rgba(16, 14, 27, 0.5);
        border: 1px solid rgba(124, 92, 252, 0.08);
        padding: 24px;
        border-radius: 16px;
        min-width: 0;
        transition: border-color 0.2s;
    }
    .dash-card:hover { border-color: rgba(124, 92, 252, 0.18); }
    .hero-card { border-color: rgba(124, 92, 252, 0.14); }

    /* --- Card Header --- */
    .card-head { margin-bottom: 20px; padding-bottom: 14px; border-bottom: 1px solid rgba(124, 92, 252, 0.06); }
    .chart-title { font-size: 13px; font-weight: 500; color: #a47efd; letter-spacing: 0.02em; margin-bottom: 4px; }
    .chart-formula { font-size: 10px; color: #3d3455; font-family: 'SF Mono', 'Fira Code', monospace; }

    /* --- Insight --- */
    .insight {
        margin-top: 14px;
        padding: 10px 14px;
        background: rgba(124, 92, 252, 0.05);
        border-left: 2px solid rgba(124, 92, 252, 0.3);
        border-radius: 0 6px 6px 0;
        font-size: 11px;
        color: #7c6fa0;
        line-height: 1.5;
    }

    /* --- Layout helpers --- */
    .split-row { display: flex; gap: 20px; flex-wrap: wrap; }
    .split-row > div { flex: 1; min-width: 420px; }
    .flex-1-5 { flex: 1.5 !important; }
    .full-row { width: 100%; }

    /* --- Empty state --- */
    .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 80px 20px;
        gap: 12px;
        color: #4a4060;
    }
    .empty-icon { font-size: 40px; opacity: 0.3; }
    .empty-title { font-size: 16px; color: #7c6fa0; }
    .empty-sub { font-size: 12px; }
</style>