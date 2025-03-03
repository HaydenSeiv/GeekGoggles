// Projects page specific code
$(document).ready(() => {
  //fetch user projects on page load
  fetchUserProjects();

  // Projects page specific event handlers
  $("#createProjectBtn").on("click", function (e) {
    e.preventDefault();
    createProject();
  });

});

//create a new project
function createProject() {
  const user = JSON.parse(sessionStorage.getItem("user"));
  // console.log(user);
  const userId = user.id;

  const projectName = $("#newProjectName").val();

  if (isEmpty(projectName)) {
    const emptyMsg = `
    <p class="error-msg">Title can not be empty</p>
    `;
    $("#createProjectCard").append(emptyMsg);

  } else {
    const project = {
      Title: projectName,
      UserID: userId
    };




    AjaxRequest(
      baseUrl + "Projects",
      "POST",
      project,
      "json",
      ProjectsCreateSuccess,
      ProjectsCreateError
    );
  }

}

//fetch user projects
function fetchUserProjects() {
  const user = JSON.parse(sessionStorage.getItem("user"));
  console.log(user);
  const userId = user.id;
  const userName = user.userName;

  /*Page Title*/
  $("#project-header").html(`${userName} Projects`);

  AjaxRequest(
    baseUrl + "projects/getUserProjects/" + userId,
    "GET",
    null,
    "json",
    ProjectsFetchSuccess,
    ProjectsFetchError
  );
}

//open a project
function openProject(projectId) {
  // Store the project ID so we can use it to fetch project data
  //sessionStorage.setItem("currentProjectId", projectId);
  console.log(projectId)
  //Store Project data
  storeProjectData(projectId);
}

//delete a project
function deleteProject(projectId) {

  //send ajax req to delete project
  AjaxRequest(
    baseUrl + "projects/deleteProject/" + projectId,
    "DELETE",
    null,
    "json",
    ProjectsDeleteSuccess,
    ProjectsDeleteError
  );
}
function storeProjectData(projID) {
  console.log(projID);
  AjaxRequest(
    baseUrl + "Projects/" + projID,
    "GET",
    null,
    "json",
    (data, status, xhr) => {
      // Store project info in sessionStorage
      sessionStorage.setItem('proj', JSON.stringify(data));
      // Only navigate after successful storage
      window.location.href = "main.html";
    },
    (ajaxReq, ajaxStatus, errorThrown) => {
      console.log("Error storing project data in session", errorThrown);
      console.log(ajaxStatus);
    }


  );
}
/////////////////////////////////////////////////////////////////////////////////////////////////////
//Success Handlers
/////////////////////////////////////////////////////////////////////////////////////////////////////
function ProjectsFetchSuccess(data, status, xhr) {
  console.log("Projects fetched successfully:", data);

  // Clear existing list
  $("#projectsList").empty();

  //sort data
  data.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));

  // Create list items for each project
  data.forEach(project => {
    const createdDate = new Date(project.createdAt).toLocaleDateString();
    const projectItem = `
      <div class="project-item">
        <h3>${project.title}</h3>
        <p>Created: ${createdDate}</p>
        <div class="project-actions">
          <button class="edit-btn" data-id="${project.id}">Edit</button>
          <button class="delete-btn" data-id="${project.id}">Delete</button>
        </div>
    </div>
    `;
    $("#projectsList").append(projectItem);

    //open user project 
    $(".edit-btn").on("click", function () {
      const projectId = $(this).data("id");
      openProject(projectId);
    });

    //delete user project
    $(".delete-btn").on("click", function () {
      const projectId = $(this).data("id");
      // console.log(projectId);
      deleteProject(projectId);
    });

  });
}


//after a project is created, fetch the user's projects again to update the list
function ProjectsCreateSuccess(data, status, xhr) {
  console.log("Project created successfully:", data);
  //clear ProjectName input
  $("#newProjectName").val("");

  //remove error message
  $("#createProjectCard p.error-msg").remove();
  fetchUserProjects();
}

//after a project is created, fetch the user's projects again to update the list
function ProjectsDeleteSuccess(data, status, xhr) {
  console.log("Project deleted successfully:", data);
  fetchUserProjects();
}

/////////////////////////////////////////////////////////////////////////////////////////////////////
//Error Handlers
/////////////////////////////////////////////////////////////////////////////////////////////////////
function ProjectsFetchError(ajaxReq, ajaxStatus, errorThrown) {
  console.error("Error fetching projects:", errorThrown);
}
function ProjectsCreateError(ajaxReq, ajaxStatus, errorThrown) {
  console.error("Error creating project:", errorThrown);
}
function ProjectsDeleteError(ajaxReq, ajaxStatus, errorThrown) {
  console.error("Error deleting project:", errorThrown);
}
