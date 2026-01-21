import React from 'react';
import { Radio, Wifi, WifiOff, Sparkles } from 'lucide-react';

export default function Header({ connected }) {
  return (
    <header className="glass-card-dark sticky top-0 z-50 border-b border-slate-700/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Title */}
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-cyan-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg glow-purple">
              <Radio className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold gradient-text flex items-center gap-2">
                Time Room
                <Sparkles className="w-4 h-4 text-purple-400" />
              </h1>
              <p className="text-xs text-slate-400">RFID Attendance Tracking</p>
            </div>
          </div>
          
          {/* Connection Status */}
          <div className="flex items-center gap-3">
            <div className={`flex items-center gap-2 px-4 py-2 rounded-xl ${
              connected 
                ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400' 
                : 'bg-rose-500/10 border border-rose-500/30 text-rose-400'
            }`}>
              {connected ? (
                <>
                  <div className="status-dot connected" />
                  <Wifi className="w-4 h-4" />
                  <span className="text-sm font-medium">Live</span>
                </>
              ) : (
                <>
                  <div className="status-dot disconnected" />
                  <WifiOff className="w-4 h-4" />
                  <span className="text-sm font-medium">Offline</span>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
