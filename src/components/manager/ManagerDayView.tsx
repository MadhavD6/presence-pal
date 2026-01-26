import { Search, Calendar, Loader2 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { format } from 'date-fns';
import { useState, useEffect } from 'react';
import { api } from '@/services/api';

const ManagerDayView = () => {
    const [date, setDate] = useState(new Date());
    const [isLoading, setIsLoading] = useState(true);
    const [stats, setStats] = useState({
        total: 0,
        present: 0,
        in: 0,
        out: 0,
        notIn: 0,
        leave: 0,
        holiday: 0,
        weeklyOff: 0
    });
    const [staffList, setStaffList] = useState<any[]>([]);

    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            try {
                const [statsData, logsData] = await Promise.all([
                    api.getManagerStats(date),
                    api.getManagerLogs(date)
                ]);
                setStats(statsData);
                setStaffList(logsData);
            } catch (error) {
                console.error("Failed to fetch manager data", error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchData();
    }, [date]);

    return (
        <div className="space-y-4 animate-fade-in">
            {/* Header Controls */}
            <div className="flex gap-2 items-center">
                <Button variant="outline" className="flex-1 justify-start font-normal">
                    <Calendar className="mr-2 h-4 w-4" />
                    {format(date, "dd MMM, yyyy")}
                </Button>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-2">
                {/* Total Staff - Blue Card */}
                <Card className="bg-primary text-primary-foreground border-none">
                    <CardContent className="p-3">
                        <span className="text-2xl font-bold block">
                            {isLoading ? <Loader2 className="h-6 w-6 animate-spin" /> : stats.total}
                        </span>
                        <span className="text-xs opacity-90">Total Staff</span>
                    </CardContent>
                </Card>

                {/* Present stats */}
                <Card>
                    <CardContent className="p-3">
                        <div className="flex justify-between items-baseline mb-1">
                            <span className="text-2xl font-bold">
                                {isLoading ? "-" : stats.present}
                            </span>
                            <span className="text-sm font-medium">Present</span>
                        </div>
                        <div className="text-[10px] text-muted-foreground flex gap-1">
                            <span>{stats.in} In</span>
                            <span>|</span>
                            <span>{stats.out} Out</span>
                        </div>
                    </CardContent>
                </Card>

                {/* Not In */}
                <Card>
                    <CardContent className="p-3">
                        <span className="text-2xl font-bold block">
                            {isLoading ? "-" : stats.notIn}
                        </span>
                        <span className="text-xs text-muted-foreground">Not yet in</span>
                    </CardContent>
                </Card>

                {/* Leave */}
                <Card>
                    <CardContent className="p-3">
                        <span className="text-2xl font-bold block">
                            {isLoading ? "-" : stats.leave}
                        </span>
                        <span className="text-xs text-muted-foreground">Leave</span>
                    </CardContent>
                </Card>

                {/* Holiday */}
                <Card>
                    <CardContent className="p-3">
                        <span className="text-2xl font-bold block">
                            {isLoading ? "-" : stats.holiday}
                        </span>
                        <span className="text-xs text-muted-foreground">Holiday</span>
                    </CardContent>
                </Card>

                {/* Weekly Off */}
                <Card>
                    <CardContent className="p-3">
                        <span className="text-2xl font-bold block">
                            {isLoading ? "-" : stats.weeklyOff}
                        </span>
                        <span className="text-xs text-muted-foreground">Weekly-Off</span>
                    </CardContent>
                </Card>
            </div>

            {/* Search */}
            <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input placeholder="Search Staff" className="pl-9 bg-card" />
            </div>

            {/* Staff List */}
            <div className="space-y-4 pb-20">
                {isLoading ? (
                    <div className="text-center py-10 text-muted-foreground">Loading...</div>
                ) : staffList.length === 0 ? (
                    <div className="text-center py-10 text-muted-foreground">No records found</div>
                ) : (
                    staffList.map((staff, idx) => (
                        <div key={idx} className="bg-card rounded-xl p-4 border border-border flex items-start justify-between">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center font-bold text-muted-foreground text-sm uppercase">
                                    {staff.avatar}
                                </div>
                                <div>
                                    <h3 className="font-bold text-sm">
                                        {staff.name} <span className="font-normal text-muted-foreground text-xs">({staff.id})</span>
                                    </h3>
                                    <div className="flex items-center gap-2 mt-1">
                                        <span className="text-success font-bold text-xs">{staff.inTime}</span>
                                        <span className="text-[10px] text-muted-foreground">---- {staff.duration} ----</span>
                                        <span className="text-xs text-muted-foreground">--</span>
                                    </div>
                                </div>
                            </div>
                            <span className={`px-2 py-0.5 text-[10px] font-bold rounded uppercase ${staff.status === 'In' ? 'bg-green-100 text-green-700' :
                                    staff.status === 'Out' ? 'bg-orange-100 text-orange-700' :
                                        'bg-gray-100 text-gray-700'
                                }`}>
                                {staff.status}
                            </span>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default ManagerDayView;
