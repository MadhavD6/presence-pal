import { Camera } from 'lucide-react';

interface CameraPreviewProps {
  className?: string;
}

const CameraPreview = ({ className = '' }: CameraPreviewProps) => {
  return (
    <div 
      className={`relative bg-gradient-to-br from-muted to-muted/60 flex items-center justify-center ${className}`}
    >
      {/* Simulated camera feed pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0 bg-[linear-gradient(45deg,transparent_25%,hsl(var(--foreground)/0.03)_25%,hsl(var(--foreground)/0.03)_50%,transparent_50%,transparent_75%,hsl(var(--foreground)/0.03)_75%)] bg-[length:20px_20px]" />
      </div>
      
      {/* Center camera icon */}
      <div className="flex flex-col items-center gap-3 text-muted-foreground">
        <div className="w-20 h-20 md:w-28 md:h-28 rounded-full border-4 border-dashed border-muted-foreground/30 flex items-center justify-center">
          <Camera className="w-10 h-10 md:w-14 md:h-14 opacity-50" />
        </div>
        <p className="text-sm md:text-base font-medium opacity-60">Camera Preview</p>
      </div>

      {/* Corner brackets for visual framing */}
      <div className="absolute top-8 left-8 w-12 h-12 border-l-2 border-t-2 border-foreground/20 rounded-tl-lg" />
      <div className="absolute top-8 right-8 w-12 h-12 border-r-2 border-t-2 border-foreground/20 rounded-tr-lg" />
      <div className="absolute bottom-8 left-8 w-12 h-12 border-l-2 border-b-2 border-foreground/20 rounded-bl-lg" />
      <div className="absolute bottom-8 right-8 w-12 h-12 border-r-2 border-b-2 border-foreground/20 rounded-br-lg" />
    </div>
  );
};

export default CameraPreview;
