const baseUrl = "https://localhost:7007/api/";
let files = [];
let nFiles = [];
$(document).ready(() => {

});

/////////////////////////////////////////////////////////////////////////////////////////////////////
//Success Handlers
/////////////////////////////////////////////////////////////////////////////////////////////////////

/////////////////////////////////////////////////////////////////////////////////////////////////////
//Error Handlers
///////////////////////////////////////////////////////////////////////////////////////////////////// 


/////////////////////////////////////////////////////////////////////////////////////////////////////
//Helper Functions
/////////////////////////////////////////////////////////////////////////////////////////////////////
/**
 * Initializes a drag-and-drop zone for file uploads
 * @param {string} dropZoneSelector - CSS selector for drop zone element
 * @param {string} fileInputSelector - CSS selector for file input element
 * @returns {Object} Object with getFiles method to access selected files
 */
function initializeDropZone(dropZoneSelector, fileInputSelector) {
  const $dropZone = $(dropZoneSelector);
  const $fileInput = $(fileInputSelector);



  // Drag and drop events
  $dropZone.on("dragover", (e) => {
    e.preventDefault();
    $dropZone.addClass("dragover");
  });

  $dropZone.on("dragleave", () => {
    $dropZone.removeClass("dragover");
  });

  $dropZone.on("drop", (e) => {
    e.preventDefault();
    $dropZone.removeClass("dragover");
    // FileStuff(e);
    const droppedFiles = e.originalEvent.dataTransfer.files;
    nFiles = FileStuff(files, droppedFiles);

  }).on("click", (e) => {
    $fileInput.click();
    console.log("James");
  });

  // Add change event for the file input
  $fileInput.on("change", (e) => {
    const selectedFiles = e.target.files;
    nFiles = FileStuff(files, selectedFiles);

  });

  // // File input change event
  // $fileInput.on("change", function () {
  //   console.log("File selected:", $fileInput[0].files);
  // });

  return {
    getFiles: () => nFiles
  };
}

/**
 * Establishes a Bluetooth connection with a device
 * Includes multiple methods for device discovery and connection
 * TODO: need to filter to certian device types, and just in general need more knowledge of bluetooth
 */
async function connectBluetooth() {
  console.log("Connecting to Bluetooth...");

  // Check if browser supports Bluetooth API
  if (!navigator.bluetooth) {
    alert("Bluetooth is not supported by your browser!");
    return;
  }

  try {
    // Method 1: Show all available advertising Bluetooth devices
    const device = await navigator.bluetooth.requestDevice({
      acceptAllDevices: true,
    });

    console.log(device);

    // Method 2: Filter by device name
    // const device = await navigator.bluetooth.requestDevice({
    //   filters: [{ name: "ExactDeviceName" }]
    // });

    // Method 3: Filter by name prefix
    // const device = await navigator.bluetooth.requestDevice({
    //   filters: [{ namePrefix: "Device" }]
    // });

    // Method 4: Filter by service
    // const device = await navigator.bluetooth.requestDevice({
    //   filters: [{ services: ['heart_rate'] }]
    // });

    // Method 5: Multiple filters
    // const device = await navigator.bluetooth.requestDevice({
    //   filters: [
    //     { namePrefix: "Device" },
    //     { manufacturerData: {
    //       0x0059: { dataPrefix: new Uint8Array([0x01, 0x02]) }
    //     }}
    //   ]
    // });

    console.log("Device selected:", device.name);

    // Connect to device GATT server
    const server = await device.gatt.connect();
    console.log("Connected to GATT server");

    // Here you would typically:
    // 1. Get the service you need: server.getPrimaryService(serviceUUID)
    // 2. Get the characteristic: service.getCharacteristic(characteristicUUID)
    // 3. Read/write characteristics as needed
  } catch (error) {
    console.error("Bluetooth Error:", error);
    alert("Bluetooth Error: " + error.message);
  }
}

