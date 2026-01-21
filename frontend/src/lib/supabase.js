import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
const supabaseKey = process.env.REACT_APP_SUPABASE_PUBLISHABLE_DEFAULT_KEY;

export const supabase = createClient(supabaseUrl, supabaseKey);

// Employee functions
export async function getEmployees() {
  const { data, error } = await supabase
    .from('employees')
    .select('*')
    .order('full_name');
  
  if (error) throw error;
  return data;
}

export async function getEmployeeByEpc(epcCode) {
  const { data, error } = await supabase
    .from('employees')
    .select('*')
    .eq('epc_code', epcCode.toUpperCase())
    .single();
  
  if (error && error.code !== 'PGRST116') throw error;
  return data;
}

// Location functions
export async function getLocations() {
  const { data, error } = await supabase
    .from('locations')
    .select('*')
    .order('antenna_port');
  
  if (error) throw error;
  return data;
}

// Attendance functions
export async function getActiveAttendance() {
  const { data, error } = await supabase
    .from('attendance_logs')
    .select(`
      *,
      employees (id, full_name, office, position, epc_code),
      locations (id, area_name, antenna_port)
    `)
    .eq('status', 'IN')
    .order('time_in', { ascending: false });
  
  if (error) throw error;
  return data;
}

export async function getAttendanceLogs(limit = 100) {
  const { data, error } = await supabase
    .from('attendance_logs')
    .select(`
      *,
      employees (id, full_name, office, position),
      locations (id, area_name, antenna_port)
    `)
    .order('time_in', { ascending: false })
    .limit(limit);
  
  if (error) throw error;
  return data;
}

export async function getTodayStats() {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const { data, error } = await supabase
    .from('attendance_logs')
    .select('status')
    .gte('time_in', today.toISOString());
  
  if (error) throw error;
  
  const total = data.length;
  const active = data.filter(log => log.status === 'IN').length;
  const completed = data.filter(log => log.status === 'COMPLETED').length;
  
  return { total_entries: total, active_now: active, completed };
}

// Subscribe to real-time changes
export function subscribeToAttendance(callback) {
  const subscription = supabase
    .channel('attendance_changes')
    .on(
      'postgres_changes',
      {
        event: '*',
        schema: 'public',
        table: 'attendance_logs'
      },
      (payload) => {
        callback(payload);
      }
    )
    .subscribe();
  
  return () => {
    supabase.removeChannel(subscription);
  };
}
