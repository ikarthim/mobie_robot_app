# Robot Controller API Contracts

## Overview
Convert frontend mock WebSocket implementation to real backend WebSocket proxy that communicates with Raspberry Pi via TCP sockets.

## API Contracts

### WebSocket Endpoint
- **URL**: `ws://backend_url/api/ws/robot/{ip_address}`
- **Protocol**: WebSocket with TCP socket proxy to Raspberry Pi

### WebSocket Message Protocol

#### Client → Server Messages
```json
{
  "command": "U|D|L|R|W|S|H|Q",
  "timestamp": 1642687200000
}
```

#### Server → Client Messages
```json
{
  "type": "status|acknowledgment|error",
  "message": "Connected|Command executed|Connection failed",
  "timestamp": 1642687200000,
  "data": {}
}
```

## Mock Data Replacement

### Frontend Changes Required:
1. Replace `mockWebSocket.connect()` with real WebSocket connection to backend
2. Update connection URL to use backend WebSocket endpoint
3. Remove mock.js utility file
4. Handle real connection errors and status messages

### Backend Implementation Required:

#### 1. WebSocket Handler (`/app/backend/websocket_handler.py`)
- WebSocket connection management
- TCP socket proxy to Raspberry Pi
- Command forwarding and response handling
- Connection state management

#### 2. Robot Controller (`/app/backend/robot_controller.py`)
- TCP socket connection to Pi (IP:65432)
- Command sending (U, D, L, R, W, S, H, Q)
- Connection management and error handling
- Automatic reconnection logic

#### 3. WebSocket Route (`/app/backend/server.py`)
- WebSocket endpoint registration
- IP address validation
- Connection lifecycle management

## Integration Plan

### Phase 1: Backend WebSocket Infrastructure
- Implement WebSocket handler with FastAPI
- Create TCP socket proxy to Raspberry Pi
- Add connection management and error handling

### Phase 2: Frontend Integration
- Replace mock WebSocket with real backend connection
- Update connection logic to use backend endpoint
- Handle real connection states and errors

### Phase 3: Testing & Validation
- Test WebSocket connection establishment
- Validate command forwarding to Pi
- Test connection failure scenarios
- Verify mobile touch controls work with real backend

## Command Protocol (Unchanged)
- `U` - Move forward
- `D` - Move backward  
- `L` - Turn left
- `R` - Turn right
- `W` - Increase speed
- `S` - Decrease speed
- `H` - Emergency stop
- `Q` - Quit/disconnect

## Error Handling
- Connection timeouts
- Invalid IP addresses
- Pi unavailable scenarios
- WebSocket disconnections
- TCP socket errors

## Security Considerations
- IP address validation
- WebSocket connection limits
- Command rate limiting
- Input sanitization