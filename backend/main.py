"""Time Room - RFID Attendance Tracking Server"""

import asyncio
import threading
import time
from http.server import HTTPServer

try:
    import websockets
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False

from config import URA4_IP, URA4_HTTP_PORT, WEBSOCKET_PORT, HTTP_API_PORT
from ura4_monitor import URA4Monitor
from websocket_handler import WebSocketHandler
from http_handler import HTTPHandler
from tag_processor import process_tag
import supabase_client as db


# Global state
is_running = True
ws_handler = WebSocketHandler()
ura4_monitor = URA4Monitor(URA4_IP, URA4_HTTP_PORT)


def monitor_loop():
    """Background thread for polling URA4"""
    global is_running
    
    while is_running:
        try:
            tags = ura4_monitor.get_tags()
            for tag in tags:
                epc = tag.get('epc', '')
                antenna = tag.get('antenna', 1)
                if epc:
                    event = process_tag(epc, antenna)
                    if event:
                        ws_handler.queue_event(event)
            time.sleep(0.1)
        except Exception:
            time.sleep(1)


async def main():
    """Main entry point"""
    global is_running
    
    print("Time Room - RFID Attendance Server")
    print(f"Reader: {URA4_IP}:{URA4_HTTP_PORT}")
    print(f"WebSocket: ws://localhost:{WEBSOCKET_PORT}")
    print(f"REST API: http://localhost:{HTTP_API_PORT}")
    
    if not db.init_supabase():
        print("ERROR: Supabase connection failed")
        return
    
    # Start monitor thread
    monitor = threading.Thread(target=monitor_loop, daemon=True)
    monitor.start()
    
    # Start HTTP server
    http_server = HTTPServer(('0.0.0.0', HTTP_API_PORT), HTTPHandler)
    http_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
    http_thread.start()
    
    if WEBSOCKET_AVAILABLE:
        async with websockets.serve(ws_handler.handle_client, "0.0.0.0", WEBSOCKET_PORT):
            queue_task = asyncio.create_task(ws_handler.queue_watcher())
            print("\nServer ready!")
            try:
                await asyncio.Future()
            except asyncio.CancelledError:
                pass
            finally:
                queue_task.cancel()
    else:
        print("WebSocket not available")
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        is_running = False
