import { useState } from 'react';
import { Video, SwitchCamera } from 'lucide-react';

interface CameraPreviewProps {
  className?: string;
  showCameraSwitch?: boolean;
  showHelperText?: boolean;
  helperText?: string;
}

const CameraPreview = ({ 
  className = '', 
  showCameraSwitch = false,
  showHelperText = false,
  helperText = "Full photo will be captured automatically"
}: CameraPreviewProps) => {
  const [cameraMode, setCameraMode] = useState<'front' | 'back'>('front');

  const handleSwitchCamera = () => {
    setCameraMode(prev => prev === 'front' ? 'back' : 'front');
  };

  return (
    <div 
      className={`relative bg-gradient-to-br from-muted to-muted/60 flex items-center justify-center overflow-hidden ${className}`}
    >
      {/* Simulated camera feed pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0 bg-[linear-gradient(45deg,transparent_25%,hsl(var(--foreground)/0.03)_25%,hsl(var(--foreground)/0.03)_50%,transparent_50%,transparent_75%,hsl(var(--foreground)/0.03)_75%)] bg-[length:20px_20px]" />
      </div>

      {/* Camera Switch Button - Top Right */}
      {showCameraSwitch && (
        <button
          onClick={handleSwitchCamera}
          className="absolute top-4 right-4 md:top-6 md:right-6 z-20 w-12 h-12 md:w-14 md:h-14 rounded-full bg-card/80 backdrop-blur flex items-center justify-center shadow-lg hover:bg-card active:scale-95 transition-all duration-150 focus-ring touch-target"
          aria-label={`Switch to ${cameraMode === 'front' ? 'back' : 'front'} camera`}
        >
          <SwitchCamera 
            className={`w-5 h-5 md:w-6 md:h-6 text-primary transition-transform duration-300 ${cameraMode === 'back' ? 'scale-x-[-1]' : ''}`} 
          />
        </button>
      )}

      {/* Camera mode indicator */}
      {showCameraSwitch && (
        <div className="absolute top-4 left-4 md:top-6 md:left-6 z-20 px-3 py-1.5 rounded-full bg-card/80 backdrop-blur text-xs font-medium text-muted-foreground">
          {cameraMode === 'front' ? 'Front Camera' : 'Back Camera'}
        </div>
      )}

      {/* Center content - Full frame indicator */}
      <div className="flex flex-col items-center gap-3 text-muted-foreground z-10">
        <div className="w-20 h-20 md:w-24 md:h-24 rounded-lg border-2 border-dashed border-muted-foreground/30 flex items-center justify-center bg-background/20 backdrop-blur-sm">
          <Video className="w-10 h-10 md:w-12 md:h-12 opacity-50" />
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-background/60 backdrop-blur-sm">
          <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
          <p className="text-sm font-medium">Live Preview</p>
        </div>
      </div>

      {/* Corner brackets for visual framing - full frame capture indication */}
      <div className="absolute top-4 left-4 md:top-6 md:left-6 w-8 h-8 md:w-10 md:h-10 border-l-2 border-t-2 border-foreground/20 rounded-tl-md" />
      <div className="absolute top-4 right-4 md:top-6 md:right-6 w-8 h-8 md:w-10 md:h-10 border-r-2 border-t-2 border-foreground/20 rounded-tr-md" />
      <div className="absolute bottom-4 left-4 md:bottom-6 md:left-6 w-8 h-8 md:w-10 md:h-10 border-l-2 border-b-2 border-foreground/20 rounded-bl-md" />
      <div className="absolute bottom-4 right-4 md:bottom-6 md:right-6 w-8 h-8 md:w-10 md:h-10 border-r-2 border-b-2 border-foreground/20 rounded-br-md" />

      {/* Helper text - subtle, non-instructional */}
      {showHelperText && (
        <div className="absolute bottom-16 md:bottom-20 left-0 right-0 text-center">
          <p className="text-xs text-muted-foreground/70 bg-background/50 backdrop-blur-sm inline-block px-3 py-1.5 rounded-full">
            {helperText}
          </p>
        </div>
      )}
    </div>
  );
};

export default CameraPreview;
