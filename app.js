// Aurora Quest - Complete Frontend-Backend Integration
const API_BASE_URL = 'http://localhost:8000/api';

// Global state
let currentUser = null;
let currentToken = null;
let currentSessionId = null;

// ============ AUTHENTICATION ============
document.getElementById('loginForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value.trim();
    
    if (!email || !password) {
        alert('❌ Please enter email and password');
        return;
    }
    
    try {
        // Use FormData for OAuth2PasswordRequestForm
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);
        
        const response = await fetch(`${API_BASE_URL}/auth/dev-login`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Login failed');
        }
        
        const data = await response.json();
        currentToken = data.access_token;
        localStorage.setItem('token', currentToken);
        
        // Get user profile
        await loadUserProfile();
        showMainApp();
    } catch (error) {
        console.error('Login error:', error);
        alert('❌ Login failed. Please try again.');
    }
});

document.getElementById('signupForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const name = document.getElementById('signupName').value.trim();
    const email = document.getElementById('signupEmail').value.trim();
    const password = document.getElementById('signupPassword').value.trim();
    
    if (!name || !email || !password) {
        alert('❌ Please fill in all fields');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, email, password })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Registration failed');
        }
        
        const data = await response.json();
        currentToken = data.access_token;
        localStorage.setItem('token', currentToken);
        
        // Get user profile
        await loadUserProfile();
        showMainApp();
    } catch (error) {
        console.error('Signup error:', error);
        alert('❌ ' + error.message);
    }
});

async function loadUserProfile() {
    try {
        const response = await fetch(`${API_BASE_URL}/user/profile`, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });
        
        if (!response.ok) throw new Error('Failed to load profile');
        
        currentUser = await response.json();
        updateUserUI();
    } catch (error) {
        console.error('Profile load error:', error);
    }
}

function updateUserUI() {
    if (!currentUser) return;
    
    const displayName = currentUser.name || 'Study Queen';
    document.getElementById('userName').textContent = displayName + ' 👑';
    
    const avatar = document.querySelector('.user-avatar');
    if (avatar) {
        avatar.textContent = displayName.charAt(0).toUpperCase();
    }
    
    // Update stats
    document.getElementById('streakCount').textContent = currentUser.current_streak || 0;
    document.getElementById('xpCount').textContent = currentUser.total_xp || 0;
}

function showMainApp() {
    document.getElementById('loginPage').style.display = 'none';
    document.getElementById('signupPage').style.display = 'none';
    document.getElementById('mainApp').style.display = 'block';
}

// ============ FILE UPLOAD ============
document.getElementById('fileInput')?.addEventListener('change', async function(e) {
    const files = e.target.files;
    if (files.length === 0) return;
    
    try {
        const formData = new FormData();
        for (let file of files) {
            formData.append('files', file);
        }
        
        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${currentToken}`
            },
            body: formData
        });
        
        if (!response.ok) throw new Error('Upload failed');
        
        const data = await response.json();
        currentSessionId = data.session_id;
        
        // Show success message in chat
        const chatMessages = document.getElementById('chatMessages');
        const aiMsg = document.createElement('div');
        aiMsg.className = 'message ai';
        aiMsg.innerHTML = `<div class="message-content">✨ Files uploaded successfully! I've processed: ${data.files.join(', ')}. You can now ask me questions about your materials! 📚💖</div>`;
        chatMessages.appendChild(aiMsg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Clear file input
        e.target.value = '';
        
        alert(`✨ Files uploaded successfully!\n\n${data.files.join('\n')}\n\nYou can now chat with your materials! 💖`);
    } catch (error) {
        console.error('Upload error:', error);
        alert('❌ Upload failed. Please try again.');
    }
});

// ============ CHAT / AI BOT ============
async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    if (!currentSessionId) {
        alert('⚠️ Please upload your study materials first!');
        return;
    }
    
    const chatMessages = document.getElementById('chatMessages');
    
    // Show user message
    const userMsg = document.createElement('div');
    userMsg.className = 'message user';
    userMsg.innerHTML = `<div class="message-content">${message}</div>`;
    chatMessages.appendChild(userMsg);
    
    input.value = '';
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${currentToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: message,
                session_id: currentSessionId
            })
        });
        
        if (!response.ok) throw new Error('Chat failed');
        
        const data = await response.json();
        
        // Show AI response
        const aiMsg = document.createElement('div');
        aiMsg.className = 'message ai';
        aiMsg.innerHTML = `<div class="message-content">${data.response} ✨<br><small style="color: var(--text-green);">+${data.xp_earned} XP earned!</small></div>`;
        chatMessages.appendChild(aiMsg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Update XP
        if (currentUser) {
            currentUser.total_xp += data.xp_earned;
            updateUserUI();
        }
    } catch (error) {
        console.error('Chat error:', error);
        const aiMsg = document.createElement('div');
        aiMsg.className = 'message ai';
        aiMsg.innerHTML = `<div class="message-content">❌ Sorry, I encountered an error. Please try again! 🥺</div>`;
        chatMessages.appendChild(aiMsg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// Allow Enter key to send message
document.getElementById('chatInput')?.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') sendMessage();
});

