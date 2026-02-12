import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';

interface EmployeeDetailModalProps {
    employee: any;
    isOpen: boolean;
    onClose: () => void;
}

const EmployeeDetailModal = ({ employee, isOpen, onClose }: EmployeeDetailModalProps) => {
    if (!employee) return null;

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-2xl">
                <DialogHeader>
                    <DialogTitle>Employee Details</DialogTitle>
                </DialogHeader>

                <div className="grid gap-6 py-4">
                    <div className="flex items-center gap-4">
                        <Avatar className="h-16 w-16">
                            <AvatarFallback className="text-lg bg-primary/10 text-primary">
                                {employee.name?.charAt(0)}
                            </AvatarFallback>
                        </Avatar>
                        <div>
                            <h3 className="text-xl font-bold">{employee.name}</h3>
                            <p className="text-muted-foreground">{employee.employee_id} • {employee.role}</p>
                            <p className="text-sm text-muted-foreground">{employee.email}</p>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="p-4 rounded-lg border bg-muted/20">
                            <div className="text-sm font-medium text-muted-foreground">Current Site</div>
                            <div className="text-lg font-semibold">{employee.site_name || 'Unassigned'}</div>
                        </div>
                        <div className="p-4 rounded-lg border bg-muted/20">
                            <div className="text-sm font-medium text-muted-foreground">Shift</div>
                            <div className="text-lg font-semibold">{employee.shift_name || 'General'}</div>
                        </div>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
};

export default EmployeeDetailModal;
