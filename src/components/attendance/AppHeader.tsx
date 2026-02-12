import { Menu, Sun, Moon, Wifi, WifiOff, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface AppHeaderProps {
  showMenu?: boolean;
  isDark: boolean;
  onToggleTheme: () => void;
  onMenuClick?: () => void;
  isOnline?: boolean;
  queueCount?: number;
  isSyncing?: boolean;
  onManualSync?: () => void;
}

const AppHeader = ({
  showMenu = true,
  isDark,
  onToggleTheme,
  onMenuClick,
  isOnline = true,
  queueCount = 0,
  isSyncing = false,
  onManualSync
}: AppHeaderProps) => {
  return (
    <header className="flex items-center justify-between px-4 py-3 md:px-6 md:py-4">
      {/* Brand Logo */}
      <div className="flex items-center gap-2">
        <img
          src="/favicon.ico"
          alt="Prodify"
          className="w-8 h-8 md:w-10 md:h-10 rounded-lg shadow-sm"
        />
        <span className="text-lg md:text-xl font-semibold text-foreground hidden sm:block">
          Prodify Face App
        </span>

        {/* Offline/Sync Status */}
        <div className="ml-4 flex items-center gap-2">
          {!isOnline && (
            <Badge variant="destructive" className="flex items-center gap-1">
              <WifiOff className="w-3 h-3" /> Offline
            </Badge>
          )}
          {isOnline && queueCount > 0 && (
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="bg-yellow-100 text-yellow-800 border-yellow-200">
                Pending: {queueCount}
              </Badge>
              <Button
                size="sm"
                variant="outline"
                onClick={onManualSync}
                disabled={isSyncing}
                className="h-7 text-xs"
              >
                {isSyncing ? <RefreshCw className="w-3 h-3 animate-spin" /> : 'Sync Now'}
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1 md:gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleTheme}
          className="text-muted-foreground hover:text-foreground hover:bg-muted transition-colors focus-ring touch-target"
          aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
        >
          {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </Button>
        {showMenu && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onMenuClick}
            className="text-muted-foreground hover:text-foreground hover:bg-muted transition-colors focus-ring touch-target"
            aria-label="Open menu"
          >
            <Menu className="w-5 h-5" />
          </Button>
        )}
      </div>
    </header>
  );
};

export default AppHeader;
