# config.py - Configuration constants

HOST = 'localhost'
PORT = 5000
BUFFER_SIZE = 1024
ENCODING = 'utf-8'

# Message types
MSG_TYPE_CHAT = 'chat'
MSG_TYPE_CLOCK_SYNC_REQUEST = 'clock_sync_request'
MSG_TYPE_CLOCK_SYNC_RESPONSE = 'clock_sync_response'
MSG_TYPE_USER_JOIN = 'user_join'
MSG_TYPE_USER_LEAVE = 'user_leave'
MSG_TYPE_BROADCAST = 'broadcast'

# Clock sync parameters
SYNC_INTERVAL = 5  # seconds between sync requests
CLOCK_DRIFT_SIMULATION = True  # simulate clock drift
MAX_CLOCK_DRIFT = 2000  # max milliseconds drift per action
    