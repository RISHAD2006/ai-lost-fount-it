<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Login – Campus Found-It AI</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body class="center-page" style="background:linear-gradient(135deg,#0f2027,#203a43,#2c5364);">

<div class="auth-card">
  <h2>Welcome Back 👋</h2>
  <p class="subtitle">Login to your account</p>

  <input class="input" type="email"    id="email"    placeholder="Email Address">
  <input class="input" type="password" id="password" placeholder="Password">

  <button class="btn btn-blue full-width" onclick="doLogin()">Login</button>
  <div class="msg" id="msg"></div>

  <p class="switch-link">No account yet? <a href="/register">Register here</a></p>
</div>

<script>
async function doLogin() {
  const email    = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value.trim();
  const msgEl    = document.getElementById("msg");

  if (!email || !password) {
    showMsg("Please enter email and password.", "error"); return;
  }

  showMsg("Logging in...", "info");

  const res  = await fetch("/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  const data = await res.json();

  if (res.ok) {
    // Save user info to localStorage (browser memory)
    localStorage.setItem("user_id", data.user_id);
    localStorage.setItem("name",    data.name);
    localStorage.setItem("email",   data.email);
    localStorage.setItem("phone",   data.phone || "");
    showMsg("Login successful! Redirecting...", "success");
    setTimeout(() => location.href = "/dashboard", 800);
  } else {
    showMsg(data.error || "Login failed", "error");
  }
}

function showMsg(text, type) {
  const el = document.getElementById("msg");
  el.textContent = text;
  el.className   = "msg msg-" + type;
}
</script>
</body>
</html>
