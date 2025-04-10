const baseUrl = "https://localhost:7007/api/";
let files = [];
let nFiles = [];
// $(document).ready(() => {

// });

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
    // Request device with battery service
    const device = await navigator.bluetooth.requestDevice({
      filters: [{ services: ["battery_service"] }]
    });

    if (!device) {
      console.warn("No device selected.");
      return;
    }

    console.log("Device selected:", device.name || "Unknown");

    // Wait 1 second before connecting (fixes some devices rejecting quick connections)
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Connect to GATT server
    const server = await device.gatt.connect();
    console.log("Connected to GATT server");

    // Get battery service
    const service = await server.getPrimaryService("battery_service");
    console.log("Battery Service found");

    // Get battery level characteristic
    const characteristic = await service.getCharacteristic("battery_level");
    console.log("Battery level characteristic found");

    // Read battery level
    const value = await characteristic.readValue();
    const batteryLevel = value.getUint8(0);
    console.log("Battery level:", batteryLevel + "%");

    // Cleanup function to disconnect
    return {
      device,
      disconnect: async () => {
        if (device.gatt.connected) {
          try {
            // Only stop notifications if supported
            if (characteristic.properties.notify) {
              await characteristic.stopNotifications();
            }
            device.gatt.disconnect();
            console.log("Disconnected from device");
          } catch (error) {
            console.error("Error while disconnecting:", error);
          }
        }
      }
    };
  } catch (error) {
    if (error.name === "NotFoundError") {
      console.warn("No device was selected.");
    } else {
      console.error("Bluetooth Error:", error);
      alert("Bluetooth Error: " + error.message);
    }
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
  window.location.href = "../../login.html";
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
  return new Promise((resolve, request) => {
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
    // return pdfBlob; //this returns a file rather than a pdf file

    //conv pdfBlob to a pdf file 
    const pdfFile = new File([pdfBlob], `${title}_Note.pdf`, { type: "application/pdf" });

    resolve(pdfFile);
  });

}


/**
 * converts a base64string to an actual file 
 * @param {*} base64String 
 * @param {*} fileName 
 * @returns the file 
 */
function base64ToFile(base64String, fileName) {
  // Split the base64 string into metadata and data
  // let arr = base64String.split(',');
  // let mime = arr[0].match(/:(.*?);/)[1]; // Extract MIME type
  let bstr = atob(base64String); // Decode Base64 string
  let n = bstr.length;
  let u8arr = new Uint8Array(n);

  // Convert to byte array
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n);
  }

  // Create a File object
  return new File([u8arr], fileName, { type: "image/png" });
}

// // Example usage:
// let base64String = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."; // Your base64 string
// let file = base64ToFile(base64String, "fluke test.png");

// console.log(file);
/**
 * Works exactly like Thread.Sleep()
 * @param {*} ms 
 * @returns 
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}