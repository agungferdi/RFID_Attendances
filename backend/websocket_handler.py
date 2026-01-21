"""WebSocket handler for real-time communication"""

import json
import asyncio
import queue
from typing import Set, Dict, Any

try:
    import websockets
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False

import supabase_client as db


class WebSocketHandler:
    """Manages WebSocket connections and broadcasting"""
    
    def __init__(self):
        self.clients: Set = set()
        self.event_queue = queue.Queue()
        self.running = True
    
    async def broadcast(self, event: Dict[str, Any]):
        """Send event to all connected clients"""
        if not self.clients:
            return
        
        message = json.dumps({'type': 'scan_event', 'event': event})
        disconnected = set()
        
        for client in self.clients:
            try:
                await client.send(message)
            except Exception:
                disconnected.add(client)
        
        for client in disconnected:
            self.clients.discard(client)
    
    async def queue_watcher(self):
        """Watch queue and broadcast events"""
        while self.running:
            try:
                await asyncio.sleep(0.05)
                while not self.event_queue.empty():
                    try:
                        event = self.event_queue.get_nowait()
                        await self.broadcast(event)
                    except queue.Empty:
                        break
            except Exception:
                await asyncio.sleep(1)
    
    def queue_event(self, event: Dict[str, Any]):
        """Add event to broadcast queue"""
        self.event_queue.put(event)
    
    async def handle_client(self, websocket):
        """Handle a WebSocket client connection"""
        self.clients.add(websocket)
        
        try:
            # Send initial data
            await websocket.send(json.dumps({
                'type': 'init',
                'data': {
                    'connected': True,
                    'recent_events': [],
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
                        await websocket.send(json.dumps({
                            'type': 'active_employees',
                            'data': db.get_active_employees_in_area(location_id)
                        }))
                    
                    elif command == 'get_logs':
                        limit = data.get('limit', 100)
                        employee_id = data.get('employee_id')
                        await websocket.send(json.dumps({
                            'type': 'attendance_logs',
                            'data': db.get_attendance_logs(limit, employee_id)
                        }))
                    
                    elif command == 'get_stats':
                        await websocket.send(json.dumps({
                            'type': 'stats',
                            'data': db.get_today_attendance_stats()
                        }))
                    
                    elif command == 'get_employees':
                        await websocket.send(json.dumps({
                            'type': 'employees',
                            'data': db.get_all_employees()
                        }))
                    
                    elif command == 'get_locations':
                        await websocket.send(json.dumps({
                            'type': 'locations',
                            'data': db.get_all_locations()
                        }))
                        
                except json.JSONDecodeError:
                    pass
                    
        except Exception:
            pass
        finally:
            self.clients.discard(websocket)
    
    def stop(self):
        """Stop the handler"""
        self.running = False
