import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { employeeApi } from '../../services/api';
import { FileText, DollarSign, Calendar, Clock, AlertCircle } from 'lucide-react';

export const PayslipScreen: React.FC = () => {
    const { data: payslips, isLoading, error } = useQuery({
        queryKey: ['my-payslips'],
        queryFn: employeeApi.getPayslips
    });

    if (isLoading) return <div className="p-8 text-center">Loading payslips...</div>;
    if (error) return <div className="p-8 text-center text-red-500">Failed to load payslips</div>;

    return (
        <div className="space-y-6">
            <header className="flex justify-between items-center">
                <h2 className="text-2xl font-bold flex items-center gap-2">
                    <DollarSign className="w-6 h-6 text-green-500" />
                    My Payslips
                </h2>
            </header>

            {!payslips || payslips.length === 0 ? (
                <div className="text-center p-8 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <p className="text-gray-500">No payslips available yet.</p>
                </div>
            ) : (
                <div className="grid gap-4">
                    {payslips.map((slip: any) => (
                        <div key={slip.id} className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow border border-gray-100 dark:border-gray-700">
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <h3 className="font-semibold text-lg">Payslip #{slip.id}</h3>
                                    <p className="text-sm text-gray-500">Run ID: {slip.run_id}</p>
                                </div>
                                <div className="text-right">
                                    <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                                        ${slip.net_pay.toFixed(2)}
                                    </p>
                                    <p className="text-xs text-gray-400">Net Pay</p>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm bg-gray-50 dark:bg-gray-900/50 p-3 rounded">
                                <div>
                                    <p className="text-gray-500">Total Hours</p>
                                    <p className="font-medium">{slip.total_hours}h</p>
                                </div>
                                <div>
                                    <p className="text-gray-500">Overtime</p>
                                    <p className="font-medium text-blue-500">{slip.ot_hours}h</p>
                                </div>
                                <div>
                                    <p className="text-gray-500">Gross Pay</p>
                                    <p className="font-medium">${slip.gross_pay.toFixed(2)}</p>
                                </div>
                                <div>
                                    <p className="text-gray-500">Deductions</p>
                                    <p className="font-medium text-red-500">-${slip.total_deductions.toFixed(2)}</p>
                                </div>
                            </div>

                            {slip.late_days > 0 && (
                                <div className="mt-3 flex items-center gap-2 text-xs text-red-500 bg-red-50 dark:bg-red-900/20 p-2 rounded w-fit">
                                    <AlertCircle className="w-3 h-3" />
                                    <span>Includes deductions for {slip.late_days} late days</span>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};
