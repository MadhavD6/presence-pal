import { useState, useEffect } from 'react';
import { Camera, X, MapPin } from 'lucide-react';
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

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

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
    ? 'bg-success hover:bg-success/90 text-success-foreground'
    : 'bg-destructive hover:bg-destructive/90 text-destructive-foreground';

  return (
    <div className="fixed inset-0 z-40 flex flex-col bg-background">
      {/* Camera Preview Area */}
      <CameraPreview className="flex-1" />

      {/* Overlay Header */}
      <div className="absolute top-0 left-0 right-0 p-4 md:p-6 bg-gradient-to-b from-background/90 to-transparent">
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
          
          {/* Decorative Camera Icon */}
          <div className="w-10 h-10 md:w-12 md:h-12 rounded-full bg-card/80 backdrop-blur flex items-center justify-center shadow-lg">
            <Camera className="w-5 h-5 md:w-6 md:h-6 text-muted-foreground" />
          </div>
        </div>
      </div>

      {/* Bottom Action Bar */}
      <div className="absolute bottom-0 left-0 right-0 p-4 md:p-6 bg-gradient-to-t from-background via-background/95 to-transparent">
        <div className="max-w-md mx-auto space-y-3">
          <Button
            onClick={onCapture}
            className={`w-full h-14 md:h-16 text-base md:text-lg font-semibold shadow-xl ${buttonColor}`}
          >
            Click to Capture
          </Button>
        </div>
      </div>

      {/* Close Button */}
      <button
        onClick={onClose}
        className="absolute bottom-6 right-6 md:bottom-8 md:right-8 w-12 h-12 rounded-full bg-card/80 backdrop-blur shadow-lg flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors"
      >
        <X className="w-5 h-5" />
      </button>
    </div>
  );
};

export default ClockCaptureScreen;
