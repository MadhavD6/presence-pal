import { ChevronLeft, ChevronRight, ChevronDown, Clock, MessageSquare, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { format } from 'date-fns';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { employeeApi } from '@/services/api';
import PunchDetailsSheet from './PunchDetailsSheet';
import RequestCorrectionScreen from './RequestCorrectionScreen';

interface TimecardScreenProps {
    date: Date;
    onBack: () => void;
}

const TimecardScreen = ({ date, onBack }: TimecardScreenProps) => {
    // Defensive check for date
    const safeDate = (date instanceof Date && !isNaN(date.getTime())) ? date : new Date();
    const dateStr = format(safeDate, "dd MMM, yyyy");

    const [selectedPunch, setSelectedPunch] = useState<any>(null);
    const [isExpanded, setIsExpanded] = useState(false);
    const [showCorrection, setShowCorrection] = useState(false);

    const { data: apiData, isLoading } = useQuery({
        queryKey: ['dailyTimesheet', dateStr],
        queryFn: () => employeeApi.getDailyTimesheet(format(safeDate, 'yyyy-MM-dd')),
    });

    const data = apiData || {
        name: "-",
        id: "-",
        status: "-",
        inTime: "-",
        outTime: "-",
        workedHours: "-",
        payableHours: "-",
        shift: "-",
        overtime: "-",
        breaktime: "-",
        subStatus: "-",
        approvalStatus: "-",
        punches: []
    };

    const mainDetails = [
        { label: 'In Time', value: data.inTime, valueClass: 'font-bold' },
        { label: 'Out Time', value: data.outTime, valueClass: 'font-bold' },
        { label: 'Worked Hours', value: data.workedHours, valueClass: 'font-bold' },
        { label: 'Payable Hours', value: data.payableHours, valueClass: 'font-bold' },
    ];

    const expandedDetails = [
        { label: 'Shift', value: data.shift, valueClass: 'font-bold text-xs' },
        { label: 'Overtime', value: data.overtime },
        { label: 'Breaktime', value: data.breaktime },
        { label: 'Sub Status', value: data.subStatus, valueClass: 'font-bold' },
        { label: 'Approval Status', value: data.approvalStatus },
    ];

    if (showCorrection) {
        return (
            <RequestCorrectionScreen
                date={safeDate}
                onBack={() => setShowCorrection(false)}
                onSubmit={(formData) => {
                    console.log("Correction Submitted:", formData);
                    setShowCorrection(false);
                }}
                userName={data.name}
                employeeId={data.id}
            />
        );
    }

    return (
        <div className="min-h-screen bg-background flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header */}
            <div className="px-4 py-4 flex items-center gap-2 bg-card border-b border-border sticky top-0 z-10">
                <Button variant="ghost" size="icon" onClick={onBack}>
                    <ChevronLeft className="w-6 h-6" />
                </Button>
                <h1 className="text-lg font-bold">Timecard <span className="text-muted-foreground font-normal">({format(safeDate, "EEE, dd MMM, yyyy")})</span></h1>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-6 pb-20">

                {/* Main Card */}
                <Card className="overflow-hidden border-border bg-card">
                    <CardContent className="p-0">
                        {/* Profile Section */}
                        <div className="p-4 flex items-start justify-between border-b border-border bg-card">
                            <div className="flex items-center gap-3">
                                <div className="w-12 h-12 rounded-full bg-black/10 overflow-hidden">
                                    <img src={`https://ui-avatars.com/api/?name=${data.name}&background=random`} alt="Profile" className="w-full h-full object-cover" />
                                </div>
                                <div>
                                    <h3 className="font-bold text-sm leading-tight max-w-[150px]">{data.name}</h3>
                                    <p className="text-xs text-muted-foreground">({data.id})</p>
                                </div>
                            </div>
                            <div className="flex flex-col items-end gap-1">
                                <span className={`px-2 py-0.5 text-xs font-bold rounded ${data.status === 'In' ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-700'}`}>{data.status}</span>
                            </div>
                        </div>

                        {/* Details List */}
                        <div className="bg-card text-sm">
                            {mainDetails.map((item, i) => (
                                <div key={i} className="flex items-center justify-between p-3 border-b border-border last:border-0">
                                    <span className="text-muted-foreground">{item.label}</span>
                                    <span className={`${item.valueClass || ''}`}>{item.value}</span>
                                </div>
                            ))}

                            {isExpanded && expandedDetails.map((item, i) => (
                                <div key={`exp-${i}`} className="flex items-center justify-between p-3 border-b border-border last:border-0 animate-in fade-in slide-in-from-top-2 duration-300">
                                    <span className="text-muted-foreground">{item.label}</span>
                                    <span className={`${item.valueClass || ''}`}>{item.value}</span>
                                </div>
                            ))}
                        </div>

                        {/* Shift Progress */}
                        <div className="p-4 bg-muted/20 border-t border-border">
                            <div className="flex justify-between text-xs mb-1">
                                <span className="text-muted-foreground">Shift Completion</span>
                                <span className="font-medium text-primary">
                                    {/* Simple fallback calc */}
                                    {(() => {
                                        if (data.workedHours === '-') return '0%';
                                        try {
                                            const [h, m] = data.workedHours.replace('h', '').replace('m', '').split(' ').map(Number);
                                            const totalMins = (h || 0) * 60 + (m || 0);
                                            // Assume 9h shift = 540 mins
                                            const pct = Math.min(100, Math.round((totalMins / 540) * 100));
                                            return `${pct}%`;
                                        } catch (e) { return '0%'; }
                                    })()}
                                </span>
                            </div>
                            <Progress value={(() => {
                                if (data.workedHours === '-') return 0;
                                try {
                                    const [h, m] = data.workedHours.replace('h', '').replace('m', '').split(' ').map(Number);
                                    const totalMins = (h || 0) * 60 + (m || 0);
                                    return Math.min(100, (totalMins / 540) * 100);
                                } catch (e) { return 0; }
                            })()} className="h-2 w-full" />
                        </div>

                        {/* Footer (More/Less) */}
                        <div
                            className="p-3 bg-white dark:bg-black/20 flex items-center justify-center gap-1 text-primary cursor-pointer border-t border-border hover:bg-muted/50 transition-colors"
                            onClick={() => setIsExpanded(!isExpanded)}
                        >
                            <ChevronDown className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                            <span className="text-sm font-medium">{isExpanded ? 'Less' : 'More'}</span>
                        </div>
                    </CardContent>
                </Card>

                {/* Actions */}
                <div className="grid grid-cols-3 gap-4 px-2">
                    <button className="flex flex-col items-center gap-2 text-foreground/80 hover:text-primary transition-colors">
                        <div className="w-10 h-10 rounded-full border border-primary text-primary flex items-center justify-center">
                            <Clock className="w-5 h-5" />
                        </div>
                        <span className="text-[10px] text-center font-medium leading-tight">Change Shift</span>
                    </button>
                    <button
                        className="flex flex-col items-center gap-2 text-foreground/80 hover:text-primary transition-colors"
                        onClick={() => setShowCorrection(true)}
                    >
                        <div className="w-10 h-10 rounded-full border border-primary text-primary flex items-center justify-center">
                            <AlertCircle className="w-5 h-5" />
                        </div>
                        <span className="text-[10px] text-center font-medium leading-tight">Request Correction</span>
                    </button>
                    <button className="flex flex-col items-center gap-2 text-foreground/80 hover:text-primary transition-colors">
                        <div className="w-10 h-10 rounded-full border border-primary text-primary flex items-center justify-center">
                            <MessageSquare className="w-5 h-5" />
                        </div>
                        <span className="text-[10px] text-center font-medium leading-tight">Add comment</span>
                    </button>
                </div>

                {/* Punch Log Timeline */}
                <div className="space-y-4">
                    <h3 className="font-bold text-lg">Punch Log</h3>
                    <div className="relative pl-4 ">
                        {data.punches.map((punch, idx) => (
                            <div
                                key={idx}
                                className="relative flex items-start gap-4 pb-8 last:pb-0 cursor-pointer"
                                onClick={() => setSelectedPunch(punch)}
                            >
                                {/* Connector Line */}
                                {idx < data.punches.length - 1 && (
                                    <div className="absolute left-[5px] top-3 bottom-0 w-[2px] bg-border z-0 flex items-center justify-center">
                                        <span className="bg-background text-[9px] text-muted-foreground px-1 py-0.5 border border-border rounded-full z-10 translate-y-4">
                                            {data.workedHours}
                                        </span>
                                    </div>
                                )}

                                {/* Dot */}
                                <div className={`w-3 h-3 rounded-full z-10 mt-1.5 shrink-0 ${punch.type === 'In' ? 'bg-cyan-400' : 'bg-gray-400'}`} />
                                <span className={`text-sm font-bold w-8 mt-0.5 ${punch.type === 'In' ? 'text-cyan-600 dark:text-cyan-400' : 'text-gray-600 dark:text-gray-400'}`}>
                                    {punch.type}
                                </span>

                                {/* Card */}
                                <div className="flex-1 flex items-center gap-3">
                                    <div className="w-8 h-8 rounded-full bg-black/10 overflow-hidden shrink-0">
                                        <img src={`https://ui-avatars.com/api/?name=${data.name}&background=random`} alt="Profile" className="w-full h-full object-cover" />
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2">
                                            <span className="font-bold text-sm">{punch.time}</span>
                                            <span className="text-xs font-bold text-muted-foreground">|</span>
                                            <span className="text-xs font-bold text-muted-foreground">{dateStr}</span>
                                        </div>
                                        <p className="text-xs text-muted-foreground">Shift : {punch.shift}</p>
                                    </div>
                                    <ChevronRight className="w-4 h-4 text-muted-foreground" />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Punch Details Drawer via shared component */}
                <PunchDetailsSheet
                    isOpen={!!selectedPunch}
                    onClose={() => setSelectedPunch(null)}
                    punch={selectedPunch}
                    employeeName={data.name}
                />

            </div>
        </div>
    );
};

export default TimecardScreen;
