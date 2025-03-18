let ws;

function connectWebSocket() {
    console.log("Connecting ...");
    const url = document.getElementById("ws-url").value;
    ws = new WebSocket(url);

    ws.onopen = () => logMessage("✅ Connected to " + url);
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        switch (data.command) {
            case "here_is_the_cat":
                let imgFile = base64ToFile(data.data, data.filename);
                console.log(imgFile);
                //add file to the database
                break;
            default:
                break;
        }
    };
    ws.onerror = (error) => logMessage("❌ WebSocket Error: " + error.message);
    ws.onclose = () => logMessage("🔌 Disconnected from WebSocket");


}

function disconnectWebSocket() {
    if (ws) {
        ws.close();
    }
}

function sendMessage() {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        logMessage("⚠️ WebSocket is not connected.");
        return;
    }
    const message = document.getElementById("messageToSend").value;
    ws.send(message);
    logMessage("📤 Sent: " + message);
}

function logMessage(message) {
    const logDiv = document.getElementById("log");
    logDiv.innerHTML += message + "<br>";
    logDiv.scrollTop = logDiv.scrollHeight;
}