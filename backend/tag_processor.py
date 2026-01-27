"""Tag processing logic"""

import time
from datetime import datetime
from typing import Dict, Any, Optional

import supabase_client as db
from config import DEBOUNCE_SECONDS

# Track processed tags for debouncing
processed_tags: Dict[str, float] = {}


def should_process(epc: str, antenna: int) -> bool:
    """Check if tag should be processed (debounce)"""
    key = f"{epc}_{antenna}"
    current_time = time.time()
    
    if key in processed_tags:
        if current_time - processed_tags[key] < DEBOUNCE_SECONDS:
            return False
    
    processed_tags[key] = current_time
    return True


def process_tag(epc: str, antenna: int) -> Optional[Dict[str, Any]]:
    """Process a tag scan and return event data.
    Only returns events for registered employees - unknown tags are ignored.
    """
    if not should_process(epc, antenna):
        return None
    
    result = db.process_tag_scan(epc, antenna)
    
    # Only broadcast events for registered employees
    # Unknown tags are silently ignored (not sent to attendance_logs or frontend)
    if result['success']:
        return {
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
    else:
        # Unknown tag or error - don't broadcast event
        # This ensures only registered employees appear in the system
        return None
