import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Navigation from './components/Navigation';
import StatsCards from './components/StatsCards';
import ActiveEmployees from './components/ActiveEmployees';
import RecentEvents from './components/RecentEvents';
import AttendanceTable from './components/AttendanceTable';
import EmployeeList from './components/EmployeeList';
import { useWebSocket } from './hooks/useBackend';
import { 
  getActiveAttendance, 
  getLocations, 
  getTodayStats,
  subscribeToAttendance 
} from './lib/supabase';

function Dashboard({ connected, events, activeEmployees, locations, stats }) {
  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <StatsCards 
        stats={stats} 
        activeCount={activeEmployees.length}
        locationsCount={locations.length}
      />
      
      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Active Employees */}
        <div className="lg:col-span-2 space-y-6">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Currently in Areas
            </h2>
            <ActiveEmployees employees={activeEmployees} locations={locations} />
          </div>
        </div>
        
        {/* Right Column - Recent Events */}
        <div className="space-y-6">
          <RecentEvents events={events} />
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const { 
    connected, 
    events, 
    activeEmployees: wsActiveEmployees, 
    locations: wsLocations, 
    stats: wsStats 
  } = useWebSocket();
  
  // Local state for Supabase data (fallback/initial load)
  const [activeEmployees, setActiveEmployees] = useState([]);
  const [locations, setLocations] = useState([]);
  const [stats, setStats] = useState({ total_entries: 0, active_now: 0, completed: 0 });

  // Load initial data from Supabase
  useEffect(() => {
    async function loadData() {
      try {
        const [activeData, locationsData, statsData] = await Promise.all([
          getActiveAttendance(),
          getLocations(),
          getTodayStats()
        ]);
        
        setActiveEmployees(activeData || []);
        setLocations(locationsData || []);
        setStats(statsData || { total_entries: 0, active_now: 0, completed: 0 });
      } catch (error) {
        console.error('Failed to load initial data:', error);
      }
    }
    
    loadData();
    
    // Subscribe to real-time changes
    const unsubscribe = subscribeToAttendance((payload) => {
      console.log('Attendance change:', payload);
      // Reload data on changes
      loadData();
    });
    
    return unsubscribe;
  }, []);

  // Use WebSocket data if available, otherwise use Supabase data
  const displayActiveEmployees = wsActiveEmployees.length > 0 ? wsActiveEmployees : activeEmployees;
  const displayLocations = wsLocations.length > 0 ? wsLocations : locations;
  const displayStats = wsStats.total_entries > 0 ? wsStats : stats;

  return (
    <div className="min-h-screen bg-gray-50">
      <Header connected={connected} />
      <Navigation activeTab={activeTab} onTabChange={setActiveTab} />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'dashboard' && (
          <Dashboard
            connected={connected}
            events={events}
            activeEmployees={displayActiveEmployees}
            locations={displayLocations}
            stats={displayStats}
          />
        )}
        
        {activeTab === 'attendance' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Attendance History
              </h2>
              <AttendanceTable />
            </div>
          </div>
        )}
        
        {activeTab === 'employees' && (
          <div className="space-y-6">
            <EmployeeList />
          </div>
        )}
      </main>
      
      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white mt-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-center text-sm text-gray-500">
            Time Room - RFID Attendance Tracking System • Powered by URA4 Reader
          </p>
        </div>
      </footer>
    </div>
  );
}
