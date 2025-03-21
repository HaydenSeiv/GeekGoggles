//#region start
const projData = JSON.parse(localStorage.getItem("proj"));
const userData = JSON.parse(localStorage.getItem("user"));


// let projID;


// let projTitle;
// let notesArr;
// let docsArr;

// console.log(projData);
// if (projData == null) {
//     KillSession();
// } else {
//     const proj = JSON.parse(projData);
//     projTitle = proj.title;
//     projID = proj.id;
//     console.log(proj);
// }
//#endregion

$(document).ready(() => {
    // Load project data using the projectId
    //loadProjectData();

    console.log(projData)
});

let ws;

async function connectWebSocket() {
    console.log("Connecting ...");
    const url = document.getElementById("ws-url").value;
    ws = new WebSocket(url);

    ws.onopen = () => logMessage("✅ Connected to " + url);
    ws.onmessage = async (event) => {
        const data = JSON.parse(event.data);
        switch (data.command) {
            case "here_is_the_cat":
                let imgFile = base64ToFile(data.data, data.filename);
                console.log(imgFile);
                //add file to the database
                console.log("Saving Image ...");
                await saveFile(imgFile, `Client/uploads/${userData.username}`);
                const mesg1 = JSON.stringify({
                    command: "ping",
                    message: "pingPong"
                });
                ws.send(mesg1);
                logMessage(mesg1);
                break;
            // case "pong":
            //     const message = JSON.stringify({
            //         command: "ping",
            //         message: "pingPong"
            //     });
            //     ws.send(message);
            case "send_dog":
                sendDog();
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

function sendDog() {
    const fileInput = document.getElementById("imgInput");
    console.log(fileInput);
    let image = fileInput.files[0];
    const reader = new FileReader();
    reader.readAsDataURL(image);  //conv to b64

    reader.onload = () => {
        const base64Data = reader.result.split(",")[1]; // Remove "data:image/png;base64," part
        const message = JSON.stringify({
            command: "here_is_the_dog",
            filename: image.name,
            data: base64Data,
        });

        ws.send(message);
        logMessage("📤 Sent: " + message);

    }

    /**    const reader = new FileReader();
    reader.readAsDataURL(file); // Convert image to Base64

    reader.onload = () => {
        const base64Data = reader.result.split(",")[1]; // Remove "data:image/png;base64," part
        const message = JSON.stringify({
            command: "send_image",
            filename: file.name,
            data: base64Data,
        }); */
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

/**
 * saves files for user
 */
function saveFile(file, customPath = null) {
    console.log(file);
    console.log(file.name)
    //get file details
    const data = new FormData();
    data.append("file", file);
    const title = file.name;
    const path = customPath === null ? "" : "&customPath=" + customPath;
    console.log(projData.id);
    console.log(data);
    //add to database
    AjaxRequest(
        baseUrl + `Files?projectId=${projData.id}&title=${title}${path}`,
        "POST",
        data,
        "json",
        (dataJ) => {

        },
        (ajaxReq, ajaxStatus, errorThrown) => {
            console.error("Error uploading file:", errorThrown);
        },
        false,
        false
    );
}