import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Monitor, Clock, MapPin, Signal, WifiOff } from 'lucide-react';

export const ManagerKioskView: React.FC = () => {
    const { data: kiosks, isLoading } = useQuery({
        queryKey: ['managerKiosks'],
        queryFn: () => api.getKiosks(),
        refetchInterval: 30000,
    });

    if (isLoading) {
        return <div className="p-4 text-muted-foreground">Loading kiosks...</div>;
    }

    // Helper to check online status (assume online if heartbeat < 5 mins ago)
    const isOnline = (lastHeartbeat: string | null) => {
        if (!lastHeartbeat) return false;
        const diff = new Date().getTime() - new Date(lastHeartbeat).getTime();
        return diff < 5 * 60 * 1000; // 5 minutes
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">Active Kiosks</h2>
                <Badge variant="outline">{kiosks?.length || 0} Devices</Badge>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {kiosks?.map((kiosk: any) => {
                    const online = isOnline(kiosk.last_heartbeat);
                    return (
                        <Card key={kiosk.id} className="overflow-hidden">
                            <CardHeader className="pb-2 bg-muted/40 border-b border-border/50">
                                <div className="flex justify-between items-start">
                                    <div className="flex items-center gap-2">
                                        <Monitor className="w-5 h-5 text-primary" />
                                        <div>
                                            <CardTitle className="text-base">{kiosk.device_id}</CardTitle>
                                            <span className="text-xs text-muted-foreground block">{kiosk.building}</span>
                                        </div>
                                    </div>
                                    <Badge variant={online ? 'default' : 'secondary'} className={online ? 'bg-green-500 hover:bg-green-600' : 'bg-muted-foreground'}>
                                        {online ? <Signal className="w-3 h-3 mr-1" /> : <WifiOff className="w-3 h-3 mr-1" />}
                                        {online ? 'Online' : 'Offline'}
                                    </Badge>
                                </div>
                            </CardHeader>
                            <CardContent className="pt-4 space-y-3">
                                <div className="flex items-center justify-between text-sm">
                                    <span className="text-muted-foreground flex items-center gap-1.5"><MapPin className="w-4 h-4" /> Location</span>
                                    <span className="font-medium">{kiosk.location}</span>
                                </div>
                                <div className="flex items-center justify-between text-sm">
                                    <span className="text-muted-foreground flex items-center gap-1.5"><Clock className="w-4 h-4" /> Last Seen</span>
                                    <span className="font-medium">
                                        {kiosk.last_heartbeat ? new Date(kiosk.last_heartbeat).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Never'}
                                    </span>
                                </div>
                            </CardContent>
                        </Card>
                    );
                })}
            </div>

            {(!kiosks || kiosks.length === 0) && (
                <div className="text-center py-10 text-muted-foreground">
                    No kiosks registered yet.
                </div>
            )}
        </div>
    );
};
