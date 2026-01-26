export interface QueueItem {
    id: string; // uuid
    user_id: number;
    timestamp: string; // ISO
    event_type: 'in' | 'out';
    confidence: number;
    kiosk_id: string;
    retryCount: number;
}

const STORAGE_KEY = 'kiosk_offline_queue';

export const offlineStorage = {
    getQueue: (): QueueItem[] => {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            return raw ? JSON.parse(raw) : [];
        } catch (e) {
            console.error("Failed to read queue", e);
            return [];
        }
    },

    saveToQueue: (item: Omit<QueueItem, 'id' | 'retryCount'>) => {
        const queue = offlineStorage.getQueue();
        const newItem: QueueItem = {
            ...item,
            id: crypto.randomUUID(),
            retryCount: 0
        };
        queue.push(newItem);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(queue));
        return newItem.id;
    },

    removeFromQueue: (ids: string[]) => {
        const queue = offlineStorage.getQueue();
        const newQueue = queue.filter(q => !ids.includes(q.id));
        localStorage.setItem(STORAGE_KEY, JSON.stringify(newQueue));
    },

    clearQueue: () => {
        localStorage.removeItem(STORAGE_KEY);
    },

    incrementRetries: (ids: string[]) => {
        const queue = offlineStorage.getQueue();
        const newQueue = queue.map(q => {
            if (ids.includes(q.id)) {
                return { ...q, retryCount: (q.retryCount || 0) + 1 };
            }
            return q;
        });
        localStorage.setItem(STORAGE_KEY, JSON.stringify(newQueue));
    }
};
