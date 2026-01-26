
const API_BASE_URL = '/api/v1';
import { offlineStorage } from './offlineStorage';

export interface User {
    id: number;
    name: string;
    employee_id?: string;
    role?: string;
    site_id?: number;
    site_name?: string;
    shift_id?: number;
}

export interface EnrollResponse {
    status: string;
    user_id: string;
}

export interface IdentifyResponse {
    status: 'success' | 'failure';
    user?: User;
    confidence?: number;
    reason?: string;
    error_code?: string;
}

// New interfaces for better type safety
export interface ManagerStats {
    active_employees: number;
    present_today: number;
    absent_today: number;
    late_today: number;
    on_leave: number;
    attendance_rate: number;
}

export interface ManagerReportEntry {
    employee_id: string;
    name: string;
    present_days: number;
    absent_days: number;
    late_days: number;
    total_hours: number;
    avg_hours: number;
}

export interface AuditLog {
    id: number;
    user_id: number;
    timestamp: string;
    event_type: 'in' | 'out';
    confidence: number;
    kiosk_id?: string;
    user_name: string;
}

export interface ManagerTimesheetEntry {
    id: number; // or user_id
    employee_id: string;
    name: string;
    date: string;
    status: string;
    in_time?: string;
    out_time?: string;
    total_hours?: string;
}

export interface OfflinePunchItem {
    user_id: number;
    timestamp: string;
    event_type: 'in' | 'out';
    confidence: number;
    kiosk_id: string;
}

export interface PayrollRunResponse {
    run_id: number;
    status: string;
    period_start: string;
    period_end: string;
}

export interface PayrollRun {
    id: number;
    period_start: string;
    period_end: string;
    status: string;
    created_at: string;
    processed_count: number;
    total_payout: number;
}

export interface PayrollSlip {
    id: number;
    user_id: number;
    user_name: string;
    net_salary: number;
    status: string;
    // add other fields as needed
}

export interface LeaveRequest {
    id: number;
    user_id: number;
    user_name: string;
    leave_type: string;
    start_date: string;
    end_date: string;
    reason: string;
    status: string;
    file_url?: string;
    created_at: string;
}

export interface CorrectionRequest {
    id: number;
    user_id: number;
    user_name: string;
    date: string;
    requested_in: string | null;
    requested_out: string | null;
    reason: string;
    status: string;
}

const getAuthHeaders = () => {
    const key = localStorage.getItem('kiosk_api_key');
    const headers: Record<string, string> = {};
    if (key) {
        headers['X-Kiosk-API-Key'] = key;
    }
    return headers;
};


