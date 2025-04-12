//#region start
const projData = sessionStorage.getItem("proj");
let projID;
let projTitle;
let notesArr;
let docsArr;
let itemID = 0;
console.log(projData);
if (projData == null) {
  KillSession();
  console.log("Proj : Null");
} else {
  const proj = JSON.parse(projData);
  projTitle = proj.title;
  projID = proj.id;
  console.log(proj);
  console.log("Proj: Not Null")
}
//#endregion

//MQTT Connection
// //const mqtt = require("mqtt");
// const client = mqtt.connect("wss://localhost:7007/mqtt");
// // const client = mqtt.connect('wss://test.mosquitto.org:8081');
// const topic = "geek_goggles/proj_info";

// $(document).ready(async () => {
//   console.log("Before Sleep");
//   await sleep(4999);
//   console.log("After Sleep");
// });
$(document).ready(async () => {
  const dropZone = initializeDropZone("#drop-zone", "#upload");

  // Load project data using the projectId
  loadProjectData();

  //await sleep(9999);
  console.log("After SLeep");


  // Handle modal dialog - "settings" screen pop up
  $("#open-settings").on("click", () => {
    $("#settings-modal").fadeIn(300);
  });

  $(".close").on("click", () => {
    $("#settings-modal").fadeOut(300);
  });

  // Close modal when clicking outside
  $(window).on("click", (event) => {
    if ($(event.target).is("#settings-modal")) {
      $("#settings-modal").fadeOut(300);
    }
  });

  // Handle upload button click
  $("#upload-button").on("click", () => {
    console.log("drop");
    const files = dropZone.getFiles();
    console.log(files);
    if (files.length > 0) {
      console.log("Files ready to upload:", files[0]);
      saveFile(files[0],"Client/uploads/pi_pics");
    }
  });


  //edit note 
  $(document).on("click", ".edit-btn", function () {
    itemID = $(this).data("id");
    console.log(itemID);
    const cl = $(this).attr("class").split(" ")[2];
    console.log(cl);
    // console.log(projectId);
    if (cl === "note") {
      console.log("here inside note");
      openNote(itemID);
    }
    else if (cl === "doc") {
      // deleteDoc(itemID);
    }
  });

  //delete project item
  $(document).on("click", ".delete-btn", function () {
    const itemID = $(this).data("id");
    console.log(itemID);
    const cl = $(this).attr("class").split(" ")[1];
    console.log(cl);
    // console.log(projectId);
    if (cl === "note") {
      console.log("here inside note");
      deleteNote(itemID);
    }
    else if (cl === "doc") {
      deleteDoc(itemID);
    }
  });
  // Handle Bluetooth connect button click
  $("#bluetooth-connect-button").on("click", function (e) {
    e.preventDefault();
    connectBluetooth();
  });

  // Handle save note button click
  $("#save-note-button").on("click", function (e) {
    e.preventDefault();
    createNote();
  });
  //Handle sync button click
  $("#sync_project").on("click", async function (e) {
    $("#sync_project").html("Syncing...");
    $("#sync_project").prop("disabled", true);
    // Send Project Info
    TransmitProjInfo(projID);
    await sleep(3999);
    $("#sync_project").html("Sync Project");
    $("#sync_project").prop("disabled", true);



  });
});



/**
* will load the project data from the backend, get notes and documents
 * TODO: need to implement this, we have the project id in session storage, now we need to get the data from the backend
 */
function loadProjectData() {
  //need to create a call to the backend to get the project data
  //such as documents and notes
  // console.log(projectId);
  $("#project-name").html("Project : " + projTitle);

  if (projID) {
    //fetch current project notes
    fetchNotes();
    //fetch current project documents 
    fetchDocuments();
  } else {
    console.log("No ProjectID");
  }


}

//////////////////////////////////////////////////////////////////////////////////
//functions
//////////////////////////////////////////////////////////////////////////////////
/**
 * Fetches and displays all Project Notes
 */
function fetchNotes() {
  /**Notes Header */
  $("#notes-title").html(projTitle + "'s Feed");

  //Ajax req to get all project Notes
  AjaxRequest(
    baseUrl + `Notes/getProjectNotes/${projID}`,
    "GET",
    null,
    "json",
    NotesFetchSuccess,
    (ajaxReq, ajaxStatus, errorThrown) => {
      console.error("Error fetching notes:", errorThrown);
    }
  );
}

/**
 * Fetches and displays all Project Documents
 */
function fetchDocuments() {
  //Ajax
  AjaxRequest(
    baseUrl + `Files/getProjectFiles/${projID}`,
    "GET",
    null,
    "json",
    DocumentFetchSuccess,
    (ajaxReq, ajaxStatus, errorThrown) => {
      console.error("Error fetching Project Documents:", errorThrown);
    }
  );
}
/**
 * Creates a new note for the Project
 */
