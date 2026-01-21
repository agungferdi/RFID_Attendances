import React, { useState, useEffect } from 'react';
import { Clock, ArrowUpDown } from 'lucide-react';
import { getAttendanceLogs } from '../lib/supabase';

function formatDateTime(isoString) {
  if (!isoString) return '-';
  const date = new Date(isoString);
  return date.toLocaleString('en-US', { 
    month: 'short',
    day: 'numeric',
    hour: '2-digit', 
    minute: '2-digit',
    hour12: false 
  });
}

function formatDuration(duration) {
  if (!duration) return '-';
  
  // Parse PostgreSQL interval format
  // Examples: "01:30:00", "2 hours 30 minutes", "1 day 02:00:00"
  if (typeof duration === 'string') {
    // Try to parse HH:MM:SS format
    const timeMatch = duration.match(/(\d+):(\d+):(\d+)/);
    if (timeMatch) {
      const hours = parseInt(timeMatch[1]);
      const minutes = parseInt(timeMatch[2]);
      
      if (hours > 0) {
        return `${hours}h ${minutes}m`;
      }
      return `${minutes}m`;
    }
    return duration;
  }
  
  return '-';
}

function StatusBadge({ status }) {
  if (status === 'IN') {
    return <span className="badge badge-in">Active</span>;
  }
  return <span className="badge badge-completed">Completed</span>;
}

export default function AttendanceTable() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortField, setSortField] = useState('time_in');
  const [sortDirection, setSortDirection] = useState('desc');

  useEffect(() => {
    loadLogs();
    
    // Refresh every 30 seconds
    const interval = setInterval(loadLogs, 30000);
    return () => clearInterval(interval);
  }, []);

  async function loadLogs() {
    try {
      const data = await getAttendanceLogs(100);
      setLogs(data || []);
    } catch (error) {
      console.error('Failed to load logs:', error);
    } finally {
      setLoading(false);
    }
  }

  function handleSort(field) {
    if (sortField === field) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  }

  const sortedLogs = [...logs].sort((a, b) => {
    let aVal = a[sortField];
    let bVal = b[sortField];
    
    if (sortField === 'employee') {
      aVal = a.employees?.full_name || '';
      bVal = b.employees?.full_name || '';
    } else if (sortField === 'location') {
      aVal = a.locations?.area_name || '';
      bVal = b.locations?.area_name || '';
    }
    
    if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
    return 0;
  });

  if (loading) {
    return (
      <div className="glass-card p-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
          <span className="ml-3 text-slate-400">Loading attendance logs...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-700/50 flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-white">Attendance History</h3>
          <p className="text-sm text-slate-400">{logs.length} records</p>
        </div>
        <button
          onClick={loadLogs}
          className="px-4 py-2 text-sm font-medium bg-purple-500/20 text-purple-400 hover:bg-purple-500/30 rounded-xl transition-colors"
        >
          Refresh
        </button>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-slate-800/50 border-b border-slate-700/50">
            <tr>
              <th 
                className="px-6 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider cursor-pointer hover:bg-slate-700/50"
                onClick={() => handleSort('employee')}
              >
                <div className="flex items-center gap-1">
                  Employee
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th 
                className="px-6 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider cursor-pointer hover:bg-slate-700/50"
                onClick={() => handleSort('location')}
              >
                <div className="flex items-center gap-1">
                  Area
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th 
                className="px-6 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider cursor-pointer hover:bg-slate-700/50"
                onClick={() => handleSort('time_in')}
              >
                <div className="flex items-center gap-1">
                  Time In
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th 
                className="px-6 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider cursor-pointer hover:bg-slate-700/50"
                onClick={() => handleSort('time_out')}
              >
                <div className="flex items-center gap-1">
                  Time Out
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Duration
              </th>
              <th 
                className="px-6 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider cursor-pointer hover:bg-slate-700/50"
                onClick={() => handleSort('status')}
              >
                <div className="flex items-center gap-1">
                  Status
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/50">
            {sortedLogs.length === 0 ? (
              <tr>
                <td colSpan="6" className="px-6 py-12 text-center text-slate-400">
                  <Clock className="w-8 h-8 mx-auto mb-2 text-slate-600" />
                  <p>No attendance records yet</p>
                </td>
              </tr>
            ) : (
              sortedLogs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-700/30 transition-colors">
                  <td className="px-6 py-4">
                    <div>
                      <p className="font-medium text-white">
                        {log.employees?.full_name || 'Unknown'}
                      </p>
                      <p className="text-sm text-slate-400">
                        {log.employees?.position || '-'}
                      </p>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-white">
                      {log.locations?.area_name || '-'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-slate-300">
                    {formatDateTime(log.time_in)}
                  </td>
                  <td className="px-6 py-4 text-slate-300">
                    {formatDateTime(log.time_out)}
                  </td>
                  <td className="px-6 py-4">
                    <span className="font-medium text-emerald-400">
                      {formatDuration(log.duration)}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={log.status} />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
