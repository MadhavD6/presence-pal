import React from 'react';
import { Bar, BarChart, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import { ChartContainer, ChartTooltip, ChartTooltipContent, ChartLegend, ChartLegendContent } from '@/components/ui/chart';

// Shared Color Palette (Clean Enterprise)
const COLORS = {
    Present: "#10b981", // emerald-500
    Late: "#f59e0b",    // amber-500
    Absent: "#f43f5e",  // rose-500
    Leave: "#3b82f6",   // blue-500
};

const chartConfig = {
    Present: { label: "Present", color: COLORS.Present },
    Late: { label: "Late", color: COLORS.Late },
    Absent: { label: "Absent", color: COLORS.Absent },
    Leave: { label: "On Leave", color: COLORS.Leave },
};

interface AttendanceTrendsChartProps {
    data: any[];
}

export const AttendanceTrendsChart = ({ data }: AttendanceTrendsChartProps) => {
    return (
        <ChartContainer config={chartConfig} className="h-[300px] w-full">
            <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                    dataKey="date"
                    tickLine={false}
                    axisLine={false}
                    tickMargin={10}
                    fontSize={12}
                    tickFormatter={(value) => value.slice(5)} // Show MM-DD
                />
                <YAxis
                    tickLine={false}
                    axisLine={false}
                    fontSize={12}
                    allowDecimals={false}
                />
                <ChartTooltip content={<ChartTooltipContent />} />
                <ChartLegend content={<ChartLegendContent />} />
                <Bar dataKey="Present" fill={COLORS.Present} radius={[4, 4, 0, 0]} stackId="a" />
                <Bar dataKey="Late" fill={COLORS.Late} radius={[4, 4, 0, 0]} stackId="a" />
                <Bar dataKey="Absent" fill={COLORS.Absent} radius={[4, 4, 0, 0]} stackId="a" />
                <Bar dataKey="Leave" fill={COLORS.Leave} radius={[4, 4, 0, 0]} stackId="a" />
            </BarChart>
        </ChartContainer>
    );
};

interface StatusDistributionChartProps {
    data: any[];
}

export const StatusDistributionChart = ({ data }: StatusDistributionChartProps) => {
    // Transform flat data to pie format if needed, or assume data is passed as { name: 'Present', value: 10 }
    // If data passed is daily stats, we might need to aggregate or take the latest slice. 
    // Assuming 'data' here is the distribution object e.g. [{name: 'Present', value: 50}, ...]

    return (
        <ChartContainer config={chartConfig} className="h-[300px] w-full mx-auto">
            <PieChart>
                <Pie
                    data={data}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={2}
                    dataKey="value"
                >
                    {data.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[entry.name as keyof typeof COLORS] || '#8884d8'} />
                    ))}
                </Pie>
                <ChartTooltip content={<ChartTooltipContent />} />
                <ChartLegend content={<ChartLegendContent />} />
            </PieChart>
        </ChartContainer>
    );
};