function createNote() {
  const noteTitle = $("#note-title").val();
  const noteBody = $("#note-body").val();

  if (isEmpty(noteTitle)) {
    const emptyMsg = `
    <p class="error-msg">Title can not be empty</p>
    `;
    $("#note-title").append(emptyMsg);
  } else {
    const note = {
      title: noteTitle,
      projectId: projID,
      noteBody: noteBody
    };

    AjaxRequest(
      baseUrl + "Notes",
      "POST",
      note,
      "json",
      NoteCreateSuccess,
      NotesCreateError
    );
  }

}

/**
 * Opens project note for editing
 */
function openNote(noteID) {
  let tempNote = `
        <section id="t-notes">
          <h2>Edit Note</h2>
          <div class="note-form" id="t-note-form">
              <label for="t-note-title">Title: </label>
              <input type="text" id="t-note-title" placeholder="Enter note title">

              <label for="t-note-body">Note:</label>
              <textarea id="t-note-body" placeholder="Enter your note here"></textarea>

              <button id="t-save-note-button">Save Note</button>
          </div>
      </section>
  `;

  $('div[data-nID="' + noteID + '"]').html(tempNote);
  //fill in title and body
  getNote(noteID);

  //save button
  $("#t-save-note-button").on("click", () => {
    resaveNote(noteID);
    console.log("Save Clicked");
  });
}

/**
 * deletes project note
 */

function deleteNote(noteID) {
  AjaxRequest(
    baseUrl + "Notes/" + noteID,
    "DELETE",
    null,
    "json",
    (data, status, xhr) => {
      console.log("Note was deleted successfully");
      loadProjectData();
    },
    (ajaxReq, ajaxStatus, errorThrown) => {
      console.error("Error while deleting note", errorThrown);
    }

  );
}
/** */
function deleteDoc(docID) {
  AjaxRequest(
    baseUrl + "Files/" + docID,
    "DELETE",
    null,
    "json",
    (data, status, xhr) => {
      console.log("Doc was deleted successfully");
      loadProjectData();
    },
    (ajaxReq, ajaxStatus, errorThrown) => {
      console.error("Error while deleting doc", errorThrown);
    }

  );
}

/**
 * fetches notes details
 */
function getNote(noteID) {
  AjaxRequest(
    baseUrl + "Notes/" + noteID,
    "GET",
    null,
    "json",
    (data, status, xhr) => {
      console.log(data);
      //save note data in session
      sessionStorage.setItem("tNote", JSON.stringify(data));
      $("#t-note-title").val(data.title);
      $("#t-note-body").val(data.noteBody);
      // fetchNotes();
    },
    (ajaxReq, ajaxStatus, errorThrown) => {
      console.error("Error getting Note details");
    }
  );
}

/**
 * resaves note with new inputs
 */
function resaveNote(noteID) {
  let newNote = JSON.parse(sessionStorage.getItem("tNote"));
  newNote.id = noteID;
  const nTitle = $("#t-note-title").val();
  const nBody = $("#t-note-body").val();
  console.log(noteID);


  const ptc = [{
    operationType: 0,
    path: "/title",
    op: "replace",
    from: null,
    value: nTitle
  }, {
    operationType: 0,
    path: "/noteBody",
    op: "replace",
    from: null,
    value: nBody
  }
  ];

  console.log(ptc);

  AjaxRequest(
    baseUrl + "Notes/" + noteID,
    "PATCH",
    ptc,
    "json",
    (data, status, xhr) => {
      console.log(data);
      console.log("i work");
      fetchNotes();
    },
    (ajaxReq, ajaxStatus, errorThrown) => {
      console.error("Error resaving Note ", ajaxReq.responseText);
    }, "application/json-patch+json"
  );
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
  console.log(projID);
  console.log(data);
  //add to database
  AjaxRequest(
    baseUrl + `Files?projectId=${projID}&title=${title}${path}`,
    "POST",
    data,
    "json",
    UploadSuccess,
    (ajaxReq, ajaxStatus, errorThrown) => {
      console.error("Error uploading file:", errorThrown);
    },
    false,
    false
  );
}
/////////////////////////////////////////////////////////////////////////////////////////////////////
//Success Handlers
/////////////////////////////////////////////////////////////////////////////////////////////////////
async function NoteCreateSuccess(data, status, xhr) {
  console.log("Note created successfully:", data);
  const nTitle = $("#note-title").val();
  const nBody = $("#note-body").val();
  // CreatePDF(nTitle, nBody).then((pdfFile) => {
  //   saveFile(pdfFile, "Client/uploads/specialFiles");
  // });

  //clear the note title and body
  $("#note-title").val("");
  $("#note-body").val("");
  console.log(data.id);
  
  itemID = data.id;
  console.log(itemID);
  itemName = data.title;

  // loadProjectData();
  // noteSnap(itemID);
  fetchNotes();
  await sleep(1000);
  noteSnap(itemID,itemName);


}
function noteSnap(nID,nName) {
  console.log("Taking snapshot of note with ID:", nID);
  
  let iden = `[data-nid='${nID}']`;
  let $element = $(`[data-nid='${nID}']`); // Select element with data-nID="27"

  if ($element.length === 0) { // Check if element exists
    console.error("Error: No element found with " + iden + " !");
    return;
  }

  html2canvas($element[0]).then(canvas => { // Convert jQuery object to raw DOM element
    const noteSSData = canvas.toDataURL("image/png");
    console.log("Captured Snapshot (Base64):", noteSSData);
    const file = base64ToFile(noteSSData,nName + ".png");
    saveFile(file, "Client/uploads/pi_pics");

  }).catch(error => {
    console.error("Error capturing snapshot:", error);
  });
}


