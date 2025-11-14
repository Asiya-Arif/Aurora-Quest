// Lightweight client app for index_quest.html
// Place at assets/js/app.js and include in index_quest.html before </body>:
// <script src="assets/js/app.js"></script>
(function () {
  const $ = (s, ctx = document) => ctx.querySelector(s);
  const $$ = (s, ctx = document) => Array.from(ctx.querySelectorAll(s));

  // Expose functions referenced by inline onclicks
  window.toggleForms = function toggleForms() {
    const login = document.getElementById('loginPage');
    const signup = document.getElementById('signupPage');
    if (!login || !signup) return;
    const showLogin = getComputedStyle(login).display !== 'none';
    login.style.display = showLogin ? 'none' : 'flex';
    signup.style.display = showLogin ? 'flex' : 'none';
  };

  window.showSection = function showSection(sectionId) {
    const mainApp = document.getElementById('mainApp');
    if (mainApp) mainApp.style.display = 'block';
    $$('.content-section').forEach(s => s.classList.toggle('active', s.id === sectionId));
    $$('.nav-item').forEach(n => n.classList.toggle('active', n.dataset.section === sectionId));
    const active = document.getElementById(sectionId);
    if (active) active.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  function showMainAppFor(name) {
    const login = document.getElementById('loginPage');
    const signup = document.getElementById('signupPage');
    const main = document.getElementById('mainApp');
    if (login) login.style.display = 'none';
    if (signup) signup.style.display = 'none';
    if (main) main.style.display = 'block';
    if (name) {
      const nameEl = document.getElementById('userName');
      const avatar = document.querySelector('.user-avatar');
      if (nameEl) nameEl.textContent = name;
      if (avatar) avatar.textContent = name.trim().charAt(0).toUpperCase() || 'A';
    }
  }

  function attachListeners() {
    // Sidebar nav
    $$('.nav-item').forEach(item => {
      item.addEventListener('click', () => {
        const section = item.dataset.section;
        if (section) window.showSection(section);
      });
      item.setAttribute('tabindex', '0');
      item.addEventListener('keypress', e => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          item.click();
        }
      });
    });

    // Login
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
      loginForm.addEventListener('submit', e => {
        e.preventDefault();
        const email = (document.getElementById('loginEmail') || {}).value || '';
        const name = email.split('@')[0] || 'Student';
        showMainAppFor(capitalizeWords(name.replace(/[._-]/g, ' ')) + ' 👑');
        window.showSection('dashboard');
      });
    }

    // Signup
    const signupForm = document.getElementById('signupForm');
    if (signupForm) {
      signupForm.addEventListener('submit', e => {
        e.preventDefault();
        const name = (document.getElementById('signupName') || {}).value || 'New Student';
        showMainAppFor(capitalizeWords(name) + ' 👑');
        window.showSection('dashboard');
      });
    }

    // Logout
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', () => {
        const login = document.getElementById('loginPage');
        const main = document.getElementById('mainApp');
        if (main) main.style.display = 'none';
        if (login) login.style.display = 'flex';
      });
    }

    // Upload area -> trigger file input
    const uploadArea = $$('.upload-area')[0];
    const fileInput = document.getElementById('fileInput');
    if (uploadArea && fileInput) {
      uploadArea.addEventListener('click', () => fileInput.click());
      fileInput.addEventListener('change', async (e) => {
        const files = Array.from(e.target.files || []);
        if (!files.length) return;
        // Provide immediate UI feedback
        appendMessage(`Uploaded ${files.length} file(s): ${files.map(f => f.name).join(', ')}`, 'user');
        // Upload to /api/upload (existing server route) as form-data
        const fd = new FormData();
        files.forEach(f => fd.append('files', f));
        try {
          const res = await fetch('/api/upload', { method: 'POST', body: fd });
          const data = await res.json();
          appendMessage(data.message || 'Files uploaded to server.', 'ai');
        } catch (err) {
          appendMessage('Upload failed. See console for details.', 'ai');
          console.error(err);
        }
      });
    }

    // Chat input + send button
    const sendBtn = $$('.send-btn')[0];
    const chatInput = $$('.chat-input')[0];
    if (sendBtn && chatInput) {
      sendBtn.addEventListener('click', () => sendChat(chatInput.value));
      chatInput.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          sendChat(chatInput.value);
        }
      });
    }

    // Mode cards fallback
    $$('.mode-card').forEach(card => {
      card.addEventListener('click', () => {
        const text = card.textContent.toLowerCase();
        if (text.includes('study')) window.showSection('study');
        if (text.includes('tutor')) window.showSection('tutors');
      });
    });
  }

  function appendMessage(text, who = 'ai') {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    const msg = document.createElement('div');
    msg.className = `message ${who === 'user' ? 'user' : 'ai'}`;
    const content = document.createElement('div');
    content.className = 'message-content';
    content.textContent = text;
    msg.appendChild(content);
    chatMessages.appendChild(msg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  async function sendChat(text) {
    const trimmed = (text || '').trim();
    if (!trimmed) return;
    appendMessage(trimmed, 'user');
    const chatInput = $$('.chat-input')[0];
    if (chatInput) chatInput.value = '';
    try {
      // POST to your FastAPI backend which will proxy to Agora Chat
      const res = await fetch('/api/agora/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, session_id: localSessionId() })
      });
      const data = await res.json();
      if (res.ok) {
        appendMessage(data.reply || 'No reply from chatbot.', 'ai');
      } else {
        appendMessage(data.detail || 'Chat error — check server logs.', 'ai');
      }
    } catch (err) {
      appendMessage('Network error while sending chat. See console.', 'ai');
      console.error(err);
    }
  }

  async function callLanguageTutor(input, targetLanguage = 'en') {
    // Example usage for the "AI Language Tutors" mode
    try {
      const res = await fetch('/api/agora/language/tutor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input, target_language: targetLanguage, session_id: localSessionId() })
      });
      const data = await res.json();
      if (res.ok) return data.reply;
      return data.detail || 'Language tutor error';
    } catch (err) {
      console.error(err);
      return 'Network error';
    }
  }

  function localSessionId() {
    // Simple local session id for demo; replace with authenticated session id as needed
    let id = localStorage.getItem('aurora_session_id');
    if (!id) {
      id = 'sess-' + Math.random().toString(36).slice(2, 10);
      localStorage.setItem('aurora_session_id', id);
    }
    return id;
  }

  function capitalizeWords(s) {
    return s.replace(/\b\w/g, c => c.toUpperCase());
  }

  document.addEventListener('DOMContentLoaded', () => {
    attachListeners();
    // Ensure main app remains hidden until login
    const main = document.getElementById('mainApp');
    if (main) main.style.display = 'none';
  });
})();