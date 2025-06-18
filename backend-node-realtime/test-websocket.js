const WebSocket = require('ws');

// Test configuration
const WS_URL = 'ws://localhost:3000/ws';
const TEST_USER_ID = 'test_user_123';
const TEST_SESSION_ID = 'test_session_456';

console.log('🧪 Starting WebSocket test client...');
console.log(`🔌 Connecting to: ${WS_URL}`);

const ws = new WebSocket(WS_URL);

ws.on('open', () => {
    console.log('✅ Connected to WebSocket server');
    
    // Send a test text message
    setTimeout(() => {
        console.log('📝 Sending test text message...');
        ws.send(JSON.stringify({
            type: 'text',
            text: 'Hello! This is a test message from the WebSocket client.',
            user_id: TEST_USER_ID,
            session_id: TEST_SESSION_ID,
            context: {
                source: 'test_client',
                timestamp: new Date().toISOString()
            }
        }));
    }, 1000);

    // Send a ping message
    setTimeout(() => {
        console.log('🏓 Sending ping...');
        ws.send(JSON.stringify({
            type: 'ping'
        }));
    }, 3000);

    // Send another test message
    setTimeout(() => {
        console.log('📝 Sending another test message...');
        ws.send(JSON.stringify({
            type: 'text',
            text: 'Can you help me with booking an appointment?',
            user_id: TEST_USER_ID,
            session_id: TEST_SESSION_ID,
            context: {
                source: 'test_client',
                intent: 'booking'
            }
        }));
    }, 5000);
});

ws.on('message', (data) => {
    try {
        const message = JSON.parse(data);
        console.log('📨 Received message:', JSON.stringify(message, null, 2));
        
        // Handle different message types
        switch (message.type) {
            case 'connection':
                console.log('🎉 Connection established successfully');
                break;
            case 'text_ack':
                console.log('📋 Text message acknowledged');
                break;
            case 'text_response':
                console.log('💬 Received text response');
                break;
            case 'pong':
                console.log('🏓 Received pong response');
                break;
            case 'error':
                console.error('❌ Received error:', message.message);
                break;
            default:
                console.log('📨 Unknown message type:', message.type);
        }
    } catch (error) {
        console.error('❌ Error parsing message:', error);
        console.log('Raw message:', data.toString());
    }
});

ws.on('error', (error) => {
    console.error('❌ WebSocket error:', error);
});

ws.on('close', (code, reason) => {
    console.log(`🔌 WebSocket closed: ${code} - ${reason}`);
    process.exit(0);
});

// Handle process termination
process.on('SIGINT', () => {
    console.log('\n🛑 Shutting down test client...');
    ws.close();
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('\n🛑 Shutting down test client...');
    ws.close();
    process.exit(0);
});

console.log('⏳ Test client running. Press Ctrl+C to exit.'); 