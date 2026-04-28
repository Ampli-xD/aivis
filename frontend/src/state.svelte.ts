import type { User, Brand, Deck, Prompt, Model, Region, Instance, Tab } from './types.ts';

class AppState {
    private baseUrl = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '');
    user = $state<User | null>(null);
    brands = $state<Brand[]>([]);
    activeBrandId = $state<string | null>(null);
    decks = $state<Deck[]>([]);
    allPrompts = $state<Prompt[]>([]);
    models = $state<Model[]>([]);
    regions = $state<Region[]>([]);
    instances = $state<Instance[]>([]);
    openTabs = $state<Tab[]>([{ id: 'home', type: 'pinned', label: 'Home' }]);
    activeTabId = $state<string>('home');
    isLoggedIn = $state<boolean>(false);
    isInitialLoading = $state<boolean>(true);
    currentTime = $state<string>('--:--:--');
    backendLatency = $state<number>(0);
    dbLatency = $state<number>(0);
    cronInterval = $state<number>(1); // Default to 1 (testing) till fetch
    toastMsg = $state<string>('');
    showToast = $state<boolean>(false);
    showCreateDeckModal = $state<boolean>(false);
    editingDeck = $state<Deck | null>(null);
    confirmModal = $state<{
        title: string;
        message: string;
        onConfirm: () => void;
        onCancel: () => void;
    } | null>(null);

    constructor() {
        this.updateTime();
        // setInterval(() => this.updateTime(), 1000); // Disable auto-update to reduce UI jitter/cycles if needed, or keep for clock
        this.measureLatency();
        // setInterval(() => this.measureLatency(), 60000); // DISABLED REPETITIVE CALLS
        this.checkAuth();
    }

    async checkAuth() {
        const token = localStorage.getItem('token');
        const userData = localStorage.getItem('user');
        if (token && userData) {
            this.user = this.mapUser(JSON.parse(userData));
            this.isLoggedIn = true;
            this.fetchAllData();
        } else {
            this.isInitialLoading = false;
        }
    }

    private mapUser(u: any): User {
        return {
            id: u.id,
            email: u.email,
            fullName: u.fullName || u.full_name || u.email.split('@')[0],
            initials: (u.fullName || u.full_name || u.email).charAt(0).toUpperCase(),
            createdAt: u.createdAt || u.created_at,
            slackId: u.slackId || u.slack_user_id || undefined
        };
    }

    private mapBrand(b: any): Brand {
        return {
            id: b.id,
            userId: b.userId || b.user_id,
            name: b.name,
            domain: b.domain,
            industry: b.industry,
            description: b.description,
            createdAt: b.createdAt || b.created_at
        };
    }

    private mapModel(m: any): Model {
        return {
            id: m.id,
            provider: m.provider,
            modelName: m.modelName || m.model_name,
            externalId: m.externalId || m.external_id,
            createdAt: m.createdAt || m.created_at
        };
    }

    private mapRegion(r: any): Region {
        return {
            id: r.id,
            name: r.name,
            countryCode: r.countryCode || r.country_code,
            region: r.region,
            city: r.city,
            createdAt: r.createdAt || r.created_at
        };
    }

    private mapPrompt(p: any): Prompt {
        return {
            id: p.id,
            brandId: p.brandId || p.brand_id,
            content: p.content,
            notes: p.notes,
            createdAt: p.createdAt || p.created_at
        };
    }

    private mapDeck(d: any): Deck {
        return {
            id: d.id,
            userId: d.userId || d.user_id,
            brandId: d.brandId || d.brand_id,
            name: d.name,
            modelIds: d.modelIds || d.model_ids || [],
            regionIds: d.regionIds || d.region_ids || [],
            promptIds: d.promptIds || d.prompt_ids || [],
            frequency: d.frequency,
            nextExecutionTime: d.nextExecutionTime || d.next_execution_time,
            toExecute: d.toExecute !== undefined ? d.toExecute : d.to_execute,
            createdAt: d.createdAt || d.created_at
        };
    }

    private mapInstance(i: any): Instance {
        return {
            id: i.id,
            timeBucket: i.timeBucket || i.time_bucket,
            initiatedAt: i.initiatedAt || i.initiated_at,
            completedAt: i.completedAt || i.completed_at,
            userId: i.userId || i.user_id,
            brandId: i.brandId || i.brand_id,
            deckId: i.deckId || i.deck_id,
            promptId: i.promptId || i.prompt_id,
            modelId: i.modelId || i.model_id,
            regionId: i.regionId || i.region_id,
            brandName: i.brandName || i.brand_name,
            deckName: i.deckName || i.deck_name,
            modelName: i.modelName || i.model_name,
            promptContent: i.promptContent || i.prompt_content,
            regionName: i.regionName || i.region_name,
            responseData: i.responseData || i.response_data,
            metrics: i.metrics
        };
    }

    updateTime() {
        const now = new Date();
        const h = now.getHours();
        const m = now.getMinutes();
        const s = now.getSeconds();
        this.currentTime = `${h < 10 ? '0' + h : h}:${m < 10 ? '0' + m : m}:${s < 10 ? '0' + s : s}`;
    }

    async measureLatency() {
        try {
            const hStart = performance.now();
            const res = await fetch(`${this.baseUrl}/health`);
            const hEnd = performance.now();

            if (res.ok) {
                const data = await res.json();
                if (data.cron_interval) this.cronInterval = data.cron_interval;
            }

            const healthLat = hEnd - hStart;
            this.backendLatency = Math.round(healthLat);

            // Now hit models (database hit)
            const mStart = performance.now();
            await fetch(`${this.baseUrl}/models`);
            const mEnd = performance.now();

            const modelsLat = mEnd - mStart;

            // Subtract health (base overhead + network) from models (base + network + db)
            // If models is faster or equal, we'll cap it at 1ms
            this.dbLatency = Math.max(1, Math.round(modelsLat - healthLat));

        } catch (e) {
            console.error('Latency check failed', e);
        }
    }

    async login(email: string, pass: string) {
        try {
            const formData = new FormData();
            formData.append('username', email);
            formData.append('password', pass);

            const res = await fetch(`${this.baseUrl}/token`, {
                method: 'POST',
                body: formData
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Login failed');
            }

            const data = await res.json();
            localStorage.setItem('token', data.access_token);

            // Fetch user info - since /token doesn't return full user, we might need to get it
            // For now, let's look at what /token payload has: sub and id.
            // We can decode JWT or just fetch user by email or ID if we have an endpoint.
            // Backend has /users/{user_id}

            // Let's decode the token to get the user ID
            const payload = JSON.parse(atob(data.access_token.split('.')[1]));
            const userId = payload.id;

            const userRes = await fetch(`${this.baseUrl}/users/${userId}`, {
                headers: { 'Authorization': `Bearer ${data.access_token}` }
            });

            if (userRes.ok) {
                const user = await userRes.json();
                this.user = this.mapUser(user);
                localStorage.setItem('user', JSON.stringify(this.user));
                this.isLoggedIn = true;
                this.isInitialLoading = true;
                this.fetchAllData();
                this.toast('Welcome back!');
                return true;
            }
            return false;
        } catch (e: any) {
            console.error(e);
            this.toast(e.message);
            return false;
        }
    }

    async updateUser(userId: string, data: any) {
        try {
            // Remap for backend
            const payload: any = {};
            if (data.fullName) payload.full_name = data.fullName;
            if (data.email) payload.email = data.email;
            if (data.slackId) payload.slack_user_id = data.slackId;

            const res = await this.fetchWithAuth(`${this.baseUrl}/users/${userId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                const updatedUser = await res.json();
                this.user = this.mapUser(updatedUser);
                localStorage.setItem('user', JSON.stringify(this.user)); // Persist updated profile
                this.toast('Profile updated successfully');
                return updatedUser;
            }
        } catch (e: any) {
            this.toast(e.message);
        }
    }

    async changePassword(currentPassword: string, newPassword: string) {
        try {
            const res = await this.fetchWithAuth(`${this.baseUrl}/users/me/password`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ current_password: currentPassword, new_password: newPassword })
            });

            if (!res.ok) {
                const data = await res.json();
                this.toast(data.detail || 'Incorrect current password');
                return false;
            }

            this.toast('Password updated successfully');
            return true;
        } catch (e: any) {
            this.toast(e.message);
            return false;
        }
    }

    async signup(email: string, pass: string, fullName: string) {
        try {
            const res = await fetch(`${this.baseUrl}/users`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password: pass, full_name: fullName })
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Signup failed');
            }

            this.toast('Account created! Please sign in.');
            return true;
        } catch (e: any) {
            console.error(e);
            this.toast(e.message);
            return false;
        }
    }

    private async fetchWithAuth(url: string, options: RequestInit = {}) {
        const token = localStorage.getItem('token');
        if (!token) throw new Error('No authentication token');

        const headers = {
            ...options.headers,
            'Authorization': `Bearer ${token}`
        };

        const res = await fetch(url, { ...options, headers });
        if (res.status === 401) {
            this.logout();
            throw new Error('Session expired');
        }
        return res;
    }

    async fetchAllData(force = false) {
        const token = localStorage.getItem('token');
        if (!token) {
            this.isInitialLoading = false;
            return;
        }
        this.isInitialLoading = true;

        const headers = { 'Authorization': `Bearer ${token}` };

        try {
            // Fetch Models and Regions (Global) - Only if empty or forced
            const skipGlobal = !force && this.models.length > 0 && this.regions.length > 0;

            const promises: Promise<Response>[] = [
                fetch(`${this.baseUrl}/brands`, { headers })
            ];

            if (!skipGlobal) {
                promises.push(fetch(`${this.baseUrl}/models`, { headers }));
                promises.push(fetch(`${this.baseUrl}/regions`, { headers }));
            }

            const resArr = await Promise.all(promises);
            const brandsRes = resArr[0];
            const modelsRes = !skipGlobal ? resArr[1] : null;
            const regionsRes = !skipGlobal ? resArr[2] : null;

            if (modelsRes && modelsRes.ok) {
                const models = await modelsRes.json();
                console.log('Fetched models:', models);
                this.models = (models || []).map((m: any) => this.mapModel(m));
            } else if (modelsRes && !modelsRes.ok) {
                console.error('Models fetch failed:', modelsRes.status);
            }

            if (regionsRes && regionsRes.ok) {
                const regions = await regionsRes.json();
                this.regions = (regions || []).map((r: any) => this.mapRegion(r));
            } else if (regionsRes && !regionsRes.ok) {
                console.error('Regions fetch failed:', regionsRes.status);
            }

            if (brandsRes.ok) {
                const brandsData = await brandsRes.json();
                this.brands = brandsData.map((b: any) => this.mapBrand(b));
                if (this.brands.length > 0 && !this.activeBrandId) {
                    this.activeBrandId = this.brands[0].id;
                }

                // For each brand, fetch prompts and decks
                const brandPromises = this.brands.map(async (brand: Brand) => {
                    const [promptsRes, decksRes] = await Promise.all([
                        fetch(`${this.baseUrl}/brands/${brand.id}/prompts`, { headers }),
                        fetch(`${this.baseUrl}/brands/${brand.id}/decks`, { headers })
                    ]);
                    const prompts = promptsRes.ok ? await promptsRes.json() : [];
                    const decks = decksRes.ok ? await decksRes.json() : [];
                    return {
                        brandId: brand.id,
                        prompts: prompts.map((p: any) => this.mapPrompt(p)),
                        decks: decks.map((d: any) => this.mapDeck(d))
                    };
                });

                const results = await Promise.all(brandPromises);

                // Consolidate prompts and decks
                this.allPrompts = results.flatMap(r => r.prompts);
                this.decks = results.flatMap(r => r.decks);
            }

            // Fetch Instances
            const instancesRes = await fetch(`${this.baseUrl}/instances`, { headers });
            if (instancesRes.ok) {
                const instances = await instancesRes.json();
                this.instances = instances.map((i: any) => this.mapInstance(i));
            }

        } catch (e) {
            console.error('Failed to fetch data:', e);
            this.toast('Failed to sync data with server');
        } finally {
            this.isInitialLoading = false;
        }
    }

    // --- Brands ---
    async createBrand(brandData: Partial<Brand>) {
        try {
            const res = await this.fetchWithAuth(`${this.baseUrl}/brands`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(brandData)
            });
            if (res.ok) {
                const newBrand = await res.json();
                const mapped = this.mapBrand(newBrand);
                this.brands.push(mapped);
                if (!this.activeBrandId) this.activeBrandId = mapped.id;
                this.toast(`Brand "${mapped.name}" created`);
                return mapped;
            }
        } catch (e: any) {
            this.toast(e.message);
        }
    }

    async updateBrand(brandId: string, brandData: Partial<Brand>) {
        try {
            const res = await this.fetchWithAuth(`${this.baseUrl}/brands/${brandId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(brandData)
            });
            if (res.ok) {
                const updatedBrand = await res.json();
                const idx = this.brands.findIndex(b => b.id === brandId);
                if (idx !== -1) this.brands[idx] = updatedBrand;
                this.toast(`Brand "${updatedBrand.name}" updated`);
                return updatedBrand;
            }
        } catch (e: any) {
            this.toast(e.message);
        }
    }

    async deleteBrand(brandId: string) {
        try {
            const res = await this.fetchWithAuth(`${this.baseUrl}/brands/${brandId}`, {
                method: 'DELETE'
            });
            if (res.ok) {
                this.brands = this.brands.filter(b => b.id !== brandId);
                this.toast('Brand deleted');
                return true;
            }
        } catch (e: any) {
            this.toast(e.message);
        }
    }

    // --- Decks ---
    async createDeck(deckData: Partial<Deck>) {
        try {
            const res = await this.fetchWithAuth(`${this.baseUrl}/deck`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(deckData)
            });
            if (res.ok) {
                const resData = await res.json();
                const newDeck = resData.data; // Backend returns {id, message, data}
                const mapped = this.mapDeck(newDeck);
                this.decks.push(mapped);
                this.toast(`Deck "${mapped.name}" created`);
                return mapped;
            }
        } catch (e: any) {
            this.toast(e.message);
        }
    }

    async updateDeck(deckId: string, deckData: Partial<Deck>) {
        try {
            const res = await this.fetchWithAuth(`${this.baseUrl}/deck/${deckId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(deckData)
            });
            if (res.ok) {
                const resData = await res.json();
                const updated = resData.data;
                const mapped = this.mapDeck(updated);
                const idx = this.decks.findIndex(d => d.id === deckId);
                if (idx !== -1) this.decks[idx] = mapped;
                this.toast(`Deck "${mapped.name}" updated`);
                return mapped;
            }
        } catch (e: any) {
            this.toast(e.message);
        }
    }

    closeEditDeck() {
        this.editingDeck = null;
    }

    async deleteDeck(deckId: string) {
        const ok = await this.confirm('Delete Deck', 'Are you sure you want to delete this deck? This will also remove all execution history!');
        if (!ok) return;
        try {
            const res = await this.fetchWithAuth(`${this.baseUrl}/deck/${deckId}`, {
                method: 'DELETE'
            });
            if (res.ok) {
                this.decks = this.decks.filter(d => d.id !== deckId);
                this.openTabs = this.openTabs.filter(t => t.id !== deckId);
                if (this.activeTabId === deckId) this.activeTabId = 'home';
                this.toast('Deck deleted');
            }
        } catch (e: any) {
            this.toast(e.message);
        }
    }

    // --- Prompts ---
    async createPrompt(brandId: string, promptData: Partial<Prompt>) {
        try {
            const res = await this.fetchWithAuth(`${this.baseUrl}/brands/${brandId}/prompts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(promptData)
            });
            if (res.ok) {
                const newPrompt = await res.json();
                const mapped = this.mapPrompt(newPrompt);
                this.allPrompts.push(mapped);
                this.toast('Prompt created');
                return mapped;
            }
        } catch (e: any) {
            this.toast(e.message);
        }
    }

    async updatePrompt(promptId: string, data: Partial<Prompt>) {
        try {
            const res = await this.fetchWithAuth(`${this.baseUrl}/prompts/${promptId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (res.ok) {
                const updated = await res.json();
                const mapped = this.mapPrompt(updated);
                const idx = this.allPrompts.findIndex(p => p.id === promptId);
                if (idx !== -1) this.allPrompts[idx] = mapped;
                this.toast('Prompt updated');
                return mapped;
            }
        } catch (e: any) {
            this.toast(e.message);
        }
    }

    async deletePrompt(promptId: string) {
        try {
            const res = await this.fetchWithAuth(`${this.baseUrl}/prompts/${promptId}`, {
                method: 'DELETE'
            });
            if (res.ok) {
                this.allPrompts = this.allPrompts.filter(p => p.id !== promptId);
                this.toast('Prompt deleted');
                return true;
            }
        } catch (e: any) {
            this.toast(e.message);
        }
    }

    logout() {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        this.user = null;
        this.isLoggedIn = false;
        this.brands = [];
        this.decks = [];
        this.allPrompts = [];
        this.instances = [];
        this.openTabs = [{ id: 'home', type: 'pinned', label: 'Home' }];
        this.activeTabId = 'home';
    }

    openTab(id: string, type: Tab['type'], label: string) {
        if (!this.openTabs.find(t => t.id === id)) {
            if (this.openTabs.length >= 10) {
                this.toast('Tab limit reached — scroll to see all open tabs');
                return;
            }
            this.openTabs.push({ id, type, label });
        }
        this.activeTabId = id;
    }

    closeTab(id: string) {
        if (id === 'home') return;
        this.openTabs = this.openTabs.filter(t => t.id !== id);
        if (this.activeTabId === id) {
            this.activeTabId = this.openTabs[this.openTabs.length - 1].id;
        }
    }

    moveTab(fromIndex: number, toIndex: number) {
        const tabs = [...this.openTabs];
        const [movedTab] = tabs.splice(fromIndex, 1);
        tabs.splice(toIndex, 0, movedTab);
        this.openTabs = tabs;
    }

    confirm(title: string, message: string): Promise<boolean> {
        return new Promise((resolve) => {
            this.confirmModal = {
                title,
                message,
                onConfirm: () => {
                    this.confirmModal = null;
                    resolve(true);
                },
                onCancel: () => {
                    this.confirmModal = null;
                    resolve(false);
                }
            };
        });
    }

    async runAnalytics(limit = 100, brandId?: string) {
        try {
            let url = `${this.baseUrl}/analytics?limit=${limit}`;
            if (brandId) {
                url += `&brand_id=${brandId}`;
            }
            const res = await this.fetchWithAuth(url, {
                method: 'POST'
            });
            if (res.ok) {
                const data = await res.json();
                this.toast(`Analyzed ${data.processed} records`);
                if (data.processed > 0) {
                    this.fetchAllData(true); // Refresh to get new metrics
                }
                return data;
            }
        } catch (e: any) {
            this.toast(e.message);
        }
    }

    toast(msg: string) {
        this.toastMsg = msg;
        this.showToast = true;
        setTimeout(() => this.showToast = false, 2200);
    }
}

export const appState = new AppState();
