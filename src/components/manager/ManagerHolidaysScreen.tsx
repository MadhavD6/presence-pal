import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { holidaysApi } from '../../services/api'; // Ensure exported
import { Plus, Trash2, Calendar, AlertTriangle } from 'lucide-react';
import { format, isBefore, startOfToday } from 'date-fns';

export const ManagerHolidaysScreen: React.FC = () => {
    const queryClient = useQueryClient();
    const [isAdding, setIsAdding] = useState(false);

    // Form State
    const [dateVal, setDateVal] = useState('');
    const [nameVal, setNameVal] = useState('');
    const [isNational, setIsNational] = useState(true);

    const { data: holidays, isLoading } = useQuery({
        queryKey: ['holidays'],
        queryFn: holidaysApi.getHolidays
    });

    const createMutation = useMutation({
        mutationFn: holidaysApi.createHoliday,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['holidays'] });
            setIsAdding(false);
            setDateVal('');
            setNameVal('');
            alert("Holiday created!");
        },
        onError: (err: any) => alert("Failed: " + err.message)
    });

    const deleteMutation = useMutation({
        mutationFn: holidaysApi.deleteHoliday,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['holidays'] });
            alert("Holiday deleted.");
        },
        onError: (err: any) => alert("Failed delete: " + err.message)
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!dateVal || !nameVal) return;
        createMutation.mutate({ date: dateVal, name: nameVal, is_national: isNational });
    };

    const isPastDate = dateVal ? isBefore(new Date(dateVal), startOfToday()) : false;

    return (
        <div className="space-y-6">
            <header className="flex justify-between items-center">
                <h2 className="text-2xl font-bold flex items-center gap-2">
                    <Calendar className="w-6 h-6 text-primary" />
                    Holiday Management
                </h2>
                <button
                    onClick={() => setIsAdding(!isAdding)}
                    className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
                >
                    <Plus className="w-4 h-4" />
                    {isAdding ? 'Cancel' : 'Add Holiday'}
                </button>
            </header>

            {isAdding && (
                <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700 animate-in fade-in slide-in-from-top-2">
                    <form onSubmit={handleSubmit} className="flex flex-col gap-4 max-w-md">
                        <div>
                            <label className="block text-sm font-medium mb-1">Date</label>
                            <input
                                type="date"
                                className="w-full p-2 rounded border border-gray-300 dark:border-gray-600 bg-background"
                                value={dateVal}
                                onChange={e => setDateVal(e.target.value)}
                                required
                            />
                            {isPastDate && (
                                <p className="text-xs text-yellow-600 flex items-center gap-1 mt-1">
                                    <AlertTriangle className="w-3 h-3" />
                                    Warning: Past date. Aggregation will be re-run retroactively.
                                </p>
                            )}
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-1">Holiday Name</label>
                            <input
                                type="text"
                                className="w-full p-2 rounded border border-gray-300 dark:border-gray-600 bg-background"
                                placeholder="e.g. Republic Day"
                                value={nameVal}
                                onChange={e => setNameVal(e.target.value)}
                                required
                            />
                        </div>
                        <div className="flex items-center gap-2">
                            <input
                                type="checkbox"
                                id="isNational"
                                checked={isNational}
                                onChange={e => setIsNational(e.target.checked)}
                                className="w-4 h-4 rounded border-gray-300"
                            />
                            <label htmlFor="isNational" className="text-sm">Is National Holiday?</label>
                        </div>
                        <button
                            type="submit"
                            disabled={createMutation.isPending}
                            className="bg-green-600 text-white py-2 rounded hover:bg-green-700 disabled:opacity-50"
                        >
                            {createMutation.isPending ? 'Saving...' : 'Save Holiday'}
                        </button>
                    </form>
                </div>
            )}

            {isLoading ? (
                <div className="p-8 text-center text-gray-500">Loading holidays...</div>
            ) : (
                <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-100 dark:border-gray-700 overflow-hidden">
                    <table className="w-full text-sm text-left">
                        <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-100 dark:border-gray-700">
                            <tr>
                                <th className="px-4 py-3 font-medium">Date</th>
                                <th className="px-4 py-3 font-medium">Name</th>
                                <th className="px-4 py-3 font-medium">Type</th>
                                <th className="px-4 py-3 font-medium text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                            {!holidays || holidays.length === 0 ? (
                                <tr>
                                    <td colSpan={4} className="p-8 text-center text-gray-500">No holidays found.</td>
                                </tr>
                            ) : (
                                holidays.map((h: any) => (
                                    <tr key={h.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                                        <td className="px-4 py-3 font-medium whitespace-nowrap">
                                            {format(new Date(h.date), 'MMM d, yyyy (EEE)')}
                                        </td>
                                        <td className="px-4 py-3">{h.name}</td>
                                        <td className="px-4 py-3">
                                            {h.is_national ? (
                                                <span className="bg-blue-100 text-blue-800 text-xs px-2 py-0.5 rounded-full">National</span>
                                            ) : (
                                                <span className="bg-gray-100 text-gray-800 text-xs px-2 py-0.5 rounded-full">Optional</span>
                                            )}
                                        </td>
                                        <td className="px-4 py-3 text-right">
                                            <button
                                                onClick={() => {
                                                    if (confirm(`Delete ${h.name}?`)) deleteMutation.mutate(h.id);
                                                }}
                                                className="text-red-500 hover:bg-red-50 p-1 rounded"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};
