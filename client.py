# client.py - Chat Client with Tkinter GUI and Clock Synchronization

import socket
import threading
import json
import time
import tkinter as tk
from tkinter import scrolledtext, messagebox
from config import *
from utils import CristianClockSync, MessageHandler, ClockDriftSimulator

class ChatClient:
    def __init__(self, root, host=HOST, port=PORT):
        self.root = root
        self.host = host
        self.port = port
        self.socket = None
        self.running = True
        self.client_id = None
        
        # Clock synchronization
        self.clock_sync = CristianClockSync()
        self.clock_offset = 0  # Adjustment to apply to local clock
        self.sync_confidence = 0
        self.last_sync_time = time.time()
        
        # Clock drift simulation
        self.drift_simulator = ClockDriftSimulator() if CLOCK_DRIFT_SIMULATION else None
        
        self.setup_gui()
        self.connect_to_server()
    
    def setup_gui(self):
        """Setup Tkinter GUI"""
        self.root.title("💬 Chat Application")
        self.root.geometry("600x700")
        self.root.resizable(True, True)
        
        # Header frame
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="💬 Distributed Chat System", 
                              font=("Arial", 16, "bold"), fg="white", bg="#2c3e50")
        title_label.pack(pady=10)
        
        # Time frame (Local & Synchronized time)
        time_frame = tk.Frame(header_frame, bg="#2c3e50")
        time_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.local_time_label = tk.Label(time_frame, text="Local Time: --:--:--", 
                                        font=("Arial", 10), fg="#3498db", bg="#2c3e50")
        self.local_time_label.pack(side=tk.LEFT, padx=10)
        
        self.sync_time_label = tk.Label(time_frame, text="Sync Time: --:--:--", 
                                       font=("Arial", 10), fg="#2ecc71", bg="#2c3e50")
        self.sync_time_label.pack(side=tk.LEFT, padx=10)
        
        self.sync_status_label = tk.Label(time_frame, text="Sync: ⚪", 
                                         font=("Arial", 10), fg="#f39c12", bg="#2c3e50")
        self.sync_status_label.pack(side=tk.RIGHT, padx=10)
        
        # Chat display area
        chat_frame = tk.Frame(self.root)
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(chat_frame, text="Messages:", font=("Arial", 11, "bold")).pack(anchor=tk.W)
        
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            height=20,
            width=70,
            wrap=tk.WORD,
            font=("Arial", 10),
            bg="#ecf0f1",
            fg="#2c3e50",
            state=tk.DISABLED
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Message input frame
        input_frame = tk.Frame(self.root)
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(input_frame, text="Your message:", font=("Arial", 10)).pack(anchor=tk.W)
        
        self.message_input = tk.Entry(input_frame, font=("Arial", 10), width=70)
        self.message_input.pack(fill=tk.X, pady=5)
        self.message_input.bind("<Return>", lambda e: self.send_message())
        
        # Buttons frame
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        send_btn = tk.Button(button_frame, text="📤 Send", command=self.send_message,
                            bg="#3498db", fg="white", font=("Arial", 10, "bold"), 
                            width=15)
        send_btn.pack(side=tk.LEFT, padx=5)
        
        sync_btn = tk.Button(button_frame, text="⏱️  Sync Clock", command=self.request_clock_sync,
                            bg="#2ecc71", fg="white", font=("Arial", 10, "bold"),
                            width=15)
        sync_btn.pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_bar = tk.Label(self.root, text="Connecting...", 
                                  font=("Arial", 9), fg="white", bg="#34495e", pady=5)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def connect_to_server(self):
        """Connect to server in a separate thread"""
        thread = threading.Thread(target=self._connect, daemon=True)
        thread.start()
    
    def _connect(self):
        """Establish connection to server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.update_status("✅ Connected to server", "green")
            print(f"✅ Connected to server at {self.host}:{self.port}")
            
            # Start receiving messages
            self.receive_messages()
        
        except ConnectionRefusedError:
            self.update_status("❌ Server not found. Is it running?", "red")
            messagebox.showerror("Connection Error", 
                                f"Could not connect to server at {self.host}:{self.port}")
        except Exception as e:
            self.update_status(f"❌ Connection error: {str(e)}", "red")
            messagebox.showerror("Error", f"Connection error: {str(e)}")
    
    def receive_messages(self):
        """Receive messages from server"""
        try:
            while self.running:
                data = self.socket.recv(BUFFER_SIZE).decode(ENCODING)
                if not data:
                    break
                
                message = MessageHandler.parse_message(data)
                if not message:
                    continue
                
                msg_type = message.get('type')
                
                if msg_type == MSG_TYPE_BROADCAST:
                    self.display_chat_message(message)
                
                elif msg_type == MSG_TYPE_USER_JOIN:
                    self.display_system_message(f"➕ {message.get('message')}", "blue")
                
                elif msg_type == MSG_TYPE_USER_LEAVE:
                    self.display_system_message(f"➖ {message.get('message')}", "red")
                
                elif msg_type == MSG_TYPE_CLOCK_SYNC_RESPONSE:
                    self.handle_clock_sync_response(message)
        
        except Exception as e:
            if self.running:
                self.update_status(f"❌ Connection lost: {str(e)}", "red")
                print(f"Error receiving messages: {e}")
        finally:
            self.disconnect()
    
    def send_message(self):
        """Send message to server"""
        content = self.message_input.get().strip()
        if not content:
            return
        
        try:
            # Get local time (with or without drift)
            if self.drift_simulator:
                client_timestamp = self.drift_simulator.get_drifted_time()
            else:
                client_timestamp = int(time.time() * 1000)
            
            message = {
                'type': MSG_TYPE_CHAT,
                'content': content,
                'client_timestamp': client_timestamp
            }
            
            self.socket.send(json.dumps(message).encode(ENCODING))
            self.message_input.delete(0, tk.END)
            self.message_input.focus()
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send message: {str(e)}")
    
    def request_clock_sync(self):
        """Request clock synchronization from server"""
        try:
            client_time_before = int(time.time() * 1000)
            
            request = {
                'type': MSG_TYPE_CLOCK_SYNC_REQUEST,
                'client_time_before': client_time_before
            }
            
            self.socket.send(json.dumps(request).encode(ENCODING))
            self.sync_status_label.config(text="Sync: 🟡", fg="#f39c12")
            print("⏱️  Clock sync request sent to server")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to sync clock: {str(e)}")
    
    def handle_clock_sync_response(self, response):
        """Handle clock synchronization response from server"""
        try:
            client_time_after = int(time.time() * 1000)
            client_time_before = response.get('client_time_before')
            server_time = response.get('server_time')
            
            # Calculate offset using Cristian's algorithm
            offset, confidence, rtt = self.clock_sync.calculate_offset(
                client_time_before,
                server_time,
                client_time_after
            )
            
            self.clock_offset = offset
            self.sync_confidence = confidence
            self.last_sync_time = time.time()
            
            # Apply correction if using drift simulator
            if self.drift_simulator:
                self.drift_simulator.apply_correction(offset)
            
            self.sync_status_label.config(text="Sync: 🟢", fg="#2ecc71")
            
            print(f"✅ Clock synchronized!")
            print(f"   Offset: {offset}ms | Confidence: {confidence}ms | RTT: {rtt}ms")
            
            # Reset to yellow after 2 seconds
            self.root.after(2000, lambda: self.sync_status_label.config(text="Sync: ⚪", fg="#f39c12"))
        
        except Exception as e:
            print(f"❌ Error handling sync response: {e}")
    
    def display_chat_message(self, message):
        """Display chat message in GUI"""
        user_id = message.get('user_id', 'Unknown')
        content = message.get('message', '')
        client_timestamp = message.get('client_timestamp', 'Unknown')
        server_timestamp = message.get('server_timestamp', '')
        
        # Format timestamp
        time_str = MessageHandler.format_time(client_timestamp) if isinstance(client_timestamp, int) else 'Unknown'
        
        display_text = f"[{time_str}] {user_id}: {content}\n"
        
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, display_text, "message")
        self.chat_display.tag_config("message", foreground="#2c3e50")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def display_system_message(self, text, color="black"):
        """Display system message (join/leave)"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{text}\n", "system")
        self.chat_display.tag_config("system", foreground=color, font=("Arial", 9, "italic"))
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def update_time_displays(self):
        """Update local and synchronized time labels"""
        if self.drift_simulator:
            local_time = self.drift_simulator.get_drifted_time()
        else:
            local_time = int(time.time() * 1000)
        
        # Synchronized time = local time + offset
        sync_time = local_time + self.clock_offset
        
        local_time_str = MessageHandler.format_time(local_time)
        sync_time_str = MessageHandler.format_time(sync_time)
        
        self.local_time_label.config(text=f"Local Time: {local_time_str}")
        self.sync_time_label.config(text=f"Sync Time: {sync_time_str}")
        
        # Auto-sync every SYNC_INTERVAL seconds
        if time.time() - self.last_sync_time > SYNC_INTERVAL:
            self.request_clock_sync()
        
        # Update every 500ms
        self.root.after(500, self.update_time_displays)
    
    def update_status(self, text, color="black"):
        """Update status bar"""
        self.status_bar.config(text=text, bg={"green": "#27ae60", "red": "#c0392b"}.get(color, "#34495e"))
    
    def disconnect(self):
        """Disconnect from server"""
        self.running = False
        try:
            if self.socket:
                self.socket.close()
        except:
            pass
        self.update_status("❌ Disconnected", "red")
    
    def on_closing(self):
        """Handle window closing"""
        self.running = False
        try:
            if self.socket:
                self.socket.close()
        except:
            pass
        self.root.destroy()


def main():
    root = tk.Tk()
    client = ChatClient(root)
    
    # Start time update loop
    client.root.after(500, client.update_time_displays)
    
    root.protocol("WM_DELETE_WINDOW", client.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()