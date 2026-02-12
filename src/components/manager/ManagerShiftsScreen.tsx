import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Checkbox } from '@/components/ui/checkbox';
import { Plus, Clock, Edit2, Trash2, Users, Search } from 'lucide-react';
import { shiftsApi, managerApi } from '@/services/api';
import { toast } from 'sonner';

export const ManagerShiftsScreen = () => {
    // --- State ---
    const [shifts, setShifts] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [editingShift, setEditingShift] = useState<any>(null);

    const [formData, setFormData] = useState({
        name: '',
        start_time: '09:00',
        end_time: '18:00',
        grace_period_mins: '15',
        crosses_midnight: false
    });

    // Assignment States
    const [isAssignOpen, setIsAssignOpen] = useState(false);
    const [assignShiftId, setAssignShiftId] = useState<number | null>(null);
    const [employees, setEmployees] = useState<any[]>([]);
    const [selectedEmps, setSelectedEmps] = useState<number[]>([]);
    const [searchEmp, setSearchEmp] = useState('');
    const [weeklyOffs, setWeeklyOffs] = useState<number[]>([6]); // Default Sunday

    const WEEKDAYS = [
        { value: 0, label: 'Mon' },
        { value: 1, label: 'Tue' },
        { value: 2, label: 'Wed' },
        { value: 3, label: 'Thu' },
        { value: 4, label: 'Fri' },
        { value: 5, label: 'Sat' },
        { value: 6, label: 'Sun' },
    ];

    // --- Effects ---
    useEffect(() => {
        loadShifts();
        loadEmployees();
    }, []);

    // --- Loading Data ---
    const loadShifts = async () => {
        setLoading(true);
        try {
            const data = await shiftsApi.getShifts();
            setShifts(data);
        } catch (error) {
            toast.error("Failed to load shifts");
        } finally {
            setLoading(false);
        }
    };

    const loadEmployees = async () => {
        try {
            const data = await managerApi.getEmployees();
            setEmployees(data);
        } catch (e) {
            console.error("Failed loading employees for shift assign");
        }
    };

    // --- Handlers: Shift CRUD ---
    const handleOpenCreate = () => {
        setEditingShift(null);
        setFormData({ name: '', start_time: '09:00', end_time: '18:00', grace_period_mins: '15', crosses_midnight: false });
        setIsCreateOpen(true);
    };

    const handleEdit = (shift: any) => {
        setEditingShift(shift);
        setFormData({
            name: shift.name,
            start_time: shift.start_time.slice(0, 5),
            end_time: shift.end_time.slice(0, 5),
            grace_period_mins: (shift.grace_period_mins || 15).toString(),
            crosses_midnight: shift.crosses_midnight || false
        });
        setIsCreateOpen(true);
    };

    const handleDelete = async (id: number) => {
        if (!confirm("Are you sure you want to delete this shift?")) return;
        try {
            await shiftsApi.deleteShift(id);
            toast.success("Shift deleted");
            loadShifts();
        } catch (error) {
            toast.error("Failed to delete shift");
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const payload = {
                name: formData.name,
                start_time: formData.start_time,
                end_time: formData.end_time,
                grace_period_mins: parseInt(formData.grace_period_mins),
                crosses_midnight: formData.crosses_midnight
            };

            if (editingShift) {
                await shiftsApi.updateShift(editingShift.id, payload);
                toast.success("Shift updated");
            } else {
                await shiftsApi.createShift(payload);
                toast.success("Shift created");
            }
            setIsCreateOpen(false);
            loadShifts();
        } catch (error) {
            toast.error("Operation failed");
        }
    };

    // --- Handlers: Assignments ---
    const fnAssign = (shift: any) => {
        setAssignShiftId(shift.id);
        setSelectedEmps([]); // Reset selection on open. Or ideally fetch current assignments.
        setIsAssignOpen(true);
    };

    const toggleEmp = (id: number) => {
        if (selectedEmps.includes(id)) setSelectedEmps(selectedEmps.filter(x => x !== id));
        else setSelectedEmps([...selectedEmps, id]);
    };

    const submitAssign = async () => {
        if (!assignShiftId) return;
        try {
            const weeklyOffsStr = weeklyOffs.join(',');
            await shiftsApi.assignRoster(assignShiftId, selectedEmps, weeklyOffsStr);
            toast.success(`Assigned ${selectedEmps.length} employees to shift`);
            setIsAssignOpen(false);
        } catch (e) {
            toast.error("Assignment failed");
        }
    };

    const filteredEmps = employees.filter(e => e.name.toLowerCase().includes(searchEmp.toLowerCase()));

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight">Shift Management</h2>
                    <p className="text-muted-foreground">Configure work hours and grace periods.</p>
                </div>
                <Button onClick={handleOpenCreate}>
                    <Plus className="w-4 h-4 mr-2" />
                    Create Shift
                </Button>
            </div>

            {/* List */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {loading ? (
                    <div className="col-span-full py-12 text-center text-muted-foreground">Loading shifts...</div>
                ) : shifts.length === 0 ? (
                    <div className="col-span-full py-12 text-center text-muted-foreground border border-dashed rounded-xl">
                        No shifts configured. Create one to get started.
                    </div>
                ) : (
                    shifts.map((shift) => (
                        <Card key={shift.id} className="group hover:border-primary/50 transition-colors">
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="font-bold text-lg">
                                    {shift.name}
                                </CardTitle>
                                <div className="flex gap-1">
                                    <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handleEdit(shift)}>
                                        <Edit2 className="w-4 h-4" />
                                    </Button>
                                    <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive hover:text-destructive" onClick={() => handleDelete(shift.id)}>
                                        <Trash2 className="w-4 h-4" />
                                    </Button>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="flex items-center gap-4 py-4">
                                    <div className="flex-1 text-center p-3 bg-muted/30 rounded-lg">
                                        <div className="text-xs text-muted-foreground uppercase">Start</div>
                                        <div className="text-xl font-mono font-bold text-emerald-600">{shift.start_time.slice(0, 5)}</div>
                                    </div>
                                    <div className="text-muted-foreground">-</div>
                                    <div className="flex-1 text-center p-3 bg-muted/30 rounded-lg">
                                        <div className="text-xs text-muted-foreground uppercase">End</div>
                                        <div className="text-xl font-mono font-bold text-rose-600">{shift.end_time.slice(0, 5)}</div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                    <Clock className="w-4 h-4" />
                                    Grace Period: {shift.late_threshold_minutes} mins
                                </div>
                                <div className="mt-4 pt-4 border-t">
                                    <Button variant="outline" className="w-full text-xs" onClick={() => fnAssign(shift)}>
                                        <Users className="w-3 h-3 mr-2" />
                                        Manage Assignments
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    ))
                )}
            </div>

            {/* Create/Edit Dialog */}
            <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>{editingShift ? 'Edit Shift' : 'Create New Shift'}</DialogTitle>
                        <DialogDescription>Define working hours and rules.</DialogDescription>
                    </DialogHeader>
                    <form onSubmit={handleSubmit} className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label>Shift Name</Label>
                            <Input
                                placeholder="e.g. General Shift"
                                value={formData.name}
                                onChange={e => setFormData({ ...formData, name: e.target.value })}
                                required
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Start Time</Label>
                                <Input
                                    type="time"
                                    value={formData.start_time}
                                    onChange={e => setFormData({ ...formData, start_time: e.target.value })}
                                    required
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>End Time</Label>
                                <Input
                                    type="time"
                                    value={formData.end_time}
                                    onChange={e => setFormData({ ...formData, end_time: e.target.value })}
                                    required
                                />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label>Grace Period (Minutes)</Label>
                            <Input
                                type="number"
                                min="0"
                                value={formData.grace_period_mins}
                                onChange={e => setFormData({ ...formData, grace_period_mins: e.target.value })}
                                required
                            />
                            <p className="text-xs text-muted-foreground">Time allowed before marking as 'Late'</p>
                        </div>
                        <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/30">
                            <Checkbox
                                id="crosses_midnight"
                                checked={formData.crosses_midnight}
                                onCheckedChange={(checked) => setFormData({ ...formData, crosses_midnight: !!checked })}
                            />
                            <div>
                                <Label htmlFor="crosses_midnight" className="cursor-pointer">Night Shift (Crosses Midnight)</Label>
                                <p className="text-xs text-muted-foreground">Enable for shifts like 10 PM - 6 AM</p>
                            </div>
                        </div>
                        <DialogFooter>
                            <Button type="button" variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
                            <Button type="submit">{editingShift ? 'Save Changes' : 'Create Shift'}</Button>
                        </DialogFooter>
                    </form>
                </DialogContent>
            </Dialog>

            {/* Assign Dialog */}
            <Dialog open={isAssignOpen} onOpenChange={setIsAssignOpen}>
                <DialogContent className="max-w-md h-[80vh] flex flex-col">
                    <DialogHeader>
                        <DialogTitle>Assign Employees to Shift</DialogTitle>
                        <DialogDescription>Select employees to move to this roster.</DialogDescription>
                    </DialogHeader>

                    <div className="relative mb-2">
                        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Search employees..."
                            className="pl-9"
                            value={searchEmp}
                            onChange={e => setSearchEmp(e.target.value)}
                        />
                    </div>

                    <div className="flex-1 overflow-y-auto border rounded-md p-2">
                        {employees.map(emp => (
                            // Only show if matches search
                            (!searchEmp || emp.name.toLowerCase().includes(searchEmp.toLowerCase())) && (
                                <div key={emp.id} className="flex items-center gap-3 p-3 border-b last:border-0 hover:bg-muted/50 cursor-pointer" onClick={() => toggleEmp(emp.id)}>
                                    <Checkbox checked={selectedEmps.includes(emp.id)} onCheckedChange={() => toggleEmp(emp.id)} />
                                    <div>
                                        <div className="text-sm font-medium">{emp.name}</div>
                                        <div className="text-xs text-muted-foreground">{emp.employee_id} | {emp.role}</div>
                                    </div>
                                </div>
                            )
                        ))}
                        {employees.length === 0 && <div className="text-center p-4 text-muted-foreground">No employees found.</div>}
                    </div>

                    {/* Weekly Offs Selector */}
                    <div className="space-y-2 pt-2 border-t">
                        <Label className="text-sm font-medium">Weekly Offs (Select days off)</Label>
                        <div className="flex flex-wrap gap-2">
                            {WEEKDAYS.map(day => (
                                <Button
                                    key={day.value}
                                    type="button"
                                    size="sm"
                                    variant={weeklyOffs.includes(day.value) ? "default" : "outline"}
                                    className="w-12"
                                    onClick={() => {
                                        if (weeklyOffs.includes(day.value)) {
                                            setWeeklyOffs(weeklyOffs.filter(d => d !== day.value));
                                        } else {
                                            setWeeklyOffs([...weeklyOffs, day.value]);
                                        }
                                    }}
                                >
                                    {day.label}
                                </Button>
                            ))}
                        </div>
                        <p className="text-xs text-muted-foreground">Selected: {weeklyOffs.length === 0 ? 'None' : weeklyOffs.map(d => WEEKDAYS.find(w => w.value === d)?.label).join(', ')}</p>
                    </div>

                    <DialogFooter className="mt-4">
                        <Button variant="outline" onClick={() => setIsAssignOpen(false)}>Cancel</Button>
                        <Button onClick={submitAssign} disabled={selectedEmps.length === 0}>
                            Assign ({selectedEmps.length})
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
};
