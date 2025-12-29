import { Menu, Sun, Moon } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface AppHeaderProps {
  showMenu?: boolean;
  isDark: boolean;
  onToggleTheme: () => void;
}

const AppHeader = ({ showMenu = true, isDark, onToggleTheme }: AppHeaderProps) => {
  return (
    <header className="flex items-center justify-between px-4 py-3 md:px-6 md:py-4">
      {/* Brand Logo */}
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 md:w-10 md:h-10 rounded-lg bg-primary flex items-center justify-center">
          <span className="text-primary-foreground font-bold text-sm md:text-base">FA</span>
        </div>
        <span className="text-lg md:text-xl font-semibold text-foreground hidden sm:block">
          Face Attendance
        </span>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleTheme}
          className="text-muted-foreground hover:text-foreground"
        >
          {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </Button>
        {showMenu && (
          <Button
            variant="ghost"
            size="icon"
            className="text-muted-foreground hover:text-foreground"
          >
            <Menu className="w-5 h-5" />
          </Button>
        )}
      </div>
    </header>
  );
};

export default AppHeader;
