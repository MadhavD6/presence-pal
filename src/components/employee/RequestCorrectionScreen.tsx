import { ChevronLeft, Calendar, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { format } from 'date-fns';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { useState } from 'react';
import { employeeApi } from '@/services/api';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/context/AuthContext';

interface RequestCorrectionScreenProps {
    date: Date;
    onBack: () => void;
    onSubmit: (data: any) => void;
}

const RequestCorrectionScreen = ({ date, onBack, onSubmit }: RequestCorrectionScreenProps) => {
    const { user } = useAuth();
    const { toast } = useToast();

    // Form State
    const [inTime, setInTime] = useState("");
    const [outTime, setOutTime] = useState("");
    const [reason, setReason] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Mock/Partial data for UI richness (since we don't have full daily stats passed in props yet)
    // In a real iteration, we should fetch these via API or pass them in.
    const currentStats = {
        status: "Absent",
        inTime: "-",
        outTime: "-",
        workedHours: "0h 0m"
    };

    const handleSubmit = async () => {
        if (!reason) {
            toast({ title: "Error", description: "Please select a reason", variant: "destructive" });
            return;
        }

        setIsSubmitting(true);
        try {
            await employeeApi.requestCorrection({
                date: format(date, 'yyyy-MM-dd'),
                in_time: inTime || null,
                out_time: outTime || null,
                reason: reason
            });
            toast({ title: "Success", description: "Correction request submitted" });
            onSubmit({}); // Trigger refresh or callback
            onBack();
        } catch (err) {
            toast({ title: "Error", description: "Failed to submit correction", variant: "destructive" });
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="min-h-screen bg-background flex flex-col animate-slide-in-right z-20 absolute inset-0 bg-background">
            {/* Header */}
            <div className="px-4 py-4 flex items-center gap-2 bg-card border-b border-border sticky top-0 z-10">
                <Button variant="ghost" size="icon" onClick={onBack}>
                    <ChevronLeft className="w-6 h-6" />
                </Button>
                <div>
                    <h1 className="text-lg font-bold">Request Correction</h1>
                    <p className="text-xs text-muted-foreground">({format(date, "EEE, dd MMM, yyyy")})</p>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto pb-20 p-4 space-y-6">
                {/* Profile Summary */}
                <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-black/10 overflow-hidden">
                            <img src={`https://ui-avatars.com/api/?name=${user?.name || "User"}&background=random`} alt="Profile" className="w-full h-full object-cover" />
                        </div>
                        <div>
                            <h3 className="font-bold text-sm">{user?.name}</h3>
                            <p className="text-xs text-muted-foreground">({user?.employee_id})</p>
                        </div>
                    </div>
                    <span className="px-2 py-0.5 text-xs font-bold rounded bg-gray-200 text-gray-700">{currentStats.status}</span>
                </div>

                {/* Current Times (Read Only View) */}
                <div className="grid grid-cols-3 gap-4 text-xs">
                    <div>
                        <p className="text-muted-foreground">In Time</p>
                        <p className="font-bold">{currentStats.inTime}</p>
                    </div>
                    <div>
                        <p className="text-muted-foreground">Out Time</p>
                        <p className="font-bold">{currentStats.outTime}</p>
                    </div>
                    <div className="text-right">
                        <p className="text-muted-foreground">Worked Hours</p>
                        <p className="font-bold">{currentStats.workedHours}</p>
                    </div>
                </div>

                <div className="flex justify-end">
                    <button className="text-primary font-bold text-sm">Split Time</button>
                </div>

                {/* Form */}
                <Card className="border-border shadow-sm">
                    <CardContent className="p-4 space-y-4">

                        <div className="space-y-2">
                            <Label>In Date & Time</Label>
                            <div className="relative">
                                {/* Using type="time" for functionality, but stylized container */}
                                <Input
                                    type="time"
                                    value={inTime}
                                    onChange={(e) => setInTime(e.target.value)}
                                // className="pr-10" 
                                />
                                {/* <Calendar className="absolute right-3 top-2.5 w-5 h-5 text-muted-foreground pointer-events-none" /> */}
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label>Out Date & Time</Label>
                            <div className="relative">
                                <Input
                                    type="time"
                                    value={outTime}
                                    onChange={(e) => setOutTime(e.target.value)}
                                // className="pr-10" 
                                />
                                {/* <Calendar className="absolute right-3 top-2.5 w-5 h-5 text-muted-foreground pointer-events-none" /> */}
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label>Reason</Label>
                            <Select onValueChange={setReason} value={reason}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Select" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="Forgot to Punch">Forgot to Punch</SelectItem>
                                    <SelectItem value="System Error">System Error</SelectItem>
                                    <SelectItem value="On Duty">On Duty</SelectItem>
                                    <SelectItem value="Work From Home">Work From Home</SelectItem>
                                    <SelectItem value="Other">Other</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        {/* Extra fields from previous UI (Visual/Disabled for now) */}
                        <div className="grid grid-cols-2 gap-4 opacity-50 pointer-events-none">
                            <div className="space-y-2">
                                <Label>Worked Hours</Label>
                                <div className="flex gap-2">
                                    <Input placeholder="-" className="text-center" disabled />
                                    <Input placeholder="-" className="text-center" disabled />
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Label>Overtime</Label>
                                <div className="flex gap-2">
                                    <Input placeholder="hrs" className="text-center placeholder:text-muted-foreground/50" disabled />
                                    <Input placeholder="min" className="text-center placeholder:text-muted-foreground/50" disabled />
                                </div>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4 opacity-50 pointer-events-none">
                            <div className="space-y-2">
                                <Label>Break Time (Paid)</Label>
                                <div className="flex gap-2">
                                    <Input placeholder="hrs" className="text-center placeholder:text-muted-foreground/50" disabled />
                                    <Input placeholder="min" className="text-center placeholder:text-muted-foreground/50" disabled />
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Label>Break Time (Unpaid)</Label>
                                <div className="flex gap-2">
                                    <Input placeholder="hrs" className="text-center placeholder:text-muted-foreground/50" disabled />
                                    <Input placeholder="min" className="text-center placeholder:text-muted-foreground/50" disabled />
                                </div>
                            </div>
                        </div>

                        <Button className="w-full mt-4" size="lg" onClick={handleSubmit} disabled={isSubmitting}>
                            {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                            Submit Request
                        </Button>

                    </CardContent>
                </Card>
            </div>
        </div>
    );
};



export default RequestCorrectionScreen;
