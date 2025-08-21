import React, { useState, useEffect, useRef } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Slider } from './ui/slider';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { 
  ChevronUp, 
  ChevronDown, 
  ChevronLeft, 
  ChevronRight, 
  Square, 
  Wifi, 
  WifiOff,
  Zap,
  Settings
} from 'lucide-react';
// Removed mock import - using real WebSocket connection

const RobotController = () => {
  const [ipAddress, setIpAddress] = useState('192.168.1.22');
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [speed, setSpeed] = useState([50]); // Using array for Slider component
  const [activeCommand, setActiveCommand] = useState('');
  const [connectionStatus, setConnectionStatus] = useState('Disconnected');
  
  const wsRef = useRef(null);
  const commandTimeoutRef = useRef(null);

  // Real WebSocket connection to backend
  const connect = async () => {
    if (!ipAddress.trim()) return;
    
    setIsConnecting(true);
    setConnectionStatus('Connecting...');
    
    try {
      // Create WebSocket connection to backend
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'ws://localhost:8001';
      const wsUrl = `${backendUrl.replace('http', 'ws')}/api/ws/robot/${ipAddress}`;
      
      const ws = new WebSocket(wsUrl);
      
      // WebSocket event handlers
      ws.onopen = () => {
        console.log('WebSocket connected to backend');
        setConnectionStatus('Establishing robot connection...');
        
        // Request robot connection
        ws.send(JSON.stringify({ type: 'connect' }));
      };
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('Received message:', message);
          
          if (message.type === 'status' && message.connected) {
            setIsConnected(true);
            setConnectionStatus('Connected');
          } else if (message.type === 'error') {
            setConnectionStatus('Connection Failed');
            console.error('Robot connection error:', message.message);
          } else if (message.type === 'acknowledgment') {
            console.log('Command acknowledged:', message.command);
          }
        } catch (e) {
          console.error('Error parsing message:', e);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('WebSocket Error');
        setIsConnecting(false);
      };
      
      ws.onclose = () => {
        console.log('WebSocket connection closed');
        setIsConnected(false);
        setConnectionStatus('Disconnected');
        wsRef.current = null;
      };
      
      wsRef.current = ws;
      
    } catch (error) {
      setConnectionStatus('Connection Failed');
      console.error('Connection error:', error);
      setIsConnecting(false);
    }
  };

  const disconnect = () => {
    if (wsRef.current) {
      // Send disconnect message to backend
      wsRef.current.send(JSON.stringify({ type: 'disconnect' }));
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
    setConnectionStatus('Disconnected');
    setActiveCommand('');
    setIsConnecting(false);
  };

  const sendCommand = (command) => {
    if (!isConnected || !wsRef.current) return;
    
    wsRef.current.send(command);
    setActiveCommand(command);
    
    // Clear active command after a brief moment for visual feedback
    clearTimeout(commandTimeoutRef.current);
    commandTimeoutRef.current = setTimeout(() => {
      setActiveCommand('');
    }, 150);
  };

  const handleSpeedChange = (newSpeed) => {
    setSpeed(newSpeed);
    // Send speed command - simplified for demo
    if (isConnected && newSpeed[0] !== speed[0]) {
      const command = newSpeed[0] > speed[0] ? 'W' : 'S';
      sendCommand(command);
    }
  };

  const emergencyStop = () => {
    sendCommand('H');
  };

  // Touch event handlers for directional controls
  const handleTouchStart = (command) => {
    sendCommand(command);
  };

  const handleTouchEnd = () => {
    // Send stop command when releasing directional buttons
    if (activeCommand && ['U', 'D', 'L', 'R'].includes(activeCommand)) {
      sendCommand('H');
    }
  };

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      clearTimeout(commandTimeoutRef.current);
    };
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-4">
      <div className="max-w-md mx-auto space-y-6">
        
        {/* Header */}
        <div className="text-center py-4">
          <h1 className="text-3xl font-bold text-slate-800 mb-2">Robot Controller</h1>
          <p className="text-slate-600">Mobile Remote Control</p>
        </div>

        {/* Connection Card */}
        <Card className="shadow-lg">
          <CardHeader className="pb-4">
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Connection Settings
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="ip">Raspberry Pi IP Address</Label>
              <Input
                id="ip"
                value={ipAddress}
                onChange={(e) => setIpAddress(e.target.value)}
                placeholder="192.168.1.22"
                disabled={isConnected}
                className="text-center font-mono"
              />
            </div>
            
            <div className="flex items-center justify-between">
              <Badge 
                variant={isConnected ? "default" : "secondary"} 
                className={`flex items-center gap-1 ${isConnected ? 'bg-green-500' : 'bg-slate-500'}`}
              >
                {isConnected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
                {connectionStatus}
              </Badge>
              
              <Button 
                onClick={isConnected ? disconnect : connect}
                disabled={isConnecting}
                variant={isConnected ? "destructive" : "default"}
                className="min-w-[100px]"
              >
                {isConnecting ? 'Connecting...' : isConnected ? 'Disconnect' : 'Connect'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Speed Control */}
        <Card className="shadow-lg">
          <CardHeader className="pb-4">
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5" />
              Speed Control
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between text-sm text-slate-600">
                <span>Slow</span>
                <span className="font-semibold">{speed[0]}%</span>
                <span>Fast</span>
              </div>
              <Slider
                value={speed}
                onValueChange={handleSpeedChange}
                max={100}
                min={10}
                step={10}
                disabled={!isConnected}
                className="w-full"
              />
            </div>
          </CardContent>
        </Card>

        {/* Direction Controls */}
        <Card className="shadow-lg">
          <CardHeader className="pb-4">
            <CardTitle>Movement Controls</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 max-w-xs mx-auto">
              {/* Top row - Forward button */}
              <div></div>
              <Button
                size="lg"
                variant={activeCommand === 'U' ? "default" : "outline"}
                disabled={!isConnected}
                onTouchStart={() => handleTouchStart('U')}
                onTouchEnd={handleTouchEnd}
                onMouseDown={() => handleTouchStart('U')}
                onMouseUp={handleTouchEnd}
                onMouseLeave={handleTouchEnd}
                className="aspect-square p-0 transition-all duration-150 active:scale-95"
              >
                <ChevronUp className="h-8 w-8" />
              </Button>
              <div></div>

              {/* Middle row - Left and Right buttons */}
              <Button
                size="lg"
                variant={activeCommand === 'L' ? "default" : "outline"}
                disabled={!isConnected}
                onTouchStart={() => handleTouchStart('L')}
                onTouchEnd={handleTouchEnd}
                onMouseDown={() => handleTouchStart('L')}
                onMouseUp={handleTouchEnd}
                onMouseLeave={handleTouchEnd}
                className="aspect-square p-0 transition-all duration-150 active:scale-95"
              >
                <ChevronLeft className="h-8 w-8" />
              </Button>
              
              <Button
                size="lg"
                variant="destructive"
                disabled={!isConnected}
                onClick={emergencyStop}
                className="aspect-square p-0 transition-all duration-150 active:scale-95"
              >
                <Square className="h-6 w-6" />
              </Button>
              
              <Button
                size="lg"
                variant={activeCommand === 'R' ? "default" : "outline"}
                disabled={!isConnected}
                onTouchStart={() => handleTouchStart('R')}
                onTouchEnd={handleTouchEnd}
                onMouseDown={() => handleTouchStart('R')}
                onMouseUp={handleTouchEnd}
                onMouseLeave={handleTouchEnd}
                className="aspect-square p-0 transition-all duration-150 active:scale-95"
              >
                <ChevronRight className="h-8 w-8" />
              </Button>

              {/* Bottom row - Backward button */}
              <div></div>
              <Button
                size="lg"
                variant={activeCommand === 'D' ? "default" : "outline"}
                disabled={!isConnected}
                onTouchStart={() => handleTouchStart('D')}
                onTouchEnd={handleTouchEnd}
                onMouseDown={() => handleTouchStart('D')}
                onMouseUp={handleTouchEnd}
                onMouseLeave={handleTouchEnd}
                className="aspect-square p-0 transition-all duration-150 active:scale-95"
              >
                <ChevronDown className="h-8 w-8" />
              </Button>
              <div></div>
            </div>
          </CardContent>
        </Card>

        {/* Emergency Stop */}
        <Card className="shadow-lg border-red-200">
          <CardContent className="pt-6">
            <Button
              size="lg"
              variant="destructive"
              disabled={!isConnected}
              onClick={emergencyStop}
              className="w-full h-16 text-lg font-semibold"
            >
              EMERGENCY STOP
            </Button>
          </CardContent>
        </Card>

        {/* Instructions */}
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-6 text-sm text-blue-700">
            <p className="mb-2 font-semibold">How to use:</p>
            <ul className="space-y-1 text-xs">
              <li>• Enter your robot's IP address</li>
              <li>• Press Connect to establish connection</li>
              <li>• Hold directional buttons to move</li>
              <li>• Release buttons to stop movement</li>
              <li>• Use speed slider to adjust movement speed</li>
              <li>• Emergency stop for immediate halt</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default RobotController;