import { useState, useEffect, useCallback } from 'react';
import { X, MapPin } from 'lucide-react';
import { Button } from '@/components/ui/button';
import CameraPreview from './CameraPreview';

interface ClockCaptureScreenProps {
  type: 'in' | 'out';
  location?: string;
  onCapture: () => void;
  onClose: () => void;
}

const ClockCaptureScreen = ({
  type,
  location = "Corporate Office",
  onCapture,
  onClose,
}: ClockCaptureScreenProps) => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [isCapturing, setIsCapturing] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Enter' && !isCapturing) {
        handleCapture();
      } else if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isCapturing, onClose]);

  const handleCapture = useCallback(() => {
    if (isCapturing) return;
    setIsCapturing(true);
    // Simulate capture delay
    setTimeout(() => {
      onCapture();
    }, 200);
  }, [isCapturing, onCapture]);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    });
  };

  const isClockIn = type === 'in';
  const title = isClockIn ? 'Clock In' : 'Clock Out';
  const buttonColor = isClockIn
    ? 'bg-success hover:bg-success/90 text-success-foreground shadow-success/30'
    : 'bg-destructive hover:bg-destructive/90 text-destructive-foreground shadow-destructive/30';

  return (
    <div className="fixed inset-0 z-40 flex flex-col bg-background">
      {/* Camera Preview Area */}
      <CameraPreview 
        className="flex-1" 
        showCameraSwitch={true}
        showHelperText={true}
        helperText="Full photo will be captured automatically"
      />

      {/* Overlay Header */}
      <div className="absolute top-0 left-0 right-0 p-4 md:p-6 bg-gradient-to-b from-background/90 via-background/60 to-transparent">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <h1 className="text-2xl md:text-3xl font-bold text-foreground">{title}</h1>
            <div className="flex flex-col gap-0.5 text-sm text-muted-foreground">
              <span className="font-medium">{formatTime(currentTime)} • {formatDate(currentTime)}</span>
              <div className="flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5" />
                <span>{location}</span>
              </div>
            </div>
          </div>
          
          {/* Camera switch is now in CameraPreview component */}
          <div className="w-12 h-12 md:w-14 md:h-14" />
        </div>
      </div>

      {/* Bottom Action Bar */}
      <div className="absolute bottom-0 left-0 right-0 p-4 md:p-6 bg-gradient-to-t from-background via-background/95 to-transparent">
        <div className="max-w-md mx-auto space-y-3">
          <Button
            onClick={handleCapture}
            disabled={isCapturing}
            className={`w-full h-16 md:h-18 text-lg md:text-xl font-bold shadow-xl hover:shadow-2xl transition-all duration-200 active:animate-button-press disabled:opacity-70 focus-ring touch-target ${buttonColor}`}
          >
            {isCapturing ? 'Capturing...' : 'Click to Capture'}
          </Button>
        </div>
      </div>

      {/* Close Button */}
      <button
        onClick={onClose}
        className="absolute bottom-6 right-6 md:bottom-8 md:right-8 w-14 h-14 rounded-full bg-card/80 backdrop-blur shadow-lg flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-card transition-colors focus-ring touch-target"
        aria-label="Close"
      >
        <X className="w-6 h-6" />
      </button>
    </div>
  );
};

export default ClockCaptureScreen;
