import { useState, useEffect, useRef } from 'react';
import { ArrowLeft, Camera, User, Briefcase, MapPin, Phone, BadgeCheck, CheckCircle2, Lightbulb } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import CameraPreview, { CameraPreviewHandle } from './CameraPreview';
import { api } from '@/services/api';
import { useToast } from '@/hooks/use-toast';

interface EmployeeRegistrationScreenProps {
  onSubmit: (name?: string, employeeId?: string) => void;
  onCancel: () => void;
}

const EmployeeRegistrationScreen = ({
  onSubmit,
  onCancel,
}: EmployeeRegistrationScreenProps) => {
  const [formData, setFormData] = useState({
    fullName: '',
    employeeId: '',
    department: '',
    location: '',
    mobileNumber: '',
    password: '',
  });
  const [photoCaptured, setPhotoCaptured] = useState(false);
  const [photoBlob, setPhotoBlob] = useState<Blob | null>(null);
  const [capturedBlobs, setCapturedBlobs] = useState<Blob[]>([]); // New state for burst
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const cameraRef = useRef<CameraPreviewHandle>(null);
  const { toast } = useToast();

  // ... existing useEffect ...

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleCapturePhoto = async () => {
    // ... capture logic ...
    console.log("Registration Screen: Capture Clicked (Burst Mode)");
    if (!cameraRef.current) return;

    // Reset
    setCapturedBlobs([]);
    setPhotoCaptured(false);

    const blobs: Blob[] = [];

    // Burst Capture: 5 Frames
    for (let i = 0; i < 5; i++) {
      // Trigger capture
      cameraRef.current.capture();
      await new Promise(r => setTimeout(r, 150)); // 150ms delay
    }
  };

  const onImageCaptured = (blob: Blob) => {
    // Append to list
    setCapturedBlobs(prev => {
      const newBlobs = [...prev, blob];
      setPhotoBlob(blob);
      setPhotoCaptured(true);
      return newBlobs.slice(-5); // Keep last 5 just in case
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (capturedBlobs.length === 0 && photoBlob) {
      // Fallback if burst failed or single capture
      capturedBlobs.push(photoBlob);
    }

    if (capturedBlobs.length === 0) return;

    setIsSubmitting(true);
    try {
      const data = new FormData();
      data.append('name', formData.fullName);
      data.append('employee_id', formData.employeeId);
      if (formData.password) {
        data.append('password', formData.password);
      }

      // Append all blobs as 'files'
      capturedBlobs.forEach((blob, idx) => {
        data.append('files', blob, `enroll_${idx}.jpg`);
      });

      const response = await api.enroll(data);
      console.log("Enrollment success:", response);
      onSubmit(formData.fullName, response.employee_id);
    } catch (err: any) {
      console.error("Enrollment failed", err);
      toast({
        title: "Registration Failed",
        description: err.message || "Could not complete registration. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Step completion checks
  const isStep1Complete = Boolean(formData.fullName && formData.password && formData.password.length >= 6);
  const isStep2Complete = Boolean(formData.department && formData.location);
  const isStep3Complete = photoCaptured;
  const isFormValid = isStep1Complete && isStep2Complete && isStep3Complete;

  // Field completion indicator component
  const FieldIndicator = ({ isComplete }: { isComplete: boolean }) => (
    <div className={`absolute right-3 top-1/2 -translate-y-1/2 transition-all duration-200 ${isComplete ? 'opacity-100 scale-100' : 'opacity-0 scale-75'}`}>
      <CheckCircle2 className="w-5 h-5 text-success" />
    </div>
  );

  // Step indicator component
  const StepIndicator = ({ step, label, isComplete, isCurrent }: { step: number; label: string; isComplete: boolean; isCurrent: boolean }) => (
    <div className="flex items-center gap-2">
      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-colors ${isComplete ? 'bg-success text-success-foreground' :
        isCurrent ? 'bg-primary text-primary-foreground' :
          'bg-muted text-muted-foreground'
        }`}>
        {isComplete ? <CheckCircle2 className="w-4 h-4" /> : step}
      </div>
      <span className={`text-sm font-medium hidden sm:block ${isCurrent ? 'text-foreground' : 'text-muted-foreground'}`}>
        {label}
      </span>
    </div>
  );

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-background/95 backdrop-blur border-b border-border px-4 py-3 md:px-6 md:py-4">
        <div className="max-w-2xl mx-auto flex items-center gap-3">
          <button
            onClick={onCancel}
            className="w-12 h-12 rounded-full hover:bg-muted flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors focus-ring touch-target"
            aria-label="Go back"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-lg md:text-xl font-semibold text-foreground">Employee Registration</h1>
            <p className="text-sm text-muted-foreground hidden sm:block">Register to use the attendance system</p>
          </div>
        </div>
      </header>

      {/* Step Progress */}
      <div className="max-w-2xl mx-auto px-4 py-4 md:px-6">
        <div className="flex items-center justify-between">
          <StepIndicator step={1} label="Personal" isComplete={isStep1Complete} isCurrent={currentStep === 1} />
          <div className="flex-1 h-0.5 bg-border mx-2">
            <div className={`h-full bg-success transition-all duration-300 ${isStep1Complete ? 'w-full' : 'w-0'}`} />
          </div>
          <StepIndicator step={2} label="Work Info" isComplete={isStep2Complete} isCurrent={currentStep === 2} />
          <div className="flex-1 h-0.5 bg-border mx-2">
            <div className={`h-full bg-success transition-all duration-300 ${isStep2Complete ? 'w-full' : 'w-0'}`} />
          </div>
          <StepIndicator step={3} label="Face" isComplete={isStep3Complete} isCurrent={currentStep === 3} />
        </div>
      </div>

      {/* Form Content */}
      <main className="max-w-2xl mx-auto px-4 pb-8 md:px-6 space-y-5">
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Step 1: Personal Information Card */}
          <Card
            className={`transition-all duration-200 ${currentStep === 1 ? 'ring-2 ring-primary/20' : ''}`}
            onClick={() => setCurrentStep(1)}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base md:text-lg flex items-center gap-2">
                  <User className="w-5 h-5 text-primary" />
                  Step 1: Personal Information
                </CardTitle>
                {isStep1Complete && <CheckCircle2 className="w-5 h-5 text-success" />}
              </div>
              <CardDescription>Enter your basic details</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="fullName">Full Name *</Label>
                <div className="relative">
                  <Input
                    id="fullName"
                    placeholder="Enter your full name"
                    value={formData.fullName}
                    onChange={(e) => handleInputChange('fullName', e.target.value)}
                    className="h-12 pr-10 focus-ring"
                  />
                  <FieldIndicator isComplete={Boolean(formData.fullName)} />
                </div>
                <FieldError show={!formData.fullName} message="Full Name is required" />
              </div>

              <div className="space-y-2">
                <Label htmlFor="employeeId">Employee ID</Label>
                {/* ... existing employeeId code ... */}
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Password *</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type="password"
                    placeholder="Create a password"
                    value={formData.password}
                    onChange={(e) => handleInputChange('password', e.target.value)}
                    className="h-12 pr-10 focus-ring"
                  />
                  <FieldIndicator isComplete={Boolean(formData.password && formData.password.length >= 6)} />
                </div>
                <FieldError show={!formData.password} message="Password is required" />
                <FieldError show={Boolean(formData.password && formData.password.length < 6)} message="Password must be at least 6 characters" />
              </div>
            </CardContent>
          </Card>

          {/* Step 2: Work Information Card */}
          <Card
            className={`transition-all duration-200 ${currentStep === 2 ? 'ring-2 ring-primary/20' : ''}`}
            onClick={() => setCurrentStep(2)}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base md:text-lg flex items-center gap-2">
                  <Briefcase className="w-5 h-5 text-primary" />
                  Step 2: Work Information
                </CardTitle>
                {isStep2Complete && <CheckCircle2 className="w-5 h-5 text-success" />}
              </div>
              <CardDescription>Your department and location details</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="department">Department *</Label>
                <div className="relative">
                  <Input
                    id="department"
                    placeholder="e.g., Engineering, Sales, HR"
                    value={formData.department}
                    onChange={(e) => handleInputChange('department', e.target.value)}
                    className="h-12 pr-10 focus-ring"
                  />
                  <FieldIndicator isComplete={Boolean(formData.department)} />
                </div>
                <FieldError show={!formData.department} message="Department is required" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="location">Location *</Label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                  <Input
                    id="location"
                    placeholder="e.g., Corporate Office, Branch A"
                    value={formData.location}
                    onChange={(e) => handleInputChange('location', e.target.value)}
                    className="h-12 pl-10 pr-10 focus-ring"
                  />
                  <FieldIndicator isComplete={Boolean(formData.location)} />
                </div>
                <FieldError show={!formData.location} message="Location is required" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="mobileNumber">Mobile Number (Optional)</Label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                  <Input
                    id="mobileNumber"
                    placeholder="+1 (555) 123-4567"
                    value={formData.mobileNumber}
                    onChange={(e) => handleInputChange('mobileNumber', e.target.value)}
                    className="h-12 pl-10 focus-ring"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Step 3: Face Registration Card */}
          <Card
            className={`transition-all duration-200 ${currentStep === 3 ? 'ring-2 ring-primary/20' : ''}`}
            onClick={() => setCurrentStep(3)}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base md:text-lg flex items-center gap-2">
                  <Camera className="w-5 h-5 text-primary" />
                  Step 3: Face Registration
                </CardTitle>
                {isStep3Complete && <CheckCircle2 className="w-5 h-5 text-success" />}
              </div>
              <CardDescription>Capture your face for attendance verification</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Guidance tips */}
              <div className="flex items-start gap-2 p-3 rounded-lg bg-muted/50 text-sm text-muted-foreground">
                <Lightbulb className="w-4 h-4 mt-0.5 shrink-0" />
                <p>Ensure good lighting. Stand naturally — your full photo will be captured.</p>
              </div>

              <div className="aspect-[4/3] rounded-lg overflow-hidden border border-border relative">
                <CameraPreview
                  ref={cameraRef}
                  className="w-full h-full"
                  showCameraSwitch={true}
                  showHelperText={true}
                  helperText="Full photo will be captured automatically"
                  onCapture={onImageCaptured}
                />
                {photoCaptured && (
                  <div className="absolute inset-0 bg-success/20 flex items-center justify-center animate-fade-in">
                    <div className="bg-success text-success-foreground px-4 py-2 rounded-full text-sm font-medium flex items-center gap-2 shadow-lg">
                      <CheckCircle2 className="w-4 h-4" />
                      Photo Captured
                    </div>
                  </div>
                )}
              </div>
              <Button
                type="button"
                variant={photoCaptured ? "secondary" : "default"}
                onClick={handleCapturePhoto}
                className="w-full h-12 transition-all duration-200 active:animate-button-press focus-ring touch-target"
              >
                <Camera className="w-5 h-5 mr-2" />
                {photoCaptured ? 'Retake Photo' : 'Capture Photo'}
              </Button>
              <FieldError show={!photoCaptured} message="Face photo is required" />
            </CardContent>
          </Card>

          {/* Form Actions */}
          <div className="flex flex-col sm:flex-row gap-3 pt-2">
            <Button
              type="submit"
              disabled={!isFormValid || isSubmitting}
              className="flex-1 h-14 text-base font-semibold bg-primary hover:bg-primary/90 shadow-lg hover:shadow-xl transition-all duration-200 active:animate-button-press disabled:opacity-50 focus-ring touch-target"
            >
              {isSubmitting ? 'Registering...' : 'Submit Registration'}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              className="flex-1 sm:flex-none sm:w-32 h-14 text-base transition-colors focus-ring touch-target"
            >
              Cancel
            </Button>
          </div>
          {/* Validation Help Text removed in favor of field-level hints */}
        </form>
      </main>
    </div>
  );
};

// Helper for inline validation
const FieldError = ({ show, message }: { show: boolean; message: string }) => (
  show ? <p className="text-xs text-destructive font-medium mt-1 animate-pulse">{message}</p> : null
);

export default EmployeeRegistrationScreen;
