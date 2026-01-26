import Dexie, { Table } from 'dexie';

export interface OfflinePunch {
    id?: number;
    images: Blob[]; // Store raw images
    eventType: 'in' | 'out';
    timestamp: number;
    synced: boolean;
}

class PresencePalDatabase extends Dexie {
    punches!: Table<OfflinePunch>;

    constructor() {
        super('PresencePalDB');
        this.version(1).stores({
            punches: '++id, timestamp, synced'
        });
    }
}

export const db = new PresencePalDatabase();

export const offlineService = {
    async savePunch(images: Blob[], eventType: 'in' | 'out') {
        return await db.punches.add({
            images,
            eventType,
            timestamp: Date.now(),
            synced: false
        });
    },

    async getPendingPunches() {
        return await db.punches.where('synced').equals(0).toArray();
    },

    async markSynced(id: number) {
        return await db.punches.update(id, { synced: true });
    },

    async deletePunch(id: number) {
        return await db.punches.delete(id);
    }
};
