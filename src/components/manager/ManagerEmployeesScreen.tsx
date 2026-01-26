import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Search, MapPin, Users, Building } from 'lucide-react';
import { api, managerApi } from '@/services/api';
import { toast } from 'sonner';

export const ManagerEmployeesScreen = () => {
    // --- State: Employees List ---
    const [employees, setEmployees] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [selectedEmployees, setSelectedEmployees] = useState<number[]>([]);

    // --- State: Create/Edit Employee ---
    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [editingEmp, setEditingEmp] = useState<any>(null);
    const [formData, setFormData] = useState<any>({ name: '', employee_id: '', role: 'user', site_id: undefined });

    // --- State: Assign Site ---
    const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
    const [sites, setSites] = useState<any[]>([]);
    const [selectedSiteId, setSelectedSiteId] = useState<string>('');

    // --- Effects ---
    useEffect(() => {
        loadData();
    }, []);

    // --- Data Loading ---
    const loadData = async () => {
        setLoading(true);
        try {
            const [emps, siteList] = await Promise.all([
                managerApi.getEmployees(),
                managerApi.getSites()
            ]);
            setEmployees(emps);
            setSites(siteList);
        } catch (error) {
            console.error(error);
            toast.error("Failed to load employees");
        } finally {
            setLoading(false);
        }
    };

    // --- Handlers: List Filtering & Selection ---
    const filteredEmployees = employees.filter(emp =>
        emp.name.toLowerCase().includes(search.toLowerCase()) ||
        emp.employee_id?.toLowerCase().includes(search.toLowerCase())
    );

    const toggleSelectAll = () => {
        if (selectedEmployees.length === filteredEmployees.length) {
            setSelectedEmployees([]);
        } else {
            setSelectedEmployees(filteredEmployees.map(e => e.id));
        }
    };

    const toggleSelect = (id: number) => {
        if (selectedEmployees.includes(id)) {
            setSelectedEmployees(prev => prev.filter(x => x !== id));
        } else {
            setSelectedEmployees(prev => [...prev, id]);
        }
    };

    // --- Handlers: Create/Edit ---
    const openCreate = () => {
        setEditingEmp(null);
        setFormData({ name: '', employee_id: '', role: 'user', site_id: undefined });
        setIsCreateOpen(true);
    };

    const openEdit = (emp: any) => {
        setEditingEmp(emp);
        setFormData({
            name: emp.name,
            employee_id: emp.employee_id,
            role: emp.role,
            site_id: emp.site_id
        });
        setIsCreateOpen(true);
    };

    const submitCreate = async () => {
        try {
            if (editingEmp) {
                await managerApi.updateEmployee(editingEmp.id, formData);
                toast.success("Employee updated");
            } else {
                await managerApi.createEmployee(formData);
                toast.success("Employee created");
            }
            setIsCreateOpen(false);
            loadData();
        } catch (e) {
            toast.error("Operation failed");
        }
    };

    // --- Handlers: Assign Site ---
    const handleAssignSite = async () => {
        if (!selectedSiteId) return;
        try {
            await managerApi.assignSite(selectedEmployees, parseInt(selectedSiteId));
            toast.success(`Assigned ${selectedEmployees.length} employees to site`);
            setIsAssignModalOpen(false);
            setSelectedEmployees([]);
            loadData(); // Refresh to show new sites
        } catch (error) {
            toast.error("Failed to assign site");
        }
    };

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            {/* Header */}
            <div className="flex flex-col sm:flex-row justify-between gap-4 items-start sm:items-center">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight">Employees</h2>
                    <p className="text-muted-foreground">Manage your staff and site assignments.</p>
                </div>
                <div className="flex gap-2 w-full sm:w-auto">
                    {selectedEmployees.length > 0 && (
                        <Button onClick={() => setIsAssignModalOpen(true)} variant="secondary">
                            <MapPin className="w-4 h-4 mr-2" />
                            Assign Site ({selectedEmployees.length})
                        </Button>
                    )}
                    <Button onClick={openCreate}>
                        <Users className="w-4 h-4 mr-2" />
                        Add Employee
                    </Button>
                </div>
            </div>

            {/* List */}
            <Card>
                <CardHeader className="pb-3">
                    <div className="relative">
                        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Search by name or ID..."
                            className="pl-9 max-w-sm"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="rounded-md border">
                        <table className="w-full text-sm">
                            <thead className="bg-muted/50 border-b">
                                <tr className="text-left">
                                    <th className="p-4 w-[50px]">
                                        <Checkbox
                                            checked={filteredEmployees.length > 0 && selectedEmployees.length === filteredEmployees.length}
                                            onCheckedChange={toggleSelectAll}
                                        />
                                    </th>
                                    <th className="p-4 font-medium text-muted-foreground">Name</th>
                                    <th className="p-4 font-medium text-muted-foreground">ID</th>
                                    <th className="p-4 font-medium text-muted-foreground">Role</th>
                                    <th className="p-4 font-medium text-muted-foreground">Site</th>
                                    <th className="p-4 font-medium text-muted-foreground text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {loading ? (
                                    <tr><td colSpan={6} className="p-8 text-center text-muted-foreground">Loading...</td></tr>
                                ) : filteredEmployees.length === 0 ? (
                                    <tr><td colSpan={6} className="p-8 text-center text-muted-foreground">No employees found</td></tr>
                                ) : (
                                    filteredEmployees.map((emp) => (
                                        <tr key={emp.id} className="border-b last:border-0 hover:bg-muted/50 transition-colors">
                                            <td className="p-4">
                                                <Checkbox
                                                    checked={selectedEmployees.includes(emp.id)}
                                                    onCheckedChange={() => toggleSelect(emp.id)}
                                                />
                                            </td>
                                            <td className="p-4 font-medium">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-xs">
                                                        {emp.name.charAt(0)}
                                                    </div>
                                                    {emp.name}
                                                </div>
                                            </td>
                                            <td className="p-4 text-muted-foreground">{emp.employee_id || '-'}</td>
                                            <td className="p-4">{emp.role || 'Employee'}</td>
                                            <td className="p-4">
                                                {emp.site_name ? (
                                                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
                                                        {emp.site_name}
                                                    </span>
                                                ) : (
                                                    <span className="text-muted-foreground italic">Unassigned</span>
                                                )}
                                            </td>
                                            <td className="p-4 text-right">
                                                <Button variant="ghost" size="sm" onClick={() => openEdit(emp)}>Edit</Button>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>

            {/* Create/Edit Modal */}
            <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>{editingEmp ? 'Edit Employee' : 'Add Employee'}</DialogTitle>
                        <DialogDescription>
                            {editingEmp ? 'Update employee details' : 'Register a new employee record'}
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label>Full Name</Label>
                            <Input
                                value={formData.name}
                                onChange={e => setFormData({ ...formData, name: e.target.value })}
                                placeholder="e.g. John Doe"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Employee ID</Label>
                            <Input
                                value={formData.employee_id}
                                onChange={e => setFormData({ ...formData, employee_id: e.target.value })}
                                placeholder="e.g. EMP001"
                                disabled={!!editingEmp} // Prevent ID change for simplicity
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Role</Label>
                                <select
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                                    value={formData.role}
                                    onChange={e => setFormData({ ...formData, role: e.target.value })}
                                >
                                    <option value="user">User</option>
                                    <option value="manager">Manager</option>
                                    <option value="admin">Admin</option>
                                </select>
                            </div>
                            <div className="space-y-2">
                                <Label>Site</Label>
                                <select
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                                    value={formData.site_id || ""}
                                    onChange={e => setFormData({ ...formData, site_id: e.target.value ? parseInt(e.target.value) : undefined })}
                                >
                                    <option value="">Unassigned</option>
                                    {sites.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                                </select>
                            </div>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
                        <Button onClick={submitCreate}>Save</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Assign Site Modal */}
            <Dialog open={isAssignModalOpen} onOpenChange={setIsAssignModalOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Assign Site</DialogTitle>
                        <DialogDescription>
                            Assigning {selectedEmployees.length} employees to a new site location.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="py-4 space-y-4">
                        <div className="grid gap-2">
                            {sites.map(site => (
                                <div
                                    key={site.id}
                                    className={`p-3 rounded-lg border cursor-pointer flex items-center gap-3 transition-all ${selectedSiteId === site.id.toString() ? 'border-primary bg-primary/5' : 'hover:border-primary/50'}`}
                                    onClick={() => setSelectedSiteId(site.id.toString())}
                                >
                                    <Building className="w-5 h-5 text-muted-foreground" />
                                    <div className="flex-1">
                                        <div className="font-semibold">{site.name}</div>
                                        <div className="text-xs text-muted-foreground">{site.address}</div>
                                    </div>
                                    {selectedSiteId === site.id.toString() && <div className="w-3 h-3 rounded-full bg-primary" />}
                                </div>
                            ))}
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setIsAssignModalOpen(false)}>Cancel</Button>
                        <Button onClick={handleAssignSite} disabled={!selectedSiteId}>Confirm Assignment</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
};