// ============ LANGUAGE TUTORS ============
let currentLanguage = null;
let languageChatActive = false;

async function startLanguagePractice(language) {
    try {
        const response = await fetch(`${API_BASE_URL}/language/start`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${currentToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                language: language,
                proficiency_level: 'beginner'
            })
        });
        
        if (!response.ok) throw new Error('Failed to start language session');
        
        const data = await response.json();
        currentSessionId = data.session_id;
        currentLanguage = language;
        
        // Open language tutor chat interface
        openLanguageTutorChat(data);
    } catch (error) {
        console.error('Language session error:', error);
        alert('❌ Failed to start language practice. Please try again.');
    }
}

function openLanguageTutorChat(sessionData) {
    languageChatActive = true;
    
    // Show chat in tutors section
    const tutorsSection = document.getElementById('tutors');
    const chatContainer = document.createElement('div');
    chatContainer.id = 'languageTutorChat';
    chatContainer.className = 'chat-container';
    chatContainer.style.marginTop = '30px';
    chatContainer.innerHTML = `
        <div class="washi-tape washi-top washi-peach"></div>
        <h3 style="font-family: 'Caveat', cursive; font-size: 28px; color: var(--text-pink); margin-bottom: 15px; text-align: center;">
            ${sessionData.language} Tutor Chat 🌍
        </h3>
        <div class="chat-messages" id="languageChatMessages">
            <div class="message ai">
                <div class="message-content">
                    ${sessionData.initial_prompt || `Hello! I'm your ${sessionData.language} tutor! 🌟 Let's practice together! Ask me anything about grammar, vocabulary, or culture! ✨`}
                </div>
            </div>
        </div>
        <div class="chat-input-area">
            <input type="text" class="chat-input" id="languageChatInput" placeholder="Type in ${sessionData.language} or ask questions... 💭">
            <button class="send-btn" onclick="sendLanguageMessage()">
                <i class="fas fa-paper-plane"></i>
            </button>
        </div>
        <div style="text-align: center; margin-top: 15px;">
            <button class="btn-primary" onclick="closeLanguageTutorChat()" style="background: linear-gradient(135deg, var(--pastel-lavender), var(--pastel-blue)); padding: 10px 24px; font-size: 14px;">
                <i class="fas fa-times"></i> Close Tutor
            </button>
        </div>
    `;
    
    // Remove existing chat if present
    const existing = document.getElementById('languageTutorChat');
    if (existing) existing.remove();
    
    tutorsSection.appendChild(chatContainer);
    
    // Scroll to chat
    chatContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    
    // Focus input
    document.getElementById('languageChatInput')?.focus();
    
    // Add enter key listener
    document.getElementById('languageChatInput')?.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') sendLanguageMessage();
    });
}

