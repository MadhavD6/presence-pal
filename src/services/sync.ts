import { db, offlineService } from './db';
import { api } from './api';

const SYNC_INTERVAL = 30000; // 30 seconds

export const syncService = {
    isSyncing: false,

    async start() {
        // Initial sync check
        await this.sync();

        // Loop
        setInterval(() => {
            this.sync();
        }, SYNC_INTERVAL);
    },

    async sync() {
        if (this.isSyncing) return;
        if (!navigator.onLine) return; // Browser check

        try {
            this.isSyncing = true;
            const pending = await offlineService.getPendingPunches();

            if (pending.length === 0) return;

            console.log(`Syncing ${pending.length} offline punches...`);

            for (const punch of pending) {
                if (!punch.id) continue;

                try {
                    // Re-upload
                    // We need to pass the raw blobs
                    const result = await api.identify(punch.images, punch.eventType);

                    if (result.status === 'success' || result.status === 'failure') {
                        // Even if failure (e.g. face not matched), we mark as synced so we don't retry forever
                        // Ideally we should log the failure somewhere else if it was a valid attempt
                        await offlineService.markSynced(punch.id);
                    }
                } catch (e) {
                    console.error("Failed to sync punch", punch.id, e);
                    // Keep in queue to retry later
                }
            }
        } catch (error) {
            console.error("Sync error", error);
        } finally {
            this.isSyncing = false;
        }
    }
};
