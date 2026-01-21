"""Configuration settings for Time Room server"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# URA4 Reader
URA4_IP = os.getenv('URA4_IP', '192.168.1.100')
URA4_HTTP_PORT = int(os.getenv('URA4_HTTP_PORT', '8080'))

# Server ports
WEBSOCKET_PORT = int(os.getenv('WEBSOCKET_PORT', '8765'))
HTTP_API_PORT = int(os.getenv('HTTP_API_PORT', '8766'))

# Tag processing
DEBOUNCE_SECONDS = 5
