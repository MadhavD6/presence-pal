import { ChevronLeft, Calendar as CalendarIcon, FileText, ChevronDown, ChevronRight, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { format, differenceInDays, parseISO } from 'date-fns';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { employeeApi } from '@/services/api';

interface LeaveHistoryScreenProps {
    onBack: () => void;
    onApplyLeave: () => void;
    defaultTab?: 'leaves' | 'corrections';
}

const LeaveHistoryScreen = ({ onBack, onApplyLeave, defaultTab = 'leaves' }: LeaveHistoryScreenProps) => {

    const { data: leavesRaw, isLoading: leavesLoading } = useQuery({
        queryKey: ['leaves'],
        queryFn: () => employeeApi.getLeaves(),
    });

    const { data: correctionsRaw, isLoading: correctionsLoading } = useQuery({
        queryKey: ['myCorrections'],
        queryFn: () => employeeApi.getCorrections(),
    });

    const leaves = (leavesRaw || []).map((l: any) => {
        const fromDate = parseISO(l.start_date);
        const toDate = parseISO(l.end_date);
        const days = differenceInDays(toDate, fromDate) + 1;

        let color = "text-yellow-600 bg-yellow-100";
        if (l.status === 'Approved') color = "text-green-600 bg-green-100";
        if (l.status === 'Rejected') color = "text-red-600 bg-red-100";

        return {
            id: l.id,
            type: l.leave_type || "Leave",
            fromDate,
            toDate,
            days,
            reason: l.reason || "-",
            managerComment: "-",
            status: l.status,
            color,
            name: "Me"
        };
    });

    const corrections = (correctionsRaw || []).map((c: any) => {
        let color = "text-yellow-600 bg-yellow-100";
        if (c.status === 'Approved') color = "text-green-600 bg-green-100";
        if (c.status === 'Rejected') color = "text-red-600 bg-red-100";

        return {
            id: c.id,
            date: parseISO(c.original_date),
            reason: c.reason,
            status: c.status,
            color,
            inTime: c.corrected_in ? format(parseISO(c.corrected_in), 'hh:mm a') : '-',
            outTime: c.corrected_out ? format(parseISO(c.corrected_out), 'hh:mm a') : '-'
        };
    });

    if (leavesLoading && correctionsLoading) {
        return <div className="min-h-screen flex items-center justify-center bg-background text-foreground">Loading...</div>;
    }

    return (
        <div className="min-h-screen bg-background flex flex-col animate-slide-in-right relative">
            {/* Header */}
            <div className="px-4 py-4 flex items-center gap-2 sticky top-0 bg-background/95 backdrop-blur z-10">
                <Button variant="ghost" size="icon" onClick={onBack}>
                    <ChevronLeft className="w-6 h-6" />
                </Button>
                <h1 className="text-xl font-bold">Request History</h1>
            </div>

            <div className="flex-1 overflow-y-auto p-4 pb-24">
                <Tabs defaultValue={defaultTab} className="w-full">
                    <TabsList className="grid w-full grid-cols-2 mb-4">
                        <TabsTrigger value="leaves">Leaves</TabsTrigger>
                        <TabsTrigger value="corrections">Corrections</TabsTrigger>
                    </TabsList>

                    <TabsContent value="leaves" className="space-y-6">
                        {/* Banner */}
                        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-2xl p-6 relative overflow-hidden h-32 flex items-center">
                            <div className="absolute right-0 top-0 bottom-0 w-32 bg-blue-100/50 dark:bg-blue-800/20 skew-x-12 translate-x-8"></div>
                            <div className="absolute right-12 top-0 bottom-0 w-32 bg-blue-200/30 dark:bg-blue-700/20 skew-x-12 translate-x-8"></div>

                            <div className="bg-white dark:bg-card px-6 py-3 rounded-lg shadow-sm z-10">
                                <span className="text-blue-600 dark:text-blue-400 font-bold flex items-center gap-1 cursor-pointer">
                                    View All <ChevronRight className="w-4 h-4" />
                                </span>
                            </div>
                        </div>

                        <div className="flex items-center justify-between">
                            <h2 className="font-bold text-lg">Leave History</h2>
                            {/* Filters hidden for brevity/MVP */}
                        </div>

                        {/* Leave List */}
                        <div className="space-y-4">
                            {leaves.length === 0 && (
                                <div className="text-center text-muted-foreground py-8">
                                    No leave history found.
                                </div>
                            )}
                            {leaves.map((leave: any) => (
                                <Card key={leave.id} className="border-border shadow-sm">
                                    <CardContent className="p-4 space-y-4">
                                        <div className="flex justify-between items-start">
                                            <div className="flex gap-3">
                                                <div className="w-10 h-10 rounded-full bg-muted overflow-hidden">
                                                    <img src={`https://ui-avatars.com/api/?name=${leave.name}&background=random`} alt="Profile" className="w-full h-full object-cover" />
                                                </div>
                                                <div className="space-y-1">
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-xs text-muted-foreground">Leave Type:</span>
                                                        <span className="font-bold text-sm block">{leave.type}</span>
                                                    </div>
                                                    <div className="text-xs font-medium">
                                                        From: <span className="font-bold">{format(leave.fromDate, "dd MMM yyyy")}</span> To: <span className="font-bold">{format(leave.toDate, "dd MMM yyyy")}</span>
                                                    </div>
                                                    <div className="text-xs font-medium">
                                                        Days: <span className="font-bold">{leave.days}</span>
                                                    </div>
                                                    <div className="text-xs font-medium text-muted-foreground">
                                                        Reason: <span className="text-foreground font-bold">{leave.reason}</span>
                                                    </div>
                                                </div>
                                            </div>
                                            <span className={`text-[10px] font-bold px-2 py-1 rounded ${leave.color}`}>
                                                {leave.status}
                                            </span>
                                        </div>
                                        <Button variant="outline" size="sm" className="w-fit text-blue-600 bg-blue-50 border-blue-100 hover:bg-blue-100 dark:bg-blue-900/20 dark:border-blue-800 dark:text-blue-400">
                                            <FileText className="w-4 h-4 mr-2" /> Attachment
                                        </Button>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                        {/* Apply Leave Button (only on Leaves tab) */}
                        <div className="fixed bottom-0 left-0 right-0 p-4 bg-background border-t border-border z-20">
                            <Button className="w-full bg-blue-700 hover:bg-blue-800 text-white rounded-xl h-12 text-base font-bold" onClick={onApplyLeave}>
                                Apply Leave
                            </Button>
                        </div>
                    </TabsContent>

                    <TabsContent value="corrections" className="space-y-6">
                        <div className="flex items-center justify-between mt-4">
                            <h2 className="font-bold text-lg">Correction Requests</h2>
                        </div>

                        <div className="space-y-4">
                            {corrections.length === 0 && (
                                <div className="text-center text-muted-foreground py-8">
                                    No correction requests found.
                                </div>
                            )}
                            {corrections.map((item: any) => (
                                <Card key={item.id} className="border-border shadow-sm">
                                    <CardContent className="p-4">
                                        <div className="flex justify-between items-start mb-2">
                                            <div className="flex items-center gap-2">
                                                <CalendarIcon className="w-4 h-4 text-muted-foreground" />
                                                <span className="font-bold text-sm">{format(item.date, "dd MMM yyyy")}</span>
                                            </div>
                                            <span className={`text-[10px] font-bold px-2 py-1 rounded ${item.color}`}>
                                                {item.status}
                                            </span>
                                        </div>

                                        <div className="space-y-2 text-sm">
                                            <div className="flex justify-between">
                                                <span className="text-muted-foreground">Reason:</span>
                                                <span className="font-medium">{item.reason}</span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span className="text-muted-foreground">Corrected In:</span>
                                                <span className="font-medium">{item.inTime}</span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span className="text-muted-foreground">Corrected Out:</span>
                                                <span className="font-medium">{item.outTime}</span>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    </TabsContent>
                </Tabs>
            </div>
        </div>
    );
};

export default LeaveHistoryScreen;
