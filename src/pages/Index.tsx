import { useState, useEffect } from 'react';
import AttendanceHomeScreen from '@/components/attendance/AttendanceHomeScreen';
import ClockCaptureScreen from '@/components/attendance/ClockCaptureScreen';
import EmployeeRegistrationScreen from '@/components/attendance/EmployeeRegistrationScreen';
import SuccessOverlay from '@/components/attendance/SuccessOverlay';

type Screen = 'home' | 'clockIn' | 'clockOut' | 'register';

const Index = () => {
  const [currentScreen, setCurrentScreen] = useState<Screen>('home');
  const [showSuccess, setShowSuccess] = useState(false);
  const [successType, setSuccessType] = useState<'in' | 'out' | 'registration'>('in');
  const [isDark, setIsDark] = useState(false);

  // Apply dark mode class to document
  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDark]);

  const handleToggleTheme = () => {
    setIsDark(prev => !prev);
  };

  const handleClockInCapture = () => {
    setSuccessType('in');
    setShowSuccess(true);
  };

  const handleClockOutCapture = () => {
    setSuccessType('out');
    setShowSuccess(true);
  };

  const handleRegistrationSubmit = () => {
    setSuccessType('registration');
    setShowSuccess(true);
  };

  const handleSuccessComplete = () => {
    setShowSuccess(false);
    setCurrentScreen('home');
  };

  const handleClose = () => {
    setCurrentScreen('home');
  };

  return (
    <>
      {/* Success Overlay - shown on top of everything */}
      {showSuccess && (
        <SuccessOverlay
          type={successType}
          message="Attendance Marked"
          onComplete={handleSuccessComplete}
          duration={700}
        />
      )}

      {/* Screen Router */}
      {currentScreen === 'home' && (
        <AttendanceHomeScreen
          isDark={isDark}
          onToggleTheme={handleToggleTheme}
          onClockIn={() => setCurrentScreen('clockIn')}
          onClockOut={() => setCurrentScreen('clockOut')}
          onRegister={() => setCurrentScreen('register')}
        />
      )}

      {currentScreen === 'clockIn' && (
        <ClockCaptureScreen
          type="in"
          onCapture={handleClockInCapture}
          onClose={handleClose}
        />
      )}

      {currentScreen === 'clockOut' && (
        <ClockCaptureScreen
          type="out"
          onCapture={handleClockOutCapture}
          onClose={handleClose}
        />
      )}

      {currentScreen === 'register' && (
        <EmployeeRegistrationScreen
          onSubmit={handleRegistrationSubmit}
          onCancel={handleClose}
        />
      )}
    </>
  );
};

export default Index;
