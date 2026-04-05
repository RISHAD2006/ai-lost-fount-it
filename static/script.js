/* =====================================================
   Campus Found-It AI  —  Global Stylesheet
   ===================================================== */

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Segoe UI', Arial, sans-serif;
  color: #1e293b;
  background: #f1f5f9;
}

/* ── CENTER PAGE (auth pages) ── */
.center-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

/* ── HERO CARD (home page) ── */
.hero-card {
  background: rgba(255,255,255,0.08);
  backdrop-filter: blur(14px);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 24px;
  padding: 50px 40px;
  max-width: 520px;
  width: 100%;
  text-align: center;
  color: white;
  box-shadow: 0 20px 60px rgba(0,0,0,0.4);
}
.hero-card .hero-icon { font-size: 52px; margin-bottom: 14px; }
.hero-card h1 { font-size: 30px; margin-bottom: 10px; }
.hero-card p  { font-size: 15px; opacity: 0.85; margin-bottom: 28px; line-height: 1.6; }

.badge-row { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; margin-bottom: 28px; }
.badge {
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.2);
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 12px;
  color: white;
}

.admin-link { margin-top: 20px; }
.admin-link a { color: rgba(255,255,255,0.6); font-size: 13px; text-decoration: none; }
.admin-link a:hover { color: white; text-decoration: underline; }

/* ── AUTH CARD ── */
.auth-card {
  background: white;
  padding: 42px 36px;
  width: 380px;
  max-width: 95vw;
  border-radius: 18px;
  box-shadow: 0 16px 40px rgba(0,0,0,0.3);
  text-align: center;
}
.auth-card h2    { font-size: 22px; margin-bottom: 6px; color: #1e293b; }
.auth-card .subtitle { font-size: 13px; color: #64748b; margin-bottom: 22px; }
.auth-card .switch-link { margin-top: 16px; font-size: 13px; color: #64748b; }
.auth-card .switch-link a { color: #6366f1; text-decoration: none; }
.auth-card .switch-link a:hover { text-decoration: underline; }

/* ── INPUT ── */
.input {
  display: block;
  width: 100%;
  padding: 12px 14px;
  margin: 8px 0;
  border-radius: 9px;
  border: 1px solid #cbd5e1;
  font-size: 14px;
  outline: none;
  transition: border 0.2s;
  font-family: inherit;
}
.input:focus { border-color: #6366f1; }

/* ── MESSAGE ── */
.msg { min-height: 22px; margin-top: 12px; font-size: 13px; border-radius: 7px; padding: 0 4px; }
.msg-success { color: #16a34a; }
.msg-error   { color: #dc2626; }
.msg-info    { color: #2563eb; }

/* ── BUTTONS ── */
.btn {
  display: inline-block;
  padding: 11px 24px;
  border-radius: 10px;
  border: none;
  font-size: 14px;
  font-weight: bold;
  cursor: pointer;
  text-decoration: none;
  transition: 0.2s;
  font-family: inherit;
}
.btn:hover { transform: translateY(-1px); opacity: 0.92; }
.btn-blue   { background: #3b82f6; color: white; }
.btn-green  { background: #10b981; color: white; }
.btn-red    { background: #ef4444; color: white; }
.btn-purple { background: #6366f1; color: white; }
.btn-dark   { background: #0f172a; color: white; }
.btn-gray   { background: #94a3b8; color: white; }
.full-width { width: 100%; margin-top: 12px; }

/* ── BTN ROW ── */
.btn-row {
  display: flex;
  gap: 14px;
  justify-content: center;
  flex-wrap: wrap;
}
.btn-row .btn { min-width: 120px; }

/* ── NAVBAR ── */
.navbar {
  background: #0f172a;
  color: white;
  padding: 14px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 12px rgba(0,0,0,0.2);
}
.nav-brand { font-size: 20px; font-weight: bold; }
.nav-right { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.nav-user  { font-size: 13px; opacity: 0.75; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #f1f5f9; }
::-webkit-scrollbar-thumb { background: #94a3b8; border-radius: 4px; }

/* ── RESPONSIVE ── */
@media (max-width: 600px) {
  .hero-card { padding: 36px 22px; }
  .auth-card { padding: 32px 22px; }
  .navbar    { padding: 12px 16px; }
}
