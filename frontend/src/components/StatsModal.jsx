import React from 'react';
import { X, Users, TrendingUp, CheckCircle2, MapPin, Clock } from 'lucide-react';

function formatTime(isoString) {
  if (!isoString) return '-';
  const date = new Date(isoString);
  return date.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit',
    hour12: false 
  });
}

export default function StatsModal({ type, onClose, activeEmployees, locations, stats, logs }) {
  const titles = {
    active: 'Active Employees',
    entries: "Today's Entries",
    completed: 'Completed Sessions',
    areas: 'Monitored Areas'
  };

  const icons = {
    active: Users,
    entries: TrendingUp,
    completed: CheckCircle2,
    areas: MapPin
  };

  const gradients = {
    active: 'from-emerald-500 to-teal-500',
    entries: 'from-cyan-500 to-blue-500',
    completed: 'from-purple-500 to-pink-500',
    areas: 'from-orange-500 to-red-500'
  };

  const Icon = icons[type];

  const renderContent = () => {
    switch (type) {
      case 'active':
        return (
          <div className="divide-y divide-slate-700/50">
            {activeEmployees.length === 0 ? (
              <div className="text-center py-8 text-slate-400">
                No active employees at the moment
              </div>
            ) : (
              activeEmployees.map((emp) => (
                <div key={emp.id} className="px-6 py-4 flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-purple-500 flex items-center justify-center">
                    <span className="text-white font-semibold">
                      {emp.employees?.full_name?.charAt(0) || '?'}
                    </span>
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-white">{emp.employees?.full_name}</p>
                    <p className="text-sm text-slate-400">{emp.locations?.area_name}</p>
                  </div>
                  <div className="text-right">
                    <span className="badge badge-in">IN</span>
                    <p className="text-xs text-slate-400 mt-1">{formatTime(emp.time_in)}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        );

      case 'entries':
        return (
          <div className="p-6">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="glass-card-dark p-4">
                <p className="text-3xl font-bold text-white">{stats.total_entries}</p>
                <p className="text-sm text-slate-400">Total</p>
              </div>
              <div className="glass-card-dark p-4">
                <p className="text-3xl font-bold text-emerald-400">{stats.active_now}</p>
                <p className="text-sm text-slate-400">Active</p>
              </div>
              <div className="glass-card-dark p-4">
                <p className="text-3xl font-bold text-blue-400">{stats.completed}</p>
                <p className="text-sm text-slate-400">Completed</p>
              </div>
            </div>
          </div>
        );

      case 'completed':
        return (
          <div className="divide-y divide-slate-700/50 max-h-80 overflow-y-auto">
            {logs.filter(l => l.status === 'COMPLETED').slice(0, 10).map((log) => (
              <div key={log.id} className="px-6 py-4 flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                  <span className="text-white font-semibold">
                    {log.employees?.full_name?.charAt(0) || '?'}
                  </span>
                </div>
                <div className="flex-1">
                  <p className="font-medium text-white">{log.employees?.full_name}</p>
                  <p className="text-sm text-slate-400">{log.locations?.area_name}</p>
                </div>
                <div className="text-right">
                  <span className="badge badge-completed">DONE</span>
                  <p className="text-xs text-slate-400 mt-1">{log.duration || '-'}</p>
                </div>
              </div>
            ))}
            {logs.filter(l => l.status === 'COMPLETED').length === 0 && (
              <div className="text-center py-8 text-slate-400">
                No completed sessions today
              </div>
            )}
          </div>
        );

      case 'areas':
        return (
          <div className="grid grid-cols-2 gap-4 p-6">
            {locations.map((loc) => (
              <div key={loc.id} className="glass-card-dark p-4 flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center">
                  <span className="text-white font-bold">{loc.antenna_port}</span>
                </div>
                <div>
                  <p className="font-medium text-white">{loc.area_name}</p>
                  <p className="text-xs text-slate-400">Antenna {loc.antenna_port}</p>
                </div>
              </div>
            ))}
            {locations.length === 0 && (
              <div className="col-span-2 text-center py-8 text-slate-400">
                No areas configured
              </div>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className={`bg-gradient-to-r ${gradients[type]} px-6 py-4 flex items-center justify-between`}>
          <div className="flex items-center gap-3">
            <Icon className="w-6 h-6 text-white" />
            <h2 className="text-xl font-bold text-white">{titles[type]}</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/20 rounded-xl transition-colors"
          >
            <X className="w-5 h-5 text-white" />
          </button>
        </div>

        {/* Content */}
        {renderContent()}
      </div>
    </div>
  );
}
