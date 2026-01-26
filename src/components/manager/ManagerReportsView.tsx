import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { api } from '@/services/api';
import { format, subDays } from 'date-fns';
import { Calendar as CalendarIcon, Download } from 'lucide-react';
import { toast } from 'sonner';
import { AttendanceTrendsChart, StatusDistributionChart } from './reports/ReportsCharts';

export const ManagerReportsView = () => {
    // --- State ---
    const [date, setDate] = useState<any>({
        from: subDays(new Date(), 7),
        to: new Date(),
    });
    const [reportData, setReportData] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    // Drill-down State
    const [selectedEmpId, setSelectedEmpId] = useState<string | null>(null);

    // --- Effects ---
    useEffect(() => {
        if (date?.from && date?.to) {
            loadReport();
        }
    }, [date]);

    // --- Actions ---
    const loadReport = async () => {
        setLoading(true);
        try {
            const data = await api.getManagerDetailedReport(date.from, date.to);
            setReportData(data || []);
        } catch (error) {
            console.error(error);
            toast.error("Failed to load report data");
        } finally {
            setLoading(false);
        }
    };

    const handleExport = async () => {
        try {
            const blob = await api.downloadManagerReport(date.from, date.to);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `attendance_report_${format(date.from, 'yyyy-MM-dd')}_to_${format(date.to, 'yyyy-MM-dd')}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            toast.success("Export downloaded");
        } catch (error) {
            toast.error("Export failed");
        }
    };

    // --- Aggregations (Overall) ---
    const totalPresent = reportData.filter(d => d.status === 'Present').length;
    const totalLate = reportData.filter(d => d.status === 'Late').length;
    const totalAbsent = reportData.filter(d => ['Absent', 'Not In'].includes(d.status)).length;
    const totalLeave = reportData.filter(d => ['Leave', 'On Leave'].includes(d.status)).length;

    const distributionData = [
        { name: 'Present', value: totalPresent },
        { name: 'Late', value: totalLate },
        { name: 'Absent', value: totalAbsent },
        { name: 'Leave', value: totalLeave },
    ];

    // Overall Trend Map
    const trendMap = new Map();
    reportData.forEach(item => {
        const d = item.date;
        if (!trendMap.has(d)) trendMap.set(d, { date: d, Present: 0, Late: 0, Absent: 0, Leave: 0 });
        const entry = trendMap.get(d);
        if (item.status === 'Present') entry.Present++;
        if (item.status === 'Late') entry.Late++;
        if (['Absent', 'Not In'].includes(item.status)) entry.Absent++;
        if (['Leave', 'On Leave'].includes(item.status)) entry.Leave++;
    });
    const trendData = Array.from(trendMap.values()).sort((a: any, b: any) => a.date.localeCompare(b.date));

    // --- Aggregations (Selected Employee) ---
    const empStats = selectedEmpId ? reportData.filter(d => d.employee_id === selectedEmpId) : [];

    const empTrendMap = new Map();
    if (selectedEmpId) {
        empStats.forEach(item => {
            const d = item.date;
            if (!empTrendMap.has(d)) empTrendMap.set(d, { date: d, Present: 0, Late: 0, Absent: 0, Leave: 0 });
            const entry = empTrendMap.get(d);
            if (item.status === 'Present') entry.Present++;
            if (item.status === 'Late') entry.Late++;
            if (['Absent', 'Not In'].includes(item.status)) entry.Absent++;
            if (['Leave', 'On Leave'].includes(item.status)) entry.Leave++;
        });
    }
    const empTrendData = Array.from(empTrendMap.values()).sort((a: any, b: any) => a.date.localeCompare(b.date));


    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            {/* Header Controls */}
            <div className="flex flex-col sm:flex-row justify-between gap-4 items-start sm:items-center">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight">Reports & Analytics</h2>
                    <p className="text-muted-foreground">Attendance trends and detailed logs.</p>
                </div>
                <div className="flex gap-2">
                    <Popover>
                        <PopoverTrigger asChild>
                            <Button variant="outline" className={`w-[240px] justify-start text-left font-normal ${!date ? "text-muted-foreground" : ""}`}>
                                <CalendarIcon className="mr-2 h-4 w-4" />
                                {date?.from ? (
                                    date.to ? (
                                        <>{format(date.from, "LLL dd, y")} - {format(date.to, "LLL dd, y")}</>
                                    ) : (
                                        format(date.from, "LLL dd, y")
                                    )
                                ) : (
                                    <span>Pick a date range</span>
                                )}
                            </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-auto p-0" align="end">
                            <Calendar
                                initialFocus
                                mode="range"
                                defaultMonth={date?.from}
                                selected={date}
                                onSelect={setDate}
                                numberOfMonths={2}
                            />
                        </PopoverContent>
                    </Popover>
                    <Button onClick={handleExport} variant="secondary">
                        <Download className="w-4 h-4 mr-2" />
                        Export CSV
                    </Button>
                </div>
            </div>

            {/* Summary KPI Cards */}
            <div className="grid gap-4 md:grid-cols-4">
                <Card>
                    <CardHeader className="p-4 pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">Total Records</CardTitle></CardHeader>
                    <CardContent className="p-4 pt-0"><div className="text-2xl font-bold">{reportData.length}</div></CardContent>
                </Card>
                <Card>
                    <CardHeader className="p-4 pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">Total Late</CardTitle></CardHeader>
                    <CardContent className="p-4 pt-0"><div className="text-2xl font-bold">{totalLate}</div></CardContent>
                </Card>
                <Card>
                    <CardHeader className="p-4 pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">Total Absent</CardTitle></CardHeader>
                    <CardContent className="p-4 pt-0"><div className="text-2xl font-bold">{totalAbsent}</div></CardContent>
                </Card>
                <Card>
                    <CardHeader className="p-4 pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">Total Leaves</CardTitle></CardHeader>
                    <CardContent className="p-4 pt-0"><div className="text-2xl font-bold">{totalLeave}</div></CardContent>
                </Card>
            </div>

            {/* Charts Area */}
            <div className="grid gap-6 md:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle>Attendance Trends</CardTitle>
                        <CardDescription>Daily breakdown of status over the selected period.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <AttendanceTrendsChart data={trendData} />
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader>
                        <CardTitle>Status Distribution</CardTitle>
                        <CardDescription>Overall percentage of attendance statuses.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <StatusDistributionChart data={distributionData} />
                    </CardContent>
                </Card>
            </div>

            {/* Detailed Table */}
            <Card>
                <CardHeader>
                    <CardTitle>Detailed Logs</CardTitle>
                    <CardDescription>Click on a row to view employee details.</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="rounded-md border">
                        <table className="w-full text-sm">
                            <thead className="bg-muted/50 border-b">
                                <tr className="text-left">
                                    <th className="p-4 font-medium text-muted-foreground">Date</th>
                                    <th className="p-4 font-medium text-muted-foreground">Employee</th>
                                    <th className="p-4 font-medium text-muted-foreground">Status</th>
                                    <th className="p-4 font-medium text-muted-foreground">In Time</th>
                                    <th className="p-4 font-medium text-muted-foreground">Out Time</th>
                                    <th className="p-4 font-medium text-muted-foreground">Duration</th>
                                </tr>
                            </thead>
                            <tbody>
                                {loading ? (
                                    <tr><td colSpan={6} className="p-8 text-center">Loading Data...</td></tr>
                                ) : reportData.length === 0 ? (
                                    <tr><td colSpan={6} className="p-8 text-center text-muted-foreground">No records found for this period.</td></tr>
                                ) : (
                                    reportData.slice(0, 50).map((row, i) => (
                                        <tr key={i} className="border-b last:border-0 hover:bg-muted/50 cursor-pointer" onClick={() => setSelectedEmpId(row.employee_id)}>
                                            <td className="p-4">{row.date}</td>
                                            <td className="p-4 font-medium">{row.employee_name}</td>
                                            <td className="p-4">
                                                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium 
                                                    ${row.status === 'Present' ? 'bg-emerald-100 text-emerald-800' :
                                                        row.status === 'Late' ? 'bg-amber-100 text-amber-800' :
                                                            ['Absent', 'Not In'].includes(row.status) ? 'bg-rose-100 text-rose-800' :
                                                                'bg-blue-100 text-blue-800'}`}>
                                                    {row.status}
                                                </span>
                                            </td>
                                            <td className="p-4 font-mono">{row.in_time || '-'}</td>
                                            <td className="p-4 font-mono">{row.out_time || '-'}</td>
                                            <td className="p-4">{row.total_hours || '-'}</td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>

            {/* Drill Down Modal - Fixed Structure */}
            <Dialog open={!!selectedEmpId} onOpenChange={(o) => !o && setSelectedEmpId(null)}>
                <DialogContent className="max-w-4xl h-[80vh] flex flex-col">
                    <DialogHeader>
                        <DialogTitle>Employee Report: {empStats[0]?.employee_name}</DialogTitle>
                        <DialogDescription>Performance overview for {selectedEmpId}</DialogDescription>
                    </DialogHeader>

                    <div className="flex-1 overflow-y-auto space-y-6 pr-2">
                        <div className="grid grid-cols-2 gap-4">
                            <Card>
                                <CardHeader><CardTitle className="text-sm">Attendance Trend</CardTitle></CardHeader>
                                <CardContent>
                                    <AttendanceTrendsChart data={empTrendData} />
                                </CardContent>
                            </Card>
                            <Card>
                                <CardHeader><CardTitle className="text-sm">Summary</CardTitle></CardHeader>
                                <CardContent className="space-y-2">
                                    <div className="flex justify-between"><span>Present</span><span className="font-bold">{empStats.filter(x => x.status === 'Present').length}</span></div>
                                    <div className="flex justify-between"><span>Late</span><span className="font-bold">{empStats.filter(x => x.status === 'Late').length}</span></div>
                                    <div className="flex justify-between"><span>Absent</span><span className="font-bold">{empStats.filter(x => ['Absent', 'Not In'].includes(x.status)).length}</span></div>
                                </CardContent>
                            </Card>
                        </div>

                        <div className="rounded-md border">
                            <table className="w-full text-sm">
                                <thead className="bg-muted/50 border-b">
                                    <tr className="text-left">
                                        <th className="p-3">Date</th>
                                        <th className="p-3">Shift</th>
                                        <th className="p-3">In</th>
                                        <th className="p-3">Out</th>
                                        <th className="p-3">Status</th>
                                        <th className="p-3">Remarks</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {empStats.map((row, i) => (
                                        <tr key={i} className="border-b last:border-0 hover:bg-muted/50">
                                            <td className="p-3">{row.date}</td>
                                            <td className="p-3">{row.shift_name}</td>
                                            <td className="p-3 font-mono">{row.in_time}</td>
                                            <td className="p-3 font-mono">{row.out_time}</td>
                                            <td className="p-3">{row.status}</td>
                                            <td className="p-3 text-muted-foreground truncate max-w-[100px]">{row.remarks}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </DialogContent>
            </Dialog>
        </div>
    );
};
