"""
URA4 Passive Tag Monitor Server

This server passively monitors the URA4 reader's tag data via HTTP API polling.
It does NOT start/stop inventory - that is controlled by the URA4 default web interface.

When you click "Start" in the URA4 default web, this server will automatically
see the tags and forward them to the React frontend.

Run this server alongside the React app to get real tag data.

Features:
- Real-time tag monitoring via WebSocket
- WhatsApp notifications when tags go OUT (exit datacenter)
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
from typing import Set, Dict, Any
import time

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Note: python-dotenv not installed. Using environment variables directly.")

# WhatsApp Configuration (Fonnte API)
WHATSAPP_PHONE = os.getenv('WHATSAPP_PHONE', '')
FONNTE_TOKEN = os.getenv('FONNTE_TOKEN', '')
WHATSAPP_ENABLED = bool(WHATSAPP_PHONE and FONNTE_TOKEN)

# Debug: Print config on load
print(f"[Config] WhatsApp Phone: {WHATSAPP_PHONE or '(not set)'}")
print(f"[Config] Fonnte Token: {'*' * 8 + FONNTE_TOKEN[-4:] if FONNTE_TOKEN else '(not set)'}")
print(f"[Config] WhatsApp Enabled: {WHATSAPP_ENABLED}")

# Try to import websockets, fallback to basic HTTP if not available
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
WEBSOCKET_PORT = 8765
HTTP_API_PORT = 8766

# Global state
connected_clients: Set = set()
monitor_thread = None
event_loop = None
is_running = True  # Always running

# WhatsApp notification queue
notification_queue = []
notification_lock = threading.Lock()


def send_whatsapp_notification(message: str):
    """Send WhatsApp notification using Fonnte API"""
    if not WHATSAPP_ENABLED:
        print(">>> WhatsApp not enabled (missing WHATSAPP_PHONE or FONNTE_TOKEN)")
        return False
    
    try:
        print(f">>> Sending WhatsApp to {WHATSAPP_PHONE}...")
        
        # Fonnte API endpoint
        url = "https://api.fonnte.com/send"
        
        # Prepare the data - Fonnte API format
        data = urllib.parse.urlencode({
            'target': WHATSAPP_PHONE,
            'message': message,
        }).encode('utf-8')
        
        # Create request with Authorization header (device token)
        request = urllib.request.Request(url, data=data, method='POST')
        request.add_header('Authorization', FONNTE_TOKEN)
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        response = urllib.request.urlopen(request, timeout=15)
        result = response.read().decode('utf-8')
        print(f">>> Fonnte API response: {result}")
        
        result_json = json.loads(result)
        
        if result_json.get('status') == True:
            print(f">>> WhatsApp notification sent successfully!")
            return True
        else:
            print(f">>> WhatsApp notification failed: {result_json.get('reason', 'Unknown error')}")
            return False
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else 'No response body'
        print(f">>> WhatsApp HTTP error {e.code}: {error_body}")
        return False
    except Exception as e:
        print(f">>> WhatsApp notification error: {type(e).__name__}: {e}")
        return False


def queue_whatsapp_notification(tag_info: dict):
    """Queue a WhatsApp notification for a tag that went OUT"""
    with notification_lock:
        notification_queue.append(tag_info)


def process_notification_queue():
    """Process queued notifications (called periodically)"""
    global notification_queue
    
    with notification_lock:
        if not notification_queue:
            return
        
        print(f">>> Processing {len(notification_queue)} notification(s) in queue...")
        tags_to_notify = notification_queue.copy()
        notification_queue = []
    
    if not tags_to_notify:
        return
    
    # Group tags by ASCII name to get correct quantities
    ascii_groups = {}
    for tag in tags_to_notify:
        ascii_name = tag['ascii']
        if ascii_name not in ascii_groups:
            ascii_groups[ascii_name] = {
                'ascii': ascii_name,
                'tags': [],
                'qty': 0
            }
        ascii_groups[ascii_name]['tags'].append(tag)
        ascii_groups[ascii_name]['qty'] += 1
    
    # Build notification message
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    total_tags = len(tags_to_notify)
    unique_assets = len(ascii_groups)
    
    if unique_assets == 1:
        # Single asset type (but may have multiple tags)
        group = list(ascii_groups.values())[0]
        message = f"[ASSET EXIT ALERT]\n\n"
        message += f"Time: {timestamp}\n"
        message += f"Asset: {group['ascii']}\n"
        message += f"Qty: {group['qty']}\n\n"
        # List all TIDs
        message += f"TID(s):\n"
        for i, tag in enumerate(group['tags'], 1):
            tid_short = tag['tid'][-12:] if len(tag['tid']) > 12 else tag['tid']
            message += f"  {i}. {tid_short}\n"
        message += f"\nAsset detected leaving datacenter via Antenna 1"
    else:
        # Multiple asset types
        message = f"[MULTIPLE ASSETS EXIT ALERT]\n\n"
        message += f"Time: {timestamp}\n"
        message += f"Total Tags OUT: {total_tags}\n"
        message += f"Unique Assets: {unique_assets}\n\n"
        for ascii_name, group in list(ascii_groups.items())[:5]:  # Max 5 asset types
            message += f"- {group['ascii']} (Qty: {group['qty']})\n"
            for tag in group['tags'][:3]:  # Max 3 TIDs per asset
                tid_short = tag['tid'][-8:] if len(tag['tid']) > 8 else tag['tid']
                message += f"    TID: ...{tid_short}\n"
        if unique_assets > 5:
            message += f"... and {unique_assets - 5} more asset types\n"
        message += f"\nAssets detected leaving datacenter"
    
    send_whatsapp_notification(message)


class TagDatabase:
    """Thread-safe tag storage - tracks by TID (unique per physical tag)"""
    
    def __init__(self):
        # Key = TID (unique per physical tag), not EPC
        self.tags: Dict[str, Dict[str, Any]] = {}
        self.counter = 0
        self.lock = threading.Lock()
    
    def update_tag(self, epc: str, tid: str, antenna: int = 1, rssi: float = -60.0, count: int = 1):
        """Add or update a tag from API data - tracked by TID"""
        with self.lock:
            epc = epc.upper().strip()
            tid = tid.upper().strip() if tid else ""
            
            # Skip invalid data
            if not epc or len(epc) < 8:
                return
            
            # Use TID as unique key if available, otherwise fall back to EPC
            # TID is factory-programmed and unique per physical tag
            tag_key = tid if tid else epc
            
            # Determine status based on antenna: Ant2 = IN, Ant1 = OUT
            status = 'in' if antenna == 2 else 'out'
            
            # Generate ASCII from EPC
            ascii_val = self._epc_to_ascii(epc)
            
            if tag_key in self.tags:
                # Check if status changed to OUT (was IN, now OUT)
                old_status = self.tags[tag_key].get('status', 'in')
                if old_status == 'in' and status == 'out':
                    # Tag just went OUT - queue notification!
                    if WHATSAPP_ENABLED:
                        queue_whatsapp_notification({
                            'epc': epc,
                            'tid': tid,
                            'ascii': ascii_val,
                            'antenna': antenna
                        })
                        print(f"  >>> TAG OUT ALERT: {ascii_val} (TID: ...{tid[-8:] if len(tid) > 8 else tid})")
                
                # Update existing tag
                self.tags[tag_key]['count'] = count
                self.tags[tag_key]['antenna'] = antenna
                self.tags[tag_key]['status'] = status
                self.tags[tag_key]['rssi'] = rssi
                self.tags[tag_key]['last_seen'] = datetime.now().isoformat()
            else:
                # Add new tag
                self.counter += 1
                self.tags[tag_key] = {
                    'number': self.counter,
                    'epc': epc,
                    'tid': tid,
                    'ascii': ascii_val,
                    'antenna': antenna,
                    'count': count,
                    'status': status,
                    'rssi': rssi,
                    'first_seen': datetime.now().isoformat(),
                    'last_seen': datetime.now().isoformat()
                }
                tid_short = tid[-8:] if len(tid) > 8 else tid
                print(f"  [{self.counter:3d}] {ascii_val} | EPC: {epc[:16]}... | TID: ...{tid_short} | Ant: {antenna} | {status.upper()}")
                
                # If new tag is immediately OUT, also notify
                if status == 'out' and WHATSAPP_ENABLED:
                    queue_whatsapp_notification({
                        'epc': epc,
                        'tid': tid,
                        'ascii': ascii_val,
                        'antenna': antenna
                    })
                    print(f"  >>> NEW TAG OUT ALERT: {ascii_val}")
    
    def _epc_to_ascii(self, epc: str) -> str:
        """Convert EPC hex to ASCII, showing readable chars"""
        try:
            result = []
            for i in range(0, len(epc), 2):
                if i + 1 < len(epc):
                    byte_val = int(epc[i:i+2], 16)
                    if 32 <= byte_val <= 126:  # Printable ASCII
                        result.append(chr(byte_val))
                    else:
                        result.append('.')
            return ''.join(result)
        except:
            return epc[:12] if len(epc) >= 12 else epc
    
    def get_all(self) -> list:
        """Get all tags as list"""
        with self.lock:
            return list(self.tags.values())
    
    def clear(self):
        """Clear all tags"""
        with self.lock:
            self.tags.clear()
            self.counter = 0
            print(">>> Tag database cleared")
    
    def get_count(self) -> int:
        """Get tag count"""
        with self.lock:
            return len(self.tags)


# Global tag database
tag_db = TagDatabase()


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
                # API response: {"type": "Reader-tagReportingResponse", "data": [...]}
                if isinstance(data, dict) and 'data' in data:
                    tags = data['data']
                    normalized = []
                    for tag in tags:
                        # Fields: epcHex, tidHex, antennaPort, rssi, readCount, etc.
                        epc = tag.get('epcHex', '')
                        tid = tag.get('tidHex', tag.get('tid', ''))  # Try tidHex first, then tid
                        if epc:
                            normalized.append({
                                'epc': epc,
                                'tid': tid,
                                'antenna': int(tag.get('antennaPort', 1)),
                                'rssi': float(tag.get('rssi', -60)),
                                'count': int(tag.get('readCount', tag.get('count', 1)))
                            })
                    return normalized
            return []
        except urllib.error.URLError:
            return []  # Reader not reachable
        except:
            return []


# Global monitor
ura4_monitor = URA4Monitor(URA4_IP, URA4_HTTP_PORT)


def monitor_thread_func():
    """Background thread that continuously polls URA4 for tag data"""
    global is_running
    
    print("\n>>> Passive monitoring started")
    print(">>> Waiting for tags... (Start inventory from URA4 default web)")
    print(">>> Poll interval: 100ms")
    if WHATSAPP_ENABLED:
        print(f">>> WhatsApp notifications: ENABLED ({WHATSAPP_PHONE})")
    else:
        print(">>> WhatsApp notifications: DISABLED (configure .env file)")
    print()
    
    last_count = 0
    empty_polls = 0
    notification_check_counter = 0
    
    while is_running:
        try:
            # Poll for tag data
            tags = ura4_monitor.get_tags()
            
            if tags:
                empty_polls = 0
                for tag in tags:
                    epc = tag.get('epc', '')
                    tid = tag.get('tid', '')
                    antenna = tag.get('antenna', 1)
                    rssi = tag.get('rssi', -60.0)
                    count = tag.get('count', 1)
                    
                    if epc:
                        tag_db.update_tag(epc, tid, antenna, rssi, count)
                
                current_count = tag_db.get_count()
                if current_count != last_count:
                    print(f"\n>>> Total unique tags: {current_count}")
                    last_count = current_count
            else:
                empty_polls += 1
                # Only print status occasionally when no tags
                if empty_polls == 50:  # Every 5 seconds (50 * 100ms)
                    print(">>> Waiting for tags... (no data)")
                    empty_polls = 0
            
            # Process WhatsApp notification queue every 2 seconds
            notification_check_counter += 1
            if notification_check_counter >= 20:  # 20 * 100ms = 2 seconds
                notification_check_counter = 0
                process_notification_queue()
            
            # Fast poll - 100ms
            time.sleep(0.1)
            
        except Exception as e:
            print(f">>> Poll error: {e}")
            time.sleep(1)
    
    print(">>> Monitor thread stopped")


async def broadcast_tags():
    """Send tag update to all connected clients"""
    if not connected_clients:
        return
    
    message = json.dumps({
        'type': 'tags',
        'tags': tag_db.get_all()
    })
    
    disconnected = set()
    for client in connected_clients:
        try:
            await client.send(message)
        except:
            disconnected.add(client)
    
    for client in disconnected:
        connected_clients.discard(client)


async def periodic_broadcast():
    """Periodically broadcast tags to clients"""
    while True:
        await asyncio.sleep(0.3)  # Broadcast every 300ms
        if connected_clients:
            await broadcast_tags()


async def websocket_handler(websocket):
    """Handle WebSocket client connections"""
    connected_clients.add(websocket)
    print(f"Client connected. Total: {len(connected_clients)}")
    
    try:
        # Send current status
        await websocket.send(json.dumps({
            'type': 'status',
            'scanning': True,  # Always "scanning" (monitoring)
            'message': 'Connected - Passive monitoring active'
        }))
        
        # Send current tags immediately
        await websocket.send(json.dumps({
            'type': 'tags',
            'tags': tag_db.get_all()
        }))
        
        async for message in websocket:
            try:
                data = json.loads(message)
                command = data.get('command')
                
                if command == 'clear':
                    tag_db.clear()
                    await broadcast_tags()
                    await websocket.send(json.dumps({
                        'type': 'status',
                        'message': 'Data cleared'
                    }))
                    
                elif command == 'get_tags':
                    await websocket.send(json.dumps({
                        'type': 'tags',
                        'tags': tag_db.get_all()
                    }))
                    
            except json.JSONDecodeError:
                print(f"Invalid JSON: {message}")
                
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        connected_clients.discard(websocket)
        print(f"Client disconnected. Total: {len(connected_clients)}")


class CORSHTTPRequestHandler(BaseHTTPRequestHandler):
    """HTTP handler with CORS support for REST API"""
    
    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        if self.path == '/api/tags':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({
                'tags': tag_db.get_all(),
                'scanning': True  # Always monitoring
            }).encode())
            
        elif self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({
                'scanning': True,
                'tagCount': tag_db.get_count(),
                'message': 'Passive monitoring active'
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/api/clear':
            tag_db.clear()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress HTTP logs


async def main():
    """Main entry point"""
    global monitor_thread
    
    print("=" * 60)
    print("URA4 Passive Tag Monitor Server")
    print("=" * 60)
    print(f"URA4 Reader:  {URA4_IP}:{URA4_HTTP_PORT}")
    print(f"WebSocket:    ws://localhost:{WEBSOCKET_PORT}")
    print(f"REST API:     http://localhost:{HTTP_API_PORT}")
    print("-" * 60)
    if WHATSAPP_ENABLED:
        print(f"WhatsApp:     ENABLED")
        print(f"Phone:        {WHATSAPP_PHONE}")
    else:
        print(f"WhatsApp:     DISABLED")
        print(f"              Configure .env with CALLMEBOT_API_KEY")
    print("=" * 60)
    print()
    print("This server passively monitors for tags.")
    print("Start/Stop inventory from the URA4 default web interface.")
    print()
    if WHATSAPP_ENABLED:
        print("WhatsApp alerts will be sent when NEW tags are detected as OUT (exit)")
    print("=" * 60)
    
    # Start monitoring thread immediately
    monitor_thread = threading.Thread(target=monitor_thread_func, daemon=True)
    monitor_thread.start()
    
    # Start HTTP API server in background thread
    http_server = HTTPServer(('0.0.0.0', HTTP_API_PORT), CORSHTTPRequestHandler)
    http_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
    http_thread.start()
    print(f"HTTP API server running on port {HTTP_API_PORT}")
    
    if WEBSOCKET_AVAILABLE:
        # Start WebSocket server
        async with websockets.serve(websocket_handler, "0.0.0.0", WEBSOCKET_PORT):
            print(f"WebSocket server running on port {WEBSOCKET_PORT}")
            print("\nReady! Open the React app to see tags.")
            print("Press Ctrl+C to stop.\n")
            
            # Start periodic broadcast task
            broadcast_task = asyncio.create_task(periodic_broadcast())
            
            try:
                await asyncio.Future()  # Run forever
            except asyncio.CancelledError:
                broadcast_task.cancel()
    else:
        print("\nWebSocket not available. Using HTTP API only.")
        print("Install websockets: pip install websockets")
        print("\nReady! Open the React app to see tags.")
        print("Press Ctrl+C to stop.\n")
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
