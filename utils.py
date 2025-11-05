# utils.py - Utility functions for clock synchronization and helpers

import time
import json
import random
from datetime import datetime

class CristianClockSync:
    """
    Implements Cristian's Clock Synchronization Algorithm.
    
    Steps:
    1. Client sends request with local timestamp T0
    2. Server receives, records S1, process time, returns S2 with server time
    3. Client receives at local time T1
    4. Calculate round trip time RTT = (T1 - T0) - (S2 - S1)
    5. Estimate transmission delay = RTT / 2
    6. Adjusted server time = S2 + RTT/2
    """
    
    @staticmethod
    def get_server_time():
        """Get current server time in milliseconds"""
        return int(time.time() * 1000)
    
    @staticmethod
    def client_send_sync_request():
        """Client initiates clock sync - returns local time in ms"""
        return int(time.time() * 1000)
    
    @staticmethod
    def calculate_offset(client_time_before, server_time_response, client_time_after):
        """
        Calculate clock offset and confidence interval
        
        Args:
            client_time_before: Client time when request sent (ms)
            server_time_response: Server time when responding (ms)
            client_time_after: Client time when response received (ms)
        
        Returns:
            offset: Amount to adjust local clock (ms)
            confidence: Confidence interval (ms)
        """
        # Round trip time
        rtt = client_time_after - client_time_before
        
        # Estimated one-way transmission time
        one_way_delay = rtt / 2
        
        # Adjusted server time accounting for transmission delay
        adjusted_server_time = server_time_response + one_way_delay
        
        # Offset to adjust client clock
        offset = adjusted_server_time - client_time_after
        
        # Confidence interval (half RTT - represents uncertainty)
        confidence = rtt / 2
        
        return offset, confidence, rtt


class MessageHandler:
    """Handle message encoding/decoding"""
    
    @staticmethod
    def create_message(msg_type, **kwargs):
        """Create a JSON message"""
        message = {
            'type': msg_type,
            'timestamp': CristianClockSync.get_server_time(),
            **kwargs
        }
        return json.dumps(message)
    
    @staticmethod
    def parse_message(data):
        """Parse JSON message"""
        try:
            return json.loads(data)
        except:
            return None
    
    @staticmethod
    def format_time(milliseconds):
        """Format milliseconds to HH:MM:SS"""
        seconds = milliseconds // 1000
        dt = datetime.fromtimestamp(seconds)
        return dt.strftime("%H:%M:%S")


class ClockDriftSimulator:
    """Simulate clock drift for testing"""
    
    def __init__(self, max_drift=2000):
        self.local_time_offset = 0
        self.max_drift = max_drift
    
    def get_drifted_time(self):
        """Get time with simulated drift"""
        if random.random() > 0.7:  # 30% chance to drift
            drift = random.randint(-self.max_drift, self.max_drift)
            self.local_time_offset += drift
        
        return int(time.time() * 1000) + self.local_time_offset
    
    def apply_correction(self, offset):
        """Apply clock correction from server"""
        self.local_time_offset += offset