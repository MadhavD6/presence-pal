import { Building2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import AppHeader from './AppHeader';
import TimeDisplay from './TimeDisplay';

interface AttendanceHomeScreenProps {
  isDark: boolean;
  onToggleTheme: () => void;
  onClockIn: () => void;
  onClockOut: () => void;
  onRegister: () => void;
}

const AttendanceHomeScreen = ({
  isDark,
  onToggleTheme,
  onClockIn,
  onClockOut,
  onRegister,
}: AttendanceHomeScreenProps) => {
  return (
    <div className="min-h-screen flex flex-col bg-background">
      <AppHeader isDark={isDark} onToggleTheme={onToggleTheme} />

      {/* Main content - centered */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 pb-8 gap-8 md:gap-10">
        {/* Time Context Section */}
        <TimeDisplay location="Corporate Office" />

        {/* Branding Panel */}
        <div className="w-full max-w-sm">
          <div className="bg-card rounded-xl shadow-lg border border-border p-6 md:p-8 flex flex-col items-center gap-4">
            {/* Company Logo Placeholder */}
            <div className="w-20 h-20 md:w-24 md:h-24 rounded-xl bg-muted flex items-center justify-center">
              <Building2 className="w-10 h-10 md:w-12 md:h-12 text-muted-foreground" />
            </div>
            <p className="text-sm text-muted-foreground font-medium">Your Company</p>
          </div>
        </div>

        {/* Primary Action Buttons */}
        <div className="w-full max-w-sm flex gap-3 md:gap-4">
          <Button
            onClick={onClockIn}
            className="flex-1 h-14 md:h-16 text-base md:text-lg font-semibold bg-success hover:bg-success/90 text-success-foreground shadow-lg"
          >
            Clock In
          </Button>
          <Button
            onClick={onClockOut}
            className="flex-1 h-14 md:h-16 text-base md:text-lg font-semibold bg-destructive hover:bg-destructive/90 text-destructive-foreground shadow-lg"
          >
            Clock Out
          </Button>
        </div>

        {/* Secondary Action */}
        <button
          onClick={onRegister}
          className="text-sm md:text-base text-muted-foreground hover:text-primary underline-offset-4 hover:underline transition-colors"
        >
          New Employee? Register
        </button>
      </main>
    </div>
  );
};

export default AttendanceHomeScreen;
