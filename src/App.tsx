import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { useEffect } from "react";
import { syncService } from "./services/sync";
import { AuthProvider } from "./context/AuthContext";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";


const queryClient = new QueryClient();

const App = () => {
  useEffect(() => {
    syncService.start();
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<Index />} />
              <Route path="/employee" element={<EmployeeRoute />} />
              <Route path="/manager" element={<ManagerRoute />} />
              <Route path="/register" element={<RegisterRoute />} />
              <Route path="/setup" element={<KioskSetupRoute />} />
              {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </TooltipProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
};

// Wrapper components for routes to handle props and navigation
import EmployeeDashboard from "@/components/employee/EmployeeDashboard";
import EmployeeLogin from "@/pages/EmployeeLogin";
import ManagerDashboard from "@/components/manager/ManagerDashboard";
import EmployeeRegistrationScreen from "@/components/attendance/EmployeeRegistrationScreen";
import { useAuth } from "@/context/AuthContext";
import { useNavigate } from "react-router-dom";

const EmployeeRoute = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  // If not authenticated, show Login. If authenticated, show Dashboard.
  // We pass simple navigation handlers.

  if (!isAuthenticated) {
    return <EmployeeLogin onBack={() => navigate('/')} onLoginSuccess={() => { }} />;
  }
  return <EmployeeDashboard onBack={() => navigate('/')} />;
};

const ManagerRoute = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <EmployeeLogin onBack={() => navigate('/')} onLoginSuccess={() => { }} />;
  }

  return <ManagerDashboard onBack={() => navigate('/')} />;
};

const RegisterRoute = () => {
  const navigate = useNavigate();
  // using alert for stability - toast caused white screen issues
  return (
    <EmployeeRegistrationScreen
      onSubmit={(name, employeeId) => {
        // Simple, reliable success feedback
        window.alert(`Registration Successful!\n\nWelcome ${name}!\nYour Employee ID is: ${employeeId}`);
        navigate('/');
      }}
      onCancel={() => navigate('/')}
    />
  )
}

import KioskSetupPage from "@/pages/KioskSetupPage";
import { useToast } from "@/hooks/use-toast";

const KioskSetupRoute = () => {
  return <KioskSetupPage />;
};

export default App;
