import React from 'react';
import { User, MapPin, Clock } from 'lucide-react';

function formatTime(isoString) {
  if (!isoString) return '-';
  const date = new Date(isoString);
  return date.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit',
    hour12: false 
  });
}

function formatDuration(timeIn) {
  if (!timeIn) return '-';
  const start = new Date(timeIn);
  const now = new Date();
  const diffMs = now - start;
  const hours = Math.floor(diffMs / (1000 * 60 * 60));
  const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
  
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
}

export default function ActiveEmployees({ employees, locations }) {
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
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8">
        <div className="text-center text-gray-500">
          <User className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p className="text-lg font-medium">No Active Employees</p>
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
          <div key={location.id} className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="bg-gradient-to-r from-primary-600 to-primary-700 px-6 py-3">
              <div className="flex items-center gap-2 text-white">
                <MapPin className="w-5 h-5" />
                <span className="font-semibold">{location.area_name}</span>
                <span className="ml-auto bg-white/20 px-2 py-0.5 rounded-full text-sm">
                  {locEmployees.length} active
                </span>
              </div>
            </div>
            
            <div className="divide-y divide-gray-100">
              {locEmployees.map((emp, index) => (
                <div
                  key={emp.id}
                  className="px-6 py-4 flex items-center gap-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center">
                      <span className="text-primary-700 font-semibold">
                        {emp.employees?.full_name?.charAt(0) || '?'}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 truncate">
                      {emp.employees?.full_name || 'Unknown'}
                    </p>
                    <p className="text-sm text-gray-500 truncate">
                      {emp.employees?.position || '-'} • {emp.employees?.office || '-'}
                    </p>
                  </div>
                  
                  <div className="flex-shrink-0 text-right">
                    <div className="flex items-center gap-1 text-sm text-gray-500">
                      <Clock className="w-4 h-4" />
                      <span>In at {formatTime(emp.time_in)}</span>
                    </div>
                    <p className="text-sm font-medium text-green-600 mt-0.5">
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
