import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import StatsCards from './components/StatsCards';
import ActiveEmployees from './components/ActiveEmployees';
import RecentEvents from './components/RecentEvents';
import AttendanceTable from './components/AttendanceTable';
import EmployeeList from './components/EmployeeList';
import StatsModal from './components/StatsModal';
import { useWebSocket } from './hooks/useBackend';
import { 
  getActiveAttendance, 
  getLocations, 
  getTodayStats,
  getAttendanceLogs,
  subscribeToAttendance 
} from './lib/supabase';

function Dashboard({ connected, events, activeEmployees, locations, stats, onCardClick }) {
  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <StatsCards 
        stats={stats} 
        activeCount={activeEmployees.length}
        locationsCount={locations.length}
        onCardClick={onCardClick}
      />
      
      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Active Employees */}
        <div className="lg:col-span-2 space-y-6">
          <div>
            <h2 className="text-lg font-semibold text-white mb-4">
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
  const [modalType, setModalType] = useState(null);
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
  const [logs, setLogs] = useState([]);

  // Load initial data from Supabase
  useEffect(() => {
    async function loadData() {
      try {
        const [activeData, locationsData, statsData, logsData] = await Promise.all([
          getActiveAttendance(),
          getLocations(),
          getTodayStats(),
          getAttendanceLogs(50)
        ]);
        
        setActiveEmployees(activeData || []);
        setLocations(locationsData || []);
        setStats(statsData || { total_entries: 0, active_now: 0, completed: 0 });
        setLogs(logsData || []);
      } catch (error) {
        console.error('Failed to load initial data:', error);
      }
    }
    
    loadData();
    
    // Subscribe to real-time changes
    const unsubscribe = subscribeToAttendance(() => {
      loadData();
    });
    
    return unsubscribe;
  }, []);

  // Use WebSocket data if available, otherwise use Supabase data
  const displayActiveEmployees = wsActiveEmployees.length > 0 ? wsActiveEmployees : activeEmployees;
  const displayLocations = wsLocations.length > 0 ? wsLocations : locations;
  const displayStats = wsStats.total_entries > 0 ? wsStats : stats;

  const handleCardClick = (type) => {
    setModalType(type);
  };

  return (
    <div className="min-h-screen">
      <Header connected={connected} activeTab={activeTab} onTabChange={setActiveTab} />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'dashboard' && (
          <Dashboard
            connected={connected}
            events={events}
            activeEmployees={displayActiveEmployees}
            locations={displayLocations}
            stats={displayStats}
            onCardClick={handleCardClick}
          />
        )}
        
        {activeTab === 'attendance' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-white mb-4">
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

      {/* Stats Modal */}
      {modalType && (
        <StatsModal
          type={modalType}
          onClose={() => setModalType(null)}
          activeEmployees={displayActiveEmployees}
          locations={displayLocations}
          stats={displayStats}
          logs={logs}
        />
      )}
    </div>
  );
}
