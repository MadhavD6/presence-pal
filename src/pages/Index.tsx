import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import AttendanceHomeScreen from '@/components/attendance/AttendanceHomeScreen';
import ClockCaptureScreen from '@/components/attendance/ClockCaptureScreen';
import EmployeeRegistrationScreen from '@/components/attendance/EmployeeRegistrationScreen';
import EmployeeDashboard from '@/components/employee/EmployeeDashboard';
import EmployeeLogin from '@/pages/EmployeeLogin';
import ManagerDashboard from '@/components/manager/ManagerDashboard';
import KioskRegistrationScreen from '@/components/admin/KioskRegistrationScreen';
import SuccessOverlay from '@/components/attendance/SuccessOverlay';
import { api } from '@/services/api';
import { toast } from 'sonner';

type Screen = 'home' | 'clockIn' | 'clockOut' | 'register' | 'employee' | 'manager' | 'kioskRegister';

const Index = () => {
  // Initialize from localStorage or default to 'home'
  const [currentScreen, setCurrentScreenState] = useState<Screen>(() => {
    return (localStorage.getItem('last_screen') as Screen) || 'home';
  });

  // Wrapper to update state and localStorage
  const setCurrentScreen = (screen: Screen) => {
    localStorage.setItem('last_screen', screen);
    setCurrentScreenState(screen);
  };
  const { isAuthenticated } = useAuth();
  const [showSuccess, setShowSuccess] = useState(false);
  const [successType, setSuccessType] = useState<'in' | 'out' | 'registration'>('in');
  const [successName, setSuccessName] = useState<string | undefined>(undefined);
  const [isDark, setIsDark] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [queueCount, setQueueCount] = useState(0);
  const [isSyncing, setIsSyncing] = useState(false);

  // Silent Auto-Registration on Mount
  useEffect(() => {
    const checkAndRegister = async () => {
      const key = localStorage.getItem('kiosk_api_key');
      if (!key) {
        console.log("No Kiosk Key found. Auto-registering...");
        try {
          // Generate Random ID
          const randomSuffix = Math.random().toString(36).substring(2, 7).toUpperCase();
          const deviceId = `AUTO-KIOSK-${randomSuffix}`;

          const { api_key } = await api.registerKiosk(deviceId, "Auto-Location", "Auto-Building");
          localStorage.setItem('kiosk_api_key', api_key);

          toast.success("Device Registered Successfully", {
            description: `ID: ${deviceId}`,
            duration: 3000
          });

        } catch (error) {
          console.error("Auto-registration failed:", error);
          toast.error("Auto-registration Failed. Please check console.");
        }
      }
    };

    checkAndRegister();
  }, []);

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

  useEffect(() => {
    const handleStatusChange = () => {
      setIsOnline(navigator.onLine);
    };

    window.addEventListener('online', handleStatusChange);
    window.addEventListener('offline', handleStatusChange);

    return () => {
      window.removeEventListener('online', handleStatusChange);
      window.removeEventListener('offline', handleStatusChange);
    };
  }, []);

  // Poll offline queue count
  useEffect(() => {
    const checkQueue = () => {
      import('@/services/offlineStorage').then(({ offlineStorage }) => {
        const queue = offlineStorage.getQueue();
        setQueueCount(queue.length);
      });
    };

    checkQueue();
    const interval = setInterval(checkQueue, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleManualSync = async () => {
    if (!isOnline) return;
    setIsSyncing(true);
    try {
      const { offlineStorage } = await import('@/services/offlineStorage');
      const queue = offlineStorage.getQueue();
      if (queue.length === 0) {
        toast.info("No items to sync");
        return;
      }

      const { api } = await import('@/services/api');
      await api.syncPunches(queue);
      offlineStorage.clearQueue();
      setQueueCount(0);
      toast.success("Sync Complete", { description: `${queue.length} records synced` });
    } catch (error) {
      console.error("Sync failed", error);
      toast.error("Sync Failed", { description: "Could not upload offline records" });
    } finally {
      setIsSyncing(false);
    }
  };

  const handleClockInCapture = (name?: string) => {
    setSuccessType('in');
    setSuccessName(name);
    setShowSuccess(true);
  };

  const handleClockOutCapture = (name?: string) => {
    setSuccessType('out');
    setSuccessName(name);
    setShowSuccess(true);
  };

  const handleRegistrationSubmit = (name?: string) => {
    setSuccessType('registration');
    setSuccessName(name);
    setShowSuccess(true);
  };

  const handleSuccessComplete = () => {
    setShowSuccess(false);
    setSuccessName(undefined);
    setCurrentScreen('home');
  };

  const handleClose = () => {
    setCurrentScreen('home');
  };

  const handleKioskRegistered = () => {
    setCurrentScreen('home');
  };

  return (
    <>
      {/* Success Overlay - shown on top of everything */}
      {showSuccess && (
        <SuccessOverlay
          type={successType}
          message="Attendance Marked"
          userName={successName}
          onComplete={handleSuccessComplete}
          duration={2000} // Increased duration to read message
        />
      )}

      {/* Screen Router */}
      {currentScreen === 'kioskRegister' && (
        <KioskRegistrationScreen onSuccess={handleKioskRegistered} />
      )}

      {currentScreen === 'home' && (
        <AttendanceHomeScreen
          isDark={isDark}
          onToggleTheme={handleToggleTheme}
          onClockIn={() => setCurrentScreen('clockIn')}
          onClockOut={() => setCurrentScreen('clockOut')}
          onRegister={() => setCurrentScreen('register')}
          onEmployee={() => setCurrentScreen('employee')}
          onManager={() => setCurrentScreen('manager')}
          isOnline={isOnline}
          queueCount={queueCount}
          isSyncing={isSyncing}
          onManualSync={handleManualSync}
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

      {currentScreen === 'employee' && (
        isAuthenticated ? (
          <EmployeeDashboard
            onBack={handleClose}
          />
        ) : (
          <EmployeeLogin
            onBack={handleClose}
            onLoginSuccess={() => { }} // AuthContext handles state, this just confirms
          />
        )
      )}

      {currentScreen === 'manager' && (
        <ManagerDashboard
          onBack={handleClose}
        />
      )}
    </>
  );
};

export default Index;
