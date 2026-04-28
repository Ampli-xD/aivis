export interface User {
    id: string;
    email: string;
    fullName: string;
    initials: string;
    createdAt: string;
    slackId?: string;
}

export interface Brand {
    id: string;
    userId: string;
    name: string;
    domain?: string;
    industry?: string;
    description?: string;
    createdAt: string;
}

export interface Model {
    id: string;
    provider: string;
    modelName: string;
    externalId: string;
    createdAt: string;
}

export interface Region {
    id: string;
    name: string;
    countryCode: string;
    region?: string;
    city?: string;
    createdAt: string;
}

export interface Prompt {
    id: string;
    brandId: string;
    content: string;
    notes?: string;
    createdAt: string;
}

export interface Deck {
    id: string;
    userId: string;
    brandId: string;
    name: string;
    modelIds: string[];
    regionIds: string[];
    promptIds: string[];
    frequency: number;
    nextExecutionTime?: string;
    toExecute: boolean;
    createdAt: string;
}

export interface Instance {
    id: string;
    timeBucket: string;
    initiatedAt: string;
    completedAt?: string;
    userId: string;
    brandId: string;
    deckId: string;
    promptId: string;
    modelId: string;
    regionId: string;
    
    // Denormalized for display
    brandName: string;
    deckName: string;
    modelName: string;
    promptContent: string;
    regionName?: string;
    
    responseData: any;
    metrics?: any;
}

export interface Tab {
    id: string;
    type: 'pinned' | 'deck' | 'prompts' | 'prompt' | 'instances' | 'instance' | 'settings' | 'profile' | 'analytics';
    label: string;
}
