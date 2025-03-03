$(document).ready(() => {
  $("#loginForm").on("submit", function (e) {
    e.preventDefault();
    loginUser();

  });
});

/*
 * send username and password to server for login and get user info
 */
function loginUser() {
  const username = $("#username").val();
  const password = $("#password").val();

  const loginData = {
    username: username,
    password: password,
  };

  AjaxRequest(
    baseUrl + "Users/Login",
    "POST",
    loginData,
    "json",
    LoginSuccess,
    LoginError
  );
}

/////////////////////////////////////////////////////////////////////////////////////////////////////
//Success Handlers
/////////////////////////////////////////////////////////////////////////////////////////////////////

/**
 * Callback handler for successful user login - stores user data in session storage then redirects to projects page
 */
function LoginSuccess(data, status, xhr) {
  console.log("Login successful:", data);
  // Handle successful login here
  // Store user info in localStorage or sessionStorage
  sessionStorage.setItem('user', JSON.stringify(data));

  // Redirect to main application page
  window.location.href = 'projects.html';
}

/////////////////////////////////////////////////////////////////////////////////////////////////////
//Error Handlers
/////////////////////////////////////////////////////////////////////////////////////////////////////
function LoginError(ajaxReq, ajaxStatus, errorThrown) {
  console.log(ajaxReq + " Status: " + ajaxStatus + " Error: " + errorThrown);
  alert("Login failed: " + errorThrown);
  let errorMsg = `
    <p class="error-msg">Invalid Username or Password</p>
  `;
  $("#loginForm").append(errorMsg);
}