async function sendLanguageMessage() {
    const input = document.getElementById('languageChatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    if (!currentSessionId || !currentLanguage) {
        alert('⚠️ Please start a language session first!');
        return;
    }
    
    const chatMessages = document.getElementById('languageChatMessages');
    
    // Show user message
    const userMsg = document.createElement('div');
    userMsg.className = 'message user';
    userMsg.innerHTML = `<div class="message-content">${message}</div>`;
    chatMessages.appendChild(userMsg);
    
    input.value = '';
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Show typing indicator
    const typingMsg = document.createElement('div');
    typingMsg.className = 'message ai';
    typingMsg.id = 'typing-indicator';
    typingMsg.innerHTML = `<div class="message-content">Typing... 💭</div>`;
    chatMessages.appendChild(typingMsg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    try {
        const response = await fetch(`${API_BASE_URL}/language/chat`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${currentToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                language: currentLanguage,
                session_id: currentSessionId
            })
        });
        
        // Remove typing indicator
        document.getElementById('typing-indicator')?.remove();
        
        if (!response.ok) throw new Error('Chat failed');
        
        const data = await response.json();
        
        // Show AI response
        const aiMsg = document.createElement('div');
        aiMsg.className = 'message ai';
        aiMsg.innerHTML = `<div class="message-content">${data.response}<br><small style="color: var(--text-green);">+${data.xp_earned} XP earned!</small></div>`;
        chatMessages.appendChild(aiMsg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Update XP
        if (currentUser) {
            currentUser.total_xp += data.xp_earned;
            updateUserUI();
        }
    } catch (error) {
        document.getElementById('typing-indicator')?.remove();
        console.error('Language chat error:', error);
        const aiMsg = document.createElement('div');
        aiMsg.className = 'message ai';
        aiMsg.innerHTML = `<div class="message-content">❌ Sorry, I encountered an error. Please try again! 🥺</div>`;
        chatMessages.appendChild(aiMsg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

function closeLanguageTutorChat() {
    const chat = document.getElementById('languageTutorChat');
    if (chat) chat.remove();
    languageChatActive = false;
    currentLanguage = null;
}

// ============ FLASHCARDS ============
let currentFlashcards = [];
let currentFlashcardIndex = 0;

async function generateFlashcards() {
    if (!currentSessionId) {
        alert('⚠️ Please upload study materials first!');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/flashcards/generate`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${currentToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: currentSessionId,
                num_cards: 10
            })
        });
        
        if (!response.ok) throw new Error('Flashcard generation failed');
        
        const data = await response.json();
        currentFlashcards = data.flashcards;
        currentFlashcardIndex = 0;
        
        displayFlashcards();
    } catch (error) {
        console.error('Flashcard error:', error);
        alert('❌ Failed to generate flashcards. Please try again.');
    }
}

function displayFlashcards() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = '';
    
    if (!currentFlashcards || currentFlashcards.length === 0) {
        chatMessages.innerHTML = `
            <div class="message ai">
                <div class="message-content">
                    No flashcards available. Upload study materials first! 📚✨
                </div>
            </div>
        `;
        return;
    }
    
    const flashcardContainer = document.createElement('div');
    flashcardContainer.className = 'flashcard-container';
    flashcardContainer.innerHTML = `
        <h3 style="font-family: 'Caveat', cursive; font-size: 28px; color: var(--text-pink); margin-bottom: 20px; text-align: center;">
            📇 Study Flashcards
        </h3>
        <div style="text-align: center; margin-bottom: 15px; color: var(--text-primary); font-weight: 600;">
            Card ${currentFlashcardIndex + 1} of ${currentFlashcards.length}
        </div>
        <div class="flashcard" id="flashcard" onclick="flipFlashcard()" style="
            background: white;
            border: 4px solid var(--pastel-pink);
            border-radius: 16px;
            padding: 60px 40px;
            min-height: 300px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: var(--shadow-medium);
            margin-bottom: 20px;
        ">
            <div class="flashcard-content" style="text-align: center; font-size: 18px; color: var(--text-primary); line-height: 1.6;">
                <div id="flashcardFront">${currentFlashcards[currentFlashcardIndex].front}</div>
                <div id="flashcardBack" style="display: none;">${currentFlashcards[currentFlashcardIndex].back}</div>
                <div style="margin-top: 20px; font-size: 14px; opacity: 0.6;">
                    💡 Click to flip
                </div>
            </div>
        </div>
        <div style="display: flex; justify-content: space-between; gap: 15px;">
            <button class="btn-primary" onclick="previousFlashcard()" style="flex: 1; padding: 12px; font-size: 14px;" ${currentFlashcardIndex === 0 ? 'disabled' : ''}>
                <i class="fas fa-arrow-left"></i> Previous
            </button>
            <button class="btn-primary" onclick="nextFlashcard()" style="flex: 1; padding: 12px; font-size: 14px;" ${currentFlashcardIndex === currentFlashcards.length - 1 ? 'disabled' : ''}>
                Next <i class="fas fa-arrow-right"></i>
            </button>
        </div>
        <div style="text-align: center; margin-top: 20px;">
            <button class="btn-primary" onclick="exitFlashcards()" style="background: linear-gradient(135deg, var(--pastel-lavender), var(--pastel-blue)); padding: 10px 24px; font-size: 14px;">
                <i class="fas fa-times"></i> Exit Flashcards
            </button>
        </div>
    `;
    
    chatMessages.appendChild(flashcardContainer);
}

let flashcardFlipped = false;

function flipFlashcard() {
    const front = document.getElementById('flashcardFront');
    const back = document.getElementById('flashcardBack');
    
    if (!flashcardFlipped) {
        front.style.display = 'none';
        back.style.display = 'block';
        flashcardFlipped = true;
    } else {
        front.style.display = 'block';
        back.style.display = 'none';
        flashcardFlipped = false;
    }
}

function nextFlashcard() {
    if (currentFlashcardIndex < currentFlashcards.length - 1) {
        currentFlashcardIndex++;
        flashcardFlipped = false;
        displayFlashcards();
    }
}

function previousFlashcard() {
    if (currentFlashcardIndex > 0) {
        currentFlashcardIndex--;
        flashcardFlipped = false;
        displayFlashcards();
    }
}

function exitFlashcards() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = `
        <div class="message ai">
            <div class="message-content">
                Great study session! 🎉 Upload more materials or ask me questions! ✨💖
            </div>
        </div>
    `;
    currentFlashcards = [];
    currentFlashcardIndex = 0;
}

// ============ QUIZ GENERATION ============
let currentQuiz = null;

async function generateQuiz() {
    if (!currentSessionId) {
        alert('⚠️ Please upload study materials first!');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/quiz/generate`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${currentToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: currentSessionId,
                num_questions: 5
            })
        });
        
        if (!response.ok) throw new Error('Quiz generation failed');
        
        const data = await response.json();
        currentQuiz = data;
        
        displayQuiz(data);
    } catch (error) {
        console.error('Quiz error:', error);
        alert('❌ Failed to generate quiz. Please try again.');
    }
}

