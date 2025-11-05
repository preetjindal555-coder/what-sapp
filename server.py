# server.py - Multi-threaded Chat Server with Clock Synchronization

import socket
import threading
import json
import time
from config import *
from utils import CristianClockSync, MessageHandler

class ChatServer:
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = {}  # {socket: client_info}
        self.clients_lock = threading.Lock()
        self.running = True
    
    def start(self):
        """Start the chat server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        
        print(f"🚀 Chat Server started on {self.host}:{self.port}")
        print(f"⏰ Server time: {MessageHandler.format_time(CristianClockSync.get_server_time())}")
        
        try:
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    
                    # Create client info
                    client_id = f"Client_{len(self.clients) + 1}"
                    client_info = {
                        'socket': client_socket,
                        'address': client_address,
                        'id': client_id,
                        'connected_at': CristianClockSync.get_server_time()
                    }
                    
                    with self.clients_lock:
                        self.clients[client_socket] = client_info
                    
                    print(f"\n✅ {client_id} connected from {client_address}")
                    
                    # Broadcast user join message
                    self.broadcast_message(
                        msg_type=MSG_TYPE_USER_JOIN,
                        user_id=client_id,
                        message=f"{client_id} joined the chat"
                    )
                    
                    # Start handling this client in a separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_id),
                        daemon=True
                    )
                    client_thread.start()
                    
                except Exception as e:
                    if self.running:
                        print(f"Error accepting connection: {e}")
        
        except KeyboardInterrupt:
            print("\n\n🛑 Server shutting down...")
        finally:
            self.shutdown()
    
    def handle_client(self, client_socket, client_id):
        """Handle individual client connection"""
        try:
            while self.running:
                data = client_socket.recv(BUFFER_SIZE).decode(ENCODING)
                
                if not data:
                    break
                
                message = MessageHandler.parse_message(data)
                if not message:
                    continue
                
                msg_type = message.get('type')
                
                if msg_type == MSG_TYPE_CLOCK_SYNC_REQUEST:
                    # Handle clock sync request
                    self.handle_clock_sync_request(client_socket, message, client_id)
                
                elif msg_type == MSG_TYPE_CHAT:
                    # Broadcast chat message
                    self.broadcast_message(
                        msg_type=MSG_TYPE_BROADCAST,
                        user_id=client_id,
                        message=message.get('content'),
                        client_timestamp=message.get('client_timestamp')
                    )
                    print(f"📨 {client_id}: {message.get('content')}")
        
        except Exception as e:
            print(f"❌ Error handling {client_id}: {e}")
        
        finally:
            # Remove client and broadcast leave message
            with self.clients_lock:
                if client_socket in self.clients:
                    del self.clients[client_socket]
            
            self.broadcast_message(
                msg_type=MSG_TYPE_USER_LEAVE,
                user_id=client_id,
                message=f"{client_id} left the chat"
            )
            
            client_socket.close()
            print(f"🔌 {client_id} disconnected. Active clients: {len(self.clients)}")
    
    def handle_clock_sync_request(self, client_socket, request, client_id):
        """Handle Cristian's clock synchronization request"""
        try:
            client_time_before = request.get('client_time_before')
            
            # Server time when receiving request
            server_time_response = CristianClockSync.get_server_time()
            
            # Create response with server time
            response = {
                'type': MSG_TYPE_CLOCK_SYNC_RESPONSE,
                'server_time': server_time_response,
                'client_time_before': client_time_before
            }
            
            client_socket.send(json.dumps(response).encode(ENCODING))
            print(f"⏱️  Clock sync response sent to {client_id} (Server time: {MessageHandler.format_time(server_time_response)})")
        
        except Exception as e:
            print(f"❌ Error in clock sync for {client_id}: {e}")
    
    def broadcast_message(self, msg_type, **kwargs):
        """Broadcast message to all connected clients"""
        message = {
            'type': msg_type,
            'server_timestamp': CristianClockSync.get_server_time(),
            **kwargs
        }
        
        data = json.dumps(message).encode(ENCODING)
        
        with self.clients_lock:
            for client_socket in list(self.clients.keys()):
                try:
                    client_socket.send(data)
                except:
                    pass
    
    def shutdown(self):
        """Shutdown server"""
        self.running = False
        with self.clients_lock:
            for client_socket in list(self.clients.keys()):
                try:
                    client_socket.close()
                except:
                    pass
        
        if self.server_socket:
            self.server_socket.close()
        
        print("✅ Server shutdown complete")


if __name__ == "__main__":
    server = ChatServer()
    server.start()