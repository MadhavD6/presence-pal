import { useState, useEffect, useCallback, useRef } from 'react';
import { X, MapPin, Camera, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import CameraPreview, { CameraPreviewHandle } from './CameraPreview';
import { api } from '@/services/api';
import { useToast } from '@/hooks/use-toast';

interface ClockCaptureScreenProps {
  type: 'in' | 'out';
  location?: string;
  onCapture: (name?: string) => void;
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
  const [captureProgress, setCaptureProgress] = useState(0); // 0-5 frames
  const [captureStatus, setCaptureStatus] = useState<string>("");
  const [retryCount, setRetryCount] = useState(0);
  const MAX_RETRIES = 2;

  // Burst Capture State
  const [capturedBlobs, setCapturedBlobs] = useState<Blob[]>([]);
  const capturedBlobsRef = useRef<Blob[]>([]); // Sync ref for safety check

  const cameraRef = useRef<CameraPreviewHandle>(null);
  const { toast } = useToast();

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

  // Handle accumulation and submission
  useEffect(() => {
    capturedBlobsRef.current = capturedBlobs; // Keep ref in sync
    if (capturedBlobs.length === 5) {
      setCaptureStatus("Verifying identity...");
      processIdentification(capturedBlobs);
      setCapturedBlobs([]); // Reset
      capturedBlobsRef.current = [];
    } else if (capturedBlobs.length > 0) {
      setCaptureProgress(capturedBlobs.length);
    }
  }, [capturedBlobs]);

  const handleCapture = useCallback(async () => {
    if (isCapturing || !cameraRef.current) return;
    setIsCapturing(true);
    setCapturedBlobs([]);
    capturedBlobsRef.current = [];
    setCaptureProgress(0);
    setCaptureStatus("Capturing frames...");

    // Burst Capture: 5 Frames
    console.log("Starting Burst ID Capture...");
    for (let i = 0; i < 5; i++) {
      cameraRef.current.capture();
      await new Promise(r => setTimeout(r, 150)); // 150ms delay
    }

    // Safety Timeout: If for some reason we don't get 5 frames (lag/error), 
    // don't hang forever. Wait 2s extra then force proceed.
    setTimeout(() => {
      if (capturedBlobsRef.current.length > 0 && capturedBlobsRef.current.length < 5) {
        console.warn("Capture timeout - proceeding with partial frames", capturedBlobsRef.current.length);
        setCaptureStatus("Verifying identity (partial)...");
        processIdentification(capturedBlobsRef.current);
        setCapturedBlobs([]);
        capturedBlobsRef.current = [];
      } else if (capturedBlobsRef.current.length === 0 && isCapturing) {
        // Still 0 after timeout? 
        toast({
          title: "Camera Error",
          description: "No frames captured. Please check camera permissions.",
          variant: "destructive"
        });
        setIsCapturing(false);
        setCaptureStatus("Capture Failed");
      }
    }, 2000);

  }, [isCapturing]);

  const onImageCaptured = (blob: Blob) => {
    setCapturedBlobs(prev => [...prev, blob]);
  };

  const processIdentification = async (blobs: Blob[]) => {
    try {
      const response = await api.identify(blobs, type);

      if (response.status === 'success') {
        setCaptureStatus("Success!");
        onCapture(response.user?.name); // Trigger success in parent with name
      } else {
        // Auto-retry on no_face error
        if (response.error_code === 'no_face_detected' && retryCount < MAX_RETRIES) {
          setRetryCount(prev => prev + 1);
          setCaptureStatus(`No face found. Check lighting... Retrying (${retryCount + 1}/${MAX_RETRIES})`);
          setIsCapturing(false);
          setCaptureProgress(0);
          // Auto retry after a short delay
          setTimeout(() => handleCapture(), 500);
          return;
        }

        toast({
          title: "Authentication Failed",
          description: response.reason || "Could not identify user",
          variant: "destructive"
        });
        setIsCapturing(false);
        setCaptureProgress(0);
        setCaptureStatus("");
        setRetryCount(0);
      }
    } catch (error) {
      console.error(error);
      toast({
        title: "Error",
        description: "Failed to connect to server",
        variant: "destructive"
      });
      setIsCapturing(false);
      setCaptureProgress(0);
      setCaptureStatus("");
      setRetryCount(0);
    }
  };

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
      {/* Header */}
      <div className="p-4 md:p-6 border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="max-w-md mx-auto flex items-start justify-between">
          <div className="space-y-1">
            <h1 className="text-2xl font-bold text-foreground">{title}</h1>
            <div className="flex flex-col gap-0.5 text-sm text-muted-foreground">
              <span className="font-medium">{formatTime(currentTime)} • {formatDate(currentTime)}</span>
              <div className="flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5" />
                <span>{location}</span>
              </div>
            </div>
          </div>

          {/* Close Button */}
          <button
            onClick={onClose}
            className="w-10 h-10 rounded-full bg-muted flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col items-center justify-center p-4">
        <div className="w-full max-w-md space-y-4">

          {/* Camera Frame */}
          <div className="aspect-[4/3] rounded-2xl overflow-hidden border-2 border-border relative bg-black/5 shadow-2xl">
            <CameraPreview
              ref={cameraRef}
              className="w-full h-full"
              showCameraSwitch={true}
              showHelperText={true}
              helperText="Ensure your face is clearly visible"
              onCapture={onImageCaptured}
            />

            {/* Capture Progress Overlay */}
            {isCapturing && (
              <div className="absolute inset-0 bg-black/40 flex flex-col items-center justify-center gap-3">
                <div className="flex items-center gap-2">
                  {captureProgress < 5 ? (
                    <Camera className="w-8 h-8 text-white animate-pulse" />
                  ) : (
                    <Loader2 className="w-8 h-8 text-white animate-spin" />
                  )}
                </div>

                {/* Progress Dots */}
                <div className="flex gap-2">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div
                      key={i}
                      className={`w-3 h-3 rounded-full transition-all duration-200 ${i <= captureProgress
                        ? 'bg-green-400 scale-110'
                        : 'bg-white/30'
                        }`}
                    />
                  ))}
                </div>

                <span className="text-white text-sm font-medium">
                  {captureStatus}
                </span>
              </div>
            )}
          </div>

          {/* Action Button */}
          <Button
            onClick={handleCapture}
            disabled={isCapturing}
            className={`w-full h-16 text-lg font-bold shadow-lg transition-all active:scale-[0.98] ${buttonColor}`}
          >
            {isCapturing ? (
              <span className="flex items-center gap-2">
                <Loader2 className="w-5 h-5 animate-spin" />
                {captureProgress < 5 ? `Capturing... ${captureProgress}/5` : 'Verifying...'}
              </span>
            ) : (
              'Capture Attendance'
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ClockCaptureScreen;

