/*
  Campus Found-It AI – script.js
  Global helpers only.
  Each page (dashboard.html, admin_dashboard.html)
  contains its own inline JS for clarity.
*/

// ── Logout (used by navbar button on any page) ──
function logout() {
  localStorage.clear();
  window.location.href = "/login-page";
}

// ── Escape HTML to prevent XSS ──
function escHtml(str) {
  const el = document.createElement("div");
  el.innerText = str || "";
  return el.innerHTML;
}
