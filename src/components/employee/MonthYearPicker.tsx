import { useState } from 'react';
import { Dialog, DialogContent } from '@/components/ui/dialog'; // Using Dialog for the modal
import { ChevronUp, ChevronDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { format, setMonth, setYear } from 'date-fns';

interface MonthYearPickerProps {
    isOpen: boolean;
    onClose: () => void;
    onSelect: (date: Date) => void;
    currentDate: Date;
}

const MonthYearPicker = ({ isOpen, onClose, onSelect, currentDate }: MonthYearPickerProps) => {
    const [screenDate, setScreenDate] = useState(currentDate);
    const [view, setView] = useState<'months' | 'years'>('months'); // Could expand to year selection list if needed

    const months = [
        "Jan", "Feb", "Mar", "Apr",
        "May", "Jun", "Jul", "Aug",
        "Sep", "Oct", "Nov", "Dec"
    ];

    const handleYearChange = (increment: number) => {
        setScreenDate(prev => setYear(prev, prev.getFullYear() + increment));
    };

    const handleMonthSelect = (monthIndex: number) => {
        setScreenDate(prev => setMonth(prev, monthIndex));
    };

    const handleOk = () => {
        onSelect(screenDate);
        onClose();
    };

    return (
        <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <DialogContent className="sm:max-w-xs p-0 gap-0 overflow-hidden bg-background rounded-xl border-none shadow-xl">
                {/* Header */}
                <div className="bg-primary p-6 text-primary-foreground">
                    <div className="text-sm font-medium opacity-80 mb-1">
                        {format(screenDate, "MMM yyyy")}
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="text-3xl font-bold">{screenDate.getFullYear()}</span>
                        <div className="flex gap-4 cursor-pointer">
                            <ChevronUp className="w-6 h-6" onClick={() => handleYearChange(-1)} />
                            <ChevronDown className="w-6 h-6" onClick={() => handleYearChange(1)} />
                        </div>
                    </div>
                    {/* The screenshot shows chevron up/down for years likely opening a year list or just incrementing. 
                        Simplified: Up/Down arrows to change year.
                        The screenshot has caret-up and caret-down next to 2026.
                    */}

                    {/* Realigning to match screenshot strictly */}
                </div>

                {/* Content */}
                <div className="p-4 grid grid-cols-4 gap-4">
                    {months.map((m, idx) => {
                        const isSelected = screenDate.getMonth() === idx;
                        return (
                            <button
                                key={m}
                                onClick={() => handleMonthSelect(idx)}
                                className={`h-10 w-10 md:w-12 md:h-12 rounded-full flex items-center justify-center text-sm font-medium transition-colors
                                    ${isSelected ? 'bg-primary text-primary-foreground' : 'text-foreground hover:bg-muted'}
                                `}
                            >
                                {m}
                            </button>
                        );
                    })}
                </div>

                {/* Footer */}
                <div className="p-4 flex justify-end gap-2">
                    <Button variant="ghost" onClick={onClose} className="text-primary hover:bg-primary/10 hover:text-primary">Cancel</Button>
                    <Button variant="ghost" onClick={handleOk} className="text-primary font-bold hover:bg-primary/10 hover:text-primary">OK</Button>
                </div>
            </DialogContent>
        </Dialog>
    );
};

export default MonthYearPicker;
