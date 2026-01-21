"""
Time Room - RFID Attendance Tracking Server

This server monitors the URA4 RFID reader and tracks employee attendance
across different areas based on antenna ports.

Features:
- Real-time RFID tag monitoring via URA4 HTTP API
- Automatic IN/OUT detection based on antenna port
- Employee lookup and attendance tracking via Supabase
- WebSocket for real-time frontend updates
- REST API for data access

Antenna Logic:
- Each antenna port is mapped to a specific area (Production, Warehouse, etc.)
- When a tag is scanned, the system checks if the employee is already IN that area
- If IN: Mark as OUT and calculate duration
- If not IN: Mark as IN and start tracking
"""

import asyncio
import json
import threading
import urllib.request
import urllib.parse
import http.cookiejar
import os
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Set, Dict, Any, Optional
import time

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Note: python-dotenv not installed. Using environment variables directly.")

# Import Supabase client
import supabase_client as db

# Try to import websockets
try:
    import websockets
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    print("Warning: websockets module not installed. Run: pip install websockets")

# URA4 Reader Configuration
URA4_IP = os.getenv('URA4_IP', '192.168.1.100')
URA4_HTTP_PORT = int(os.getenv('URA4_HTTP_PORT', '8080'))

# Server Configuration
WEBSOCKET_PORT = int(os.getenv('WEBSOCKET_PORT', '8765'))
HTTP_API_PORT = int(os.getenv('HTTP_API_PORT', '8766'))

# Global state
connected_clients: Set = set()
monitor_thread = None
is_running = True

# Track processed tags to avoid duplicate processing
# Key: EPC + antenna, Value: last processed timestamp
processed_tags: Dict[str, float] = {}
DEBOUNCE_SECONDS = 5  # Ignore same tag on same antenna for 5 seconds


class RecentEvents:
    """Store recent scan events for display"""
    
    def __init__(self, max_size: int = 50):
        self.events = []
        self.max_size = max_size
        self.lock = threading.Lock()
    
    def add(self, event: Dict[str, Any]):
        with self.lock:
            self.events.insert(0, event)
            if len(self.events) > self.max_size:
                self.events = self.events[:self.max_size]
    
    def get_all(self) -> list:
        with self.lock:
            return self.events.copy()
    
    def clear(self):
        with self.lock:
            self.events.clear()


# Global events storage
recent_events = RecentEvents()


