import React from 'react';
import { 
  Users, 
  MapPin, 
  CheckCircle2, 
  TrendingUp 
} from 'lucide-react';

export default function StatsCards({ stats, activeCount, locationsCount, onCardClick }) {
  const cards = [
    {
      id: 'active',
      title: 'Active Now',
      value: stats.active_now || activeCount || 0,
      icon: Users,
      gradient: 'from-emerald-500 to-teal-500',
      glow: 'glow-cyan',
    },
    {
      id: 'entries',
      title: "Today's Entries",
      value: stats.total_entries || 0,
      icon: TrendingUp,
      gradient: 'from-cyan-500 to-blue-500',
      glow: 'glow-cyan',
    },
    {
      id: 'completed',
      title: 'Completed',
      value: stats.completed || 0,
      icon: CheckCircle2,
      gradient: 'from-purple-500 to-pink-500',
      glow: 'glow-purple',
    },
    {
      id: 'areas',
      title: 'Areas',
      value: locationsCount || 0,
      icon: MapPin,
      gradient: 'from-orange-500 to-red-500',
      glow: 'glow-pink',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <button
            key={card.id}
            onClick={() => onCardClick && onCardClick(card.id)}
            className={`glass-card p-6 text-left hover:scale-105 transition-all duration-300 cursor-pointer group ${card.glow}`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-400">{card.title}</p>
                <p className="text-4xl font-bold text-white mt-1">{card.value}</p>
              </div>
              <div className={`p-3 rounded-xl bg-gradient-to-br ${card.gradient} shadow-lg group-hover:scale-110 transition-transform`}>
                <Icon className="w-6 h-6 text-white" />
              </div>
            </div>
            <div className="mt-3 text-xs text-slate-300">Click to view details →</div>
          </button>
        );
      })}
    </div>
  );
}
