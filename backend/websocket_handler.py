import asyncio
import json
import logging
from typing import Dict, Optional
from fastapi import WebSocket, WebSocketDisconnect
from .robot_controller import RobotController
import ipaddress

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str, ip_address: str):
        """Accept WebSocket connection and establish robot connection"""
        await websocket.accept()
        
        # Validate IP address
        try:
            ipaddress.ip_address(ip_address)
        except ValueError:
            await websocket.close(code=1003, reason="Invalid IP address")
            return False
        
        # Create robot controller
        robot = RobotController(ip_address)
        
        # Store connection info
        self.active_connections[client_id] = {
            "websocket": websocket,
            "robot": robot,
            "ip_address": ip_address,
            "connected": False
        }
        
        logger.info(f"WebSocket client {client_id} connected for IP {ip_address}")
        return True
    
    async def disconnect(self, client_id: str):
        """Disconnect WebSocket and robot"""
        if client_id in self.active_connections:
            connection = self.active_connections[client_id]
            
            # Disconnect robot
            if connection["robot"]:
                await connection["robot"].disconnect()
            
            # Remove from active connections
            del self.active_connections[client_id]
            logger.info(f"WebSocket client {client_id} disconnected")
    
    async def send_message(self, client_id: str, message: dict):
        """Send message to WebSocket client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]["websocket"]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to {client_id}: {e}")
    
    async def handle_robot_connection(self, client_id: str) -> bool:
        """Establish connection to robot"""
        if client_id not in self.active_connections:
            return False
        
        connection = self.active_connections[client_id]
        robot = connection["robot"]
        
        try:
            success = await robot.connect()
            connection["connected"] = success
            
            if success:
                await self.send_message(client_id, {
                    "type": "status",
                    "message": "Connected to robot",
                    "connected": True
                })
            else:
                await self.send_message(client_id, {
                    "type": "error",
                    "message": "Failed to connect to robot",
                    "connected": False
                })
            
            return success
            
        except Exception as e:
            logger.error(f"Robot connection error for {client_id}: {e}")
            await self.send_message(client_id, {
                "type": "error",
                "message": f"Connection error: {str(e)}",
                "connected": False
            })
            return False
    
    async def handle_command(self, client_id: str, command: str) -> bool:
        """Forward command to robot"""
        if client_id not in self.active_connections:
            return False
        
        connection = self.active_connections[client_id]
        robot = connection["robot"]
        
        if not connection["connected"] or not robot.is_connected():
            await self.send_message(client_id, {
                "type": "error",
                "message": "Robot not connected",
                "connected": False
            })
            return False
        
        # Validate command
        valid_commands = ['U', 'D', 'L', 'R', 'W', 'S', 'H', 'Q']
        if command not in valid_commands:
            await self.send_message(client_id, {
                "type": "error", 
                "message": f"Invalid command: {command}"
            })
            return False
        
        try:
            success = await robot.send_command(command)
            
            if success:
                await self.send_message(client_id, {
                    "type": "acknowledgment",
                    "message": f"Command '{command}' executed",
                    "command": command
                })
            else:
                await self.send_message(client_id, {
                    "type": "error",
                    "message": f"Failed to execute command '{command}'"
                })
            
            return success
            
        except Exception as e:
            logger.error(f"Command execution error for {client_id}: {e}")
            await self.send_message(client_id, {
                "type": "error",
                "message": f"Command error: {str(e)}"
            })
            return False

# Global WebSocket manager instance
manager = WebSocketManager()

async def websocket_endpoint(websocket: WebSocket, ip_address: str):
    """WebSocket endpoint for robot control"""
    client_id = f"{websocket.client.host}_{id(websocket)}"
    
    # Connect WebSocket
    connected = await manager.connect(websocket, client_id, ip_address)
    if not connected:
        return
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                command_type = message.get("type", "")
                
                if command_type == "connect":
                    await manager.handle_robot_connection(client_id)
                
                elif command_type == "command":
                    command = message.get("command", "")
                    await manager.handle_command(client_id, command)
                
                elif command_type == "disconnect":
                    break
                
                else:
                    await manager.send_message(client_id, {
                        "type": "error",
                        "message": f"Unknown command type: {command_type}"
                    })
                    
            except json.JSONDecodeError:
                await manager.send_message(client_id, {
                    "type": "error", 
                    "message": "Invalid JSON message"
                })
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
    finally:
        await manager.disconnect(client_id)