"""URA4 RFID Reader Monitor"""

import json
import urllib.request
import http.cookiejar


class URA4Monitor:
    """Monitors URA4 reader for tag data via HTTP API polling"""
    
    def __init__(self, ip: str, port: int):
        self.base_url = f"http://{ip}:{port}"
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )
    
    def get_tags(self) -> list:
        """Fetch current tags from the reader"""
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
        except Exception:
            return []