/////////////////////////////////////////////////////////////////////////////////////////////////////
//Base Functions
/////////////////////////////////////////////////////////////////////////////////////////////////////
/**
 * Generic success handler for Ajax requests
 * @param {Object} serverData - Response data from server
 * @param {string} serverStatus - Server status message
 */
function SuccessHandler(serverData, serverStatus) {
  console.log(serverData);
  console.log(serverStatus);
}
/**
 * Generic error handler for Ajax requests
 * @param {Object} ajaxReq - Ajax request object
 * @param {string} ajaxStatus - Status of the request
 * @param {string} errorThrown - Error message
 */
function errorHandler(ajaxReq, ajaxStatus, errorThrown) {
  console.log(ajaxReq + " Status: " + ajaxStatus + " Error: " + errorThrown);
}
/**
 * Wrapper function for making Ajax requests
 * @param {string} URL - The endpoint URL
 * @param {string} type - HTTP method (GET, POST, etc.)
 * @param {Object} data - Data to send to server
 * @param {string} dataType - Expected response data type
 * @param {Function} success - Success callback function
 * @param {Function} error - Error callback function
 */
function AjaxRequest(URL, type, data, dataType, success, error, contentType = 'application/json', processData = 'true') {
  let ajaxRequest = {};
  ajaxRequest["url"] = URL;
  ajaxRequest["type"] = type;
  // ajaxRequest["data"] = JSON.stringify(data);
  ajaxRequest["dataType"] = dataType;
  ajaxRequest["success"] = success;
  ajaxRequest["error"] = error;
  ajaxRequest["contentType"] = contentType;
  ajaxRequest["processData"] = processData;

  if (data instanceof FormData) {
    ajaxRequest.data = data;
  } else {
    ajaxRequest.data = JSON.stringify(data);
  }
  $.ajax(ajaxRequest);
}

/**
 * End all sessions
 */
function KillSession() {
  window.location.href = "login.html";
  sessionStorage.clear();
  console.log("Logout");
}
/**
 * Head to project page
 */
function OpenProj() {
  window.location.href = "projects.html";
}
/**
 * Check if inputs are valid
 */
function isEmpty(input) {
  if (input.trim() === '') {
    console.log("input is empty");
    return true;
  }
  return false;
}

/**
 * Do some file stuff
 */
function FileStuff(files, filesList) {
  files = [...filesList];
  $("#file-list").html("<strong>Uploaded Files: </strong>");
  files.forEach(file => {
    let fileItem = $("<div class='file-item'></div>");
    fileItem.append(`<p>${file.name}</p>`);
    // check if the file is an image
    if (file.type.startsWith("image/")) {
      let reader = new FileReader();
      reader.onload = (e) => {
        let img = $("<img class='preview-img'>").attr("src", e.target.result);
        fileItem.append(img);
      };
      reader.readAsDataURL(file);
    }
    //check if file is pdf
    else if (file.type === "application/pdf") {
      let reader = new FileReader();
      reader.onload = (e) => {
        let pdf = $(`<embed class='pdf-preview' src="${e.target.result}" type="application/pdf">`);
        fileItem.append(pdf);
      };
      reader.readAsDataURL(file);
    }
    console.log(file);
    // console.log(filesList);
    $("#file-list").append(fileItem);
  });

  return files;
};

/**
 * Make a pdf file with given title and text
 */
function CreatePDF(title, text) {
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF();

  doc.setProperties({
    title: title
  });
  // Add title to the document
  doc.setFontSize(22);
  doc.text(title, 20, 30);

  // Add text content
  doc.setFontSize(12);

  // Handle multi-line text with line breaks
  const textLines = doc.splitTextToSize(text, 170);
  doc.text(textLines, 20, 50);

  doc.save(title + ".pdf");
  const pdfBlob = doc.output('blob');
  console.log(pdfBlob);
  return pdfBlob;
}