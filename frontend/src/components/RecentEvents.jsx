import React from 'react';
import { ArrowRightCircle, ArrowLeftCircle, AlertCircle, Zap } from 'lucide-react';

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
      return <ArrowRightCircle className="w-5 h-5 text-emerald-400" />;
    case 'OUT':
      return <ArrowLeftCircle className="w-5 h-5 text-rose-400" />;
    default:
      return <AlertCircle className="w-5 h-5 text-amber-400" />;
  }
}

function getActionBadge(action) {
  switch (action) {
    case 'IN':
      return <span className="badge badge-in">IN</span>;
    case 'OUT':
      return <span className="badge badge-out">OUT</span>;
    default:
      return <span className="badge bg-amber-500/20 text-amber-400 border border-amber-500/30">UNKNOWN</span>;
  }
}

export default function RecentEvents({ events }) {
  if (events.length === 0) {
    return (
      <div className="glass-card p-8">
        <div className="text-center text-slate-400">
          <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-slate-700/50 flex items-center justify-center">
            <Zap className="w-7 h-7 text-slate-500" />
          </div>
          <p className="text-lg font-medium text-slate-300">No Recent Events</p>
          <p className="text-sm mt-1">Scan events will appear here in real-time</p>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-700/50">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <h3 className="font-semibold text-white">Live Feed</h3>
        </div>
        <p className="text-sm text-slate-400">Real-time RFID scan events</p>
      </div>
      
      <div className="divide-y divide-slate-700/50 max-h-[500px] overflow-y-auto">
        {events.map((event, index) => (
          <div
            key={event.id || index}
            className={`px-6 py-4 flex items-center gap-4 hover:bg-slate-700/30 transition-colors ${
              index === 0 ? 'animate-highlight' : ''
            }`}
          >
            <div className="flex-shrink-0">
              {getActionIcon(event.action)}
            </div>
            
            <div className="flex-1 min-w-0">
              {event.employee ? (
                <>
                  <p className="font-medium text-white truncate">
                    {event.employee.full_name}
                  </p>
                  <p className="text-sm text-slate-400 truncate">
                    {event.location?.area_name || `Antenna ${event.antenna}`}
                  </p>
                </>
              ) : (
                <>
                  <p className="font-medium text-white truncate">
                    Unknown Card
                  </p>
                  <p className="text-sm text-slate-500 font-mono truncate">
                    {event.epc?.substring(0, 20)}...
                  </p>
                </>
              )}
            </div>
            
            <div className="flex-shrink-0 text-right">
              <p className="text-sm text-slate-400">{formatTime(event.timestamp)}</p>
              <div className="mt-1">{getActionBadge(event.action)}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
