import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { api, managerApi } from '@/services/api';
import { toast } from 'sonner';

interface Kiosk {
    id: number;
    device_id: string;
    location: string;
    building: string;
    site_id?: number;
}

interface Site {
    id: number;
    name: string;
}

interface KioskSettingsDialogProps {
    isOpen: boolean;
    onClose: () => void;
    kiosk: Kiosk;
    onUpdate: (updatedKiosk: Kiosk) => void;
}

const KioskSettingsDialog = ({ isOpen, onClose, kiosk, onUpdate }: KioskSettingsDialogProps) => {
    const [deviceId, setDeviceId] = useState(kiosk.device_id);
    const [location, setLocation] = useState(kiosk.location);
    const [building, setBuilding] = useState(kiosk.building);
    const [siteId, setSiteId] = useState<string>(kiosk.site_id ? kiosk.site_id.toString() : "");
    const [sites, setSites] = useState<Site[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchSites = async () => {
            try {
                const res = await managerApi.getSites();
                setSites(res);
            } catch (error) {
                console.error("Failed to fetch sites", error);
            }
        };
        if (isOpen) {
            fetchSites();
        }
    }, [isOpen]);

    const handleSave = async () => {
        setLoading(true);
        try {
            const payload: any = { device_id: deviceId, location, building };
            if (siteId && siteId !== "none") {
                payload.site_id = parseInt(siteId);
            }

            const res = await api.updateKiosk(kiosk.id, payload);
            if (res.status === 'success') {
                toast.success('Kiosk updated successfully');
                // Ensure UI updates with new data
                onUpdate(res.kiosk);
                onClose();
            }
        } catch (error: any) {
            toast.error(error.message || 'Failed to update kiosk');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Kiosk Settings</DialogTitle>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                    <div className="grid gap-2">
                        <Label htmlFor="device_id">Device Name / ID</Label>
                        <Input
                            id="device_id"
                            value={deviceId}
                            onChange={(e) => setDeviceId(e.target.value)}
                        />
                        <p className="text-[0.8rem] text-muted-foreground">
                            This unique ID identifies this physical device.
                        </p>
                    </div>

                    <div className="grid gap-2">
                        <Label htmlFor="site">Assigned Site</Label>
                        <Select value={siteId} onValueChange={setSiteId}>
                            <SelectTrigger>
                                <SelectValue placeholder="Select a site..." />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="none">No Site (Global)</SelectItem>
                                {sites.map((site) => (
                                    <SelectItem key={site.id} value={site.id.toString()}>
                                        {site.name}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                        <p className="text-[0.8rem] text-muted-foreground">
                            Linking to a site ensures correct attendance validation.
                        </p>
                    </div>

                    <div className="grid gap-2">
                        <Label htmlFor="location">Location Description</Label>
                        <Input
                            id="location"
                            value={location}
                            onChange={(e) => setLocation(e.target.value)}
                            placeholder="e.g. Lobby Entrance"
                        />
                    </div>
                    <div className="grid gap-2">
                        <Label htmlFor="building">Building</Label>
                        <Input
                            id="building"
                            value={building}
                            onChange={(e) => setBuilding(e.target.value)}
                        />
                    </div>
                </div>
                <DialogFooter>
                    <Button variant="outline" onClick={onClose} disabled={loading}>
                        Cancel
                    </Button>
                    <Button onClick={handleSave} disabled={loading}>
                        {loading ? 'Saving...' : 'Save Changes'}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
};

export default KioskSettingsDialog;
