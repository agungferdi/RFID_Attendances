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
        return False
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        return True
    except Exception:
        return False


def get_employee_by_epc(epc_code: str) -> Optional[Dict[str, Any]]:
    """
    Look up employee by their RFID EPC code
    
    Returns employee data including:
    - id, full_name, office, position, address
    """
    if not supabase:
        return None
    
    try:
        epc_code = epc_code.upper().strip()
        response = supabase.table('employees').select('*').eq('epc_code', epc_code).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception:
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
    except Exception:
        return None


def get_all_locations() -> List[Dict[str, Any]]:
    """Get all configured locations/areas"""
    if not supabase:
        return []
    
    try:
        response = supabase.table('locations').select('*').order('antenna_port').execute()
        return response.data or []
    except Exception:
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
    except Exception:
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
    except Exception:
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
    except Exception:
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
    except Exception:
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
    except Exception:
        return []


def get_all_employees() -> List[Dict[str, Any]]:
    """Get all registered employees"""
    if not supabase:
        return []
    
    try:
        response = supabase.table('employees').select('*').order('full_name').execute()
        return response.data or []
    except Exception:
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
    except Exception:
        return {'total_entries': 0, 'active_now': 0, 'completed': 0}


def process_tag_scan(epc_code: str, antenna_port: int) -> Dict[str, Any]:
    """
    Main function to process an RFID tag scan
    
    Logic:
    1. Look up employee by EPC code
    2. Look up location by antenna port
    3. Check if employee has active attendance at this location
       - If YES and more than 10 seconds since IN: Complete the attendance (OUT)
       - If YES but within 10 seconds: Ignore (prevent accidental OUT)
       - If NO: Create new attendance (IN)
    
    Returns result with action taken and employee/location info
    """
    # Minimum seconds before allowing OUT after IN
    MIN_SECONDS_BEFORE_OUT = 10
    
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
        # Check if enough time has passed since check-in
        time_in_str = active_attendance.get('time_in')
        if time_in_str:
            try:
                # Parse the time_in from database
                # Remove timezone suffix for naive datetime comparison
                time_in_clean = time_in_str
                for suffix in ['+00:00', 'Z', '+00']:
                    time_in_clean = time_in_clean.replace(suffix, '')
                # Also remove any microseconds timezone like +07:00
                if '+' in time_in_clean:
                    time_in_clean = time_in_clean.split('+')[0]
                
                time_in = datetime.fromisoformat(time_in_clean)
                now = datetime.now()
                
                seconds_since_in = (now - time_in).total_seconds()
                print(f"[DEBUG] time_in: {time_in}, now: {now}, seconds_since_in: {seconds_since_in}")
                
                if seconds_since_in < MIN_SECONDS_BEFORE_OUT:
                    # Too soon - ignore this scan to prevent accidental OUT
                    result['message'] = f'Ignored: {employee["full_name"]} checked in {seconds_since_in:.0f}s ago (min {MIN_SECONDS_BEFORE_OUT}s)'
                    return result
            except Exception as e:
                # If we can't parse the time, allow the OUT
                print(f"[DEBUG] Time parsing error: {e}, time_in_str: {time_in_str}")
                pass
                pass
        
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


def create_employee(epc_code: str, full_name: str, office: str = None, 
                   position: str = None, address: str = None) -> Dict[str, Any]:
    """
    Create a new employee in the database

    Args:
        epc_code: RFID card EPC code (must be unique)
        full_name: Employee's full name (required)
        office: Office location (optional)
        position: Job position (optional)
        address: Home address (optional)

    Returns:
        Dictionary with success status and employee data
    """
    if not supabase:
        return {'success': False, 'error': 'Supabase not initialized'}

    try:
        # Normalize EPC code to uppercase
        epc_code_upper = epc_code.upper().strip()
    
        # Check if EPC already exists
        existing = get_employee_by_epc(epc_code_upper)
        if existing:
            return {
                'success': False,
                'error': f'EPC code already registered to {existing["full_name"]}'
            }
    
        # Insert new employee
        response = supabase.table('employees').insert({
            'epc_code': epc_code_upper,
            'full_name': full_name.strip(),
            'office': office.strip() if office else None,
            'position': position.strip() if position else None,
            'address': address.strip() if address else None
        }).execute()
    
        if response.data and len(response.data) > 0:
            return {
                'success': True,
                'employee': response.data[0]
            }
        else:
            return {'success': False, 'error': 'Failed to create employee'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}
