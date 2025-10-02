// Test multiple users connecting to the same document
const WebSocket = require('ws');

const documentId = '93b40566-5a9f-4adb-9448-c27cfb5dd996';

function createUser(username, userId) {
  const wsUrl = `ws://localhost:8000/collab/ws/docs/${documentId}`;
  const ws = new WebSocket(wsUrl);
  
  ws.on('open', () => {
    console.log(`✅ ${username} connected`);
    
    // Send authentication
    ws.send(JSON.stringify({
      type: 'auth',
      user_id: userId,
      username: username
    }));
  });
  
  ws.on('message', (data) => {
    const message = JSON.parse(data.toString());
    
    if (message.type === 'active_users') {
      console.log(`👥 ${username} received active users:`, message.users.map(u => u.username));
    }
    
    if (message.type === 'auth_success') {
      console.log(`✅ ${username} authenticated successfully`);
    }
  });
  
  ws.on('close', () => {
    console.log(`🔌 ${username} disconnected`);
  });
  
  return ws;
}

// Create multiple users
const user1 = createUser('Alice', 'user-alice-123');
const user2 = createUser('Bob', 'user-bob-456');

// Close connections after 5 seconds
setTimeout(() => {
  console.log('⏰ Closing connections');
  user1.close();
  user2.close();
}, 5000);
