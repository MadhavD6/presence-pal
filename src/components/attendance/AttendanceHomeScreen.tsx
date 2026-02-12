import { useState, useEffect } from 'react';
import KioskSettingsDialog from './KioskSettingsDialog';
import { Building2, UserPlus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import AppHeader from './AppHeader';
import TimeDisplay from './TimeDisplay';
import SideDrawer from './SideDrawer';

interface AttendanceHomeScreenProps {
  isDark: boolean;
  onToggleTheme: () => void;
  onClockIn: () => void;
  onClockOut: () => void;
  onRegister: () => void;
  onEmployee: () => void;
  onManager: () => void;
  onKioskSetup: () => void;
  isOnline?: boolean;
  queueCount?: number;
  isSyncing?: boolean;
  onManualSync?: () => void;
}

const AttendanceHomeScreen = ({
  isDark,
  onToggleTheme,
  onClockIn,
  onClockOut,
  onRegister,
  onEmployee,
  onManager,
  onKioskSetup,
  isOnline = true,
  queueCount = 0,
  isSyncing = false,
  onManualSync
}: AttendanceHomeScreenProps) => {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [kiosk, setKiosk] = useState<{ id: number, device_id: string, location: string, building: string } | null>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchKiosk = async () => {
      try {
        const { api } = await import('@/services/api');
        const res = await api.getKioskDetails();
        setKiosk(res.kiosk);
        setError(null);
      } catch (e: any) {
        console.error("Failed to fetch kiosk details", e);

        // Auto-Register on Authorization failure or 401
        if (e.message.includes('401') || e.message.includes('Unauthorized') || e.message.includes('Failed to fetch kiosk')) {
          console.log("Authorization failed. Attempting Auto-Registration...");
          try {
            // Try to Auto-Register
            const { api } = await import('@/services/api');
            const reg = await api.autoRegisterKiosk();
            console.log("Auto-Registered as:", reg.device_id);

            // Save Key
            localStorage.setItem('kiosk_api_key', reg.api_key);

            // Retry Fetch
            const retryRes = await api.getKioskDetails();
            setKiosk(retryRes.kiosk);
            setError(null);

          } catch (regErr) {
            console.error("Auto-Registration failed", regErr);
            setError("Kiosk Authorization Failed. Manual Setup Required.");
          }
        } else {
          setError("Connection Error. Unable to verify status.");
        }
      }
    };
    fetchKiosk();
  }, []);

  const handleNavigate = (screen: 'home' | 'register' | 'employee' | 'manager' | 'kioskSetup') => {
    if (screen === 'register') {
      onRegister();
    } else if (screen === 'employee') {
      onEmployee();
    } else if (screen === 'manager') {
      onManager();
    } else if (screen === 'kioskSetup') {
      onKioskSetup();
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-background relative">
      {/* Kiosk Settings Dialog */}
      {kiosk && (
        <KioskSettingsDialog
          isOpen={isSettingsOpen}
          onClose={() => setIsSettingsOpen(false)}
          kiosk={kiosk}
          onUpdate={setKiosk}
        />
      )}

      <AppHeader
        isDark={isDark}
        onToggleTheme={onToggleTheme}
        onMenuClick={() => setIsDrawerOpen(true)}
        isOnline={isOnline}
        queueCount={queueCount}
        isSyncing={isSyncing}
        onManualSync={onManualSync}
      />

      {/* Side Drawer */}
      <SideDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        onNavigate={handleNavigate}
        isDark={isDark}
        onToggleTheme={onToggleTheme}
      />

      {/* Main content - centered */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 pb-8 gap-6 md:gap-8">
        {/* Time Context Section - Primary visual element */}
        <TimeDisplay location={kiosk ? kiosk.location : "Loading..."} />

        {/* Branding Panel - Prodify Logo */}
        <div className="w-full max-w-xs">
          <div className="bg-card/60 rounded-xl border border-border/50 p-4 md:p-5 flex flex-col items-center gap-2">
            {/* Prodify Logo */}
            <img
              src="/prodify-logo.png"
              alt="Prodify"
              className="h-12 md:h-14 object-contain"
            />
            {kiosk && (
              <div className="text-xs text-muted-foreground flex items-center gap-1.5 mt-1 cursor-pointer hover:text-primary transition-colors" onClick={() => setIsSettingsOpen(true)}>
                <div className={`w-1.5 h-1.5 rounded-full ${isOnline ? 'bg-green-500' : 'bg-yellow-500'}`} />
                <span className="font-medium underline decoration-dashed underline-offset-2">{kiosk.device_id}</span>
              </div>
            )}
            {!kiosk && !error && (
              <div className="text-xs text-muted-foreground mt-1 animate-pulse">Connecting to Kiosk...</div>
            )}
            {error && (
              <div className="flex flex-col items-center gap-2 mt-2">
                <div className="px-3 py-1 rounded bg-destructive/10 text-destructive text-xs font-bold border border-destructive/20 text-center">
                  {error}
                </div>
                {(error.includes("Authorization") || error.includes("Activation")) && (
                  <Button variant="outline" size="sm" className="h-7 text-xs" onClick={() => handleNavigate('kioskSetup')}>
                    Setup Kiosk
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Primary Action Buttons - Enhanced prominence */}
        <div className="w-full max-w-sm flex flex-col sm:flex-row gap-3 md:gap-4">
          <Button
            onClick={onClockIn}
            className="flex-1 h-16 md:h-18 text-lg md:text-xl font-bold bg-success hover:bg-success/90 text-success-foreground shadow-lg hover:shadow-xl transition-all duration-200 active:animate-button-press focus-ring touch-target"
          >
            Clock In
          </Button>
          <Button
            onClick={onClockOut}
            className="flex-1 h-16 md:h-18 text-lg md:text-xl font-bold bg-destructive hover:bg-destructive/90 text-destructive-foreground shadow-lg hover:shadow-xl transition-all duration-200 active:animate-button-press focus-ring touch-target"
          >
            Clock Out
          </Button>
        </div>

        {/* Secondary Action - Enhanced with icon and states */}
        <button
          onClick={onRegister}
          className="group flex items-center gap-2 px-4 py-2.5 rounded-lg text-muted-foreground hover:text-primary hover:bg-primary/5 transition-all duration-200 focus-ring touch-target"
        >
          <UserPlus className="w-4 h-4 transition-transform group-hover:scale-110" />
          <span className="text-sm md:text-base font-medium underline-offset-4 group-hover:underline">
            New Employee? Register
          </span>
        </button>
      </main >

      {/* Footer / Version info */}
      < div className="absolute bottom-2 right-2 text-[10px] text-muted-foreground/30 select-none" >
        v1.2.0 • {kiosk?.id ? `KID:${kiosk.id}` : 'Unregistered'}
      </div >
    </div >
  );
};


export default AttendanceHomeScreen;
