import { useEffect, useRef } from 'react';
import { X, Home, UserPlus, HelpCircle, Sun, Moon } from 'lucide-react';

interface SideDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate: (screen: 'home' | 'register') => void;
  isDark: boolean;
  onToggleTheme: () => void;
}

const SideDrawer = ({ isOpen, onClose, onNavigate, isDark, onToggleTheme }: SideDrawerProps) => {
  const drawerRef = useRef<HTMLDivElement>(null);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  // Prevent body scroll when drawer is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const menuItems = [
    { icon: Home, label: 'Home', action: () => { onNavigate('home'); onClose(); } },
    { icon: UserPlus, label: 'Register', action: () => { onNavigate('register'); onClose(); } },
    { icon: HelpCircle, label: 'Help', action: () => { onClose(); } },
  ];

  return (
    <div className="fixed inset-0 z-50">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-foreground/40 backdrop-blur-sm animate-overlay-fade-in"
        onClick={onClose}
      />

      {/* Drawer */}
      <div 
        ref={drawerRef}
        className="absolute top-0 right-0 h-full w-72 max-w-[80vw] bg-card shadow-2xl animate-slide-in-right flex flex-col"
      >
        {/* Drawer Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-sm">FA</span>
            </div>
            <span className="font-semibold text-foreground">Menu</span>
          </div>
          <button
            onClick={onClose}
            className="w-10 h-10 rounded-full hover:bg-muted flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors focus-ring touch-target"
            aria-label="Close menu"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Menu Items */}
        <nav className="flex-1 p-4 space-y-1">
          {menuItems.map((item) => (
            <button
              key={item.label}
              onClick={item.action}
              className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-foreground hover:bg-muted transition-colors focus-ring touch-target"
            >
              <item.icon className="w-5 h-5 text-muted-foreground" />
              <span className="font-medium">{item.label}</span>
            </button>
          ))}
        </nav>

        {/* Theme Toggle */}
        <div className="p-4 border-t border-border">
          <button
            onClick={onToggleTheme}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-foreground hover:bg-muted transition-colors focus-ring touch-target"
          >
            {isDark ? (
              <>
                <Sun className="w-5 h-5 text-muted-foreground" />
                <span className="font-medium">Light Mode</span>
              </>
            ) : (
              <>
                <Moon className="w-5 h-5 text-muted-foreground" />
                <span className="font-medium">Dark Mode</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SideDrawer;