class URA4Monitor:
    """Monitors URA4 reader for tag data via HTTP API polling"""
    
    def __init__(self, ip: str, port: int):
        self.base_url = f"http://{ip}:{port}"
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )
    
    def get_tags(self) -> list:
        """Fetch current tags from the reader via HTTP API"""
        url = f"{self.base_url}/InventoryController/tagReporting"
        try:
            request = urllib.request.Request(
                url,
                data=b'',
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            response = self.opener.open(request, timeout=1)
            result = response.read().decode('utf-8')
            
            if result:
                data = json.loads(result)
                if isinstance(data, dict) and 'data' in data:
                    tags = data['data']
                    normalized = []
                    for tag in tags:
                        epc = tag.get('epcHex', '')
                        tid = tag.get('tidHex', tag.get('tid', ''))
                        if epc:
                            normalized.append({
                                'epc': epc.upper().strip(),
                                'tid': tid.upper().strip() if tid else '',
                                'antenna': int(tag.get('antennaPort', 1)),
                                'rssi': float(tag.get('rssi', -60)),
                                'count': int(tag.get('readCount', tag.get('count', 1)))
                            })
                    return normalized
            return []
        except urllib.error.URLError:
            return []
        except Exception as e:
            return []


# Global monitor
ura4_monitor = URA4Monitor(URA4_IP, URA4_HTTP_PORT)


def should_process_tag(epc: str, antenna: int) -> bool:
    """Check if tag should be processed (debounce logic)"""
    global processed_tags
    
    key = f"{epc}_{antenna}"
    current_time = time.time()
    
    if key in processed_tags:
        last_time = processed_tags[key]
        if current_time - last_time < DEBOUNCE_SECONDS:
            return False
    
    processed_tags[key] = current_time
    return True


def process_tag(epc: str, antenna: int) -> Optional[Dict[str, Any]]:
    """Process a single tag scan and return the result"""
    
    # Debounce check
    if not should_process_tag(epc, antenna):
        return None
    
    print(f"\n>>> Processing tag: {epc} on Antenna {antenna}")
    
    # Process the scan through Supabase
    result = db.process_tag_scan(epc, antenna)
    
    if result['success']:
        action = result['action']
        employee = result['employee']
        location = result['location']
        
        print(f">>> {action}: {employee['full_name']} @ {location['area_name']}")
        
        # Create event for frontend
        event = {
            'id': str(time.time()),
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'epc': epc,
            'antenna': antenna,
            'employee': {
                'id': employee['id'],
                'full_name': employee['full_name'],
                'office': employee.get('office', ''),
                'position': employee.get('position', '')
            },
            'location': {
                'id': location['id'],
                'area_name': location['area_name']
            },
            'message': result['message']
        }
        
        recent_events.add(event)
        return event
    else:
        print(f">>> Failed: {result['message']}")
        
        # Still create an event for unknown/failed scans
        event = {
            'id': str(time.time()),
            'timestamp': datetime.now().isoformat(),
            'action': 'UNKNOWN',
            'epc': epc,
            'antenna': antenna,
            'employee': None,
            'location': None,
            'message': result['message']
        }
        
        recent_events.add(event)
        return event


def monitor_thread_func():
    """Background thread that continuously polls URA4 for tag data"""
    global is_running
    
    print("\n>>> Tag monitoring started")
    print(f">>> Polling URA4 at {URA4_IP}:{URA4_HTTP_PORT}")
    print(">>> Start inventory from URA4 web interface to begin scanning")
    print()
    
    empty_polls = 0
    
    while is_running:
        try:
            # Poll for tag data
            tags = ura4_monitor.get_tags()
            
            if tags:
                empty_polls = 0
                for tag in tags:
                    epc = tag.get('epc', '')
                    antenna = tag.get('antenna', 1)
                    
                    if epc:
                        # Process the tag (handles debouncing internally)
                        process_tag(epc, antenna)
            else:
                empty_polls += 1
                if empty_polls == 50:  # Every 5 seconds
                    print(">>> Waiting for tags... (no data from reader)")
                    empty_polls = 0
            
            # Fast poll - 100ms
            time.sleep(0.1)
            
        except Exception as e:
            print(f">>> Poll error: {e}")
            time.sleep(1)
    
    print(">>> Monitor thread stopped")


async def broadcast_event(event: Dict[str, Any]):
    """Send event to all connected WebSocket clients"""
    if not connected_clients:
        return
    
    message = json.dumps({
        'type': 'scan_event',
        'event': event
    })
    
    disconnected = set()
    for client in connected_clients:
        try:
            await client.send(message)
        except:
            disconnected.add(client)
    
    for client in disconnected:
        connected_clients.discard(client)


async def websocket_handler(websocket):
    """Handle WebSocket client connections"""
    connected_clients.add(websocket)
    print(f"[WS] Client connected. Total: {len(connected_clients)}")
    
    try:
        # Send initial data
        await websocket.send(json.dumps({
            'type': 'init',
            'data': {
                'connected': True,
                'recent_events': recent_events.get_all(),
                'active_employees': db.get_active_employees_in_area(),
                'locations': db.get_all_locations(),
                'stats': db.get_today_attendance_stats()
            }
        }))
        
        async for message in websocket:
            try:
                data = json.loads(message)
                command = data.get('command')
                
                if command == 'get_active':
                    location_id = data.get('location_id')
                    active = db.get_active_employees_in_area(location_id)
                    await websocket.send(json.dumps({
                        'type': 'active_employees',
                        'data': active
                    }))
                
                elif command == 'get_logs':
                    limit = data.get('limit', 100)
                    employee_id = data.get('employee_id')
                    logs = db.get_attendance_logs(limit, employee_id)
                    await websocket.send(json.dumps({
                        'type': 'attendance_logs',
                        'data': logs
                    }))
                
                elif command == 'get_stats':
                    stats = db.get_today_attendance_stats()
                    await websocket.send(json.dumps({
                        'type': 'stats',
                        'data': stats
                    }))
                
                elif command == 'get_employees':
                    employees = db.get_all_employees()
                    await websocket.send(json.dumps({
                        'type': 'employees',
                        'data': employees
                    }))
                
                elif command == 'get_locations':
                    locations = db.get_all_locations()
                    await websocket.send(json.dumps({
                        'type': 'locations',
                        'data': locations
                    }))
                    
            except json.JSONDecodeError:
                print(f"[WS] Invalid JSON: {message}")
                
    except Exception as e:
        if "ConnectionClosed" not in str(type(e)):
            print(f"[WS] Error: {e}")
    finally:
        connected_clients.discard(websocket)
        print(f"[WS] Client disconnected. Total: {len(connected_clients)}")


class CORSHTTPRequestHandler(BaseHTTPRequestHandler):
    """HTTP handler with CORS support for REST API"""
    
    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def send_json_response(self, data: Any, status: int = 200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        path = self.path.split('?')[0]
        
        if path == '/api/status':
            self.send_json_response({
                'connected': True,
                'reader': f"{URA4_IP}:{URA4_HTTP_PORT}",
                'websocket_clients': len(connected_clients)
            })
        
        elif path == '/api/events':
            self.send_json_response({
                'events': recent_events.get_all()
            })
        
        elif path == '/api/active':
            self.send_json_response({
                'active': db.get_active_employees_in_area()
            })
        
        elif path == '/api/logs':
            self.send_json_response({
                'logs': db.get_attendance_logs(100)
            })
        
        elif path == '/api/employees':
            self.send_json_response({
                'employees': db.get_all_employees()
            })
        
        elif path == '/api/locations':
            self.send_json_response({
                'locations': db.get_all_locations()
            })
        
        elif path == '/api/stats':
            self.send_json_response({
                'stats': db.get_today_attendance_stats()
            })
        
        else:
            self.send_json_response({'error': 'Not found'}, 404)
    
    def do_POST(self):
        path = self.path.split('?')[0]
        
        if path == '/api/simulate':
            # For testing: simulate a tag scan
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            
            try:
                data = json.loads(body)
                epc = data.get('epc', '').upper().strip()
                antenna = int(data.get('antenna', 1))
                
                if epc:
                    result = db.process_tag_scan(epc, antenna)
                    
                    if result['success']:
                        event = {
                            'id': str(time.time()),
                            'timestamp': datetime.now().isoformat(),
                            'action': result['action'],
                            'epc': epc,
                            'antenna': antenna,
                            'employee': {
                                'id': result['employee']['id'],
                                'full_name': result['employee']['full_name'],
                                'office': result['employee'].get('office', ''),
                                'position': result['employee'].get('position', '')
                            },
                            'location': {
                                'id': result['location']['id'],
                                'area_name': result['location']['area_name']
                            },
                            'message': result['message']
                        }
                        recent_events.add(event)
                        self.send_json_response({'success': True, 'event': event})
                    else:
                        self.send_json_response({'success': False, 'message': result['message']})
                else:
                    self.send_json_response({'success': False, 'message': 'EPC required'}, 400)
            except Exception as e:
                self.send_json_response({'success': False, 'message': str(e)}, 500)
        
        elif path == '/api/clear':
            recent_events.clear()
            self.send_json_response({'success': True})
        
        else:
            self.send_json_response({'error': 'Not found'}, 404)
    
    def log_message(self, format, *args):
        pass  # Suppress HTTP logs


async def main():
    """Main entry point"""
    global monitor_thread
    
    print("=" * 60)
    print("Time Room - RFID Attendance Tracking Server")
    print("=" * 60)
    print(f"URA4 Reader:  {URA4_IP}:{URA4_HTTP_PORT}")
    print(f"WebSocket:    ws://localhost:{WEBSOCKET_PORT}")
    print(f"REST API:     http://localhost:{HTTP_API_PORT}")
    print("=" * 60)
    
    # Initialize Supabase connection
    print("\nConnecting to Supabase...")
    if not db.init_supabase():
        print("ERROR: Failed to connect to Supabase. Check your .env configuration.")
        print("Required: SUPABASE_URL and SUPABASE_KEY")
        return
    
    # Load locations
    locations = db.get_all_locations()
    if locations:
        print(f"\nConfigured areas ({len(locations)}):")
        for loc in locations:
            print(f"  - Antenna {loc['antenna_port']}: {loc['area_name']}")
    else:
        print("\nWarning: No locations configured in database.")
        print("Add entries to the 'locations' table to map antenna ports to areas.")
    
    print("\n" + "=" * 60)
    
    # Start monitoring thread
    monitor_thread = threading.Thread(target=monitor_thread_func, daemon=True)
    monitor_thread.start()
    
    # Start HTTP API server
    http_server = HTTPServer(('0.0.0.0', HTTP_API_PORT), CORSHTTPRequestHandler)
    http_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
    http_thread.start()
    print(f"HTTP API server running on port {HTTP_API_PORT}")
    
    if WEBSOCKET_AVAILABLE:
        async with websockets.serve(websocket_handler, "0.0.0.0", WEBSOCKET_PORT):
            print(f"WebSocket server running on port {WEBSOCKET_PORT}")
            print("\nServer ready! Open the frontend app to view dashboard.")
            print("Press Ctrl+C to stop.\n")
            
            try:
                await asyncio.Future()
            except asyncio.CancelledError:
                pass
    else:
        print("\nWebSocket not available. Using HTTP API only.")
        print("Install websockets: pip install websockets")
        print("\nServer ready! Press Ctrl+C to stop.\n")
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
        is_running = False