function displayQuiz(quiz) {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = '';
    
    const quizContainer = document.createElement('div');
    quizContainer.className = 'quiz-container';
    quizContainer.innerHTML = `
        <h3 style="font-family: 'Caveat', cursive; font-size: 28px; color: var(--text-pink); margin-bottom: 20px; text-align: center;">
            📝 Quiz Time! 🎯
        </h3>
    `;
    
    quiz.questions.forEach((q, index) => {
        const questionDiv = document.createElement('div');
        questionDiv.className = 'quiz-question';
        questionDiv.style.cssText = 'background: white; padding: 20px; margin-bottom: 15px; border-radius: 12px; border: 3px solid var(--pastel-pink);';
        questionDiv.innerHTML = `
            <p style="font-weight: 700; margin-bottom: 12px; color: var(--text-primary);">
                ${index + 1}. ${q.question}
            </p>
            <label style="display: block; padding: 8px; margin: 5px 0; cursor: pointer; border-radius: 8px; background: var(--pastel-cream);">
                <input type="radio" name="q${q.id}" value="A"> A) ${q.option_a}
            </label>
            <label style="display: block; padding: 8px; margin: 5px 0; cursor: pointer; border-radius: 8px; background: var(--pastel-cream);">
                <input type="radio" name="q${q.id}" value="B"> B) ${q.option_b}
            </label>
            <label style="display: block; padding: 8px; margin: 5px 0; cursor: pointer; border-radius: 8px; background: var(--pastel-cream);">
                <input type="radio" name="q${q.id}" value="C"> C) ${q.option_c}
            </label>
            <label style="display: block; padding: 8px; margin: 5px 0; cursor: pointer; border-radius: 8px; background: var(--pastel-cream);">
                <input type="radio" name="q${q.id}" value="D"> D) ${q.option_d}
            </label>
        `;
        quizContainer.appendChild(questionDiv);
    });
    
    const submitBtn = document.createElement('button');
    submitBtn.className = 'btn-primary';
    submitBtn.textContent = '✨ Submit Quiz';
    submitBtn.style.marginTop = '20px';
    submitBtn.onclick = submitQuiz;
    quizContainer.appendChild(submitBtn);
    
    chatMessages.appendChild(quizContainer);
}

