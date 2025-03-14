const WebSocket = require('ws');
// https://chatgpt.com/canvas/shared/67d46b3efa00819189c2f2b73ca0aa94
const wss = new WebSocket.Server({ port: 8765 });

wss.on('connection', (ws) => {
    console.log('Client connected');

    ws.on('message', (message) => {
        const data = JSON.parse(message);
        console.log('Received:', data);

        // Simulate responses based on received commands
        switch (data.command) {
            case 'sync_project':
                ws.send(JSON.stringify({ command: 'sync_project_response', message: 'Project synced successfully' }));
                break;
            case 'upload_file':
                ws.send(JSON.stringify({ command: 'upload_file_response', message: `File ${data.file_name} uploaded` }));
                break;
            case 'get_updates':
                ws.send(JSON.stringify({
                    command: 'get_updates_response',
                    updates: { images: [{ file_name: 'test.jpg', file_data: '...' }] }
                }));
                break;
            case 'josh_test':
                ws.send(JSON.stringify({
                    command: 'This is a test-Command',
                    message: 'This is a test-Message'
                }));
                break;
            default:
                ws.send(JSON.stringify({ command: 'error', message: 'Unknown command' }));
        }
    });

    ws.on('close', () => console.log('Client disconnected'));
});

console.log('WebSocket server running on ws://localhost:8765');
