import { useState } from 'react';
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
  isOnline = true,
  queueCount = 0,
  isSyncing = false,
  onManualSync
}: AttendanceHomeScreenProps) => {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const handleNavigate = (screen: 'home' | 'register' | 'employee' | 'manager') => {
    if (screen === 'register') {
      onRegister();
    } else if (screen === 'employee') {
      onEmployee();
    } else if (screen === 'manager') {
      onManager();
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
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
        <TimeDisplay location="Corporate Office" />

        {/* Branding Panel - Prodify Logo */}
        <div className="w-full max-w-xs">
          <div className="bg-card/60 rounded-xl border border-border/50 p-4 md:p-5 flex flex-col items-center gap-2">
            {/* Prodify Logo */}
            <img
              src="/prodify-logo.png"
              alt="Prodify"
              className="h-12 md:h-14 object-contain"
            />
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
      </main>
    </div>
  );
};

export default AttendanceHomeScreen;
