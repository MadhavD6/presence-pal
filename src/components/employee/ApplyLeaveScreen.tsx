import { ChevronLeft, Paperclip, ChevronRight, Calendar as CalendarIcon, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';
import { format } from 'date-fns';
import { useState, useRef } from 'react';
import { cn } from '@/lib/utils';
import { employeeApi } from '@/services/api';
import { useToast } from '@/components/ui/use-toast';

interface ApplyLeaveScreenProps {
    onBack: () => void;
}

const ApplyLeaveScreen = ({ onBack }: ApplyLeaveScreenProps) => {
    const [startDate, setStartDate] = useState<Date>();
    const [endDate, setEndDate] = useState<Date>();
    const [leaveType, setLeaveType] = useState<string>('');
    const [reason, setReason] = useState('');
    const [file, setFile] = useState<File | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const { toast } = useToast();

    const handleSubmit = async () => {
        if (!startDate || !endDate || !leaveType) {
            toast({
                title: "Missing Fields",
                description: "Please fill in all required fields",
                variant: "destructive"
            });
            return;
        }

        setIsSubmitting(true);
        try {
            await employeeApi.applyLeave({
                leave_type: leaveType,
                start_date: format(startDate, 'yyyy-MM-dd'),
                end_date: format(endDate, 'yyyy-MM-dd'),
                reason: reason,
                file: file
            });
            toast({
                title: "Success",
                description: "Leave application submitted successfully",
            });
            onBack();
        } catch (error) {
            toast({
                title: "Error",
                description: "Failed to submit leave application",
                variant: "destructive"
            });
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="min-h-screen bg-background flex flex-col animate-slide-in-right relative">
            {/* Header */}
            <div className="px-4 py-4 flex items-center gap-2 sticky top-0 bg-background/95 backdrop-blur z-10">
                <Button variant="ghost" size="icon" onClick={onBack}>
                    <ChevronLeft className="w-6 h-6" />
                </Button>
                <h1 className="text-xl font-bold">Apply Leave</h1>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-8 pb-24">

                {/* Leave Details Section */}
                <div className="space-y-4">
                    <h3 className="font-bold text-md">Leave Details</h3>
                    <Select onValueChange={setLeaveType} value={leaveType}>
                        <SelectTrigger className="w-full h-12 bg-card border-border">
                            <SelectValue placeholder="Leave Type" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="Sick Leave">Sick Leave</SelectItem>
                            <SelectItem value="Casual Leave">Casual Leave</SelectItem>
                            <SelectItem value="Privilege Leave">Privilege Leave</SelectItem>
                        </SelectContent>
                    </Select>

                    <div className="flex items-center gap-2">
                        {/* Start Date */}
                        <div className="flex-1 p-3 bg-card border border-border rounded-md">
                            <p className="text-xs text-muted-foreground mb-1">First Day of Leave</p>
                            <Popover>
                                <PopoverTrigger asChild>
                                    <Button
                                        variant={"ghost"}
                                        className={cn(
                                            "w-full justify-start text-left font-normal p-0 h-auto hover:bg-transparent",
                                            !startDate && "text-muted-foreground"
                                        )}
                                    >
                                        {startDate ? format(startDate, "dd MMM yyyy") : <span>- --</span>}
                                    </Button>
                                </PopoverTrigger>
                                <PopoverContent className="w-auto p-0" align="start">
                                    <Calendar
                                        mode="single"
                                        selected={startDate}
                                        onSelect={setStartDate}
                                        initialFocus
                                    />
                                </PopoverContent>
                            </Popover>
                        </div>

                        <ChevronRight className="w-4 h-4 text-muted-foreground" />

                        {/* End Date */}
                        <div className="flex-1 p-3 bg-card border border-border rounded-md">
                            <p className="text-xs text-muted-foreground mb-1">Last Day of Leave</p>
                            <Popover>
                                <PopoverTrigger asChild>
                                    <Button
                                        variant={"ghost"}
                                        className={cn(
                                            "w-full justify-start text-left font-normal p-0 h-auto hover:bg-transparent",
                                            !endDate && "text-muted-foreground"
                                        )}
                                    >
                                        {endDate ? format(endDate, "dd MMM yyyy") : <span>- --</span>}
                                    </Button>
                                </PopoverTrigger>
                                <PopoverContent className="w-auto p-0" align="start">
                                    <Calendar
                                        mode="single"
                                        selected={endDate}
                                        onSelect={setEndDate}
                                        initialFocus
                                    />
                                </PopoverContent>
                            </Popover>
                        </div>
                    </div>
                </div>

                {/* Reason Section */}
                <div className="space-y-2">
                    <h3 className="font-bold text-md">Reason</h3>
                    <Textarea
                        placeholder="Specify your reason for leave"
                        className="min-h-[100px] resize-none border-border bg-card"
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                    />
                </div>

                {/* Attachment Section */}
                <div className="space-y-4">
                    <h3 className="font-bold text-md">Attachment</h3>
                    <input
                        type="file"
                        ref={fileInputRef}
                        className="hidden"
                        onChange={(e) => {
                            if (e.target.files && e.target.files[0]) {
                                setFile(e.target.files[0]);
                            }
                        }}
                    />
                    <div
                        className="bg-blue-50 dark:bg-blue-900/20 border-border rounded-lg p-4 flex items-center justify-between cursor-pointer hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
                        onClick={() => fileInputRef.current?.click()}
                    >
                        <span className="text-blue-700 dark:text-blue-300 font-medium text-sm">
                            {file ? file.name : "Select Attachment"}
                        </span>
                        <Paperclip className="w-5 h-5 text-blue-700 dark:text-blue-300" />
                    </div>
                </div>

            </div>

            {/* Footer Button */}
            <div className="fixed bottom-0 left-0 right-0 p-4 bg-background border-t border-border z-20">
                <Button
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded-xl h-12 text-base font-bold"
                    onClick={handleSubmit}
                    disabled={isSubmitting}
                >
                    {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : "Apply Leave"}
                </Button>
            </div>
        </div>
    );
};

export default ApplyLeaveScreen;
