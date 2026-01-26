import { useState } from 'react';
import { Home, User, MoreHorizontal, Calendar, ChevronRight, LogOut } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useQuery } from '@tanstack/react-query';
import { employeeApi } from '@/services/api';
import { useAuth } from '@/context/AuthContext';
import { useNavigate } from 'react-router-dom';
import TimesheetScreen from './TimesheetScreen';
import TimecardScreen from './TimecardScreen';
import LeaveHistoryScreen from './LeaveHistoryScreen';
import ApplyLeaveScreen from './ApplyLeaveScreen';
import { PayslipScreen } from './PayslipScreen';
import MonthYearPicker from './MonthYearPicker';
import PunchDetailsSheet from './PunchDetailsSheet';

interface EmployeeDashboardProps {
    onBack: () => void;
}

type ViewState = 'overview' | 'scan' | 'punch-details' | 'timesheet' | 'timecard' | 'leaves' | 'apply-leave' | 'leave-history' | 'payslips';

const EmployeeDashboard = ({ onBack }: EmployeeDashboardProps) => {
    const [activeTab, setActiveTab] = useState('home');
    const [currentView, setCurrentView] = useState<ViewState>('overview');
    const [selectedDate, setSelectedDate] = useState<Date>(new Date());
    const { logout, isAuthenticated } = useAuth();
    const navigate = useNavigate();

    // New State for UI interactions
    const [isMonthPickerOpen, setIsMonthPickerOpen] = useState(false);
    const [selectedPunch, setSelectedPunch] = useState<any>(null);
    const [historyTab, setHistoryTab] = useState<'leaves' | 'corrections'>('leaves');

    // Data Fetching
    const { data: dashboardData, isLoading, error } = useQuery({
        queryKey: ['employeeDashboard'],
        queryFn: () => employeeApi.getDashboard(),
        retry: 2, // Retry up to 2 times on failure
        retryDelay: 500, // Wait 500ms between retries
        enabled: isAuthenticated, // Only run if authenticated
    });

    const handleLogout = () => {
        logout();
        onBack();
    };

    if (isLoading) {
        return <div className="min-h-screen flex items-center justify-center bg-background text-foreground">Loading Dashboard...</div>;
    }

    if (error) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-background text-foreground gap-4 p-4">
                <p className="text-destructive font-medium">Failed to load dashboard data. Please contact your manager.</p>
                <Button variant="ghost" onClick={handleLogout}>Back to Home</Button>
            </div>
        );
    }

    // Process Data
    const employeeName = dashboardData?.name || "Employee";
    const employeeId = dashboardData?.employee_id || "ID-000";
    const shifts = dashboardData?.shifts || [];
    const todayStatus = dashboardData?.today_status || "Absent";
    const workedHours = dashboardData?.worked_hours || "0h 0m";
    const isLate = dashboardData?.is_late || false;
    const lateMinutes = dashboardData?.late_minutes || 0;
    const recentPunches = dashboardData?.recent_punches || []; // Not yet in basic response, let's use what we have

    // Mock Punch for Home Screen (if real data is missing detail, or use today's status)
    // We are generating 'recent_punches' in dashboard API, but schema didn't fully expose simple list?
    // Let's rely on dashboardData for now.

    // Helper to format shift
    const formatShift = (shift: any) => ({
        day: shift.day,
        date: new Date(shift.date).getDate().toString(),
        type: shift.shift_name === 'General' ? 'S8' : 'S?',
        isToday: new Date(shift.date).toDateString() === new Date().toDateString(),
        isOff: shift.shift_name === 'WO'
    });

    const displayShifts = shifts.map(formatShift);

    if (currentView === 'timesheet') {
        return (
            <TimesheetScreen
                initialDate={selectedDate}
                onBack={() => setCurrentView('overview')}
                onDateSelect={(date) => {
                    setSelectedDate(date);
                    setCurrentView('timecard');
                }}
            />
        );
    }

    if (currentView === 'timecard') {
        return (
            <TimecardScreen
                date={selectedDate}
                onBack={() => setCurrentView('timesheet')}
            />
        );
    }

    if (currentView === 'leave-history') {
        return (
            <LeaveHistoryScreen
                onBack={() => setCurrentView('overview')}
                onApplyLeave={() => setCurrentView('apply-leave')}
                defaultTab={historyTab}
            />
        );
    }

    if (currentView === 'apply-leave') {
        return (
            <ApplyLeaveScreen
                onBack={() => setCurrentView('leave-history')}
            />
        );
    }

    return (
        <div className="min-h-screen bg-background flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Top Header */}
            <header className="px-4 py-4 bg-primary text-primary-foreground">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center text-lg font-bold">
                            {employeeName.charAt(0)}
                        </div>
                        <div>
                            <h1 className="font-semibold text-lg">Hi {employeeName.split(' ')[0]}</h1>
                            <p className="text-xs opacity-80">{employeeId} | {dashboardData?.role || 'Staff'}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => navigate('/manager')}
                            className="text-xs font-semibold bg-white/20 hover:bg-white/30 text-white border-0 active:scale-95 transition-transform"
                        >
                            Manager View
                        </Button>
                        <Button variant="ghost" size="icon" onClick={handleLogout} className="text-primary-foreground hover:bg-white/20 active:scale-95 transition-transform">
                            <LogOut className="w-5 h-5" />
                        </Button>
                    </div>
                </div>
            </header>

            {/* Main Content Area */}
            <main className="flex-1 overflow-y-auto pb-20 p-4 space-y-6">

                {activeTab === 'home' && (
                    <div className="space-y-6 animate-fade-in">
                        {/* Status Card */}
                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center justify-between mb-4">
                                    <div>
                                        <p className="text-sm text-muted-foreground mb-1">Today's Status</p>
                                        <h2 className={`text-2xl font-bold ${todayStatus === 'In' ? 'text-green-500 animate-pulse' : 'text-foreground'}`}>
                                            {todayStatus}
                                            {isLate && (
                                                <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300" title={`Late by ${Math.floor(lateMinutes / 60)}h ${lateMinutes % 60}m`}>
                                                    Late ({Math.floor(lateMinutes / 60).toString().padStart(2, '0')}:{(lateMinutes % 60).toString().padStart(2, '0')})
                                                </span>
                                            )}
                                        </h2>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-sm text-muted-foreground mb-1">Worked</p>
                                        <p className="font-mono text-xl">{workedHours}</p>
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border">
                                    <div>
                                        <p className="text-xs text-muted-foreground">First In</p>
                                        <p className="font-medium text-sm">{dashboardData?.first_in || '-'}</p>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-xs text-muted-foreground">Last Out</p>
                                        <p className="font-medium text-sm">{dashboardData?.last_out || '-'}</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Shift Schedule */}
                        <div className="space-y-3">
                            <div className="flex items-center justify-between">
                                <h2 className="font-bold text-lg">My Shift Schedule</h2>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className="flex items-center gap-1 text-sm font-medium hover:bg-transparent active:scale-95 transition-transform"
                                    onClick={() => setIsMonthPickerOpen(true)}
                                >
                                    Jan 2026 <Calendar className="w-4 h-4 ml-1" />
                                </Button>
                            </div>
                            <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
                                {displayShifts.map((shift, idx) => (
                                    <div
                                        key={idx}
                                        onClick={() => setCurrentView('timesheet')}
                                        className={`flex-shrink-0 w-16 h-20 rounded-xl flex flex-col items-center justify-center gap-1 border cursor-pointer transition-transform active:scale-95 ${shift.isToday ? 'border-primary bg-primary/5' : 'border-border bg-card'} ${shift.isOff ? 'bg-muted/50' : ''}`}
                                    >
                                        <span className="text-xs text-muted-foreground">{shift.day}</span>
                                        <span className="text-lg font-bold">{shift.date}</span>
                                        <span className={`text-xs font-medium ${shift.isOff ? 'text-muted-foreground' : 'text-primary'}`}>{shift.type}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Punch Log Preview */}
                        <div className="space-y-3">
                            <h2 className="font-bold text-lg">Recent Activity</h2>
                            {recentPunches.length > 0 ? (
                                <div className="space-y-2">
                                    {recentPunches.map((punch: any, idx: number) => (
                                        <div
                                            key={idx}
                                            style={{ animationDelay: `${idx * 100}ms` }}
                                            className="bg-card rounded-xl border border-border p-4 flex items-center gap-4 hover:bg-muted/50 transition-colors animate-in fade-in slide-in-from-bottom-2 duration-300 fill-mode-backwards"
                                        >
                                            <div className="flex flex-col items-center gap-1">
                                                <span className={`font-bold text-sm ${punch.type === 'In' ? 'text-success' : 'text-orange-500'}`}>
                                                    Punch {punch.type}
                                                </span>
                                                <div className={`w-2 h-2 rounded-full ${punch.type === 'In' ? 'bg-success' : 'bg-orange-500'}`}></div>
                                                <div className="w-0.5 h-8 bg-border"></div>
                                            </div>
                                            <div className="flex-1">
                                                <h3 className="font-bold">{punch.time} | Today</h3>
                                                <div className="flex items-center gap-2">
                                                    <p className="text-xs text-muted-foreground">{dashboardData?.current_shift}</p>
                                                    {isLate && idx === 0 && (
                                                        <span className="text-[10px] text-red-500 font-medium">Latemark ({Math.floor(lateMinutes / 60).toString().padStart(2, '0')}:{(lateMinutes % 60).toString().padStart(2, '0')})</span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-sm text-muted-foreground">No recent punches today.</p>
                            )}
                        </div>
                    </div>
                )}

                {activeTab === 'profile' && (
                    <div className="space-y-6 animate-fade-in">
                        <Card>
                            <CardHeader>
                                <CardTitle>Profile Details</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div>
                                    <p className="text-sm text-muted-foreground">Full Name</p>
                                    <p className="font-medium">{employeeName}</p>
                                </div>
                                <div>
                                    <p className="text-sm text-muted-foreground">Employee ID</p>
                                    <p className="font-medium">{employeeId}</p>
                                </div>
                                <div>
                                    <p className="text-sm text-muted-foreground">Role</p>
                                    <p className="font-medium">{dashboardData?.role || 'User'}</p>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                )}

                {activeTab === 'more' && (
                    <div className="space-y-6 animate-fade-in">
                        <div className="space-y-2">
                            <h2 className="font-bold text-lg px-2">Time Tracking</h2>
                            <div className="bg-card rounded-xl border border-border overflow-hidden">
                                <div onClick={() => setCurrentView('timesheet')} className="flex items-center justify-between p-4 border-b border-border hover:bg-muted/50 cursor-pointer active:bg-muted/70 transition-colors">
                                    <span className="font-medium">My Timesheet</span>
                                    <ChevronRight className="w-5 h-5 text-muted-foreground" />
                                </div>
                                {['My Overtime History', 'My Reg History', 'My Shift & Weekly Off History'].map((item, i) => (
                                    <div key={i} className="flex items-center justify-between p-4 border-b border-border last:border-0 hover:bg-muted/50 cursor-pointer active:bg-muted/70 transition-colors"
                                        onClick={() => {
                                            if (item === 'My Reg History') {
                                                setHistoryTab('corrections');
                                                setCurrentView('leave-history');
                                            }
                                        }}
                                    >
                                        <span className="font-medium">{item}</span>
                                        <ChevronRight className="w-5 h-5 text-muted-foreground" />
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="space-y-2">
                            <h2 className="font-bold text-lg px-2">Leave Management</h2>
                            <div className="bg-card rounded-xl border border-border overflow-hidden">
                                <div onClick={() => setCurrentView('apply-leave')} className="flex items-center justify-between p-4 border-b border-border hover:bg-muted/50 cursor-pointer active:bg-muted/70 transition-colors">
                                    <span className="font-medium">Apply Leave</span>
                                    <ChevronRight className="w-5 h-5 text-muted-foreground" />
                                </div>
                                <div onClick={() => {
                                    setHistoryTab('leaves');
                                    setCurrentView('leave-history');
                                }} className="flex items-center justify-between p-4 border-b border-border hover:bg-muted/50 cursor-pointer active:bg-muted/70 transition-colors">
                                    <span className="font-medium">Leave History</span>
                                    <ChevronRight className="w-5 h-5 text-muted-foreground" />
                                </div>
                            </div>
                        </div>

                        {/* New Payslips Section */}
                        <div className="space-y-2">
                            <h2 className="font-bold text-lg px-2">Payroll</h2>
                            <div className="bg-card rounded-xl border border-border overflow-hidden">
                                <div onClick={() => setCurrentView('payslips')} className="flex items-center justify-between p-4 hover:bg-muted/50 cursor-pointer active:bg-muted/70 transition-colors">
                                    <span className="font-medium">My Payslips</span>
                                    <ChevronRight className="w-5 h-5 text-muted-foreground" />
                                </div>
                            </div>
                        </div>
                    </div>
                )}

            </main>

            {/* Bottom Navigation Bar */}
            <nav className="fixed bottom-0 left-0 right-0 bg-card border-t border-border px-6 py-2 flex justify-between items-center z-50 pb-safe">
                <button
                    onClick={() => setActiveTab('home')}
                    className={`flex flex-col items-center gap-1 p-2 rounded-lg transition-transform active:scale-95 ${activeTab === 'home' ? 'text-primary' : 'text-muted-foreground'}`}
                >
                    <Home className="w-6 h-6" />
                    <span className="text-xs font-medium">Home</span>
                </button>
                <button
                    onClick={() => setActiveTab('profile')}
                    className={`flex flex-col items-center gap-1 p-2 rounded-lg transition-transform active:scale-95 ${activeTab === 'profile' ? 'text-primary' : 'text-muted-foreground'}`}
                >
                    <User className="w-6 h-6" />
                    <span className="text-xs font-medium">Profile</span>
                </button>
                <button
                    onClick={() => setActiveTab('more')}
                    className={`flex flex-col items-center gap-1 p-2 rounded-lg transition-transform active:scale-95 ${activeTab === 'more' ? 'text-primary' : 'text-muted-foreground'}`}
                >
                    <MoreHorizontal className="w-6 h-6" />
                    <span className="text-xs font-medium">More</span>
                </button>
            </nav>

            {/* Overlays */}
            <MonthYearPicker
                isOpen={isMonthPickerOpen}
                onClose={() => setIsMonthPickerOpen(false)}
                currentDate={selectedDate}
                onSelect={(date) => {
                    setSelectedDate(date);
                    // In a real app, this would refresh the dashboard data for the selected month
                }}
            />

            <PunchDetailsSheet
                isOpen={!!selectedPunch}
                onClose={() => setSelectedPunch(null)}
                punch={selectedPunch}
                employeeName={employeeName}
            />

        </div>
    );
};

export default EmployeeDashboard;
