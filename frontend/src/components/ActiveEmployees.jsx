import React, { useState, useEffect } from 'react';
import { User, MapPin, Clock } from 'lucide-react';

function formatTime(isoString) {
  if (!isoString) return '-';
  // Parse ISO string and extract time directly to avoid timezone issues
  // Database stores local time, so we use UTC methods to read it as-is
  const date = new Date(isoString);
  const hours = date.getUTCHours().toString().padStart(2, '0');
  const minutes = date.getUTCMinutes().toString().padStart(2, '0');
  return `${hours}:${minutes}`;
}

function formatDuration(timeIn) {
  if (!timeIn) return '-';
  
  // Parse the stored time as UTC to get the raw values
  const start = new Date(timeIn);
  const now = new Date();
  
  // Calculate difference using UTC values to avoid timezone issues
  const startMs = Date.UTC(
    start.getUTCFullYear(), start.getUTCMonth(), start.getUTCDate(),
    start.getUTCHours(), start.getUTCMinutes(), start.getUTCSeconds()
  );
  const nowMs = Date.UTC(
    now.getFullYear(), now.getMonth(), now.getDate(),
    now.getHours(), now.getMinutes(), now.getSeconds()
  );
  
  const diffMs = nowMs - startMs;
  
  // Handle edge case where duration is negative or very small
  if (diffMs < 60000) {
    return 'Just now';
  }
  
  const hours = Math.floor(diffMs / (1000 * 60 * 60));
  const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
  
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
}

export default function ActiveEmployees({ employees, locations }) {
  // Force re-render every 30 seconds to update durations
  const [, setTick] = useState(0);
  
  useEffect(() => {
    const interval = setInterval(() => {
      setTick(t => t + 1);
    }, 10000); // Update every 30 seconds
    
    return () => clearInterval(interval);
  }, []);

  // Group employees by location
  const groupedByLocation = {};
  
  locations.forEach(loc => {
    groupedByLocation[loc.id] = {
      location: loc,
      employees: []
    };
  });
  
  employees.forEach(emp => {
    const locId = emp.location_id;
    if (groupedByLocation[locId]) {
      groupedByLocation[locId].employees.push(emp);
    }
  });

  if (employees.length === 0) {
    return (
      <div className="glass-card p-8">
        <div className="text-center text-slate-400">
          <User className="w-14 h-14 mx-auto mb-4 text-slate-600" />
          <p className="text-lg font-medium text-slate-300">No Active Employees</p>
          <p className="text-sm mt-1">Employees will appear here when they check in</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {Object.values(groupedByLocation).map(({ location, employees: locEmployees }) => {
        if (locEmployees.length === 0) return null;
        
        return (
          <div key={location.id} className="glass-card overflow-hidden">
            <div className="bg-gradient-to-r from-purple-600 to-pink-600 px-6 py-3">
              <div className="flex items-center gap-2 text-white">
                <MapPin className="w-5 h-5" />
                <span className="font-semibold">{location.area_name}</span>
                <span className="ml-auto bg-white/20 px-3 py-0.5 rounded-full text-sm font-medium">
                  {locEmployees.length} active
                </span>
              </div>
            </div>
            
            <div className="divide-y divide-slate-700/50">
              {locEmployees.map((emp) => (
                <div
                  key={emp.id}
                  className="px-6 py-4 flex items-center gap-4 hover:bg-slate-700/30 transition-colors"
                >
                  <div className="flex-shrink-0">
                    <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-cyan-500 to-purple-500 flex items-center justify-center shadow-lg">
                      <span className="text-white font-semibold text-lg">
                        {emp.employees?.full_name?.charAt(0) || '?'}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-white truncate">
                      {emp.employees?.full_name || 'Unknown'}
                    </p>
                    <p className="text-sm text-slate-300 truncate">
                      {emp.employees?.position || '-'} • {emp.employees?.office || '-'}
                    </p>
                  </div>
                  
                  <div className="flex-shrink-0 text-right">
                    <div className="flex items-center gap-1 text-sm text-slate-300">
                      <Clock className="w-4 h-4" />
                      <span>In at {formatTime(emp.time_in)}</span>
                    </div>
                    <p className="text-sm font-medium text-emerald-400 mt-0.5">
                      {formatDuration(emp.time_in)}
                    </p>
                  </div>
                  
                  <div className="flex-shrink-0">
                    <span className="badge badge-in">IN</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
