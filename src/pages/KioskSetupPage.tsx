import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { api } from '@/services/api';
import { useNavigate } from 'react-router-dom';
import { Check, ChevronRight, Building2, Monitor, MapPin, ArrowLeft } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

type SetupStep = 'SITE' | 'KIOSK' | 'DETAILS' | 'ACTIVATE';

interface KioskSetupPageProps {
    onCancel?: () => void;
}

const KioskSetupPage = ({ onCancel }: KioskSetupPageProps) => {
    const [step, setStep] = useState<SetupStep>('SITE');
    const [sites, setSites] = useState<any[]>([]);
    const [kiosks, setKiosks] = useState<any[]>([]);
    const [selectedSite, setSelectedSite] = useState<any>(null);
    const [selectedKiosk, setSelectedKiosk] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    // For new kiosk registration
    const [deviceId, setDeviceId] = useState('');
    const [location, setLocation] = useState('');
    const [building, setBuilding] = useState('');

    const navigate = useNavigate();
    const { toast } = useToast();

    useEffect(() => {
        loadSites();
    }, []);

    const loadSites = async () => {
        setLoading(true);
        try {
            const data = await api.getSetupSites();
            setSites(data);
        } catch (err) {
            toast({ title: 'Error', description: 'Failed to load sites', variant: 'destructive' });
        } finally {
            setLoading(false);
        }
    };

    const loadKiosks = async (siteId: number) => {
        setLoading(true);
        try {
            const data = await api.getSetupKiosks(siteId);
            setKiosks(data);
        } catch (err) {
            toast({ title: 'Error', description: 'Failed to load kiosks', variant: 'destructive' });
        } finally {
            setLoading(false);
        }
    };

    const handleSiteSelect = (site: any) => {
        setSelectedSite(site);
        loadKiosks(site.id);
        setStep('KIOSK');
    };

    const handleKioskSelect = (kiosk: any) => {
        if (kiosk === 'NEW') {
            setSelectedKiosk(null);
            setDeviceId('');
            setLocation('');
            setBuilding('');
            setStep('DETAILS');
        } else {
            setSelectedKiosk(kiosk);
            setDeviceId(kiosk.device_id);
            setLocation(kiosk.location);
            setBuilding(kiosk.building);
            setStep('DETAILS');
        }
    };

    const handleActivate = async () => {
        setLoading(true);
        try {
            const payload = {
                site_id: selectedSite.id,
                device_id: deviceId,
                location: location,
                building: building,
                kiosk_id: selectedKiosk?.id
            };
            const { api_key } = await api.activateKiosk(payload);
            localStorage.setItem('kiosk_api_key', api_key);

            toast({ title: 'Success', description: 'Kiosk activated successfully!' });
            navigate('/');
        } catch (err: any) {
            toast({ title: 'Activation Failed', description: err.message, variant: 'destructive' });
        } finally {
            setLoading(false);
        }
    };

    const renderStepHeader = () => {
        const steps = [
            { id: 'SITE', label: 'Select Site' },
            { id: 'KIOSK', label: 'Select Kiosk' },
            { id: 'DETAILS', label: 'Device Info' },
            { id: 'ACTIVATE', label: 'Activate' }
        ];

        return (
            <div className="flex items-center justify-between mb-8 px-2">
                {steps.map((s, idx) => (
                    <React.Fragment key={s.id}>
                        <div className="flex flex-col items-center gap-1">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${step === s.id ? 'bg-primary text-primary-foreground' :
                                steps.findIndex(x => x.id === step) > idx ? 'bg-green-500 text-white' : 'bg-muted text-muted-foreground'
                                }`}>
                                {steps.findIndex(x => x.id === step) > idx ? <Check className="w-4 h-4" /> : idx + 1}
                            </div>
                            <span className="text-[10px] uppercase font-medium text-muted-foreground">{s.label}</span>
                        </div>
                        {idx < steps.length - 1 && <div className="h-[2px] flex-grow bg-muted mx-2 -mt-4" />}
                    </React.Fragment>
                ))}
            </div>
        );
    };

    return (
        <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
            <div className="w-full max-w-xl">
                {renderStepHeader()}

                <Card className="border-border/50 bg-card/95 backdrop-blur shadow-2xl overflow-hidden">
                    <CardHeader className="text-center pb-2">
                        {step !== 'SITE' && (
                            <Button
                                variant="ghost"
                                size="sm"
                                className="absolute left-4 top-4"
                                onClick={() => {
                                    if (step === 'KIOSK') setStep('SITE');
                                    if (step === 'DETAILS') setStep('KIOSK');
                                    if (step === 'ACTIVATE') setStep('DETAILS');
                                }}
                            >
                                <ArrowLeft className="w-4 h-4 mr-1" /> Back
                            </Button>
                        )}
                        <CardTitle className="text-2xl font-bold tracking-tight">Kiosk Setup</CardTitle>
                        <CardDescription>
                            {step === 'SITE' && 'Choose the site where this kiosk will be located'}
                            {step === 'KIOSK' && `Select a registered kiosk for ${selectedSite?.name}`}
                            {step === 'DETAILS' && 'Confirm or enter device details'}
                            {step === 'ACTIVATE' && 'Ready to generate security keys'}
                        </CardDescription>
                    </CardHeader>

                    <CardContent className="pt-6">
                        {step === 'SITE' && (
                            <div className="grid grid-cols-1 gap-3">
                                {loading ? (
                                    <div className="py-8 text-center text-muted-foreground">Loading sites...</div>
                                ) : (
                                    sites.map(site => (
                                        <Button
                                            key={site.id}
                                            variant="outline"
                                            className="h-16 justify-between px-6 border-border/60 hover:border-primary/50 hover:bg-primary/5"
                                            onClick={() => handleSiteSelect(site)}
                                        >
                                            <div className="flex items-center gap-4">
                                                <Building2 className="w-5 h-5 text-primary/70" />
                                                <div className="text-left">
                                                    <div className="font-semibold">{site.name}</div>
                                                    <div className="text-xs text-muted-foreground">{site.location || 'Active Site'}</div>
                                                </div>
                                            </div>
                                            <ChevronRight className="w-4 h-4 text-muted-foreground" />
                                        </Button>
                                    ))
                                )}
                                {sites.length === 0 && !loading && (
                                    <div className="py-8 flex flex-col items-center gap-4 text-center text-muted-foreground">
                                        <p>No active sites found. Please create one in Manager Dashboard.</p>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={loadSites}
                                            className="gap-2"
                                        >
                                            <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" style={{ animationDuration: '0s' }} />
                                            Refresh Sites
                                        </Button>
                                    </div>
                                )}
                            </div>
                        )}

                        {step === 'KIOSK' && (
                            <div className="grid grid-cols-1 gap-3">
                                <Button
                                    variant="outline"
                                    className="h-16 justify-between px-6 border-dashed border-primary/40 bg-primary/5 hover:bg-primary/10"
                                    onClick={() => handleKioskSelect('NEW')}
                                >
                                    <div className="flex items-center gap-4">
                                        <Monitor className="w-5 h-5 text-primary" />
                                        <div className="text-left">
                                            <div className="font-semibold text-primary">Register New Kiosk</div>
                                            <div className="text-xs text-primary/70">Create a new kiosk identity for this site</div>
                                        </div>
                                    </div>
                                    <ChevronRight className="w-4 h-4 text-primary" />
                                </Button>

                                <div className="relative my-4">
                                    <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-muted"></div></div>
                                    <div className="relative flex justify-center text-xs uppercase"><span className="bg-card px-2 text-muted-foreground">Or select existing</span></div>
                                </div>

                                {kiosks.map(kiosk => (
                                    <Button
                                        key={kiosk.id}
                                        variant="outline"
                                        className="h-16 justify-between px-6 border-border/60"
                                        onClick={() => handleKioskSelect(kiosk)}
                                    >
                                        <div className="flex items-center gap-4">
                                            <Monitor className="w-5 h-5 text-muted-foreground" />
                                            <div className="text-left">
                                                <div className="font-semibold">{kiosk.device_id}</div>
                                                <div className="text-xs text-muted-foreground">{kiosk.location} - {kiosk.building}</div>
                                            </div>
                                        </div>
                                        <ChevronRight className="w-4 h-4 text-muted-foreground" />
                                    </Button>
                                ))}
                            </div>
                        )}

                        {step === 'DETAILS' && (
                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="deviceId">Device ID (Unique Identifier)</Label>
                                    <Input
                                        id="deviceId"
                                        placeholder="e.g. LOBBY_TAB_01"
                                        value={deviceId}
                                        onChange={e => setDeviceId(e.target.value)}
                                        className="bg-muted/30"
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="location">Location Name</Label>
                                        <Input
                                            id="location"
                                            placeholder="e.g. Reception"
                                            value={location}
                                            onChange={e => setLocation(e.target.value)}
                                            className="bg-muted/30"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="building">Building/Wing</Label>
                                        <Input
                                            id="building"
                                            placeholder="e.g. Tower A"
                                            value={building}
                                            onChange={e => setBuilding(e.target.value)}
                                            className="bg-muted/30"
                                        />
                                    </div>
                                </div>
                                <Button
                                    className="w-full mt-6"
                                    disabled={!deviceId || !location || !building}
                                    onClick={() => setStep('ACTIVATE')}
                                >
                                    Review & Activate
                                </Button>
                            </div>
                        )}

                        {step === 'ACTIVATE' && (
                            <div className="space-y-6">
                                <div className="p-6 rounded-xl bg-primary/5 border border-primary/10 space-y-4">
                                    <div className="flex items-start gap-4">
                                        <Building2 className="w-5 h-5 text-primary mt-1" />
                                        <div>
                                            <div className="text-xs text-muted-foreground uppercase font-semibold">Site</div>
                                            <div className="text-lg font-bold">{selectedSite?.name}</div>
                                        </div>
                                    </div>
                                    <div className="flex items-start gap-4">
                                        <Monitor className="w-5 h-5 text-primary mt-1" />
                                        <div>
                                            <div className="text-xs text-muted-foreground uppercase font-semibold">Kiosk Identity</div>
                                            <div className="text-lg font-bold">{deviceId}</div>
                                            <div className="text-sm text-muted-foreground flex items-center gap-1">
                                                <MapPin className="w-3 h-3" /> {location}, {building}
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-600 dark:text-amber-400">
                                    <strong>Important:</strong> Activating this kiosk will generate a new security key. Existing keys for this Device ID (if any) will be invalidated.
                                </div>

                                <Button
                                    className="w-full h-12 text-lg font-bold shadow-lg shadow-primary/20"
                                    onClick={handleActivate}
                                    disabled={loading}
                                >
                                    {loading ? 'Activating...' : 'Confirm & Activate Kiosk'}
                                </Button>
                            </div>
                        )}
                    </CardContent>

                    <CardFooter className="bg-muted/30 border-t border-border/40 py-3 justify-center">
                        <span className="text-[10px] text-muted-foreground flex items-center gap-1 uppercase tracking-widest font-bold">
                            PresencePal Security Protocol v2.0
                        </span>
                    </CardFooter>
                </Card>

                <div className="mt-8 text-center text-sm">
                    <button
                        className="text-muted-foreground hover:text-primary underline underline-offset-4 transition-colors p-2"
                        onClick={() => {
                            if (onCancel) {
                                onCancel();
                            } else {
                                navigate('/');
                            }
                        }}
                    >
                        Cancel setup and go back
                    </button>
                </div>
            </div>
        </div>
    );
};

export default KioskSetupPage;
