$(document).ready(() => {
  // Handle register form submission
  $("#registerForm").on("submit", function (e) {
    e.preventDefault();
    registerUser(e);
  });
});

/**
 * Handles user registration by collecting form data and sending it to the server

 * @param {Event} e - The event object from form submission
 */
function registerUser(e) {
  e.preventDefault();

  const username = $("#username").val();  
  const email = $("#email").val();
  const firstName = $("#firstName").val();
  const lastName = $("#lastName").val();
  const password = $("#password").val();
  const confirmPassword = $("#confirmPassword").val();

  // Validate passwords match
  if (password !== confirmPassword) {
    alert("Passwords do not match!");
    return;
  }

  const registrationData = {
    userName: username,
    passwordHash: password,
    email: email,
    firstName: firstName,
    lastName: lastName,
  };

  console.log(registrationData);

  AjaxRequest(
    baseUrl + "Users",
    "POST",
    registrationData,
    "json",
    RegisterSuccess,
    errorHandler
  );
}

/////////////////////////////////////////////////////////////////////////////////////////////////////
//Success Handlers
/////////////////////////////////////////////////////////////////////////////////////////////////////
/**
 * Callback handler for successful user registration
 */
function RegisterSuccess(data, status, xhr) {
  console.log("Registration successful:", data);
  //redirect to login page
  window.location.href = "login.html";
}
/////////////////////////////////////////////////////////////////////////////////////////////////////
//Error Handlers
/////////////////////////////////////////////////////////////////////////////////////////////////////
function RegisterError(ajaxReq, ajaxStatus, errorThrown) {
  console.log(ajaxReq + " Status: " + ajaxStatus + " Error: " + errorThrown);
  alert("Registration failed: " + errorThrown);
}
