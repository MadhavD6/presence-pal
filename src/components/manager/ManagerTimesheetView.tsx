import { ChevronLeft, ChevronRight, SlidersHorizontal } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { format, addDays, startOfWeek, endOfWeek } from 'date-fns';
import { useState, useEffect } from 'react';
import { api } from '@/services/api';
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip"

interface DayStatus {
    status: string;
    shift_code: string;
    tooltip: string;
}

interface TimesheetEntry {
    name: string;
    id: string;
    dept: string;
    avatar: string;
    stats: { payable: string, worked: string };
    days: DayStatus[];
}

const ManagerTimesheetView = () => {
    const [currentDate, setCurrentDate] = useState(new Date());
    const [staffList, setStaffList] = useState<TimesheetEntry[]>([]);
    const [loading, setLoading] = useState(false);

    // Generate dates for current week view
    const weekStart = startOfWeek(currentDate);
    const weekDays = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));

    useEffect(() => {
        const fetchTimesheet = async () => {
            setLoading(true);
            try {
                const start = weekStart;
                const end = endOfWeek(currentDate);
                const data = await api.getManagerTimesheet(start, end);
                setStaffList(data);
            } catch (error) {
                console.error("Failed to fetch timesheet", error);
            } finally {
                setLoading(false);
            }
        };
        fetchTimesheet();
    }, [currentDate]);

    return (
        <div className="space-y-4 animate-fade-in h-full flex flex-col">
            {/* Search and Filter */}
            <div className="flex gap-2">
                <Input placeholder="Search Staff" className="bg-card flex-1" />
                <Button variant="ghost" size="icon">
                    <SlidersHorizontal className="h-5 w-5" />
                </Button>
            </div>

            {/* Date Navigation */}
            <div className="flex items-center justify-between bg-card p-2 rounded-lg border border-border">
                <Button variant="ghost" size="icon" onClick={() => setCurrentDate(addDays(currentDate, -7))}>
                    <ChevronLeft className="w-5 h-5" />
                </Button>
                <span className="font-bold text-sm">
                    {format(weekStart, "dd MMM, yyyy")} - {format(endOfWeek(currentDate), "dd MMM, yyyy")}
                </span>
                <Button variant="ghost" size="icon" onClick={() => setCurrentDate(addDays(currentDate, 7))}>
                    <ChevronRight className="w-5 h-5" />
                </Button>
            </div>

            {/* Calendar Header Row */}
            <div className="grid grid-cols-7 gap-1 bg-card p-2 rounded-lg border border-border">
                {weekDays.map((day, i) => (
                    <div key={i} className="flex flex-col items-center justify-center p-1">
                        <span className="text-[10px] text-muted-foreground font-medium">{format(day, 'EEE')}</span>
                        <span className="text-sm font-bold">{format(day, 'd')}</span>
                    </div>
                ))}
            </div>

            {/* Staff List */}
            <div className="space-y-4 pb-20 overflow-y-auto">
                {loading ? (
                    <div className="text-center p-4 text-muted-foreground">Loading timesheet...</div>
                ) : (
                    staffList.map((staff, idx) => (
                        <div key={idx} className="bg-card rounded-xl border border-border overflow-hidden">
                            <div className="p-4 border-b border-border/50">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-full bg-muted overflow-hidden">
                                        <img src={`https://ui-avatars.com/api/?name=${staff.name}&background=random`} alt={staff.name} />
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-sm">
                                            {staff.name} <span className="font-normal text-muted-foreground text-xs">({staff.id})</span>
                                        </h3>
                                        <p className="text-xs text-muted-foreground">Department: {staff.dept}</p>
                                    </div>
                                </div>
                            </div>

                            {/* Weekly Status Grid */}
                            <div className="p-4 pt-2">
                                <div className="grid grid-cols-7 gap-1 mb-4">
                                    <TooltipProvider>
                                        {staff.days.map((day, dIdx) => (
                                            <Tooltip key={dIdx}>
                                                <TooltipTrigger asChild>
                                                    <div
                                                        className={`
                                                        h-10 rounded flex items-center justify-center text-[10px] font-bold border cursor-default
                                                        ${day.status === 'PR' ? 'bg-green-100 text-green-700 border-green-200' :
                                                                day.status === 'WO' ? 'bg-gray-200 text-gray-600 border-gray-300' :
                                                                    day.status === 'LV' ? 'bg-orange-100 text-orange-700 border-orange-200' :
                                                                        'bg-background border-border text-muted-foreground'}
                                                    `}
                                                    >
                                                        {day.shift_code || day.status}
                                                    </div>
                                                </TooltipTrigger>
                                                <TooltipContent>
                                                    <p>{day.tooltip}</p>
                                                </TooltipContent>
                                            </Tooltip>
                                        ))}
                                    </TooltipProvider>
                                </div>

                                <div className="flex justify-between text-xs">
                                    <div>
                                        <span className="font-bold text-sm block">{staff.stats.payable}</span>
                                        <span className="text-muted-foreground">Payable Hrs</span>
                                    </div>
                                    <div className="text-right">
                                        <span className="font-bold text-sm block">{staff.stats.worked}</span>
                                        <span className="text-muted-foreground">Worked Hrs</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default ManagerTimesheetView;
