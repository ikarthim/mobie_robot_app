// Mock WebSocket implementation for frontend demo
class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = WebSocket.CONNECTING;
    this.onopen = null;
    this.onclose = null;
    this.onmessage = null;
    this.onerror = null;
  }

  static connect(ipAddress) {
    return new Promise((resolve, reject) => {
      // Simulate connection delay
      setTimeout(() => {
        if (ipAddress && ipAddress.trim()) {
          const mockWS = new MockWebSocket(`ws://${ipAddress}:65432`);
          mockWS.readyState = WebSocket.OPEN;
          
          // Mock successful connection
          if (mockWS.onopen) {
            mockWS.onopen({ type: 'open' });
          }
          
          resolve(mockWS);
        } else {
          reject(new Error('Invalid IP address'));
        }
      }, 1000 + Math.random() * 1500); // 1-2.5 second delay
    });
  }

  send(data) {
    if (this.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not open');
    }
    
    console.log(`Mock: Sending command "${data}" to robot at ${this.url}`);
    
    // Simulate command acknowledgment
    setTimeout(() => {
      if (this.onmessage) {
        this.onmessage({
          type: 'message',
          data: JSON.stringify({ 
            command: data, 
            status: 'executed',
            timestamp: Date.now()
          })
        });
      }
    }, 50);
  }

  close() {
    this.readyState = WebSocket.CLOSED;
    console.log('Mock: WebSocket connection closed');
    
    if (this.onclose) {
      this.onclose({ type: 'close', code: 1000, reason: 'Normal closure' });
    }
  }
}

// Mock WebSocket constants
MockWebSocket.CONNECTING = 0;
MockWebSocket.OPEN = 1;
MockWebSocket.CLOSING = 2;
MockWebSocket.CLOSED = 3;

export const mockWebSocket = {
  connect: MockWebSocket.connect
};