function NotesFetchSuccess(data, status, xhr) {
  console.log("Notes fetched successfully:", data);
  //clear previous list
  // $("#notes-list").empty();
  // console.log(data);
  if (data === undefined) {
    notesArr = [];
  } else {
    notesArr = data;
  }

  if (notesArr !== undefined && docsArr !== undefined) {
    DisplayProjectInfos(notesArr, docsArr);
  }
}

function DocumentFetchSuccess(data, status, xhr) {
  if (data === undefined) {
    docsArr = [];
  } else {
    docsArr = data;
  } console.log("Documents fetched successfuly:", data);
  if (notesArr !== undefined && docsArr !== undefined) {
    DisplayProjectInfos(notesArr, docsArr);
  }
}

function DisplayProjectInfos(d1, d2) {
  $("#notes-list").empty();
  const info = d1.concat(d2);
  console.log(info);

  info.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));


  //find a way to inject 'doc' in the class for file and 'not' for notes
  info.forEach(item => {
    const createdDate = new Date(item.createdAt).toLocaleDateString();
    const itemClass = item.fileType ? "doc" : "note";

    const type = itemClass === "doc" ? item.fileType : null;
    const fileAddr = itemClass == "doc" ? item.fileAddress : null;
    const nData = itemClass === "note" ? { title: item.title, body: item.noteBody } : null;
    console.log(fileAddr);
    const prev = itemClass === "doc" ? `<iframe src="uploads/pi_pics/${fileAddr}" type="${type}" width="100%" height="200px">      
    `: `<div class="custNote" id="custNote">
          <h3>${nData.title}</h3>
          <pre>${nData.body}</pre>
        </div>`;

    // console.log(type);
    const infoItem = `
    <div class="note-item">
      <div class="left">
        <h3>${item.title}</h3>
        <p>Created: ${createdDate}</p>
        <div class= "note-actions">
          <button class="edit-btn  ${itemClass} action" data-id="${item.id}">Edit</button>
          <button class="delete-btn ${itemClass} action" data-id="${item.id}">Delete</button>
        </div>
      </div>
      <div class="right" data-nID="${item.id}">
        ${prev}
      </div>
    </div>
    <hr>
    `;

    $("#notes-list").append(infoItem);

    // //open project 
    // $(".edit-btn").on("click", function () {
    //   const itemID = $(this).data("id");
    //   const cl = $(this).attr("class");
    //   console.log(cl);
    //   // cl === "doc" ? console.log("DOCUMENT") : console.log("NOTE");
    //   // openNote(itemID);
    // });

    // //delete project
    // $(".delete-btn").on("click", function () {
    //   const itemID = $(this).data("id");
    //   // console.log(projectId);
    //   deleteNote(itemID);
    // });

  });


}

function TransmitProjInfo(projID) {
  console.log("MQTT Connected");
  AjaxRequest(baseUrl + "Projects/project/info/" + projID,
    "POST",
    null,
    "json",
    (data, status, xhr) => {
      console.log(data)
    },
    (ajaxReq, ajaxStatus, errorThrown) => {
      console.error("Error sending proj Info - JS");
    }
  );
}
/////////////////////////////////////////////////////////////////////////////////////////////////////
//Error Handlers
/////////////////////////////////////////////////////////////////////////////////////////////////////
function NotesCreateError(ajaxReq, ajaxStatus, errorThrown) {
  console.error("Error creating notes:", errorThrown);
}

function NotesFetchError(ajaxReq, ajaxStatus, errorThrown) {
  console.error("Error fetching notes:", errorThrown);
}
function NotesDeleteError(ajaxReq, ajaxStatus, errorThrown) {
  console.error("Error deleting notes:", errorThrown);
}

function UploadSuccess(data, status, xhr) {
  //console.log("I worked");
}