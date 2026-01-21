import { useState, useEffect, useCallback, useRef } from 'react';

const WS_URL = process.env.REACT_APP_BACKEND_WS || 'ws://localhost:8765';
const API_URL = process.env.REACT_APP_BACKEND_API || 'http://localhost:8766';

export function useWebSocket() {
  const [connected, setConnected] = useState(false);
  const [events, setEvents] = useState([]);
  const [activeEmployees, setActiveEmployees] = useState([]);
  const [locations, setLocations] = useState([]);
  const [stats, setStats] = useState({ total_entries: 0, active_now: 0, completed: 0 });
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[WS] Connected');
        setConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'init') {
            setEvents(data.data.recent_events || []);
            setActiveEmployees(data.data.active_employees || []);
            setLocations(data.data.locations || []);
            setStats(data.data.stats || { total_entries: 0, active_now: 0, completed: 0 });
          } else if (data.type === 'scan_event') {
            setEvents(prev => [data.event, ...prev].slice(0, 50));
            // Refresh active employees after a scan
            sendCommand('get_active');
            sendCommand('get_stats');
          } else if (data.type === 'active_employees') {
            setActiveEmployees(data.data || []);
          } else if (data.type === 'stats') {
            setStats(data.data || { total_entries: 0, active_now: 0, completed: 0 });
          } else if (data.type === 'locations') {
            setLocations(data.data || []);
          }
        } catch (err) {
          console.error('[WS] Parse error:', err);
        }
      };

      ws.onclose = () => {
        console.log('[WS] Disconnected');
        setConnected(false);
        // Attempt to reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(connect, 3000);
      };

      ws.onerror = (error) => {
        console.error('[WS] Error:', error);
      };
    } catch (err) {
      console.error('[WS] Connection error:', err);
      reconnectTimeoutRef.current = setTimeout(connect, 3000);
    }
  }, []);

  const sendCommand = useCallback((command, params = {}) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ command, ...params }));
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  // Stable refresh functions
  const refreshActive = useCallback(() => sendCommand('get_active'), [sendCommand]);
  const refreshStats = useCallback(() => sendCommand('get_stats'), [sendCommand]);

  return {
    connected,
    events,
    activeEmployees,
    locations,
    stats,
    sendCommand,
    refreshActive,
    refreshStats,
  };
}

// Fallback HTTP API calls
export async function fetchEvents() {
  const response = await fetch(`${API_URL}/api/events`);
  const data = await response.json();
  return data.events || [];
}

export async function fetchActiveEmployees() {
  const response = await fetch(`${API_URL}/api/active`);
  const data = await response.json();
  return data.active || [];
}

export async function fetchLogs() {
  const response = await fetch(`${API_URL}/api/logs`);
  const data = await response.json();
  return data.logs || [];
}

export async function fetchStats() {
  const response = await fetch(`${API_URL}/api/stats`);
  const data = await response.json();
  return data.stats || { total_entries: 0, active_now: 0, completed: 0 };
}

export async function simulateScan(epc, antenna) {
  const response = await fetch(`${API_URL}/api/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ epc, antenna }),
  });
  return response.json();
}
