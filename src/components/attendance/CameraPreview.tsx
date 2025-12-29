import { Camera, Video } from 'lucide-react';

interface CameraPreviewProps {
  className?: string;
  showFaceOverlay?: boolean;
  showHelperText?: boolean;
  helperText?: string;
}

const CameraPreview = ({ 
  className = '', 
  showFaceOverlay = false,
  showHelperText = false,
  helperText = "Align your face and tap capture"
}: CameraPreviewProps) => {
  return (
    <div 
      className={`relative bg-gradient-to-br from-muted to-muted/60 flex items-center justify-center overflow-hidden ${className}`}
    >
      {/* Simulated camera feed pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0 bg-[linear-gradient(45deg,transparent_25%,hsl(var(--foreground)/0.03)_25%,hsl(var(--foreground)/0.03)_50%,transparent_50%,transparent_75%,hsl(var(--foreground)/0.03)_75%)] bg-[length:20px_20px]" />
      </div>
      
      {/* Face framing overlay - soft oval */}
      {showFaceOverlay && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          {/* Darkened corners */}
          <div className="absolute inset-0 bg-foreground/10" />
          {/* Clear oval center */}
          <div 
            className="relative w-56 h-72 md:w-64 md:h-80 rounded-[50%] border-2 border-primary/40 shadow-[0_0_0_9999px_rgba(0,0,0,0.15)]"
            style={{
              background: 'transparent',
            }}
          />
        </div>
      )}

      {/* Center camera icon */}
      <div className="flex flex-col items-center gap-3 text-muted-foreground z-10">
        <div className="w-20 h-20 md:w-24 md:h-24 rounded-full border-2 border-dashed border-muted-foreground/30 flex items-center justify-center bg-background/20 backdrop-blur-sm">
          <Camera className="w-10 h-10 md:w-12 md:h-12 opacity-50" />
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-background/60 backdrop-blur-sm">
          <Video className="w-3.5 h-3.5 text-success animate-pulse" />
          <p className="text-sm font-medium">Live Preview</p>
        </div>
      </div>

      {/* Corner brackets for visual framing */}
      <div className="absolute top-6 left-6 md:top-8 md:left-8 w-10 h-10 md:w-12 md:h-12 border-l-2 border-t-2 border-foreground/20 rounded-tl-lg" />
      <div className="absolute top-6 right-6 md:top-8 md:right-8 w-10 h-10 md:w-12 md:h-12 border-r-2 border-t-2 border-foreground/20 rounded-tr-lg" />
      <div className="absolute bottom-6 left-6 md:bottom-8 md:left-8 w-10 h-10 md:w-12 md:h-12 border-l-2 border-b-2 border-foreground/20 rounded-bl-lg" />
      <div className="absolute bottom-6 right-6 md:bottom-8 md:right-8 w-10 h-10 md:w-12 md:h-12 border-r-2 border-b-2 border-foreground/20 rounded-br-lg" />

      {/* Helper text */}
      {showHelperText && (
        <div className="absolute bottom-20 md:bottom-24 left-0 right-0 text-center">
          <p className="text-sm text-muted-foreground/80 bg-background/60 backdrop-blur-sm inline-block px-4 py-2 rounded-full">
            {helperText}
          </p>
        </div>
      )}
    </div>
  );
};

export default CameraPreview;
