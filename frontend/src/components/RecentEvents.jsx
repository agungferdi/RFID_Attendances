import React from 'react';
import { ArrowRightCircle, ArrowLeftCircle, AlertCircle } from 'lucide-react';

function formatTime(isoString) {
  if (!isoString) return '-';
  const date = new Date(isoString);
  return date.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit',
    second: '2-digit',
    hour12: false 
  });
}

function getActionIcon(action) {
  switch (action) {
    case 'IN':
      return <ArrowRightCircle className="w-5 h-5 text-green-500" />;
    case 'OUT':
      return <ArrowLeftCircle className="w-5 h-5 text-red-500" />;
    default:
      return <AlertCircle className="w-5 h-5 text-yellow-500" />;
  }
}

function getActionBadge(action) {
  switch (action) {
    case 'IN':
      return <span className="badge badge-in">IN</span>;
    case 'OUT':
      return <span className="badge badge-out">OUT</span>;
    default:
      return <span className="badge bg-yellow-100 text-yellow-800">UNKNOWN</span>;
  }
}

export default function RecentEvents({ events }) {
  if (events.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8">
        <div className="text-center text-gray-500">
          <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-gray-100 flex items-center justify-center">
            <ArrowRightCircle className="w-6 h-6 text-gray-400" />
          </div>
          <p className="text-lg font-medium">No Recent Events</p>
          <p className="text-sm mt-1">Scan events will appear here in real-time</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
        <h3 className="font-semibold text-gray-900">Recent Scans</h3>
        <p className="text-sm text-gray-500">Real-time RFID scan events</p>
      </div>
      
      <div className="divide-y divide-gray-100 max-h-[500px] overflow-y-auto">
        {events.map((event, index) => (
          <div
            key={event.id || index}
            className={`px-6 py-4 flex items-center gap-4 hover:bg-gray-50 transition-colors ${
              index === 0 ? 'animate-highlight' : ''
            }`}
          >
            <div className="flex-shrink-0">
              {getActionIcon(event.action)}
            </div>
            
            <div className="flex-1 min-w-0">
              {event.employee ? (
                <>
                  <p className="font-medium text-gray-900 truncate">
                    {event.employee.full_name}
                  </p>
                  <p className="text-sm text-gray-500 truncate">
                    {event.location?.area_name || `Antenna ${event.antenna}`}
                  </p>
                </>
              ) : (
                <>
                  <p className="font-medium text-gray-900 truncate">
                    Unknown Card
                  </p>
                  <p className="text-sm text-gray-500 font-mono truncate">
                    {event.epc?.substring(0, 24)}...
                  </p>
                </>
              )}
            </div>
            
            <div className="flex-shrink-0 text-right">
              <p className="text-sm text-gray-500">{formatTime(event.timestamp)}</p>
              <div className="mt-1">{getActionBadge(event.action)}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
