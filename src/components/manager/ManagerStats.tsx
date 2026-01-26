import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, UserCheck, UserX, Clock, CalendarOff, AlertCircle } from 'lucide-react';
import { api } from '@/services/api';
import { toast } from 'sonner';

export const ManagerStats = () => {
    const [stats, setStats] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const data = await api.getManagerStats(new Date());
                setStats(data);
            } catch (error) {
                console.error("Failed to fetch stats", error);
                toast.error("Failed to load dashboard statistics");
            } finally {
                setLoading(false);
            }
        };
        fetchStats();
    }, []);

    const statItems = [
        {
            title: "Total Staff",
            value: stats?.total || 0,
            icon: Users,
            color: "text-blue-600 bg-blue-50 dark:bg-blue-900/20 dark:text-blue-400",
            description: "Registered Employees"
        },
        {
            title: "Present Today",
            value: stats?.present || 0,
            icon: UserCheck,
            color: "text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 dark:text-emerald-400",
            description: "Checked In"
        },
        {
            title: "Late Arrivals",
            value: stats?.late || 0,
            icon: Clock,
            color: "text-amber-600 bg-amber-50 dark:bg-amber-900/20 dark:text-amber-400",
            description: "Arrived after shift start"
        },
        {
            title: "Absent",
            value: stats?.notIn || 0,
            icon: UserX,
            color: "text-rose-600 bg-rose-50 dark:bg-rose-900/20 dark:text-rose-400",
            description: "Not checked in"
        },
        {
            title: "On Leave",
            value: stats?.leave || 0,
            icon: CalendarOff,
            color: "text-purple-600 bg-purple-50 dark:bg-purple-900/20 dark:text-purple-400",
            description: "Approved leave"
        }
    ];

    if (loading) {
        return <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3, 4, 5].map(i => (
                <Card key={i} className="animate-pulse">
                    <CardContent className="p-6 h-32" />
                </Card>
            ))}
        </div>;
    }

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {statItems.map((item, index) => {
                    const Icon = item.icon;
                    return (
                        <Card key={index} className="border-border shadow-sm hover:shadow-md transition-all">
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium text-muted-foreground">
                                    {item.title}
                                </CardTitle>
                                <div className={`p-2 rounded-lg ${item.color}`}>
                                    <Icon className="h-4 w-4" />
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">{item.value}</div>
                                <p className="text-xs text-muted-foreground mt-1">
                                    {item.description}
                                </p>
                            </CardContent>
                        </Card>
                    );
                })}
            </div>

            {/* Recently Active / Pending Actions Preview could go here */}
            {stats?.pending_requests > 0 && (
                <div className="bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-900/50 rounded-lg p-4 flex items-center gap-3">
                    <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-500" />
                    <div>
                        <h4 className="font-semibold text-amber-900 dark:text-amber-400">Action Required</h4>
                        <p className="text-sm text-amber-800 dark:text-amber-300">
                            You have {stats.pending_requests} pending approval requests.
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
};
