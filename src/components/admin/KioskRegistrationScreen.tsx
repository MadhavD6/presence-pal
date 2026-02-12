import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { api } from '@/services/api';

interface KioskRegistrationScreenProps {
    onSuccess: () => void;
}

const KioskRegistrationScreen = ({ onSuccess }: KioskRegistrationScreenProps) => {
    const [deviceId, setDeviceId] = useState('');
    const [location, setLocation] = useState('');
    const [building, setBuilding] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const { api_key } = await api.registerKiosk(deviceId, location, building);
            localStorage.setItem('kiosk_api_key', api_key);
            onSuccess();
        } catch (err: any) {
            setError(err.message || 'Registration failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-background flex items-center justify-center p-4">
            <Card className="w-full max-w-md border-border/50 bg-card/95 backdrop-blur shadow-xl">
                <CardHeader>
                    <CardTitle className="text-2xl text-center font-bold">Resgitering New Kiosk</CardTitle>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="deviceId">Device ID (Unique)</Label>
                            <Input
                                id="deviceId"
                                placeholder="e.g. LOBBY_TAB_01"
                                value={deviceId}
                                onChange={(e) => setDeviceId(e.target.value)}
                                required
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="location">Location</Label>
                            <Input
                                id="location"
                                placeholder="e.g. Main Reception"
                                value={location}
                                onChange={(e) => setLocation(e.target.value)}
                                required
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="building">Building</Label>
                            <Input
                                id="building"
                                placeholder="e.g. HQ Tower A"
                                value={building}
                                onChange={(e) => setBuilding(e.target.value)}
                                required
                            />
                        </div>

                        {error && <div className="text-red-500 text-sm font-medium">{error}</div>}

                        <Button type="submit" className="w-full" disabled={loading}>
                            {loading ? 'Registering...' : 'Register Device'}
                        </Button>
                    </form>
                </CardContent>
            </Card>
        </div>
    );
};

export default KioskRegistrationScreen;
