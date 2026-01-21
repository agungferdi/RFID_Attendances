"""
Supabase Database Client for Time Room Attendance System

Handles all database operations:
- Employee lookup by EPC code
- Location lookup by antenna port
- Attendance log creation and updates
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from supabase import create_client, Client

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')

# Initialize Supabase client
supabase: Optional[Client] = None

def init_supabase() -> bool:
    """Initialize Supabase client"""
    global supabase
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[Supabase] ERROR: Missing SUPABASE_URL or SUPABASE_KEY in environment")
        return False
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(f"[Supabase] Connected to: {SUPABASE_URL}")
        return True
    except Exception as e:
        print(f"[Supabase] Connection error: {e}")
        return False


def get_employee_by_epc(epc_code: str) -> Optional[Dict[str, Any]]:
    """
    Look up employee by their RFID EPC code
    
    Returns employee data including:
    - id, full_name, office, position, address
    """
    if not supabase:
        print("[Supabase] Client not initialized")
        return None
    
    try:
        # Normalize EPC code (uppercase, strip whitespace)
        epc_code = epc_code.upper().strip()
        
        response = supabase.table('employees').select('*').eq('epc_code', epc_code).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"[Supabase] Error fetching employee: {e}")
        return None


def get_location_by_antenna(antenna_port: int) -> Optional[Dict[str, Any]]:
    """
    Look up location/area by antenna port number
    
    Returns location data including:
    - id, antenna_port, area_name
    """
    if not supabase:
        return None
    
    try:
        response = supabase.table('locations').select('*').eq('antenna_port', antenna_port).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"[Supabase] Error fetching location: {e}")
        return None


def get_all_locations() -> List[Dict[str, Any]]:
    """Get all configured locations/areas"""
    if not supabase:
        return []
    
    try:
        response = supabase.table('locations').select('*').order('antenna_port').execute()
        return response.data or []
    except Exception as e:
        print(f"[Supabase] Error fetching locations: {e}")
        return []


def get_active_attendance(employee_id: str, location_id: int) -> Optional[Dict[str, Any]]:
    """
    Check if employee has an active (IN) attendance record for a location
    
    Returns the active attendance log if exists
    """
    if not supabase:
        return None
    
    try:
        response = supabase.table('attendance_logs')\
            .select('*')\
            .eq('employee_id', employee_id)\
            .eq('location_id', location_id)\
            .eq('status', 'IN')\
            .execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"[Supabase] Error checking active attendance: {e}")
        return None


def create_attendance_in(employee_id: str, location_id: int) -> Optional[Dict[str, Any]]:
    """
    Create a new attendance record when employee enters an area
    
    Sets status to 'IN' and records time_in
    """
    if not supabase:
        return None
    
    try:
        data = {
            'employee_id': employee_id,
            'location_id': location_id,
            'time_in': datetime.now().isoformat(),
            'status': 'IN'
        }
        
        response = supabase.table('attendance_logs').insert(data).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"[Supabase] Error creating attendance: {e}")
        return None


def complete_attendance(attendance_id: str) -> Optional[Dict[str, Any]]:
    """
    Complete an attendance record when employee exits an area
    
    Sets status to 'COMPLETED' and records time_out
    Duration is automatically calculated by the database
    """
    if not supabase:
        return None
    
    try:
        data = {
            'time_out': datetime.now().isoformat(),
            'status': 'COMPLETED'
        }
        
        response = supabase.table('attendance_logs')\
            .update(data)\
            .eq('id', attendance_id)\
            .execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"[Supabase] Error completing attendance: {e}")
        return None


def get_attendance_logs(limit: int = 100, employee_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get recent attendance logs with employee and location details
    
    Optionally filter by employee_id
    """
    if not supabase:
        return []
    
    try:
        query = supabase.table('attendance_logs')\
            .select('*, employees(full_name, office, position), locations(area_name)')\
            .order('time_in', desc=True)\
            .limit(limit)
        
        if employee_id:
            query = query.eq('employee_id', employee_id)
        
        response = query.execute()
        return response.data or []
    except Exception as e:
        print(f"[Supabase] Error fetching attendance logs: {e}")
        return []


def get_active_employees_in_area(location_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get all employees currently IN an area
    
    Optionally filter by location_id
    """
    if not supabase:
        return []
    
    try:
        query = supabase.table('attendance_logs')\
            .select('*, employees(full_name, office, position, epc_code), locations(area_name)')\
            .eq('status', 'IN')\
            .order('time_in', desc=True)
        
        if location_id:
            query = query.eq('location_id', location_id)
        
        response = query.execute()
        return response.data or []
    except Exception as e:
        print(f"[Supabase] Error fetching active employees: {e}")
        return []


def get_all_employees() -> List[Dict[str, Any]]:
    """Get all registered employees"""
    if not supabase:
        return []
    
    try:
        response = supabase.table('employees').select('*').order('full_name').execute()
        return response.data or []
    except Exception as e:
        print(f"[Supabase] Error fetching employees: {e}")
        return []


def get_today_attendance_stats() -> Dict[str, Any]:
    """Get attendance statistics for today"""
    if not supabase:
        return {'total_entries': 0, 'active_now': 0, 'completed': 0}
    
    try:
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        
        # Get all today's entries
        response = supabase.table('attendance_logs')\
            .select('status')\
            .gte('time_in', today_start)\
            .execute()
        
        logs = response.data or []
        total = len(logs)
        active = sum(1 for log in logs if log['status'] == 'IN')
        completed = sum(1 for log in logs if log['status'] == 'COMPLETED')
        
        return {
            'total_entries': total,
            'active_now': active,
            'completed': completed
        }
    except Exception as e:
        print(f"[Supabase] Error fetching stats: {e}")
        return {'total_entries': 0, 'active_now': 0, 'completed': 0}


def process_tag_scan(epc_code: str, antenna_port: int) -> Dict[str, Any]:
    """
    Main function to process an RFID tag scan
    
    Logic:
    1. Look up employee by EPC code
    2. Look up location by antenna port
    3. Check if employee has active attendance at this location
       - If YES: Complete the attendance (OUT)
       - If NO: Create new attendance (IN)
    
    Returns result with action taken and employee/location info
    """
    result = {
        'success': False,
        'action': None,  # 'IN' or 'OUT'
        'employee': None,
        'location': None,
        'attendance': None,
        'message': ''
    }
    
    # Look up employee
    employee = get_employee_by_epc(epc_code)
    if not employee:
        result['message'] = f'Unknown EPC: {epc_code}'
        return result
    
    result['employee'] = employee
    
    # Look up location
    location = get_location_by_antenna(antenna_port)
    if not location:
        result['message'] = f'Unknown antenna port: {antenna_port}'
        return result
    
    result['location'] = location
    
    # Check for active attendance at this location
    active_attendance = get_active_attendance(employee['id'], location['id'])
    
    if active_attendance:
        # Employee is leaving - complete the attendance
        completed = complete_attendance(active_attendance['id'])
        if completed:
            result['success'] = True
            result['action'] = 'OUT'
            result['attendance'] = completed
            result['message'] = f"{employee['full_name']} checked OUT from {location['area_name']}"
        else:
            result['message'] = 'Failed to complete attendance record'
    else:
        # Employee is entering - create new attendance
        new_attendance = create_attendance_in(employee['id'], location['id'])
        if new_attendance:
            result['success'] = True
            result['action'] = 'IN'
            result['attendance'] = new_attendance
            result['message'] = f"{employee['full_name']} checked IN to {location['area_name']}"
        else:
            result['message'] = 'Failed to create attendance record'
    
    return result
