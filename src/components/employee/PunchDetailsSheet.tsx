import { Drawer, DrawerContent, DrawerHeader, DrawerFooter } from '@/components/ui/drawer';
import { format } from 'date-fns';

interface Punch {
    type: 'In' | 'Out';
    time: string;
    date: string | Date; // Can be string "dd MMM, yyyy" or Date object
    shift: string;
    location: string;
    address: string;
    id?: number;
}

interface PunchDetailsSheetProps {
    punch: Punch | null;
    isOpen: boolean;
    onClose: () => void;
    // For profile image
    employeeName?: string;
}

const PunchDetailsSheet = ({ punch, isOpen, onClose, employeeName = "User" }: PunchDetailsSheetProps) => {
    if (!punch) return null;

    const punchDate = punch.date instanceof Date
        ? format(punch.date, "dd MMM, yyyy")
        : punch.date;

    return (
        <Drawer open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <DrawerContent>
                <DrawerHeader className="text-left space-y-4 pt-6">
                    {/* Profile Row */}
                    <div className="flex items-center gap-3 border-b border-border pb-4">
                        <div className="w-12 h-12 rounded-full bg-black/10 overflow-hidden relative">
                            <img src={`https://ui-avatars.com/api/?name=${employeeName}&background=random`} alt="Profile" className="w-full h-full object-cover" />
                            {/* Status Dot */}
                            <div className={`absolute bottom-0 right-0 w-3 h-3 rounded-full border-2 border-background ${punch.type === 'In' ? 'bg-cyan-400' : 'bg-gray-400'}`}></div>
                        </div>
                        <div>
                            <div className="flex items-center gap-2">
                                <span className={`text-sm font-bold ${punch.type === 'In' ? 'text-cyan-600 dark:text-cyan-400' : 'text-gray-600 dark:text-gray-400'}`}>
                                    {punch.type}
                                </span>
                            </div>
                            <h3 className="font-bold text-lg leading-tight">
                                {punch.time} | {punchDate}
                            </h3>
                        </div>
                    </div>
                </DrawerHeader>

                <div className="p-4 space-y-4">
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <span className="font-medium text-sm">Shift</span>
                            <span className="font-bold text-sm">{punch.shift}</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="font-medium text-sm">Location</span>
                            <span className="font-bold text-sm">{punch.location}</span>
                        </div>
                    </div>

                    <div className="space-y-1">
                        <span className="font-medium text-sm">Address</span>
                        <p className="text-xs font-medium text-right leading-relaxed text-muted-foreground ml-12">
                            {punch.address}
                        </p>
                    </div>

                    {/* Map Preview */}
                    <div className="w-full h-48 bg-muted rounded-xl overflow-hidden relative">
                        <img
                            src={`https://maps.googleapis.com/maps/api/staticmap?center=${encodeURIComponent(punch.location)}&zoom=15&size=600x300&maptype=roadmap&markers=color:red%7C${encodeURIComponent(punch.location)}&key=${import.meta.env.VITE_GOOGLE_MAPS_KEY || ''}`}
                            alt="Map Location"
                            className="w-full h-full object-cover opacity-80"
                            onError={(e) => {
                                (e.target as HTMLImageElement).src = "https://placehold.co/600x400/e2e8f0/64748b?text=Map+Preview";
                            }}
                        />
                        {/* Overlay Pin fallback if image fails or for decoration */}
                        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                            <div className="w-8 h-8 text-red-500 drop-shadow-md">
                                <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" /></svg>
                            </div>
                        </div>
                    </div>
                </div>

                <DrawerFooter>
                    {/* Optional formatting, usually close button */}
                </DrawerFooter>
            </DrawerContent>
        </Drawer>
    );
};

export default PunchDetailsSheet;
