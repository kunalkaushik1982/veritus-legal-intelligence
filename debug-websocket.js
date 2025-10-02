// Debug WebSocket connection issues
const WebSocket = require('ws');

const documentId = 'd38349b7-a34b-4800-a132-fd60eeb112b9';
const wsUrl = `ws://localhost:8000/collab/ws/docs/${documentId}`;

console.log(`🔍 Debugging WebSocket connection: ${wsUrl}`);

const ws = new WebSocket(wsUrl);

ws.on('open', () => {
  console.log('✅ WebSocket opened successfully');
  console.log('📊 WebSocket readyState:', ws.readyState);
  console.log('🌐 WebSocket URL:', ws.url);
  
  // Send authentication
  const authMessage = {
    type: 'auth',
    user_id: 'debug-user-123',
    username: 'Debug User'
  };
  
  console.log('📤 Sending auth message:', JSON.stringify(authMessage));
  ws.send(JSON.stringify(authMessage));
});

ws.on('message', (data) => {
  console.log('📥 Received message:', data.toString());
});

ws.on('close', (code, reason) => {
  console.log(`🔌 WebSocket closed: ${code} - ${reason}`);
  console.log('📊 Final readyState:', ws.readyState);
});

ws.on('error', (error) => {
  console.error('❌ WebSocket error:', error);
  console.error('📊 Error readyState:', ws.readyState);
  console.error('🌐 Error URL:', ws.url);
});

// Keep connection alive for 10 seconds to see what happens
setTimeout(() => {
  console.log('⏰ Closing WebSocket after 10 seconds');
  ws.close(1000, 'Debug test completed');
}, 10000);
