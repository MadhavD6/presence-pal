import { useEffect } from 'react';
import { Check } from 'lucide-react';

interface SuccessOverlayProps {
  type?: 'in' | 'out' | 'registration';
  message?: string;
  onComplete: () => void;
  duration?: number;
}

const SuccessOverlay = ({ 
  type = 'in',
  message = "Attendance Marked", 
  onComplete, 
  duration = 700 
}: SuccessOverlayProps) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onComplete();
    }, duration);

    return () => clearTimeout(timer);
  }, [onComplete, duration]);

  // Determine background color based on type
  const bgColor = type === 'out' ? 'bg-destructive' : 'bg-success';
  const checkBgColor = type === 'out' ? 'bg-destructive-foreground/20' : 'bg-success-foreground/20';
  const textColor = type === 'out' ? 'text-destructive-foreground' : 'text-success-foreground';

  return (
    <div className={`fixed inset-0 z-50 flex items-center justify-center ${bgColor} animate-fade-in`}>
      <div className="flex flex-col items-center gap-5 animate-success-scale-in">
        {/* Checkmark circle */}
        <div className={`w-28 h-28 md:w-36 md:h-36 rounded-full ${checkBgColor} flex items-center justify-center`}>
          <Check 
            className={`w-16 h-16 md:w-20 md:h-20 ${textColor} animate-checkmark-draw`}
            strokeWidth={3}
          />
        </div>
        
        {/* Success text */}
        <div className="text-center space-y-1 animate-slide-up">
          <p className={`text-2xl md:text-3xl font-bold ${textColor}`}>
            {message}
          </p>
          <p className={`text-sm md:text-base ${textColor}/80`}>
            {type === 'in' ? 'Clock In Successful' : type === 'out' ? 'Clock Out Successful' : 'Registration Complete'}
          </p>
        </div>
      </div>
    </div>
  );
};

export default SuccessOverlay;
