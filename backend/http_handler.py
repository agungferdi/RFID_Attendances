"""HTTP REST API handler"""

import json
from http.server import BaseHTTPRequestHandler
from typing import Any

import supabase_client as db
from config import URA4_IP, URA4_HTTP_PORT


class HTTPHandler(BaseHTTPRequestHandler):
    """HTTP handler with CORS support for REST API"""
    
    ws_handler = None  # Set by main.py
    
    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def send_json(self, data: Any, status: int = 200):
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
        
        routes = {
            '/api/status': lambda: {
                'connected': True,
                'reader': f"{URA4_IP}:{URA4_HTTP_PORT}"
            },
            '/api/events': lambda: {'events': []},
            '/api/active': lambda: {'active': db.get_active_employees_in_area()},
            '/api/logs': lambda: {'logs': db.get_attendance_logs(100)},
            '/api/employees': lambda: {'employees': db.get_all_employees()},
            '/api/locations': lambda: {'locations': db.get_all_locations()},
            '/api/stats': lambda: {'stats': db.get_today_attendance_stats()}
        }
        
        if path in routes:
            self.send_json(routes[path]())
        else:
            self.send_json({'error': 'Not found'}, 404)
    
    def do_POST(self):
        path = self.path.split('?')[0]
        
        if path == '/api/clear':
            self.send_json({'success': True})
        else:
            self.send_json({'error': 'Not found'}, 404)
    
    def log_message(self, format, *args):
        pass
