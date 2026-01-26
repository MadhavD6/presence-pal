import { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, addMonths, subMonths, parseISO } from 'date-fns';
import { useQuery } from '@tanstack/react-query';
import { employeeApi } from '@/services/api';

interface TimesheetScreenProps {
    onBack: () => void;
    onDateSelect: (date: Date) => void;
    initialDate?: Date;
}

// Types matching API
interface DailyLog {
    date: Date;
    status: string;
    in_time: string;
    out_time: string;
    worked_hours: string;
    shift: string;
    is_late: boolean;
    late_minutes: number;
    color: string;
}

const TimesheetScreen = ({ onBack, onDateSelect, initialDate }: TimesheetScreenProps) => {
    const [currentMonth, setCurrentMonth] = useState(initialDate || new Date());

    // Fetch Data
    const { data: rawData, isLoading } = useQuery({
        queryKey: ['timesheet', currentMonth.getMonth(), currentMonth.getFullYear()],
        queryFn: () => employeeApi.getTimesheet(format(currentMonth, 'yyyy-MM')),
    });

    // Process Data into days map for easy access
    const daysMap = new Map<string, DailyLog>();
    if (rawData) {
        rawData.forEach((item: any) => {
            daysMap.set(item.date, { // item.date is YYYY-MM-DD string
                ...item,
                date: parseISO(item.date),
                in_time: item.first_in,
                out_time: item.last_out,
                worked_hours: item.total_hours ? `${item.total_hours}h` : '-',
            });
        });
    }

    const start = startOfMonth(currentMonth);
    const end = endOfMonth(currentMonth);
    const days = eachDayOfInterval({ start, end });

    // Combine API data with calendar days (fill gaps if any, though API handles it mostly)
    const monthlyData = days.map(day => {
        const dateStr = format(day, 'yyyy-MM-dd');
        return daysMap.get(dateStr) || {
            date: day,
            status: '-',
            in_time: '-',
            out_time: '-',
            worked_hours: '-',
            shift: '-',
            is_late: false,
            late_minutes: 0,
            color: 'gray'
        };
    });

    const handlePrevMonth = () => setCurrentMonth(subMonths(currentMonth, 1));
    const handleNextMonth = () => setCurrentMonth(addMonths(currentMonth, 1));

    // Get stats for the month from actual data
    const stats = {
        present: monthlyData.filter(d => d.status === 'Present').length,
        absent: monthlyData.filter(d => d.status === 'Absent').length,
        leaves: monthlyData.filter(d => d.status === 'Leave').length,
        holidays: monthlyData.filter(d => d.status === 'Holiday').length,
    };

    if (isLoading) {
        return <div className="min-h-screen flex items-center justify-center bg-background text-foreground">Loading Timesheet...</div>;
    }

    return (
        <div className="min-h-screen bg-background flex flex-col animate-fade-in">
            {/* Header */}
            <div className="px-4 py-4 flex items-center gap-4 bg-card border-b border-border">
                <Button variant="ghost" size="icon" onClick={onBack}>
                    <ChevronLeft className="w-6 h-6" />
                </Button>
                <h1 className="text-xl font-bold">My Timesheet</h1>
                {/* <div className="ml-auto text-xs text-muted-foreground p-1 border rounded">
                    ID: {userId}
                </div> */}
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-6 pb-safe">

                {/* Month Selector */}
                <div className="flex items-center justify-between bg-card p-2 rounded-lg border border-border">
                    <Button variant="ghost" size="icon" onClick={handlePrevMonth}>
                        <ChevronLeft className="w-5 h-5" />
                    </Button>
                    <span className="font-bold text-lg">{format(currentMonth, 'MMMM yyyy')}</span>
                    <Button variant="ghost" size="icon" onClick={handleNextMonth}>
                        <ChevronRight className="w-5 h-5" />
                    </Button>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-4 gap-2">
                    <Card className="shadow-none border-border">
                        <CardContent className="p-3 text-center">
                            <span className="text-2xl font-bold block">{stats.present}</span>
                            <span className="text-xs text-muted-foreground">Present</span>
                        </CardContent>
                    </Card>
                    <Card className="shadow-none border-border">
                        <CardContent className="p-3 text-center">
                            <span className="text-2xl font-bold block">{stats.absent}</span>
                            <span className="text-xs text-muted-foreground">Absent</span>
                        </CardContent>
                    </Card>
                    <Card className="shadow-none border-border">
                        <CardContent className="p-3 text-center">
                            <span className="text-2xl font-bold block">{stats.leaves}</span>
                            <span className="text-xs text-muted-foreground">Leaves</span>
                        </CardContent>
                    </Card>
                    <Card className="shadow-none border-border">
                        <CardContent className="p-3 text-center">
                            <span className="text-2xl font-bold block">{stats.holidays}</span>
                            <span className="text-xs text-muted-foreground">Holidays</span>
                        </CardContent>
                    </Card>
                </div>

                {/* Calendar Grid */}
                <div className="bg-card rounded-xl border border-border overflow-hidden">
                    {/* Weekday Headers */}
                    <div className="grid grid-cols-7 border-b border-border bg-muted/30">
                        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                            <div key={day} className="py-2 text-center text-xs font-medium text-muted-foreground">
                                {day}
                            </div>
                        ))}
                    </div>

                    {/* Days */}
                    <div className="grid grid-cols-7">
                        {/* Empty cells for start of month offset */}
                        {Array.from({ length: startOfMonth(currentMonth).getDay() }).map((_, i) => (
                            <div key={`empty-${i}`} className="aspect-square border-b border-r border-border/50" />
                        ))}

                        {monthlyData.map((day, i) => (
                            <button
                                key={i}
                                onClick={() => onDateSelect(day.date)}
                                className={`aspect-square border-b border-r border-border/50 p-1 flex flex-col items-center justify-center relative transition-colors hover:bg-muted/50
                                     ${day.status === 'Present' ? (day.is_late ? 'bg-yellow-500/20' : 'bg-green-500/20') : day.status === 'Absent' ? 'bg-red-500/10' : day.status === 'WO' ? 'bg-gray-100 dark:bg-gray-800' : ''}`}
                            >
                                <span className={`text-sm font-medium flex items-center gap-0.5`}>
                                    {format(day.date, 'd')}
                                    {day.is_late && <span className="w-1.5 h-1.5 rounded-full bg-red-500" title={`Late ${Math.floor(day.late_minutes / 60).toString().padStart(2, '0')}:${(day.late_minutes % 60).toString().padStart(2, '0')}`} />}
                                </span>
                                {day.status !== '-' && day.status !== 'WO' && (
                                    <div className="flex flex-col items-center mt-1">
                                        <span className="text-[10px] leading-tight font-bold">{day.worked_hours}</span>
                                        <span className="text-[9px] text-muted-foreground">{day.shift}</span>
                                    </div>
                                )}
                                {day.status === 'WO' && <span className="text-[10px] text-muted-foreground mt-1">WO</span>}
                            </button>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TimesheetScreen;
