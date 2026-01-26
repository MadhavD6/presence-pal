import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Check, X, Clock, FileText, AlertCircle } from 'lucide-react';
import { managerApi } from '@/services/api';
import { toast } from 'sonner';
import { format } from 'date-fns';

export const ManagerApprovalsScreen = () => {
    const [leaves, setLeaves] = useState<any[]>([]);
    const [corrections, setCorrections] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setLoading(true);
        try {
            const [leaveData, correctionData] = await Promise.all([
                managerApi.getPendingLeaves(),
                managerApi.getPendingCorrections()
            ]);
            setLeaves(leaveData);
            setCorrections(correctionData);
        } catch (error) {
            console.error(error);
            toast.error("Failed to load approvals");
        } finally {
            setLoading(false);
        }
    };

    const handleLeaveAction = async (id: number, action: 'approve' | 'reject') => {
        try {
            await managerApi.processLeave(id, action);
            toast.success(`Leave ${action}d`);
            loadData();
        } catch (error) {
            toast.error(`Failed to ${action} leave`);
        }
    };

    const handleCorrectionAction = async (id: number, action: 'approve' | 'reject') => {
        try {
            await managerApi.processCorrection(id, action);
            toast.success(`Correction ${action}d`);
            loadData();
        } catch (error) {
            toast.error(`Failed to ${action} correction`);
        }
    };

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            <div>
                <h2 className="text-2xl font-bold tracking-tight">Approvals</h2>
                <p className="text-muted-foreground">Review and action pending requests.</p>
            </div>

            <Tabs defaultValue="leaves" className="w-full">
                <TabsList className="grid w-full max-w-md grid-cols-2">
                    <TabsTrigger value="leaves" className="relative">
                        Leaves
                        {leaves.length > 0 && (
                            <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] text-white animate-pulse">
                                {leaves.length}
                            </span>
                        )}
                    </TabsTrigger>
                    <TabsTrigger value="corrections" className="relative">
                        Corrections
                        {corrections.length > 0 && (
                            <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] text-white animate-pulse">
                                {corrections.length}
                            </span>
                        )}
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="leaves" className="space-y-4 py-4">
                    {leaves.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-12 text-muted-foreground bg-muted/10 rounded-xl border border-dashed">
                            <FileText className="w-10 h-10 mb-3 opacity-20" />
                            <p>No pending leave requests</p>
                        </div>
                    ) : (
                        leaves.map((leave) => (
                            <Card key={leave.id} className="overflow-hidden border-l-4 border-l-blue-500 shadow-sm">
                                <CardContent className="p-6">
                                    <div className="flex flex-col md:flex-row justify-between gap-4">
                                        <div className="flex-1 space-y-2">
                                            <div className="flex items-center gap-2">
                                                <h3 className="font-semibold text-lg">{leave.user_name}</h3>
                                                <Badge variant="outline" className="text-blue-600 bg-blue-50 border-blue-200">
                                                    {leave.leave_type}
                                                </Badge>
                                            </div>
                                            <div className="flex items-center gap-4 text-sm text-muted-foreground">
                                                <div className="flex items-center gap-1">
                                                    <Clock className="w-4 h-4" />
                                                    <span>Applied on {format(new Date(leave.created_at), 'dd MMM yyyy')}</span>
                                                </div>
                                            </div>
                                            <div className="p-3 bg-muted/30 rounded-lg text-sm">
                                                <span className="font-medium text-foreground">Duration: </span>
                                                {format(new Date(leave.start_date), 'dd MMM')} - {format(new Date(leave.end_date), 'dd MMM')}
                                                <div className="mt-2 text-muted-foreground italic">
                                                    "{leave.reason}"
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex flex-row md:flex-col gap-2 justify-center min-w-[120px]">
                                            <Button
                                                className="w-full bg-emerald-600 hover:bg-emerald-700"
                                                onClick={() => handleLeaveAction(leave.id, 'approve')}
                                            >
                                                <Check className="w-4 h-4 mr-2" /> Approve
                                            </Button>
                                            <Button
                                                variant="outline"
                                                className="w-full text-destructive hover:bg-destructive/10 border-destructive/20"
                                                onClick={() => handleLeaveAction(leave.id, 'reject')}
                                            >
                                                <X className="w-4 h-4 mr-2" /> Reject
                                            </Button>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))
                    )}
                </TabsContent>

                <TabsContent value="corrections" className="space-y-4 py-4">
                    {corrections.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-12 text-muted-foreground bg-muted/10 rounded-xl border border-dashed">
                            <AlertCircle className="w-10 h-10 mb-3 opacity-20" />
                            <p>No pending correction requests</p>
                        </div>
                    ) : (
                        corrections.map((req) => (
                            <Card key={req.id} className="overflow-hidden border-l-4 border-l-amber-500 shadow-sm">
                                <CardContent className="p-6">
                                    <div className="flex flex-col md:flex-row justify-between gap-4">
                                        <div className="flex-1 space-y-2">
                                            <div className="flex items-center gap-2">
                                                <h3 className="font-semibold text-lg">{req.user_name}</h3>
                                                <Badge variant="outline" className="text-amber-600 bg-amber-50 border-amber-200">
                                                    Time Correction
                                                </Badge>
                                            </div>
                                            <div className="text-sm font-medium">
                                                For Date: {format(new Date(req.date_of_correction), 'EEEE, dd MMM yyyy')}
                                            </div>
                                            <div className="grid grid-cols-2 gap-4 max-w-sm mt-2">
                                                <div className="p-2 border rounded bg-background text-center">
                                                    <div className="text-xs text-muted-foreground uppercase tracking-wider">Requested In</div>
                                                    <div className="font-mono font-bold text-lg text-emerald-600">{req.new_in_time || '--:--'}</div>
                                                </div>
                                                <div className="p-2 border rounded bg-background text-center">
                                                    <div className="text-xs text-muted-foreground uppercase tracking-wider">Requested Out</div>
                                                    <div className="font-mono font-bold text-lg text-rose-600">{req.new_out_time || '--:--'}</div>
                                                </div>
                                            </div>
                                            <p className="text-sm text-muted-foreground italic mt-2">"{req.reason}"</p>
                                        </div>
                                        <div className="flex flex-row md:flex-col gap-2 justify-center min-w-[120px]">
                                            <Button
                                                className="w-full bg-emerald-600 hover:bg-emerald-700"
                                                onClick={() => handleCorrectionAction(req.id, 'approve')}
                                            >
                                                <Check className="w-4 h-4 mr-2" /> Approve
                                            </Button>
                                            <Button
                                                variant="outline"
                                                className="w-full text-destructive hover:bg-destructive/10 border-destructive/20"
                                                onClick={() => handleCorrectionAction(req.id, 'reject')}
                                            >
                                                <X className="w-4 h-4 mr-2" /> Reject
                                            </Button>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))
                    )}
                </TabsContent>
            </Tabs>
        </div>
    );
};


