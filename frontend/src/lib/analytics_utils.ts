import type { Instance, Model, Prompt } from '../types';

export interface AnalyticsResult {
    totalGenerations: number;
    brandMentionedGenerations: number;
    narrativeMentionedGenerations: number;
    uasr: number;
    uaair: number;
    amp: number | null;
    ucsr: number | null;
    sentimentAuthority: number | null;
    sourceDiversity: number;
}

export function computePromptMetrics(instances: Instance[]): AnalyticsResult {
    const atg = instances.length;
    if (atg === 0) {
        return { totalGenerations: 0, brandMentionedGenerations: 0, narrativeMentionedGenerations: 0, uasr: 0, uaair: 0, amp: null, ucsr: null, sentimentAuthority: null, sourceDiversity: 0 };
    }

    const gbm = instances.filter(i => i.metrics?.brand_mentioned).length;
    const gnbm = instances.filter(i => i.metrics?.narrative_mention).length;
    
    const uasr = gbm / atg;
    const uaair = gnbm / atg;

    // AMP
    const gbmInstances = instances.filter(i => i.metrics?.brand_mentioned);
    const sumPosition = gbmInstances.reduce((acc, i) => acc + (i.metrics?.brand_position || 0), 0);
    const amp = gbm > 0 ? sumPosition / gbm : null;

    // UCSR
    const ucsr = (uasr - uaair) !== 0 ? uaair / (uasr - uaair) : null;

    // Sentiment Authority (Narrative mentions only)
    const gnbmInstances = instances.filter(i => i.metrics?.narrative_mention);
    const sumSentiment = gnbmInstances.reduce((acc, i) => acc + (i.metrics?.sentiment_score || 0), 0);
    const sentimentAuthority = gnbm > 0 ? sumSentiment / gnbm : null;

    // USDS
    const allSources = instances.flatMap(i => i.metrics?.mention_sources || []);
    const uniqueSources = new Set(allSources.map(s => s.source)).size;
    const totalSources = allSources.length;
    const sourceDiversity = totalSources > 0 ? uniqueSources / totalSources : 0;

    return {
        totalGenerations: atg,
        brandMentionedGenerations: gbm,
        narrativeMentionedGenerations: gnbm,
        uasr,
        uaair,
        amp,
        ucsr,
        sentimentAuthority,
        sourceDiversity
    };
}

export function getWeeklyBuckets(instances: Instance[]) {
    const buckets: Record<string, Instance[]> = {};
    instances.forEach(inst => {
        const date = new Date(inst.timeBucket);
        // Start of week
        const d = date.getDate() - date.getDay();
        const startOfWeek = new Date(date.setDate(d)).toISOString().split('T')[0];
        if (!buckets[startOfWeek]) buckets[startOfWeek] = [];
        buckets[startOfWeek].push(inst);
    });
    return Object.fromEntries(Object.entries(buckets).sort());
}

export function getMonthlyBuckets(instances: Instance[]) {
    const buckets: Record<string, Instance[]> = {};
    instances.forEach(inst => {
        const date = new Date(inst.timeBucket);
        const month = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-01`;
        if (!buckets[month]) buckets[month] = [];
        buckets[month].push(inst);
    });
    return Object.fromEntries(Object.entries(buckets).sort());
}