async function submitQuiz() {
    if (!currentQuiz) return;
    
    const answers = [];
    
    for (let q of currentQuiz.questions) {
        const selected = document.querySelector(`input[name="q${q.id}"]:checked`);
        if (!selected) {
            alert('⚠️ Please answer all questions!');
            return;
        }
        answers.push({
            question_id: q.id,
            answer: selected.value
        });
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/quiz/submit`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${currentToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                quiz_id: currentQuiz.quiz_id,
                answers: answers
            })
        });
        
        if (!response.ok) throw new Error('Quiz submission failed');
        
        const data = await response.json();
        
        alert(`🎉 Quiz Complete!\n\n` +
              `📊 Score: ${data.score.toFixed(1)}%\n` +
              `✅ Correct: ${data.correct_answers}/${data.total_questions}\n` +
              `⭐ XP Earned: ${data.xp_earned}\n\n` +
              `Great job! Keep studying! 💖`);
        
        // Update XP
        if (currentUser) {
            currentUser.total_xp += data.xp_earned;
            updateUserUI();
        }
        
        // Clear quiz
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = `
            <div class="message ai">
                <div class="message-content">
                    Great work! 🎉 You scored ${data.score.toFixed(1)}%! 
                    ${data.score >= 80 ? 'Excellent! 🌟' : data.score >= 60 ? 'Good job! 💪' : 'Keep practicing! 📚'}
                    <br><br>Upload more materials or take another quiz! ✨
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Quiz submission error:', error);
        alert('❌ Failed to submit quiz. Please try again.');
    }
}

// ============ NAVIGATION ============
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', function() {
        const section = this.dataset.section;
        showSection(section);
        
        document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
        this.classList.add('active');
    });
});

function showSection(sectionId) {
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.add('active');
    }
    
    if (sectionId === 'calendar') {
        setTimeout(() => renderCalendar(), 100);
    } else if (sectionId === 'progress') {
        loadProgressData();
    } else if (sectionId === 'sessions') {
        loadSessionHistory();
    }
}

// ============ PROGRESS TRACKING ============
async function loadProgressData() {
    try {
        const response = await fetch(`${API_BASE_URL}/user/profile`, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });
        
        if (!response.ok) throw new Error('Failed to load progress');
        
        const userData = await response.json();
        
        // Update progress stats in the UI
        console.log('Progress data loaded:', userData);
    } catch (error) {
        console.error('Progress load error:', error);
    }
}

