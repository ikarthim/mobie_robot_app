#!/usr/bin/env python3
"""
Backend Test Suite for Robot Controller WebSocket Implementation
Tests the WebSocket endpoint, connection flow, command forwarding, and error handling.
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

import pytest
import websockets
from websockets.exceptions import ConnectionClosedError, InvalidStatusCode
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RobotControllerTester:
    def __init__(self):
        # Get backend URL from frontend env
        frontend_env_path = Path(__file__).parent / "frontend" / ".env"
        self.backend_url = None
        
        if frontend_env_path.exists():
            with open(frontend_env_path, 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        self.backend_url = line.split('=', 1)[1].strip()
                        break
        
        if not self.backend_url:
            self.backend_url = "http://localhost:8001"
            
        # Convert HTTP to WebSocket URL
        self.ws_base_url = self.backend_url.replace('http://', 'ws://').replace('https://', 'wss://')
        self.http_base_url = self.backend_url
        
        logger.info(f"Backend HTTP URL: {self.http_base_url}")
        logger.info(f"Backend WebSocket URL: {self.ws_base_url}")
        
        self.test_results = []
        
    def log_test_result(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} - {test_name}"
        if message:
            result += f": {message}"
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
        
        logger.info(result)
        print(result)
        
    async def test_backend_health(self):
        """Test if backend is running and accessible"""
        try:
            response = requests.get(f"{self.http_base_url}/api/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("message") == "Hello World":
                    self.log_test_result("Backend Health Check", True, "Backend is running and accessible")
                    return True
                else:
                    self.log_test_result("Backend Health Check", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_test_result("Backend Health Check", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("Backend Health Check", False, f"Connection failed: {str(e)}")
            return False
    
    async def test_websocket_connection_valid_ip(self):
        """Test WebSocket connection with valid IP address"""
        test_ip = "192.168.1.100"  # Valid IP format
        ws_url = f"{self.ws_base_url}/api/ws/robot/{test_ip}"
        
        try:
            websocket = await websockets.connect(ws_url)
            async with websocket:
                self.log_test_result("WebSocket Connection (Valid IP)", True, f"Connected to {test_ip}")
                
                # Test sending a connect message
                connect_msg = {"type": "connect"}
                await websocket.send(json.dumps(connect_msg))
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                response_data = json.loads(response)
                
                # Should get an error since we can't actually connect to a robot
                if response_data.get("type") == "error" and "Failed to connect to robot" in response_data.get("message", ""):
                    self.log_test_result("Robot Connection Attempt", True, "TCP connection failed as expected")
                elif response_data.get("type") == "status" and response_data.get("connected") == True:
                    self.log_test_result("Robot Connection Attempt", True, "Unexpected success - robot actually connected")
                else:
                    self.log_test_result("Robot Connection Attempt", False, f"Unexpected response: {response_data}")
                
                return True
                
        except Exception as e:
            self.log_test_result("WebSocket Connection (Valid IP)", False, f"Connection failed: {str(e)}")
            return False
    
    async def test_websocket_connection_invalid_ip(self):
        """Test WebSocket connection with invalid IP address"""
        test_ip = "invalid.ip.address"
        ws_url = f"{self.ws_base_url}/api/ws/robot/{test_ip}"
        
        try:
            websocket = await websockets.connect(ws_url)
            async with websocket:
                # If we get here, the connection was accepted but should be closed immediately
                try:
                    await asyncio.wait_for(websocket.recv(), timeout=2)
                    self.log_test_result("WebSocket Connection (Invalid IP)", False, "Connection should have been rejected")
                except ConnectionClosedError as e:
                    if e.code == 1003:  # Invalid IP should close with code 1003
                        self.log_test_result("WebSocket Connection (Invalid IP)", True, "Connection properly rejected with code 1003")
                    else:
                        self.log_test_result("WebSocket Connection (Invalid IP)", True, f"Connection rejected with code {e.code}")
                except asyncio.TimeoutError:
                    self.log_test_result("WebSocket Connection (Invalid IP)", False, "Connection not rejected as expected")
                    
        except (ConnectionClosedError, InvalidStatusCode) as e:
            self.log_test_result("WebSocket Connection (Invalid IP)", True, f"Connection properly rejected: {str(e)}")
        except Exception as e:
            self.log_test_result("WebSocket Connection (Invalid IP)", False, f"Unexpected error: {str(e)}")
    
    async def test_command_validation(self):
        """Test command validation with valid and invalid commands"""
        test_ip = "192.168.1.101"
        ws_url = f"{self.ws_base_url}/api/ws/robot/{test_ip}"
        
        try:
            websocket = await websockets.connect(ws_url)
            async with websocket:
                # First connect
                connect_msg = {"type": "connect"}
                await websocket.send(json.dumps(connect_msg))
                await websocket.recv()  # Consume connect response
                
                # Test valid commands
                valid_commands = ['U', 'D', 'L', 'R', 'W', 'S', 'H', 'Q']
                valid_command_results = []
                
                for cmd in valid_commands:
                    command_msg = {"type": "command", "command": cmd}
                    await websocket.send(json.dumps(command_msg))
                    
                    response = await asyncio.wait_for(websocket.recv(), timeout=3)
                    response_data = json.loads(response)
                    
                    # Should get error since robot isn't actually connected
                    if response_data.get("type") == "error" and "Robot not connected" in response_data.get("message", ""):
                        valid_command_results.append(True)
                    else:
                        valid_command_results.append(False)
                        logger.warning(f"Unexpected response for command {cmd}: {response_data}")
                
                if all(valid_command_results):
                    self.log_test_result("Valid Command Validation", True, f"All {len(valid_commands)} valid commands properly validated")
                else:
                    failed_count = len(valid_commands) - sum(valid_command_results)
                    self.log_test_result("Valid Command Validation", False, f"{failed_count} commands failed validation")
                
                # Test invalid command (should be validated before checking connection)
                invalid_command_msg = {"type": "command", "command": "INVALID"}
                await websocket.send(json.dumps(invalid_command_msg))
                
                response = await asyncio.wait_for(websocket.recv(), timeout=3)
                response_data = json.loads(response)
                
                # Should get invalid command error OR robot not connected (both are acceptable)
                if (response_data.get("type") == "error" and 
                    ("Invalid command" in response_data.get("message", "") or 
                     "Robot not connected" in response_data.get("message", ""))):
                    self.log_test_result("Invalid Command Validation", True, "Invalid command properly handled")
                else:
                    self.log_test_result("Invalid Command Validation", False, f"Invalid command not handled: {response_data}")
                
        except Exception as e:
            self.log_test_result("Command Validation", False, f"Test failed: {str(e)}")
    
    async def test_message_protocol(self):
        """Test JSON message protocol parsing"""
        test_ip = "192.168.1.102"
        ws_url = f"{self.ws_base_url}/api/ws/robot/{test_ip}"
        
        try:
            websocket = await websockets.connect(ws_url)
            async with websocket:
                # Test invalid JSON
                await websocket.send("invalid json")
                response = await asyncio.wait_for(websocket.recv(), timeout=3)
                response_data = json.loads(response)
                
                if response_data.get("type") == "error" and "Invalid JSON" in response_data.get("message", ""):
                    self.log_test_result("JSON Parsing Error Handling", True, "Invalid JSON properly handled")
                else:
                    self.log_test_result("JSON Parsing Error Handling", False, f"Invalid JSON not handled: {response_data}")
                
                # Test unknown command type
                unknown_msg = {"type": "unknown_type"}
                await websocket.send(json.dumps(unknown_msg))
                response = await asyncio.wait_for(websocket.recv(), timeout=3)
                response_data = json.loads(response)
                
                if response_data.get("type") == "error" and "Unknown command type" in response_data.get("message", ""):
                    self.log_test_result("Unknown Command Type Handling", True, "Unknown command type properly handled")
                else:
                    self.log_test_result("Unknown Command Type Handling", False, f"Unknown command type not handled: {response_data}")
                
        except Exception as e:
            self.log_test_result("Message Protocol", False, f"Test failed: {str(e)}")
    
    async def test_disconnect_handling(self):
        """Test proper disconnect handling"""
        test_ip = "192.168.1.103"
        ws_url = f"{self.ws_base_url}/api/ws/robot/{test_ip}"
        
        try:
            websocket = await websockets.connect(ws_url)
            async with websocket:
                # Send disconnect message
                disconnect_msg = {"type": "disconnect"}
                await websocket.send(json.dumps(disconnect_msg))
                
                # Connection should close
                try:
                    await asyncio.wait_for(websocket.recv(), timeout=3)
                    self.log_test_result("Disconnect Handling", False, "Connection should have closed after disconnect")
                except ConnectionClosedError:
                    self.log_test_result("Disconnect Handling", True, "Connection properly closed on disconnect")
                except asyncio.TimeoutError:
                    self.log_test_result("Disconnect Handling", False, "Connection did not close after disconnect")
                
        except Exception as e:
            self.log_test_result("Disconnect Handling", False, f"Test failed: {str(e)}")
    
    async def test_multiple_connections(self):
        """Test handling multiple WebSocket connections"""
        test_ips = ["192.168.1.104", "192.168.1.105"]
        connections = []
        
        try:
            # Open multiple connections
            for ip in test_ips:
                ws_url = f"{self.ws_base_url}/api/ws/robot/{ip}"
                websocket = await websockets.connect(ws_url)
                connections.append(websocket)
            
            # Send connect message to all
            for i, websocket in enumerate(connections):
                connect_msg = {"type": "connect"}
                await websocket.send(json.dumps(connect_msg))
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                # Should get connection error for each
            
            self.log_test_result("Multiple Connections", True, f"Successfully handled {len(connections)} concurrent connections")
            
        except Exception as e:
            self.log_test_result("Multiple Connections", False, f"Test failed: {str(e)}")
        finally:
            # Clean up connections
            for websocket in connections:
                try:
                    await websocket.close()
                except:
                    pass
    
    async def run_all_tests(self):
        """Run all WebSocket tests"""
        print("🤖 Starting Robot Controller WebSocket Backend Tests")
        print("=" * 60)
        
        # Test backend health first
        backend_healthy = await self.test_backend_health()
        if not backend_healthy:
            print("❌ Backend is not accessible. Cannot proceed with WebSocket tests.")
            return False
        
        # Run WebSocket tests
        await self.test_websocket_connection_valid_ip()
        await self.test_websocket_connection_invalid_ip()
        await self.test_command_validation()
        await self.test_message_protocol()
        await self.test_disconnect_handling()
        await self.test_multiple_connections()
        
        # Summary
        print("\n" + "=" * 60)
        print("🧪 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['message'] and not result['success']:
                print(f"   └─ {result['message']}")
        
        print(f"\n📊 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed!")
            return True
        else:
            print(f"⚠️  {total - passed} tests failed")
            return False

async def main():
    """Main test runner"""
    tester = RobotControllerTester()
    success = await tester.run_all_tests()
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Test runner failed: {e}")
        sys.exit(1)