const getEmployeeHeaders = () => {
    const token = localStorage.getItem('employee_access_token');
    const headers: Record<string, string> = {
        'Content-Type': 'application/json'
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
};

export const api = {
    // ... existing ...
    /**
     * Get manager statistics for a given date
     */
    async getManagerStats(date: Date): Promise<ManagerStats> {
        const dateStr = date.toISOString().split('T')[0];
        const response = await fetch(`${API_BASE_URL}/manager/stats?date_str=${dateStr}`, {
            method: 'GET',
            headers: getAuthHeaders(),
        });
        if (!response.ok) throw new Error('Failed to fetch manager stats');
        return response.json();
    },

    async getManagerDetailedReport(from: Date, to: Date): Promise<ManagerReportEntry[]> {
        const fromStr = from.toISOString().split('T')[0];
        const toStr = to.toISOString().split('T')[0];
        const response = await fetch(`${API_BASE_URL}/manager/reports/detailed?start_date_str=${fromStr}&end_date_str=${toStr}`, {
            method: 'GET',
            headers: getAuthHeaders(),
        });
        if (!response.ok) throw new Error('Failed to fetch detailed report');
        return response.json();
    },

    async downloadManagerReport(from: Date, to: Date): Promise<Blob> {
        const fromStr = from.toISOString().split('T')[0];
        const toStr = to.toISOString().split('T')[0];
        const response = await fetch(`${API_BASE_URL}/manager/reports/export?start_date_str=${fromStr}&end_date_str=${toStr}`, {
            method: 'GET',
            headers: getAuthHeaders(),
        });
        if (!response.ok) throw new Error('Failed to download report');
        return response.blob();
    },
    // ... rest of existing api object ...
    async getManagerLogs(date: Date): Promise<AuditLog[]> {
        const dateStr = date.toISOString().split('T')[0];
        const response = await fetch(`${API_BASE_URL}/manager/daily-log?date_str=${dateStr}`, {
            method: 'GET',
            headers: getAuthHeaders(),
        });
        if (!response.ok) throw new Error('Failed to fetch manager logs');
        return response.json();
    },

    async getManagerTimesheet(startDate: Date, endDate: Date): Promise<ManagerTimesheetEntry[]> {
        const startStr = startDate.toISOString().split('T')[0];
        const endStr = endDate.toISOString().split('T')[0];
        const response = await fetch(`${API_BASE_URL}/manager/timesheet?start_date_str=${startStr}&end_date_str=${endStr}`, {
            method: 'GET',
            headers: getAuthHeaders(),
        });
        if (!response.ok) throw new Error('Failed to fetch timesheet');
        return response.json();
    },

    async registerKiosk(deviceId: string, location: string, building: string): Promise<{ api_key: string }> {
        const params = new URLSearchParams({
            device_id: deviceId,
            location: location,
            building: building
        });
        const response = await fetch(`${API_BASE_URL}/kiosk/register?${params.toString()}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });
        if (!response.ok) throw new Error('Registration failed');
        return response.json();
    },

    async enroll(data: FormData): Promise<EnrollResponse> {
        const headers = getAuthHeaders();
        // Remove Content-Type header to allow browser to set boundary for FormData
        delete headers['Content-Type'];

        const response = await fetch(`${API_BASE_URL}/admin/enroll`, {
            method: 'POST',
            headers: headers,
            body: data,
        });
        if (!response.ok) {
            const text = await response.text();
            try {
                const err = JSON.parse(text);
                throw new Error(err.detail || `Enrollment failed: ${response.statusText}`);
            } catch (e) {
                throw new Error(`Enrollment failed (${response.status}): ${text || response.statusText}`);
            }
        }
        return response.json();
    },

    identify: async (images: Blob[], type: 'in' | 'out'): Promise<IdentifyResponse> => {
        const formData = new FormData();
        images.forEach((img, idx) => {
            formData.append('file', img, `capture_${idx}.jpg`);
        });
        formData.append('type', type);

        try {
            const response = await fetch(`${API_BASE_URL}/kiosk/identify`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: formData,
            });

            if (!response.ok) {
                const errText = await response.text();
                console.error("Server Identify Error:", response.status, errText);
                throw new Error(`Identification failed: ${response.status} ${errText}`);
            }
            return response.json();
        } catch (error) {
            console.error("Identify failed, checking offline...", error);

            // Check if actually offline
            if (!navigator.onLine) {
                // SIMULATION FOR OFFLINE TESTING
                // In a real app we'd need local face matching.
                // For now, we queue a 'Simulated' punch to demonstrate Phase 6 Sync.
                const simulatedUserId = 999;

                offlineStorage.saveToQueue({
                    user_id: simulatedUserId,
                    timestamp: new Date().toISOString(),
                    event_type: type,
                    confidence: 1.0,
                    kiosk_id: 'offline-kiosk'
                });

                return {
                    status: 'success',
                    confidence: 1.0,
                    user: { id: 999, name: 'Saved Offline (Simulated)' },
                    reason: 'offline_queue'
                };
            }
            throw error;
        }
    },

    syncPunches: async (items: OfflinePunchItem[]) => {
        const response = await fetch(`${API_BASE_URL}/kiosk/sync`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
            body: JSON.stringify(items)
        });
        if (!response.ok) throw new Error('Sync failed');
        return response.json();
    }
};

export const managerApi = {
    generatePayroll: async (startDate: Date, endDate: Date): Promise<PayrollRunResponse> => {
        const start = startDate.toISOString().split('T')[0];
        const end = endDate.toISOString().split('T')[0];
        const response = await fetch(`${API_BASE_URL}/manager/payroll/generate?start_date=${start}&end_date=${end}`, {
            method: 'POST',
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Failed to generate payroll');
        return response.json();
    },

    getPayrollRuns: async (): Promise<PayrollRun[]> => {
        const response = await fetch(`${API_BASE_URL}/manager/payroll/runs`, {
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch payroll runs');
        return response.json();
    },

    getPayrollRunDetails: async (runId: number): Promise<PayrollSlip[]> => {
        const response = await fetch(`${API_BASE_URL}/manager/payroll/run/${runId}`, {
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch run details');
        return response.json();
    },

    finalizePayrollRun: async (runId: number): Promise<{ message: string, count: number }> => {
        const response = await fetch(`${API_BASE_URL}/manager/payroll/run/${runId}/finalize`, {
            method: 'POST',
            headers: getAuthHeaders()
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to finalize run');
        }
        return response.json();
    },

    // Manager: Approvals
    getPendingLeaves: async (): Promise<LeaveRequest[]> => {
        const response = await fetch(`${API_BASE_URL}/manager/approvals/leaves`, {
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch pending leaves');
        return response.json();
    },

    processLeave: async (id: number, action: 'approve' | 'reject'): Promise<{ status: string }> => {
        const response = await fetch(`${API_BASE_URL}/manager/approvals/leaves/${id}?action=${action}`, {
            method: 'POST',
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Failed to process leave');
        return response.json();
    },

    getPendingCorrections: async (): Promise<CorrectionRequest[]> => {
        const response = await fetch(`${API_BASE_URL}/manager/approvals/corrections`, {
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch pending corrections');
        return response.json();
    },

    processCorrection: async (id: number, action: 'approve' | 'reject'): Promise<{ status: string }> => {
        const response = await fetch(`${API_BASE_URL}/manager/approvals/corrections/${id}?action=${action}`, {
            method: 'POST',
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Failed to process correction');
        return response.json();
    },

    getKiosks: async () => {
        const response = await fetch(`${API_BASE_URL}/manager/kiosks`, {
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch kiosks');
        return response.json();
    },

    getApprovalHistory: async (): Promise<any[]> => {
        const response = await fetch(`${API_BASE_URL}/manager/approvals/history`, {
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch approval history');
        return response.json();
    },

    async getEmployees() {
        const response = await fetch(`${API_BASE_URL}/manager/employees`, {
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch employees');
        return response.json();
    },

    async getSites() {
        const response = await fetch(`${API_BASE_URL}/manager/sites`, {
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch sites');
        return response.json();
    },

    async assignSite(userIds: number[], siteId: number) {
        const response = await fetch(`${API_BASE_URL}/manager/employees/assign-site`, {
            method: 'POST',
            headers: {
                ...getAuthHeaders(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ user_ids: userIds, site_id: siteId })
        });
        if (!response.ok) throw new Error('Failed to assign site');
        return response.json();
    },

    async createEmployee(data: any) {
        const response = await fetch(`${API_BASE_URL}/manager/employees`, {
            method: 'POST',
            headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Failed to create employee');
        return response.json();
    },

    async updateEmployee(id: number, data: any) {
        const response = await fetch(`${API_BASE_URL}/manager/employees/${id}`, {
            method: 'PUT',
            headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Failed to update employee');
        return response.json();
    }
};

export const holidaysApi = {
    getHolidays: async () => {
        const response = await fetch(`${API_BASE_URL}/manager/holidays/`, {
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch holidays');
        return response.json();
    },

    createHoliday: async (data: { date: string, name: string, is_national: boolean }) => {
        const response = await fetch(`${API_BASE_URL}/manager/holidays/`, {
            method: 'POST',
            headers: {
                ...getAuthHeaders(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to create holiday');
        }
        return response.json();
    },

    deleteHoliday: async (id: number) => {
        const response = await fetch(`${API_BASE_URL}/manager/holidays/${id}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Failed to delete holiday');
        return response.json();
    }
};

export const shiftsApi = {
    getShifts: async () => {
        const response = await fetch(`${API_BASE_URL}/manager/shifts`, {
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch shifts');
        return response.json();
    },

    createShift: async (data: { name: string, start_time: string, end_time: string }): Promise<{ id: number, name: string }> => {
        const response = await fetch(`${API_BASE_URL}/manager/shifts`, {
            method: 'POST',
            headers: {
                ...getAuthHeaders(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Failed to create shift');
        return response.json();
    },

    updateShift: async (id: number, data: { name?: string, start_time?: string, end_time?: string }): Promise<{ status: string }> => {
        const response = await fetch(`${API_BASE_URL}/manager/shifts/${id}`, {
            method: 'PUT',
            headers: {
                ...getAuthHeaders(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Failed to update shift');
        return response.json();
    },

    deleteShift: async (id: number) => {
        const response = await fetch(`${API_BASE_URL}/manager/shifts/${id}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Failed to delete shift');
        return response.json();
    },

    assignRoster: async (userIds: number[], shiftId: number, isPermanent: boolean = true) => {
        const response = await fetch(`${API_BASE_URL}/manager/roster/assign`, {
            method: 'POST',
            headers: {
                ...getAuthHeaders(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ user_ids: userIds, shift_id: shiftId, is_permanent: isPermanent })
        });
        if (!response.ok) throw new Error('Failed to assign roster');
        return response.json();
    }
};

export const authApi = {
    login: async (username: string, password: string): Promise<{ access_token: string, token_type: string }> => {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        try {
            const response = await fetch(`${API_BASE_URL}/employee/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData,
            });

            if (!response.ok) {
                // Safely handle non-JSON errors
                const text = await response.text();
                try {
                    const err = JSON.parse(text);
                    throw new Error(err.detail || `Login failed: ${response.statusText}`);
                } catch (e) {
                    // If JSON parse fails, throw the raw text or status
                    throw new Error(`Login failed (${response.status}): ${text || response.statusText}`);
                }
            }
            return response.json();
        } catch (error: any) {
            console.error("Login API Error:", error);
            throw error;
        }
    }
};

export const employeeApi = {
    getDashboard: async () => {
        const response = await fetch(`${API_BASE_URL}/employee/dashboard`, {
            headers: getEmployeeHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch dashboard');
        return response.json();
    },

    getTimesheet: async (month: string) => {
        // month format YYYY-MM
        const response = await fetch(`${API_BASE_URL}/employee/timesheet?month=${month}`, {
            headers: getEmployeeHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch timesheet');
        return response.json();
    },

    getLeaves: async () => {
        const response = await fetch(`${API_BASE_URL}/employee/me/leaves`, {
            headers: getEmployeeHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch leaves');
        return response.json();
    },

    submitLeaveWait: async (data: { leave_type: string, start_date: string, end_date: string, reason: string }): Promise<{ status: string, id: number }> => {
        const response = await fetch(`${API_BASE_URL}/employee/me/leaves`, {
            method: 'POST',
            headers: getEmployeeHeaders(),
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Failed to submit leave');
        return response.json();
    },

    // Payroll
    getPayslips: async () => {
        const response = await fetch(`${API_BASE_URL}/payroll/slips/me`, {
            headers: getEmployeeHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch payslips');
        return response.json();
    },

    applyLeave: async (data: { leave_type: string, start_date: string, end_date: string, reason?: string, file?: File }): Promise<{ status: string, id: number }> => {
        const formData = new FormData();
        formData.append('leave_type', data.leave_type);
        formData.append('start_date', data.start_date);
        formData.append('end_date', data.end_date);
        if (data.reason) formData.append('reason', data.reason);
        if (data.file) formData.append('file', data.file);

        const token = localStorage.getItem('employee_access_token');
        const headers: Record<string, string> = {};
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_BASE_URL}/employee/me/leaves`, {
            method: 'POST',
            headers: headers,
            body: formData
        });
        if (!response.ok) throw new Error('Failed to apply leave');
        return response.json();
    },

    async getDailyTimesheet(dateStr: string) {
        const response = await fetch(`${API_BASE_URL}/employee/me/timesheet/day?date=${dateStr}`, {
            headers: getEmployeeHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch daily timesheet');
        return response.json();
    },

    async requestCorrection(data: { date: string, in_time: string | null, out_time: string | null, reason: string }) {
        const response = await fetch(`${API_BASE_URL}/employee/me/corrections`, {
            method: 'POST',
            headers: getEmployeeHeaders(),
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Failed to submit correction');
        return response.json();
    },

    async getCorrections() {
        const response = await fetch(`${API_BASE_URL}/employee/me/corrections`, {
            headers: getEmployeeHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch corrections');
        return response.json();
    }
};
