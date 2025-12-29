import { useState } from 'react';
import { ArrowLeft, Camera, User, Briefcase, MapPin, Phone, BadgeCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import CameraPreview from './CameraPreview';

interface EmployeeRegistrationScreenProps {
  onSubmit: () => void;
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
  });
  const [photoCaptured, setPhotoCaptured] = useState(false);

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleCapturePhoto = () => {
    setPhotoCaptured(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit();
  };

  const isFormValid = formData.fullName && formData.employeeId && formData.department && formData.location && photoCaptured;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-background/95 backdrop-blur border-b border-border px-4 py-3 md:px-6 md:py-4">
        <div className="max-w-2xl mx-auto flex items-center gap-3">
          <button
            onClick={onCancel}
            className="w-10 h-10 rounded-full hover:bg-muted flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-lg md:text-xl font-semibold text-foreground">Employee Registration</h1>
            <p className="text-sm text-muted-foreground hidden sm:block">Register to use the attendance system</p>
          </div>
        </div>
      </header>

      {/* Form Content */}
      <main className="max-w-2xl mx-auto px-4 py-6 md:px-6 md:py-8 space-y-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Personal Information Card */}
          <Card>
            <CardHeader className="pb-4">
              <CardTitle className="text-base md:text-lg flex items-center gap-2">
                <User className="w-5 h-5 text-primary" />
                Personal Information
              </CardTitle>
              <CardDescription>Enter your basic details</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="fullName">Full Name *</Label>
                <Input
                  id="fullName"
                  placeholder="Enter your full name"
                  value={formData.fullName}
                  onChange={(e) => handleInputChange('fullName', e.target.value)}
                  className="h-12"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="employeeId">Employee ID *</Label>
                <div className="relative">
                  <BadgeCheck className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                  <Input
                    id="employeeId"
                    placeholder="Enter your employee ID"
                    value={formData.employeeId}
                    onChange={(e) => handleInputChange('employeeId', e.target.value)}
                    className="h-12 pl-10"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Work Information Card */}
          <Card>
            <CardHeader className="pb-4">
              <CardTitle className="text-base md:text-lg flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-primary" />
                Work Information
              </CardTitle>
              <CardDescription>Your department and location details</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="department">Department *</Label>
                <Input
                  id="department"
                  placeholder="e.g., Engineering, Sales, HR"
                  value={formData.department}
                  onChange={(e) => handleInputChange('department', e.target.value)}
                  className="h-12"
                />
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
                    className="h-12 pl-10"
                  />
                </div>
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
                    className="h-12 pl-10"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Face Registration Card */}
          <Card>
            <CardHeader className="pb-4">
              <CardTitle className="text-base md:text-lg flex items-center gap-2">
                <Camera className="w-5 h-5 text-primary" />
                Face Registration
              </CardTitle>
              <CardDescription>Capture your face for attendance verification</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="aspect-[4/3] rounded-lg overflow-hidden border border-border relative">
                <CameraPreview className="w-full h-full" />
                {photoCaptured && (
                  <div className="absolute inset-0 bg-success/20 flex items-center justify-center">
                    <div className="bg-success text-success-foreground px-4 py-2 rounded-full text-sm font-medium">
                      Photo Captured ✓
                    </div>
                  </div>
                )}
              </div>
              <Button
                type="button"
                variant={photoCaptured ? "secondary" : "default"}
                onClick={handleCapturePhoto}
                className="w-full h-12"
              >
                <Camera className="w-5 h-5 mr-2" />
                {photoCaptured ? 'Retake Photo' : 'Capture Photo'}
              </Button>
            </CardContent>
          </Card>

          {/* Form Actions */}
          <div className="flex flex-col sm:flex-row gap-3 pt-4">
            <Button
              type="submit"
              disabled={!isFormValid}
              className="flex-1 h-14 text-base font-semibold bg-primary hover:bg-primary/90"
            >
              Submit Registration
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              className="flex-1 sm:flex-none sm:w-32 h-14 text-base"
            >
              Cancel
            </Button>
          </div>
        </form>
      </main>
    </div>
  );
};

export default EmployeeRegistrationScreen;
