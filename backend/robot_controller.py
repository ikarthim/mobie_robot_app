import socket
import asyncio
import logging
from typing import Optional
import time

logger = logging.getLogger(__name__)

class RobotController:
    def __init__(self, ip_address: str, port: int = 65432):
        self.ip_address = ip_address
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.last_command_time = 0
        self.command_cooldown = 0.1  # 100ms between commands
        
    async def connect(self) -> bool:
        """Establish TCP connection to Raspberry Pi robot"""
        try:
            # Create socket connection
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)  # 5 second timeout
            
            # Connect to Pi
            await asyncio.get_event_loop().run_in_executor(
                None, self.socket.connect, (self.ip_address, self.port)
            )
            
            self.connected = True
            logger.info(f"Connected to robot at {self.ip_address}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to robot: {e}")
            self.connected = False
            if self.socket:
                self.socket.close()
                self.socket = None
            return False
    
    async def disconnect(self):
        """Close connection to robot"""
        try:
            if self.socket:
                # Send quit command before closing
                await self.send_command('Q')
                self.socket.close()
                self.socket = None
            self.connected = False
            logger.info("Disconnected from robot")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    async def send_command(self, command: str) -> bool:
        """Send command to robot with rate limiting"""
        if not self.connected or not self.socket:
            logger.warning("Cannot send command: not connected to robot")
            return False
        
        # Rate limiting
        current_time = time.time()
        if current_time - self.last_command_time < self.command_cooldown:
            await asyncio.sleep(self.command_cooldown)
        
        try:
            # Send command to robot
            await asyncio.get_event_loop().run_in_executor(
                None, self.socket.sendall, command.encode()
            )
            
            self.last_command_time = time.time()
            logger.debug(f"Sent command '{command}' to robot")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send command '{command}': {e}")
            self.connected = False
            return False
    
    def is_connected(self) -> bool:
        """Check if robot is connected"""
        return self.connected and self.socket is not None
    
    async def health_check(self) -> bool:
        """Check if connection is still alive"""
        if not self.is_connected():
            return False
        
        try:
            # Try to get socket status
            self.socket.settimeout(0.1)
            ready = self.socket.recv(1, socket.MSG_PEEK)
            return True
        except socket.timeout:
            return True  # Timeout is expected when no data available
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            self.connected = False
            return False