// ============ SESSION HISTORY ============
async function loadSessionHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/user/sessions`, {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });
        
        if (!response.ok) throw new Error('Failed to load sessions');
        
        const sessions = await response.json();
        
        const sessionsContainer = document.getElementById('sessions');
        if (!sessionsContainer) return;
        
        const sessionsList = sessions.map(s => `
            <div class="card" style="margin-bottom: 18px; border-color: var(--pastel-yellow);">
                <div class="washi-tape washi-top washi-yellow"></div>
                <h4 style="color: var(--text-orange); margin-bottom: 10px; font-family: 'Caveat', cursive; font-size: 22px;">
                    ${s.session_type === 'language' ? '🗣️ ' + (s.language || 'Language') : '📚 Study'} Session
                </h4>
                <p style="font-size: 13px; color: var(--text-primary);">
                    ${new Date(s.start_time).toLocaleDateString()} • ${s.duration_minutes || 0} minutes
                </p>
                <span style="color: var(--text-green); font-weight: 700; font-size: 18px; float: right;">
                    +${s.xp_earned || 0} XP
                </span>
            </div>
        `).join('');
        
        sessionsContainer.querySelector('.content-section').innerHTML = `
            <h2 class="section-header">Session History 📝</h2>
            ${sessionsList || '<p>No sessions yet. Start studying! 📚✨</p>'}
        `;
    } catch (error) {
        console.error('Session history error:', error);
    }
}

// ============ LOGOUT ============
document.getElementById('logoutBtn')?.addEventListener('click', function() {
    if (confirm('Are you sure you want to logout? 🥺')) {
        currentToken = null;
        currentUser = null;
        currentSessionId = null;
        localStorage.removeItem('token');
        
        document.getElementById('loginEmail').value = '';
        document.getElementById('loginPassword').value = '';
        
        document.getElementById('mainApp').style.display = 'none';
        document.getElementById('loginPage').style.display = 'flex';
    }
});

// ============ FORM TOGGLE ============
function toggleForms() {
    const loginPage = document.getElementById('loginPage');
    const signupPage = document.getElementById('signupPage');
    
    if (loginPage.style.display === 'none') {
        loginPage.style.display = 'flex';
        signupPage.style.display = 'none';
    } else {
        loginPage.style.display = 'none';
        signupPage.style.display = 'flex';
    }
}

// ============ CALENDAR FUNCTIONS ============
let currentDate = new Date();
let currentYear = currentDate.getFullYear();
let currentMonth = currentDate.getMonth();

let examDates = {
    '2025-11-18': { type: 'exam', title: 'Biology Mid-term', subject: 'Biology', color: 'yellow', notes: 'Focus on cell division', files: [] },
    '2025-11-22': { type: 'exam', title: 'Math Final', subject: 'Math', color: 'pink', notes: '', files: [] },
    '2025-11-25': { type: 'quiz', title: 'Geography Quiz', subject: 'Geography', color: 'mint', notes: '', files: [] },
    '2025-11-28': { type: 'assignment', title: 'History Paper', subject: 'History', color: 'blue', notes: '', files: [] },
    '2025-11-30': { type: 'test', title: 'Chemistry Test', subject: 'Chemistry', color: 'lavender', notes: '', files: [] }
};

const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

function renderCalendar() {
    const calendarGrid = document.getElementById('calendarGrid');
    const monthHeader = document.getElementById('currentMonth');
    
    if (!calendarGrid || !monthHeader) return;
    
    monthHeader.textContent = `${monthNames[currentMonth]} ${currentYear}`;
    calendarGrid.innerHTML = '';
    
    const firstDay = new Date(currentYear, currentMonth, 1).getDay();
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    
    const today = new Date();
    const isCurrentMonth = today.getMonth() === currentMonth && today.getFullYear() === currentYear;
    const todayDate = today.getDate();
    
    for (let i = 0; i < firstDay; i++) {
        const emptyCell = document.createElement('div');
        calendarGrid.appendChild(emptyCell);
    }
    
    for (let day = 1; day <= daysInMonth; day++) {
        const dayCell = document.createElement('div');
        dayCell.className = 'calendar-day';
        
        const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const isToday = isCurrentMonth && day === todayDate;
        const hasEvent = examDates[dateStr];
        
        const rotations = [-1.5, -0.8, 0, 0.8, 1.5];
        const randomRotation = rotations[Math.floor(Math.random() * rotations.length)];
        
        if (isToday) {
            dayCell.style.background = 'linear-gradient(135deg, var(--pastel-pink), var(--pastel-lavender))';
            dayCell.style.borderColor = 'var(--pastel-pink-dark)';
            dayCell.style.transform = `rotate(0deg)`;
        } else if (hasEvent) {
            if (hasEvent.color === 'yellow') {
                dayCell.style.background = 'var(--pastel-yellow)';
                dayCell.style.borderColor = '#f9d671';
            } else if (hasEvent.color === 'pink') {
                dayCell.style.background = 'var(--pastel-pink)';
                dayCell.style.borderColor = 'var(--pastel-pink-dark)';
            } else if (hasEvent.color === 'mint') {
                dayCell.style.background = 'var(--pastel-mint)';
                dayCell.style.borderColor = '#b8e6c3';
            } else if (hasEvent.color === 'blue') {
                dayCell.style.background = 'var(--pastel-blue)';
                dayCell.style.borderColor = '#a8d5f5';
            } else if (hasEvent.color === 'lavender') {
                dayCell.style.background = 'var(--pastel-lavender)';
                dayCell.style.borderColor = '#d4bfff';
            }
            dayCell.style.borderStyle = 'dashed';
            dayCell.style.transform = `rotate(${randomRotation}deg)`;
        } else {
            dayCell.style.borderColor = 'var(--pastel-beige)';
            dayCell.style.transform = `rotate(${randomRotation}deg)`;
        }
        
        const dayNumber = document.createElement('div');
        dayNumber.className = 'calendar-day-number';
        dayNumber.style.color = isToday ? 'white' : 'var(--text-pink)';
        dayNumber.textContent = day;
        dayCell.appendChild(dayNumber);
        
        if (hasEvent) {
            const emoji = document.createElement('div');
            emoji.className = 'calendar-day-emoji';
            emoji.textContent = hasEvent.type === 'exam' ? '📝' : hasEvent.type === 'quiz' ? '✏️' : hasEvent.type === 'assignment' ? '📄' : '📚';
            dayCell.appendChild(emoji);
            
            const subject = document.createElement('div');
            subject.className = 'calendar-day-subject';
            subject.textContent = hasEvent.subject;
            subject.style.background = isToday ? 'rgba(255,255,255,0.3)' : 'rgba(255,255,255,0.7)';
            subject.style.color = isToday ? 'white' : 'var(--text-primary)';
            dayCell.appendChild(subject);
        }
        
        dayCell.addEventListener('mouseenter', function() {
            this.style.transform = 'rotate(0deg) translateY(-5px) scale(1.05)';
            this.style.zIndex = '10';
        });
        
        dayCell.addEventListener('mouseleave', function() {
            this.style.transform = `rotate(${randomRotation}deg) translateY(0) scale(1)`;
            this.style.zIndex = '1';
        });
        
        dayCell.addEventListener('click', function() {
            if (hasEvent) {
                let details = `📚 ${hasEvent.title}\n📖 Subject: ${hasEvent.subject}\n📅 ${dateStr}`;
                if (hasEvent.notes) details += `\n📔 Notes: ${hasEvent.notes}`;
                if (hasEvent.files && hasEvent.files.length > 0) details += `\n📎 Files: ${hasEvent.files.length} attached`;
                alert(details + '\n\nGood luck studying! ✨');
            }
        });
        
        calendarGrid.appendChild(dayCell);
    }
}

function changeMonth(delta) {
    currentMonth += delta;
    
    if (currentMonth > 11) {
        currentMonth = 0;
        currentYear++;
    } else if (currentMonth < 0) {
        currentMonth = 11;
        currentYear--;
    }
    
    renderCalendar();
}

function addExamToCalendar() {
    const name = document.getElementById('examName').value.trim();
    const subject = document.getElementById('examSubject').value.trim();
    const date = document.getElementById('examDate').value;
    const color = document.getElementById('examType').value;
    const notes = document.getElementById('examNotes').value.trim();
    const files = Array.from(document.getElementById('examFiles').files);
    
    if (!name || !subject || !date) {
        alert('❌ Please fill in exam name, subject and date!');
        return;
    }
    
    examDates[date] = {
        type: color === 'yellow' ? 'exam' : color === 'mint' ? 'quiz' : 'assignment',
        title: name,
        subject: subject,
        color: color,
        notes: notes,
        files: files.map(f => f.name)
    };
    
    document.getElementById('examName').value = '';
    document.getElementById('examSubject').value = '';
    document.getElementById('examDate').value = '';
    document.getElementById('examNotes').value = '';
    document.getElementById('examFiles').value = '';
    document.getElementById('filesList').innerHTML = '';
    
    const examDate = new Date(date);
    currentMonth = examDate.getMonth();
    currentYear = examDate.getFullYear();
    
    renderCalendar();
    
    let msg = `✨ ${name} added to calendar!\n📅 ${date}\n📚 Subject: ${subject}`;
    if (notes) msg += `\n📔 Notes saved`;
    if (files.length > 0) msg += `\n📎 ${files.length} file(s) attached`;
    alert(msg + '\n\nGood luck! 💖');
}

// File upload display for exam form
document.getElementById('examFiles')?.addEventListener('change', function(e) {
    const filesList = document.getElementById('filesList');
    const files = Array.from(e.target.files);
    if (files.length > 0) {
        filesList.innerHTML = '✅ ' + files.length + ' file(s) selected: ' + files.map(f => f.name).join(', ');
    } else {
        filesList.innerHTML = '';
    }
});

// ============ INITIALIZE APP ============
window.addEventListener('load', async function() {
    const token = localStorage.getItem('token');
    if (token) {
        currentToken = token;
        try {
            await loadUserProfile();
            showMainApp();
        } catch (error) {
            console.error('Auto-login failed:', error);
            localStorage.removeItem('token');
        }
    }
});

// Make functions globally available
window.sendMessage = sendMessage;
window.startLanguagePractice = startLanguagePractice;
window.generateQuiz = generateQuiz;
window.toggleForms = toggleForms;
window.showSection = showSection;
window.changeMonth = changeMonth;
window.addExamToCalendar = addExamToCalendar;
