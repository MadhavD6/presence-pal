import { useEffect } from 'react';
import { Check } from 'lucide-react';

interface SuccessOverlayProps {
  message?: string;
  onComplete: () => void;
  duration?: number;
}

const SuccessOverlay = ({ 
  message = "Success!", 
  onComplete, 
  duration = 800 
}: SuccessOverlayProps) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onComplete();
    }, duration);

    return () => clearTimeout(timer);
  }, [onComplete, duration]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-success animate-fade-in">
      <div className="flex flex-col items-center gap-4 animate-success-scale-in">
        <div className="w-24 h-24 md:w-32 md:h-32 rounded-full bg-success-foreground/20 flex items-center justify-center">
          <Check 
            className="w-14 h-14 md:w-20 md:h-20 text-success-foreground animate-checkmark-draw" 
            strokeWidth={3}
          />
        </div>
        <p className="text-2xl md:text-3xl font-semibold text-success-foreground animate-slide-up">
          {message}
        </p>
      </div>
    </div>
  );
};

export default SuccessOverlay;
