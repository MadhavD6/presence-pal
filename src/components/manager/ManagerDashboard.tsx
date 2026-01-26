import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { ChevronDown, Bell, LayoutDashboard, FileText, DollarSign, Store, LogOut, Calendar, Users } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { ManagerStats } from './ManagerStats';
import { ManagerKioskView } from './ManagerKioskView';
import { ManagerPayrollScreen } from './ManagerPayrollScreen';
import { ManagerHolidaysScreen } from './ManagerHolidaysScreen';
import { ManagerApprovalsScreen } from './ManagerApprovalsScreen';
import { ManagerReportsView } from './ManagerReportsView';
import { ManagerShiftsScreen } from './ManagerShiftsScreen';
import { ClipboardCheck, Clock } from 'lucide-react';

import { ManagerEmployeesScreen } from './ManagerEmployeesScreen';

type Tab = 'overview' | 'kiosks' | 'reports' | 'payroll' | 'holidays' | 'approvals' | 'shifts' | 'employees';

interface ManagerDashboardProps {
    onBack?: () => void;
}

export const ManagerDashboard: React.FC<ManagerDashboardProps> = ({ onBack }) => {
    const [activeTab, setActiveTab] = useState<Tab>('overview');
    const { logout } = useAuth();
    const orgName = "Prodify Innovatives";

    return (
        <div className="min-h-screen bg-background flex flex-col">
            {/* Header */}
            <div className="p-4 pt-6 pb-2 space-y-4">
                <div className="flex items-center justify-between">
                    <h1 className="text-2xl font-bold">Dashboard</h1>
                    <Button variant="ghost" size="icon" className="rounded-full bg-muted/50">
                        <Bell className="w-5 h-5 text-foreground" />
                    </Button>
                </div>

                {/* Org Dropdown */}
                <div className="flex items-center gap-2 bg-white dark:bg-card border border-border rounded-lg px-3 py-2 w-max shadow-sm">
                    <span className="font-medium text-sm">{orgName}</span>
                    <ChevronDown className="w-4 h-4 text-muted-foreground" />
                </div>

                {/* Tabs */}
                <div className="flex bg-muted/30 p-1 rounded-xl gap-1 overflow-x-auto no-scrollbar">
                    <button
                        onClick={() => setActiveTab('overview')}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${activeTab === 'overview' ? 'bg-primary text-primary-foreground shadow-md' : 'text-muted-foreground hover:bg-background/50 hover:text-foreground'}`}
                    >
                        <LayoutDashboard className="w-4 h-4" />
                        Overview
                    </button>
                    <button
                        onClick={() => setActiveTab('employees')}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${activeTab === 'employees' ? 'bg-primary text-primary-foreground shadow-md' : 'text-muted-foreground hover:bg-background/50 hover:text-foreground'}`}
                    >
                        <Users className="w-4 h-4" />
                        Employees
                    </button>
                    <button
                        onClick={() => setActiveTab('approvals')}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${activeTab === 'approvals' ? 'bg-primary text-primary-foreground shadow-md' : 'text-muted-foreground hover:bg-background/50 hover:text-foreground'}`}
                    >
                        <ClipboardCheck className="w-4 h-4" />
                        Approvals
                    </button>
                    <button
                        onClick={() => setActiveTab('reports')}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${activeTab === 'reports' ? 'bg-primary text-primary-foreground shadow-md' : 'text-muted-foreground hover:bg-background/50 hover:text-foreground'}`}
                    >
                        <FileText className="w-4 h-4" />
                        Reports
                    </button>
                    <button
                        onClick={() => setActiveTab('kiosks')}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${activeTab === 'kiosks' ? 'bg-primary text-primary-foreground shadow-md' : 'text-muted-foreground hover:bg-background/50 hover:text-foreground'}`}
                    >
                        <Store className="w-4 h-4" />
                        Kiosks
                    </button>
                    <button
                        onClick={() => setActiveTab('holidays')}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${activeTab === 'holidays' ? 'bg-primary text-primary-foreground shadow-md' : 'text-muted-foreground hover:bg-background/50 hover:text-foreground'}`}
                    >
                        <Calendar className="w-4 h-4" />
                        Holidays
                    </button>
                    <button
                        onClick={() => setActiveTab('payroll')}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${activeTab === 'payroll' ? 'bg-primary text-primary-foreground shadow-md' : 'text-muted-foreground hover:bg-background/50 hover:text-foreground'}`}
                    >
                        <DollarSign className="w-4 h-4" />
                        Payroll
                    </button>
                    <button
                        onClick={() => setActiveTab('shifts')}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${activeTab === 'shifts' ? 'bg-primary text-primary-foreground shadow-md' : 'text-muted-foreground hover:bg-background/50 hover:text-foreground'}`}
                    >
                        <Clock className="w-4 h-4" />
                        Shifts
                    </button>
                </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-y-auto px-4 pb-20">
                {activeTab === 'overview' && <ManagerStats />}
                {activeTab === 'kiosks' && <ManagerKioskView />}
                {activeTab === 'payroll' && <ManagerPayrollScreen />}
                {activeTab === 'holidays' && <ManagerHolidaysScreen />}
                {activeTab === 'shifts' && <ManagerShiftsScreen />}
                {activeTab === 'reports' && <ManagerReportsView />}
                {activeTab === 'approvals' && <ManagerApprovalsScreen />}
                {activeTab === 'employees' && <ManagerEmployeesScreen />}
            </div>

            {/* Bottom Nav */}
            <nav className="fixed bottom-0 left-0 right-0 bg-card border-t border-border px-6 py-2 flex justify-between items-center z-50 pb-safe">
                <button
                    onClick={() => setActiveTab('overview')}
                    className={`flex flex-col items-center gap-1 p-2 ${activeTab === 'overview' ? 'text-primary' : 'text-muted-foreground hover:text-foreground'}`}>
                    <div className={`${activeTab === 'overview' ? 'bg-primary/10' : ''} p-1 rounded`}>
                        <LayoutDashboard className="w-5 h-5" />
                    </div>
                    <span className="text-[10px] font-medium">Dashboard</span>
                </button>
                <button
                    onClick={() => {
                        logout();
                        if (onBack) onBack();
                    }}
                    className="flex flex-col items-center gap-1 p-2 text-muted-foreground hover:text-destructive transition-colors">
                    <LogOut className="w-5 h-5" />
                    <span className="text-[10px] font-medium">Logout</span>
                </button>
            </nav>
        </div>
    );
};

export default ManagerDashboard;
