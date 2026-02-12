import { useState, useRef, useEffect, forwardRef, useImperativeHandle } from 'react';
import { Video, SwitchCamera } from 'lucide-react';

interface CameraPreviewProps {
  className?: string;
  showCameraSwitch?: boolean;
  showHelperText?: boolean;
  helperText?: string;
  onCapture?: (blob: Blob) => void;
}

export interface CameraPreviewHandle {
  capture: () => void;
}

const CameraPreview = forwardRef<CameraPreviewHandle, CameraPreviewProps>(({
  className = '',
  showCameraSwitch = false,
  showHelperText = false,
  helperText = "Full photo will be captured automatically",
  onCapture
}, ref) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [cameraMode, setCameraMode] = useState<'user' | 'environment'>('user');
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    startCamera();
    return () => stopCamera();
  }, [cameraMode]);

  const startCamera = async () => {
    try {
      if (streamRef.current) {
        stopCamera();
      }

      // 1. Check for Secure Context (HTTPS/Localhost)
      if (!window.isSecureContext) {
        throw new Error("INSECURE_CONTEXT: Camera requires HTTPS or Localhost");
      }

      // 2. Check if mediaDevices exists
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("UNSUPPORTED_BROWSER: Camera API not available");
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: cameraMode }
      });

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setHasPermission(true);
    } catch (err: any) {
      console.error("Camera access denied:", err);
      setHasPermission(false);

      // Log specific reason for debugging
      let reason = "Unknown Error";
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        reason = "Permission Denied: Please allow camera access in browser settings.";
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        reason = "No Camera Found: Please ensure camera is connected.";
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        reason = "Camera In Use: Please close other apps using the camera.";
      } else if (err.message && err.message.includes("INSECURE_CONTEXT")) {
        reason = "Insecure Connection: Camera requires HTTPS. Please use the secure Cloudflare link.";
      }

      // Update helper text if possible, or just log
      console.warn("Camera Failure Reason:", reason);
      setErrorMessage(reason);
      // We could use a toast here if we imported it, but for now console is good enough for remote debug
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
  };

  const handleSwitchCamera = () => {
    setCameraMode(prev => prev === 'user' ? 'environment' : 'user');
  };

  useImperativeHandle(ref, () => ({
    capture: () => {
      if (videoRef.current && canvasRef.current && onCapture) {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        const context = canvas.getContext('2d');

        if (context) {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          context.drawImage(video, 0, 0, canvas.width, canvas.height);

          canvas.toBlob((blob) => {
            if (blob) {
              onCapture(blob);
            }
          }, 'image/jpeg', 0.95);
        }
      }
    }
  }));

  return (
    <div
      className={`relative bg-background flex items-center justify-center overflow-hidden ${className}`}
    >
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className={`absolute inset-0 w-full h-full object-cover ${cameraMode === 'user' ? 'scale-x-[-1]' : ''}`}
      />
      <canvas ref={canvasRef} className="hidden" />

      {hasPermission === false && (
        <div className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-background/90 text-center p-4">
          <Video className="w-12 h-12 mb-4 text-muted-foreground" />
          <h3 className="text-lg font-semibold mb-2">Camera Access Required</h3>
          <p className="text-sm text-muted-foreground mb-4">Please allow camera access to use this feature.</p>
          {errorMessage && (
            <div className="bg-destructive/10 p-3 rounded-md max-w-xs">
              <p className="text-xs text-destructive font-medium">{errorMessage}</p>
            </div>
          )}
        </div>
      )}

      {/* Simulated camera feed pattern overlay (optional, maybe remove for clarity or keep for style) */}
      <div className="absolute inset-0 pointer-events-none opacity-10">
        <div className="absolute inset-0 bg-[linear-gradient(45deg,transparent_25%,hsl(var(--foreground)/0.03)_25%,hsl(var(--foreground)/0.03)_50%,transparent_50%,transparent_75%,hsl(var(--foreground)/0.03)_75%)] bg-[length:20px_20px]" />
      </div>

      {/* Camera Switch Button - Top Right */}
      {showCameraSwitch && (
        <button
          onClick={handleSwitchCamera}
          type="button"
          className="absolute top-4 right-4 md:top-6 md:right-6 z-20 w-12 h-12 md:w-14 md:h-14 rounded-full bg-card/80 backdrop-blur flex items-center justify-center shadow-lg hover:bg-card active:scale-95 transition-all duration-150 focus-ring touch-target"
          aria-label={`Switch to ${cameraMode === 'user' ? 'back' : 'front'} camera`}
        >
          <SwitchCamera
            className={`w-5 h-5 md:w-6 md:h-6 text-primary transition-transform duration-300 ${cameraMode === 'environment' ? 'scale-x-[-1]' : ''}`}
          />
        </button>
      )}

      {/* Center content - Full frame indicator (Removed for cleaner real view usually, but preserving "Live Preview" badge) */}
      {hasPermission !== false && (
        <div className="absolute top-4 left-4 md:top-6 md:left-6 z-20 flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-background/60 backdrop-blur-sm">
          <div className={`w-2 h-2 rounded-full ${hasPermission ? 'bg-success animate-pulse' : 'bg-yellow-500'}`} />
          <p className="text-sm font-medium">{hasPermission ? 'Live' : 'Initializing...'}</p>
        </div>
      )}

      {/* Corner brackets for visual framing */}
      <div className="absolute top-4 left-4 md:top-6 md:left-6 w-8 h-8 md:w-10 md:h-10 border-l-2 border-t-2 border-foreground/20 rounded-tl-md pointer-events-none" />
      <div className="absolute top-4 right-4 md:top-6 md:right-6 w-8 h-8 md:w-10 md:h-10 border-r-2 border-t-2 border-foreground/20 rounded-tr-md pointer-events-none" />
      <div className="absolute bottom-4 left-4 md:bottom-6 md:left-6 w-8 h-8 md:w-10 md:h-10 border-l-2 border-b-2 border-foreground/20 rounded-bl-md pointer-events-none" />
      <div className="absolute bottom-4 right-4 md:bottom-6 md:right-6 w-8 h-8 md:w-10 md:h-10 border-r-2 border-b-2 border-foreground/20 rounded-br-md pointer-events-none" />

      {/* Helper text */}
      {showHelperText && (
        <div className="absolute bottom-16 md:bottom-20 left-0 right-0 text-center pointer-events-none">
          <p className="text-xs text-muted-foreground/70 bg-background/50 backdrop-blur-sm inline-block px-3 py-1.5 rounded-full">
            {helperText}
          </p>
        </div>
      )}
    </div>
  );
});

CameraPreview.displayName = "CameraPreview";

export default CameraPreview;
