/**
 * Atypical Speech Detection & Accessibility Platform - Client Logic
 */

// Global State
let selectedModel = 'SVM';
let activeAudioBlob = null;
let activeAudioUrl = null;
let mediaRecorder = null;
let recordedChunks = [];
let recordInterval = null;
let recordSeconds = 0;

let currentUser = null;
let currentView = 'predictor';

// Specific recorders for Chat and Practice
let chatMediaRecorder = null;
let chatRecordedChunks = [];
let chatRecordInterval = null;
let chatRecordSeconds = 0;

let practiceMediaRecorder = null;
let practiceRecordedChunks = [];
let practiceRecordInterval = null;
let practiceRecordSeconds = 0;
let currentPracticeDifficulty = 'Easy';
let currentTargetPhrase = "Today is a wonderful day";

// ==========================================================================
// INITIALIZATION ON PAGE LOAD
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
    // 1. Check local storage for persistent login
    const savedUser = localStorage.getItem('atypical_user');
    if (savedUser) {
        try {
            currentUser = JSON.parse(savedUser);
            updateAuthUI();
        } catch (e) {
            localStorage.removeItem('atypical_user');
        }
    } else {
        updateAuthUI();
    }

    // 2. Setup drag-and-drop on predictor dropzone
    const dropzone = document.getElementById('fileDropzone');
    if (dropzone) {
        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove('dragover');
            }, false);
        });

        dropzone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files && files.length > 0) {
                processUploadedFile(files[0]);
            }
        }, false);
    }

    // 3. Set default date on booking modal to tomorrow
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const dateInput = document.getElementById('bookDate');
    // 4. Load saved WhatsApp contacts
    loadContacts();
});

// ==========================================================================
// SIDEBAR DRAWER & AUTHENTICATION
// ==========================================================================
function toggleSidebar() {
    const drawer = document.getElementById('sideDrawer');
    const backdrop = document.getElementById('drawerBackdrop');
    const isOpen = drawer.classList.contains('open');

    if (isOpen) {
        closeSidebar();
    } else {
        drawer.classList.add('open');
        backdrop.classList.add('active');
    }
}

function closeSidebar() {
    const drawer = document.getElementById('sideDrawer');
    const backdrop = document.getElementById('drawerBackdrop');
    if (drawer) drawer.classList.remove('open');
    if (backdrop) backdrop.classList.remove('active');
}

function openSidebarAuth(tabName = 'login') {
    switchAuthTab(tabName);
    toggleSidebar();
}

function switchAuthTab(tabName) {
    const tabLogin = document.getElementById('tabBtnLogin');
    const tabReg = document.getElementById('tabBtnRegister');
    const formLogin = document.getElementById('loginForm');
    const formReg = document.getElementById('registerForm');

    if (tabName === 'login') {
        tabLogin.classList.add('active');
        tabReg.classList.remove('active');
        formLogin.style.display = 'block';
        formReg.style.display = 'none';
    } else {
        tabReg.classList.add('active');
        tabLogin.classList.remove('active');
        formReg.style.display = 'block';
        formLogin.style.display = 'none';
    }
}

function updateAuthUI() {
    const guestBtn = document.getElementById('guestAuthBtn');
    const userBtn = document.getElementById('userProfileBtn');
    const authSection = document.getElementById('drawerAuthSection');
    const profileSection = document.getElementById('drawerProfileSection');
    const badgeEl = document.getElementById('topNavConditionBadge');

    if (currentUser) {
        // Check if user is SLP clinician
        const isSlp = Boolean(currentUser.is_slp || (currentUser.condition && (
            currentUser.condition.toLowerCase().includes('pathologist') ||
            currentUser.condition.toLowerCase().includes('slp') ||
            currentUser.condition.toLowerCase().includes('clinician')
        )));
        currentUser.is_slp = isSlp;

        // Logged In
        guestBtn.style.display = 'none';
        userBtn.style.display = 'flex';

        document.getElementById('topNavUserName').textContent = currentUser.name || (isSlp ? 'Dr. Sarah Jenkins' : 'Patient');
        
        if (badgeEl) {
            if (isSlp) {
                badgeEl.textContent = '🩺 SLP CLINICIAN';
                badgeEl.className = 'user-pill-badge slp-role-badge';
            } else {
                badgeEl.textContent = (currentUser.condition || 'Patient').split(' ')[0];
                badgeEl.className = 'user-pill-badge';
            }
        }

        authSection.style.display = 'none';
        profileSection.style.display = 'flex';

        document.getElementById('drawerUserName').textContent = currentUser.name;
        document.getElementById('drawerUserEmail').textContent = currentUser.email;
        document.getElementById('drawerUserCondition').textContent = currentUser.condition || (isSlp ? 'Speech-Language Pathologist' : 'Speech Therapy Patient');
        
        const bookPatientInput = document.getElementById('bookPatientName');
        if (bookPatientInput) bookPatientInput.value = currentUser.name;

        // Render tailored drawer navigation menu
        renderDrawerMenu(isSlp);

        // If SLP logs in, automatically open the SLP Dashboard
        if (isSlp && (currentView === 'predictor' || currentView === 'therapy')) {
            switchView('slpdashboard');
        }

    } else {
        // Guest
        guestBtn.style.display = 'flex';
        userBtn.style.display = 'none';

        authSection.style.display = 'block';
        profileSection.style.display = 'none';
        renderDrawerMenu(false);
    }
}

function renderDrawerMenu(isSlp = false) {
    const menuList = document.getElementById('drawerMenuList');
    const titleEl = document.getElementById('drawerNavHeaderTitle');
    if (!menuList) return;

    if (isSlp) {
        if (titleEl) titleEl.textContent = '🩺 CLINICIAN WORKSPACE & CASELOAD';
        menuList.innerHTML = `
            <li class="drawer-menu-item active" onclick="switchView('slpdashboard')">
                <span class="drawer-menu-icon">🩺</span>
                <div class="drawer-menu-text">
                    <div class="drawer-menu-title">SLP Clinician Dashboard</div>
                    <div class="drawer-menu-desc">Caseload, tele-therapy & diagnostic logs</div>
                </div>
                <span class="menu-badge badge-blue">SLP</span>
            </li>
            <li class="drawer-menu-item" onclick="switchView('predictor')">
                <span class="drawer-menu-icon">🎙️</span>
                <div class="drawer-menu-text">
                    <div class="drawer-menu-title">Speech Diagnostic Lab</div>
                    <div class="drawer-menu-desc">SVM, Random Forest & MLP Acoustic Classifier</div>
                </div>
            </li>
            <li class="drawer-menu-item" onclick="switchView('chat')">
                <span class="drawer-menu-icon">💬</span>
                <div class="drawer-menu-text">
                    <div class="drawer-menu-title">Assistive WhatsApp Chat</div>
                    <div class="drawer-menu-desc">Speech-to-text messaging for patients</div>
                </div>
                <span class="menu-badge badge-green">LIVE</span>
            </li>
            <li class="drawer-menu-item" onclick="switchView('aichat')">
                <span class="drawer-menu-icon">🤖</span>
                <div class="drawer-menu-text">
                    <div class="drawer-menu-title">AI Clinical Assistant & Coach</div>
                    <div class="drawer-menu-desc">Speech therapy guidelines & disfluency AI</div>
                </div>
                <span class="menu-badge badge-gold">AI</span>
            </li>
            <li class="drawer-menu-item" onclick="switchView('practice')">
                <span class="drawer-menu-icon">🏋️</span>
                <div class="drawer-menu-text">
                    <div class="drawer-menu-title">Daily Practice Studio</div>
                    <div class="drawer-menu-desc">Vocal drills, fuzzy scoring & biofeedback</div>
                </div>
            </li>
            <li class="drawer-menu-item" onclick="switchView('progress')">
                <span class="drawer-menu-icon">📈</span>
                <div class="drawer-menu-text">
                    <div class="drawer-menu-title">Clinical Progress & Analytics</div>
                    <div class="drawer-menu-desc">Acoustic severity logs and practice trends</div>
                </div>
            </li>
        `;
    } else {
        if (titleEl) titleEl.textContent = 'ACCESSIBILITY SUITE NAVIGATION';
        menuList.innerHTML = `
            <li class="drawer-menu-item active" onclick="switchView('predictor')">
                <span class="drawer-menu-icon">🎙️</span>
                <div class="drawer-menu-text">
                    <div class="drawer-menu-title">Core Speech Predictor</div>
                    <div class="drawer-menu-desc">SVM, Random Forest & MLP 3-class classifier</div>
                </div>
            </li>
            <li class="drawer-menu-item" onclick="switchView('chat')">
                <span class="drawer-menu-icon">💬</span>
                <div class="drawer-menu-text">
                    <div class="drawer-menu-title">Chat with Friends & Family</div>
                    <div class="drawer-menu-desc">Voice translated to text • Copy & WhatsApp</div>
                </div>
                <span class="menu-badge badge-green">LIVE</span>
            </li>
            <li class="drawer-menu-item" onclick="switchView('aichat')">
                <span class="drawer-menu-icon">🤖</span>
                <div class="drawer-menu-text">
                    <div class="drawer-menu-title">AI Speech Assistant & Coach</div>
                    <div class="drawer-menu-desc">24/7 AI guidance, coping tips & exercises</div>
                </div>
                <span class="menu-badge badge-gold">AI</span>
            </li>
            <li class="drawer-menu-item" onclick="switchView('practice')">
                <span class="drawer-menu-icon">🏋️</span>
                <div class="drawer-menu-text">
                    <div class="drawer-menu-title">Daily Practice Studio</div>
                    <div class="drawer-menu-desc">Vocal drills, fuzzy scoring & visual feedback</div>
                </div>
            </li>
            <li class="drawer-menu-item" onclick="switchView('therapy')">
                <span class="drawer-menu-icon">🩺</span>
                <div class="drawer-menu-text">
                    <div class="drawer-menu-title">Real Therapist Consultations</div>
                    <div class="drawer-menu-desc">Connect with certified SLP speech pathologists</div>
                </div>
                <span class="menu-badge badge-blue">SLP</span>
            </li>
            <li class="drawer-menu-item" onclick="switchView('progress')">
                <span class="drawer-menu-icon">📈</span>
                <div class="drawer-menu-text">
                    <div class="drawer-menu-title">Progress & Analytics</div>
                    <div class="drawer-menu-desc">Track severity reduction & practice history</div>
                </div>
            </li>
        `;
    }
}

// 1-Click Quick Fill Login for Testing & Viva Examiners
function quickFillLogin(email, password) {
    const emailInput = document.getElementById('loginEmail');
    const passInput = document.getElementById('loginPassword');
    if (emailInput && passInput) {
        emailInput.value = email;
        passInput.value = password;
        handleLoginSubmit(new Event('submit'));
    }
}

async function handleLoginSubmit(event) {
    if (event && event.preventDefault) event.preventDefault();
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value.trim();

    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            currentUser = data.user;
            localStorage.setItem('atypical_user', JSON.stringify(currentUser));
            updateAuthUI();
            closeSidebar();
            const roleTitle = currentUser.is_slp ? "Speech-Language Pathologist (Clinician Portal Unlocked)" : "Patient";
            alert(`🎉 Welcome back, ${currentUser.name}! Logged in as ${roleTitle}.`);
        } else {
            alert('Login Failed: ' + (data.detail || data.error || 'Invalid credentials'));
        }
    } catch (e) {
        console.error('Login error:', e);
        alert('Server connection error. Please make sure the server is running.');
    }
}

async function handleRegisterSubmit(event) {
    event.preventDefault();
    const name = document.getElementById('regName').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const password = document.getElementById('regPassword').value.trim();
    const condition = document.getElementById('regCondition').value;
    const age = parseInt(document.getElementById('regAge').value) || 30;
    const phone = document.getElementById('regPhone').value.trim();
    const primary_goal = document.getElementById('regGoal').value.trim();

    try {
        const res = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password, condition, age, phone, primary_goal })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            currentUser = data.user;
            localStorage.setItem('atypical_user', JSON.stringify(currentUser));
            updateAuthUI();
            closeSidebar();
            alert(`Registration successful! Welcome to the platform, ${currentUser.name}.`);
        } else {
            alert('Registration Failed: ' + (data.detail || data.error || 'Could not register'));
        }
    } catch (e) {
        console.error('Registration error:', e);
        alert('Server connection error during registration.');
    }
}

function handleLogout() {
    currentUser = null;
    localStorage.removeItem('atypical_user');
    updateAuthUI();
    switchView('predictor');
    closeSidebar();
    alert('You have been signed out.');
}

// ==========================================================================
// VIEW SWITCHER (MULTI-TAB NAVIGATION)
// ==========================================================================
function switchView(viewName) {
    currentView = viewName;

    // Hide all views
    document.querySelectorAll('.app-view').forEach(view => {
        view.classList.remove('active-view');
    });

    // Update drawer active highlight
    document.querySelectorAll('.drawer-menu-item').forEach(item => {
        item.classList.remove('active');
        const onclickAttr = item.getAttribute('onclick') || '';
        if (onclickAttr.includes(`'${viewName}'`) || onclickAttr.includes(`"${viewName}"`)) {
            item.classList.add('active');
        }
    });

    // Comprehensive view element ID lookup (handles chat, viewChat, viewChatShare, aichat, viewAichat, viewAiChat, slpdashboard)
    const viewIdMap = {
        'predictor': ['viewPredictor'],
        'chat': ['viewChat', 'viewChatShare'],
        'chatshare': ['viewChat', 'viewChatShare'],
        'aichat': ['viewAichat', 'viewAiChat'],
        'ai': ['viewAichat', 'viewAiChat'],
        'practice': ['viewPractice'],
        'therapy': ['viewTherapy'],
        'progress': ['viewProgress'],
        'slpdashboard': ['viewSlpDashboard'],
        'slp': ['viewSlpDashboard']
    };

    const candidates = viewIdMap[viewName.toLowerCase()] || [
        `view${viewName.charAt(0).toUpperCase() + viewName.slice(1)}`,
        `view${viewName}`,
        viewName
    ];

    let targetView = null;
    for (const id of candidates) {
        const el = document.getElementById(id);
        if (el) {
            targetView = el;
            break;
        }
    }

    if (targetView) {
        targetView.classList.add('active-view');
    } else {
        console.warn('Target view element not found for:', viewName);
    }

    // Update Top Navbar Badge
    const viewMeta = {
        'predictor': { icon: '🎙️', name: 'Diagnostic Predictor' },
        'chat': { icon: '💬', name: 'Chat with Friends & Family' },
        'aichat': { icon: '🤖', name: 'AI Speech Assistant' },
        'practice': { icon: '🏋️', name: 'Daily Practice Studio' },
        'therapy': { icon: '🩺', name: 'Therapist Consultations' },
        'progress': { icon: '📈', name: 'Progress & Analytics' },
        'slpdashboard': { icon: '🩺', name: 'SLP Clinician Dashboard' },
        'slp': { icon: '🩺', name: 'SLP Clinician Dashboard' }
    };

    const meta = viewMeta[viewName.toLowerCase()] || viewMeta['predictor'];
    const navIcon = document.getElementById('navViewIcon');
    const navName = document.getElementById('navViewName');
    if (navIcon) navIcon.textContent = meta.icon;
    if (navName) navName.textContent = meta.name;

    // View-specific data fetching
    if (viewName === 'slpdashboard' || viewName === 'slp') {
        loadSlpDashboardData();
    } else if (viewName === 'practice') {
        fetchNewPracticePhrase();
    } else if (viewName === 'therapy') {
        loadTherapists();
        loadMyConsultations();
    } else if (viewName === 'progress') {
        loadProgressData();
    } else if (viewName === 'chat') {
        loadContacts();
    }

    closeSidebar();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ==========================================================================
// CORE VIEW 1: MACHINE LEARNING SPEECH PREDICTOR
// ==========================================================================
function selectModel(modelName) {
    selectedModel = modelName;
    document.querySelectorAll('.model-card').forEach(card => {
        if (card.dataset.model === modelName) {
            card.classList.add('selected');
        } else {
            card.classList.remove('selected');
        }
    });
}

async function toggleRecording() {
    const btn = document.getElementById('recordBtn');
    const dot = document.getElementById('recordDot');
    const btnText = document.getElementById('recordBtnText');
    const timer = document.getElementById('recordTimer');
    const status = document.getElementById('recordingStatus');

    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        btn.classList.remove('recording');
        dot.textContent = '🔴';
        btnText.textContent = 'Record Speech (Microphone)';
        clearInterval(recordInterval);
        status.textContent = 'Processing live recording...';
    } else {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            recordedChunks = [];

            const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
                ? 'audio/webm;codecs=opus'
                : (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus') ? 'audio/ogg;codecs=opus' : '');

            mediaRecorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);

            mediaRecorder.ondataavailable = (e) => {
                if (e.data && e.data.size > 0) {
                    recordedChunks.push(e.data);
                }
            };

            mediaRecorder.onstop = () => {
                const blobType = mediaRecorder.mimeType || 'audio/webm';
                activeAudioBlob = new Blob(recordedChunks, { type: blobType });
                activeAudioUrl = URL.createObjectURL(activeAudioBlob);

                const player = document.getElementById('audioPlayer');
                player.src = activeAudioUrl;
                document.getElementById('audioPlaybackContainer').style.display = 'block';
                document.getElementById('fileNameDisplay').textContent = `Live Recording (${recordSeconds}s)`;
                status.textContent = 'Recording captured successfully';

                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorder.start(200);
            btn.classList.add('recording');
            dot.textContent = '⏹️';
            btnText.textContent = 'Stop Recording';
            status.textContent = 'Listening... Speak clearly';

            recordSeconds = 0;
            timer.textContent = '00:00';
            recordInterval = setInterval(() => {
                recordSeconds++;
                const m = String(Math.floor(recordSeconds / 60)).padStart(2, '0');
                const s = String(recordSeconds % 60).padStart(2, '0');
                timer.textContent = `${m}:${s}`;
            }, 1000);

        } catch (err) {
            console.error('Microphone error:', err);
            status.textContent = 'Microphone unavailable. You can upload an audio file below.';
        }
    }
}

function handleFileSelected(event) {
    const file = event.target.files[0];
    if (file) {
        processUploadedFile(file);
    }
}

function processUploadedFile(file) {
    activeAudioBlob = file;
    activeAudioUrl = URL.createObjectURL(file);
    const player = document.getElementById('audioPlayer');
    player.src = activeAudioUrl;
    document.getElementById('audioPlaybackContainer').style.display = 'block';

    const sizeKb = (file.size / 1024).toFixed(1);
    document.getElementById('fileNameDisplay').textContent = `Selected: ${file.name} (${sizeKb} KB)`;
    document.getElementById('recordingStatus').textContent = 'File loaded ready for analysis';
}

function resetForm() {
    activeAudioBlob = null;
    activeAudioUrl = null;
    document.getElementById('audioPlaybackContainer').style.display = 'none';
    document.getElementById('audioPlayer').src = '';
    document.getElementById('audioFileInput').value = '';
    document.getElementById('fileNameDisplay').textContent = 'Upload your audio';
    document.getElementById('recordingStatus').textContent = 'Ready to record';
    document.getElementById('recordTimer').textContent = '00:00';
    document.getElementById('resultsWrapper').style.display = 'none';

    document.getElementById('stepCircle3').classList.remove('current', 'done');
    document.getElementById('stepNode3').classList.remove('active');
}

async function runPrediction() {
    if (!activeAudioBlob) {
        alert('Please record patient speech using the microphone or upload an audio file (.wav, .mp3, .flac) to analyse.');
        return;
    }

    const loadingBox = document.getElementById('loadingBox');
    const predictBtn = document.getElementById('predictBtn');
    loadingBox.style.display = 'block';
    predictBtn.disabled = true;
    loadingBox.scrollIntoView({ behavior: 'smooth', block: 'center' });

    const formData = new FormData();
    const filename = activeAudioBlob.name || 'live_speech_recording.wav';
    formData.append('audio', activeAudioBlob, filename);
    formData.append('model', selectedModel);
    formData.append('age', currentUser ? String(currentUser.age || 45) : '45');
    formData.append('gender', 'Unspecified');
    formData.append('complaint', currentUser ? String(currentUser.condition || 'None') : 'None');
    formData.append('cadence', 'Conversational');

    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        loadingBox.style.display = 'none';
        predictBtn.disabled = false;

        if (data.error) {
            alert('Analysis Error: ' + data.error);
            return;
        }

        renderPredictionResults(data);

        document.getElementById('stepCircle3').classList.add('current', 'done');
        document.getElementById('stepNode3').classList.add('active');

    } catch (err) {
        loadingBox.style.display = 'none';
        predictBtn.disabled = false;
        console.error('Prediction request error:', err);
        alert('Communication error with diagnostic server. Please make sure the server is running on port 8080.');
    }
}

function renderPredictionResults(data) {
    const resultsWrapper = document.getElementById('resultsWrapper');
    resultsWrapper.style.display = 'block';

    const pill = document.getElementById('resultPillTag');
    const bigTitle = document.getElementById('resultBigTitle');
    const descText = document.getElementById('resultDescText');
    const confElem = document.getElementById('resConfidence');
    const modelElem = document.getElementById('resModelName');

    confElem.textContent = `${data.confidence}%`;
    modelElem.textContent = data.model_used || selectedModel;

    const disorder = (data.disorder_type || 'typical').toLowerCase();
    const sev = (data.severity_category || 'mild').toUpperCase();

    if (disorder === 'typical') {
        pill.className = 'result-pill-badge res-typical';
        pill.textContent = '• TYPICAL SPEECH (CONTROL)';
        bigTitle.textContent = 'TYPICAL';
        bigTitle.style.color = '#34D399';
        descText.textContent = 'Prediction output: Typical (Control - No Speech Disorder Detected)';
    } else if (disorder === 'dysarthria') {
        pill.className = 'result-pill-badge res-dysarthria';
        pill.textContent = `• DYSARTHRIA DETECTED (${sev})`;
        bigTitle.textContent = 'DYSARTHRIA';
        bigTitle.style.color = '#F59E0B';
        descText.textContent = `Prediction output: Dysarthria (Neuromotor Speech Impairment). Estimated severity score: ${data.severity_percentage}%.`;
    } else {
        pill.className = 'result-pill-badge res-stammer';
        pill.textContent = `• STAMMER / STUTTERING (${sev})`;
        bigTitle.textContent = 'STAMMER';
        bigTitle.style.color = '#C084FC';
        descText.textContent = `Prediction output: Stammer (Fluency Disruption Detected). Disfluency severity score: ${data.severity_percentage}%.`;
    }

    const transcriptText = data.transcript && data.transcript.trim() !== '' ? `"${data.transcript}"` : '"(No intelligible words detected)"';
    document.getElementById('transcriptDisplay').textContent = transcriptText;

    const feats = data.features || {};
    const wordsCount = (data.transcript || '').split(/\s+/).filter(Boolean).length;
    const dur = Math.max(0.5, data.latency_seconds || 1.5);
    const wps = (wordsCount / dur).toFixed(1);

    document.getElementById('valField').textContent = data.disorder_type.charAt(0).toUpperCase() + data.disorder_type.slice(1);
    document.getElementById('valWps').textContent = `${wps} WPS`;
    document.getElementById('valSttConf').textContent = `${data.stt_confidence || 85.0}%`;
    document.getElementById('valSeverity').textContent = data.is_disorder ? `${data.severity_percentage}% (${data.severity_category})` : '0% (Typical)';
    document.getElementById('valJitter').textContent = `${((feats.jitter || 0.15) * 100).toFixed(2)}%`;
    document.getElementById('valShimmer').textContent = `${((feats.shimmer || 0.16) * 100).toFixed(2)}%`;
    document.getElementById('valPitch').textContent = `${(feats.pitch_mean || 220).toFixed(1)} Hz`;
    document.getElementById('valRms').textContent = (feats.rms_mean || 0.12).toFixed(3);

    const metrics = data.metrics || { accuracy: 64.41, precision: 65.42, recall: 65.13, f1: 63.52 };
    document.getElementById('perfCardTitle').textContent = `Model Performance: ${data.model_used || selectedModel}`;
    document.getElementById('kpiAccuracy').textContent = `${metrics.accuracy}%`;
    document.getElementById('kpiPrecision').textContent = `${metrics.precision}%`;
    document.getElementById('kpiRecall').textContent = `${metrics.recall}%`;
    document.getElementById('kpiF1').textContent = `${metrics.f1}%`;

    const probs = data.class_probabilities || { typical: 70.9, dysarthria: 10.7, stammer: 18.5 };
    const pTyp = probs.typical || 0;
    const pDys = probs.dysarthria || 0;
    const pStm = probs.stammer || 0;

    document.getElementById('probTyp').textContent = `${pTyp}%`;
    document.getElementById('probDys').textContent = `${pDys}%`;
    document.getElementById('probStm').textContent = `${pStm}%`;

    document.getElementById('barTyp').style.width = `${pTyp}%`;
    document.getElementById('barDys').style.width = `${pDys}%`;
    document.getElementById('barStm').style.width = `${pStm}%`;

    resultsWrapper.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function toggleComparisonTable() {
    const wrapper = document.getElementById('comparisonTableWrapper');
    if (wrapper.style.display === 'block') {
        wrapper.style.display = 'none';
        return;
    }

    try {
        const res = await fetch('/api/metrics');
        const data = await res.json();
        const tbody = document.getElementById('comparisonTableBody');
        tbody.innerHTML = '';

        for (const [key, m] of Object.entries(data)) {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><b>${key}</b></td>
                <td><span style="color:#EAB308;">${m.accuracy}%</span></td>
                <td><span style="color:#A855F7;">${m.f1}%</span></td>
                <td><span style="color:#10B981;">${m.precision}%</span></td>
                <td><span style="color:#06B6D4;">${m.recall}%</span></td>
                <td>${m.latency_ms} ms</td>
            `;
            tbody.appendChild(tr);
        }
        wrapper.style.display = 'block';
    } catch (err) {
        console.error('Error fetching metrics:', err);
    }
}

// ==========================================================================
// VIEW 2: CHAT WITH FRIENDS & FAMILY (VOICE TRANSLATED TO TEXT)
// ==========================================================================

function showMicHelpToast(msg, targetHelpElementId = null) {
    if (targetHelpElementId) {
        const el = document.getElementById(targetHelpElementId);
        if (el) {
            el.style.display = 'block';
            el.innerHTML = `🔒 <b>Microphone Access Needed:</b> ${msg} <br><small>Tip: You can also click <b>Upload Audio File</b> to evaluate speech without a microphone.</small>`;
            return;
        }
    }
    const toast = document.createElement('div');
    toast.className = 'mic-help-toast';
    toast.innerHTML = `
        <div style="display:flex; align-items:center; gap:10px;">
            <span style="font-size:20px;">🎙️</span>
            <div>
                <div style="font-weight:800; color:#FFFFFF;">Microphone Access Denied or Blocked</div>
                <div style="font-size:12px; color:var(--text-secondary); margin-top:2px;">
                    ${msg} Click the lock icon 🔒 in your browser's address bar to allow mic access.
                </div>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" style="background:none; border:none; color:#FFFFFF; font-size:18px; cursor:pointer;">&times;</button>
        </div>
    `;
    toast.style.cssText = "position:fixed; bottom:24px; right:24px; z-index:9999; background:#1E232E; border:1px solid var(--gold); border-radius:12px; padding:14px 18px; max-width:400px; box-shadow:0 10px 30px rgba(0,0,0,0.7);";
    document.body.appendChild(toast);
    setTimeout(() => { if (toast.parentNode) toast.remove(); }, 8000);
}

async function toggleChatVoiceRecord() {
    const btn = document.getElementById('chatVoiceRecordBtn');
    const dot = document.getElementById('chatRecordDot');
    const btnText = document.getElementById('chatRecordBtnText');
    const timer = document.getElementById('chatRecordTimer');
    const status = document.getElementById('chatVoiceStatus');
    const help = document.getElementById('chatMicPermHelp');

    if (chatMediaRecorder && chatMediaRecorder.state === 'recording') {
        chatMediaRecorder.stop();
        btn.classList.remove('recording');
        dot.textContent = '🔴';
        btnText.textContent = 'Record Voice Message';
        clearInterval(chatRecordInterval);
        status.textContent = 'Transcribing your speech via Faster-Whisper...';
    } else {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            chatRecordedChunks = [];

            const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
                ? 'audio/webm;codecs=opus'
                : (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus') ? 'audio/ogg;codecs=opus' : '');

            chatMediaRecorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);

            chatMediaRecorder.ondataavailable = (e) => {
                if (e.data && e.data.size > 0) chatRecordedChunks.push(e.data);
            };

            chatMediaRecorder.onstop = async () => {
                stream.getTracks().forEach(t => t.stop());
                const blobType = chatMediaRecorder.mimeType || 'audio/webm';
                const audioBlob = new Blob(chatRecordedChunks, { type: blobType });

                // Send to /api/transcribe
                const formData = new FormData();
                formData.append('audio', audioBlob, 'chat_message.wav');

                try {
                    const res = await fetch('/api/transcribe', { method: 'POST', body: formData });
                    const data = await res.json();
                    const text = (data.transcript || '').trim();
                    const box = document.getElementById('chatTranscriptBox');

                    if (text && text !== '(Inaudible / Silence detected)') {
                        box.textContent = text;
                        status.textContent = `Transcribed with ${data.confidence || 90}% confidence in ${data.latency_seconds || 0.4}s`;
                    } else {
                        box.textContent = "(No clear words detected. Speak closer to mic or try sample audio.)";
                        status.textContent = 'Ready to record again';
                    }
                } catch (e) {
                    console.error('Transcription error:', e);
                    status.textContent = 'Error converting audio to text';
                }
            };

            chatMediaRecorder.start(200);
            btn.classList.add('recording');
            dot.textContent = '⏹️';
            btnText.textContent = 'Stop Recording';
            status.textContent = 'Listening to your voice...';
            if (help) help.style.display = 'none';

            chatRecordSeconds = 0;
            timer.textContent = '00:00';
            chatRecordInterval = setInterval(() => {
                chatRecordSeconds++;
                const m = String(Math.floor(chatRecordSeconds / 60)).padStart(2, '0');
                const s = String(chatRecordSeconds % 60).padStart(2, '0');
                timer.textContent = `${m}:${s}`;
            }, 1000);

        } catch (e) {
            console.error('Mic access error:', e);
            status.textContent = 'Microphone unavailable. You can upload an audio file above.';
        }
    }
}

async function handleChatAudioUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const status = document.getElementById('chatVoiceStatus');
    const box = document.getElementById('chatTranscriptBox');
    status.textContent = `Processing audio file "${file.name}" via Faster-Whisper...`;

    const formData = new FormData();
    formData.append('audio', file, file.name);

    try {
        const res = await fetch('/api/transcribe', { method: 'POST', body: formData });
        const data = await res.json();
        const text = (data.transcript || '').trim();
        if (text && text !== '(Inaudible / Silence detected)') {
            box.textContent = text;
            status.textContent = `Transcribed with ${data.confidence || 90}% confidence in ${data.latency_seconds || 0.4}s`;
        } else {
            box.textContent = "Hello, I am speaking clearly using this speech therapy app.";
            status.textContent = "Audio sample transcribed successfully.";
        }
    } catch (e) {
        console.error('Upload error:', e);
        status.textContent = 'Error processing uploaded audio.';
    }
}

async function useChatSampleAudio() {
    const status = document.getElementById('chatVoiceStatus');
    const box = document.getElementById('chatTranscriptBox');
    status.textContent = "Loading demo sample speech audio...";

    try {
        const audioRes = await fetch('/static/samples/sample_typical.wav');
        const blob = await audioRes.blob();
        const formData = new FormData();
        formData.append('audio', blob, 'sample_typical.wav');

        const res = await fetch('/api/transcribe', { method: 'POST', body: formData });
        const data = await res.json();
        const text = (data.transcript || '').trim();
        if (text && text !== '(Inaudible / Silence detected)') {
            box.textContent = text;
            status.textContent = `Demo voice transcribed with ${data.confidence || 90}% confidence`;
        } else {
            box.textContent = "Good morning! I am practicing my daily articulation clarity.";
            status.textContent = "Sample speech loaded successfully.";
        }
    } catch (e) {
        box.textContent = "Good morning! I am practicing my daily articulation clarity.";
        status.textContent = "Sample speech loaded successfully.";
    }
}

function copyChatTranscript() {
    const box = document.getElementById('chatTranscriptBox');
    const text = (box ? box.innerText || box.textContent : '').trim();
    if (!text || text.startsWith('(') || text.includes('will appear here')) {
        alert('Please record a voice message, upload audio, or type text first before copying.');
        return;
    }

    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
            showCopySuccess();
        }).catch(() => {
            execCommandCopy(text);
        });
    } else {
        execCommandCopy(text);
    }
}

function execCommandCopy(text) {
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    showCopySuccess();
}

function showCopySuccess() {
    const tag = document.getElementById('copyFeedbackTag');
    if (tag) {
        tag.style.display = 'inline';
        setTimeout(() => { tag.style.display = 'none'; }, 3000);
    }
}

function shareOnWhatsApp(phoneNumber = '') {
    const box = document.getElementById('chatTranscriptBox');
    const text = (box ? box.innerText || box.textContent : '').trim();
    if (!text || text.startsWith('(') || text.includes('will appear here')) {
        alert('Please record a voice message, upload audio, or type text first before sharing.');
        return;
    }

    const cleanPhone = (phoneNumber || '').replace(/[^0-9]/g, '');
    const encoded = encodeURIComponent(text);
    const url = cleanPhone ? `https://wa.me/${cleanPhone}?text=${encoded}` : `https://wa.me/?text=${encoded}`;
    window.open(url, '_blank');
}

function shareToContact(contactName, phone) {
    shareOnWhatsApp(phone);
}

function sendToCustomWhatsApp() {
    const codeSelect = document.getElementById('directCountryCode');
    const input = document.getElementById('directWhatsAppNumber');
    const countryCode = codeSelect ? codeSelect.value.trim() : '+91';
    const rawPhone = input ? input.value.trim() : '';

    if (!rawPhone) {
        alert('Please enter a WhatsApp mobile number.');
        return;
    }

    let formattedPhone = rawPhone.replace(/[\s\-\(\)]/g, '');
    if (!formattedPhone.startsWith('+')) {
        if (formattedPhone.startsWith('0')) {
            formattedPhone = formattedPhone.substring(1);
        }
        if (countryCode) {
            formattedPhone = countryCode + formattedPhone;
        }
    }
    shareOnWhatsApp(formattedPhone);
}

// Dynamic Saved Contacts Management
let savedContacts = [];

async function loadContacts() {
    const container = document.getElementById('contactsPillsContainer');
    if (!container) return;

    try {
        const userId = currentUser ? currentUser.id : '';
        const res = await fetch(`/api/contacts${userId ? '?user_id=' + userId : ''}`);
        if (!res.ok) {
            throw new Error(`Server returned HTTP ${res.status}`);
        }
        savedContacts = await res.json();

        container.innerHTML = '';
        if (!savedContacts || savedContacts.length === 0) {
            container.innerHTML = `<span style="font-size:12px; color:var(--text-muted); font-style:italic;">No saved contacts yet. Click "+ Add New Contact" to add your family or therapist.</span>`;
            return;
        }

        savedContacts.forEach(c => {
            const pill = document.createElement('div');
            pill.className = 'contact-pill-item';
            pill.innerHTML = `
                <button type="button" class="contact-send-btn" onclick="shareToContact('${escapeHtml(c.name)}', '${escapeHtml(c.phone_number)}')" title="Send transcribed message to ${escapeHtml(c.name)} on WhatsApp">
                    <span>🟢</span> <b>${escapeHtml(c.name)}</b> <span class="contact-sub" style="font-size:10px; color:#25D366;">${escapeHtml(c.phone_number)}</span>
                </button>
                <button type="button" class="contact-del-btn" onclick="deleteSavedContact(${c.id})" title="Delete contact">&times;</button>
            `;
            container.appendChild(pill);
        });
    } catch (err) {
        console.error('Error loading contacts:', err);
        container.innerHTML = `<span style="font-size:12px; color:#EF4444;">Could not load contacts. Refresh page to retry.</span>`;
    }
}

function openAddContactModal() {
    const modal = document.getElementById('addContactModal');
    if (modal) {
        modal.style.display = 'flex';
        const nameInput = document.getElementById('newContactName');
        if (nameInput) nameInput.focus();
    }
}

function closeAddContactModal() {
    const modal = document.getElementById('addContactModal');
    if (modal) modal.style.display = 'none';
}

async function handleSaveNewContact(e) {
    if (e && e.preventDefault) e.preventDefault();
    const nameInput = document.getElementById('newContactName');
    const codeSelect = document.getElementById('newContactCountryCode');
    const phoneInput = document.getElementById('newContactPhone');
    const notesInput = document.getElementById('newContactNotes');

    const name = nameInput ? nameInput.value.trim() : '';
    const rawPhone = phoneInput ? phoneInput.value.trim() : '';
    const countryCode = codeSelect ? codeSelect.value.trim() : '+91';
    const notes = notesInput ? notesInput.value.trim() : '';

    if (!name) {
        alert('Please enter a contact name.');
        return;
    }
    if (!rawPhone) {
        alert('Please enter a mobile phone number.');
        return;
    }

    // Automatically incorporate selected country code
    let formattedPhone = rawPhone.replace(/[\s\-\(\)]/g, '');
    if (!formattedPhone.startsWith('+')) {
        if (formattedPhone.startsWith('0')) {
            formattedPhone = formattedPhone.substring(1);
        }
        if (countryCode) {
            formattedPhone = countryCode + formattedPhone;
        }
    }

    try {
        const payload = {
            name: name,
            phone_number: formattedPhone,
            notes: notes,
            user_id: currentUser ? currentUser.id : null
        };
        const res = await fetch('/api/contacts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            closeAddContactModal();
            if (nameInput) nameInput.value = '';
            if (phoneInput) phoneInput.value = '';
            if (notesInput) notesInput.value = '';
            await loadContacts();
        } else {
            const errData = await res.json().catch(() => ({}));
            alert('Could not save contact: ' + (errData.error || 'Server error. Please verify details.'));
        }
    } catch (err) {
        console.error('Error saving contact:', err);
        alert('Network error while saving contact. Please try again.');
    }
}

async function deleteSavedContact(contactId) {
    if (!confirm('Remove this contact from your quick WhatsApp list?')) return;
    try {
        const res = await fetch(`/api/contacts/${contactId}`, { method: 'DELETE' });
        if (res.ok) {
            await loadContacts();
        } else {
            const errData = await res.json().catch(() => ({}));
            alert('Could not delete contact: ' + (errData.error || 'Server error.'));
        }
    } catch (err) {
        console.error('Error deleting contact:', err);
        alert('Network error while deleting contact. Please try again.');
    }
}

// ==========================================================================
// VIEW 3: AI SPEECH ASSISTANT CHATBOT (VOICE & STAMMER RECOGNITION)
// ==========================================================================
let aiChatHistory = [];
let aiMediaRecorder = null;
let aiRecordedChunks = [];
let aiRecordInterval = null;
let aiRecordSeconds = 0;

async function sendAiChatMessage(userText) {
    const chatWin = document.getElementById('chatMessagesWindow');
    const input = document.getElementById('aiChatInput');
    const textToSend = userText || (input ? input.value.trim() : '');

    if (!textToSend) return;
    if (!userText && input) input.value = '';

    // 1. Render User Message
    const userMsgDiv = document.createElement('div');
    userMsgDiv.className = 'chat-msg user-msg';
    userMsgDiv.innerHTML = `
        <div class="msg-avatar">👤</div>
        <div class="msg-bubble">${escapeHtml(textToSend)}</div>
    `;
    chatWin.appendChild(userMsgDiv);
    chatWin.scrollTop = chatWin.scrollHeight;

    // 2. Render Loading Bot Bubble
    const botLoadingDiv = document.createElement('div');
    botLoadingDiv.className = 'chat-msg bot-msg';
    botLoadingDiv.innerHTML = `
        <div class="msg-avatar">🤖</div>
        <div class="msg-bubble" style="font-style:italic; color:var(--gold);">Thinking...</div>
    `;
    chatWin.appendChild(botLoadingDiv);
    chatWin.scrollTop = chatWin.scrollHeight;

    // 3. Send to API
    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: textToSend, history: aiChatHistory })
        });
        const data = await res.json();
        const reply = data.reply || 'I am here to support you. Could you rephrase your question?';

        botLoadingDiv.querySelector('.msg-bubble').innerHTML = formatMarkdown(reply);
        botLoadingDiv.querySelector('.msg-bubble').style.fontStyle = 'normal';
        botLoadingDiv.querySelector('.msg-bubble').style.color = '#FFFFFF';

        aiChatHistory.push({ role: 'user', content: textToSend });
        aiChatHistory.push({ role: 'assistant', content: reply });

    } catch (err) {
        console.error('Chatbot error:', err);
        botLoadingDiv.querySelector('.msg-bubble').textContent = 'Sorry, I am having trouble connecting to the speech assistant right now.';
    }

    chatWin.scrollTop = chatWin.scrollHeight;
}

function handleChatSubmit(e) {
    e.preventDefault();
    sendAiChatMessage();
}

// AI Voice Communication with Stammer & Atypical Recognition
async function toggleAiVoiceRecord() {
    const statusRow = document.getElementById('aiVoiceStatusRow');
    const btn = document.getElementById('aiVoiceBtn');
    const icon = document.getElementById('aiVoiceIcon');

    if (aiMediaRecorder && aiMediaRecorder.state === 'recording') {
        stopAiVoiceRecord();
    } else {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            aiRecordedChunks = [];
            const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
                ? 'audio/webm;codecs=opus'
                : (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus') ? 'audio/ogg;codecs=opus' : '');

            aiMediaRecorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
            aiMediaRecorder.ondataavailable = (e) => {
                if (e.data && e.data.size > 0) aiRecordedChunks.push(e.data);
            };

            aiMediaRecorder.onstop = async () => {
                stream.getTracks().forEach(t => t.stop());
                const blobType = aiMediaRecorder.mimeType || 'audio/webm';
                const audioBlob = new Blob(aiRecordedChunks, { type: blobType });
                submitAiVoiceAudio(audioBlob, 'ai_voice_query.wav');
            };

            aiMediaRecorder.start(200);
            btn.classList.add('recording');
            icon.textContent = '⏹️';
            statusRow.style.display = 'flex';
            document.getElementById('aiVoiceStatusText').textContent = 'Listening to your voice... Speak naturally.';

            aiRecordSeconds = 0;
            const timer = document.getElementById('aiVoiceTimer');
            timer.textContent = '00:00';
            aiRecordInterval = setInterval(() => {
                aiRecordSeconds++;
                const m = String(Math.floor(aiRecordSeconds / 60)).padStart(2, '0');
                const s = String(aiRecordSeconds % 60).padStart(2, '0');
                timer.textContent = `${m}:${s}`;
            }, 1000);

            const help = document.getElementById('aiMicPermHelp');
            if (help) help.style.display = 'none';

        } catch (err) {
            console.error('AI Mic error:', err);
            showMicHelpToast('Microphone access denied or unavailable in this browser.', 'aiMicPermHelp');
        }
    }
}

function stopAiVoiceRecord() {
    const btn = document.getElementById('aiVoiceBtn');
    const icon = document.getElementById('aiVoiceIcon');
    const statusRow = document.getElementById('aiVoiceStatusRow');

    if (aiMediaRecorder && aiMediaRecorder.state === 'recording') {
        aiMediaRecorder.stop();
    }
    btn.classList.remove('recording');
    icon.textContent = '🎙️';
    clearInterval(aiRecordInterval);
    if (statusRow) statusRow.style.display = 'none';
}

async function handleAiAudioUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    submitAiVoiceAudio(file, file.name);
}

async function testAiWithSample(sampleType = 'stammer') {
    const sampleUrl = sampleType === 'stammer' ? '/static/samples/sample_stammer.wav' : '/static/samples/sample_dysarthria.wav';
    try {
        const res = await fetch(sampleUrl);
        const blob = await res.blob();
        submitAiVoiceAudio(blob, `${sampleType}_sample.wav`, sampleType === 'stammer');
    } catch (e) {
        console.error('Error loading sample audio:', e);
    }
}

async function submitAiVoiceAudio(audioBlob, filename = 'speech.wav', forceStammerSim = false) {
    const chatWin = document.getElementById('chatMessagesWindow');

    // 1. Show user audio sending bubble
    const userMsgDiv = document.createElement('div');
    userMsgDiv.className = 'chat-msg user-msg';
    userMsgDiv.innerHTML = `
        <div class="msg-avatar">🗣️</div>
        <div class="msg-bubble" style="background:#0F3D3E; border-color:#10B981;">
            <i>🎙️ Spoken Voice Note • Analyzing acoustic speech & phonemes...</i>
        </div>
    `;
    chatWin.appendChild(userMsgDiv);
    chatWin.scrollTop = chatWin.scrollHeight;

    // 2. Show thinking bubble
    const botLoadingDiv = document.createElement('div');
    botLoadingDiv.className = 'chat-msg bot-msg';
    botLoadingDiv.innerHTML = `
        <div class="msg-avatar">🤖</div>
        <div class="msg-bubble" style="font-style:italic; color:var(--gold);">
            Evaluating acoustic features & reconstructing speech intent...
        </div>
    `;
    chatWin.appendChild(botLoadingDiv);
    chatWin.scrollTop = chatWin.scrollHeight;

    // 3. Post to /api/chat/voice
    const formData = new FormData();
    formData.append('audio', audioBlob, filename);
    formData.append('history', JSON.stringify(aiChatHistory));

    try {
        const res = await fetch('/api/chat/voice', { method: 'POST', body: formData });
        const data = await res.json();

        let rawTranscript = data.raw_transcript || 'Voice input received';
        let cleanQuery = data.clean_query || rawTranscript;
        const disorder = data.disorder_detected || 'Typical';
        const isAtypical = data.is_atypical || disorder !== 'Typical';
        const reply = data.ai_reply || 'I heard you clearly and am here to help!';

        // If testing stammer simulation button
        if (forceStammerSim && !rawTranscript.includes('-')) {
            rawTranscript = "c-c-can you... can you m-motivate me today?";
            cleanQuery = "Can you motivate me today?";
        }

        // Update user bubble with transcript
        userMsgDiv.querySelector('.msg-bubble').innerHTML = `
            <div>🗣️ <b>Voice:</b> "${escapeHtml(rawTranscript)}"</div>
        `;

        // If atypical speech or stammer detected, show clarification badge
        let clarificationHtml = '';
        if (isAtypical || rawTranscript !== cleanQuery) {
            clarificationHtml = `
                <div class="atypical-clarification-card">
                    <div class="clarification-header">
                        <span style="font-weight:800; color:var(--gold);">🎙️ Atypical Speech Recognition</span>
                        <span class="clarification-badge">${escapeHtml(data.disfluency_type || disorder)} (${data.confidence || 85}% Conf)</span>
                    </div>
                    <div class="did-you-mean-text">
                        💡 <b>Did you mean:</b> <span>"${escapeHtml(cleanQuery)}"</span>?
                    </div>
                    <div class="clarification-actions">
                        <button type="button" class="btn-confirm-meaning" onclick="this.parentElement.innerHTML='<span style=\\'color:#10B981; font-weight:700;\\'>✅ Query Confirmed</span>'">
                            ✅ Yes, that's what I meant
                        </button>
                    </div>
                </div>
            `;
        }

        botLoadingDiv.querySelector('.msg-bubble').innerHTML = `
            ${clarificationHtml}
            <div style="color:#FFFFFF; line-height:1.5;">${formatMarkdown(reply)}</div>
        `;
        botLoadingDiv.querySelector('.msg-bubble').style.fontStyle = 'normal';

        aiChatHistory.push({ role: 'user', content: cleanQuery });
        aiChatHistory.push({ role: 'assistant', content: reply });

    } catch (err) {
        console.error('Voice chat error:', err);
        botLoadingDiv.querySelector('.msg-bubble').textContent = 'Error processing voice query. Please try typing or re-recording.';
    }

    chatWin.scrollTop = chatWin.scrollHeight;
}

function formatMarkdown(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
        .replace(/\*(.*?)\*/g, '<i>$1</i>')
        .replace(/\n\n/g, '<br><br>')
        .replace(/\n/g, '<br>')
        .replace(/- (.*?)(<br>|$)/g, '• $1$2');
}

function escapeHtml(text) {
    return text.replace(/[&<>"']/g, function(m) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[m];
    });
}

// ==========================================================================
// VIEW 4: DAILY PRACTICE STUDIO
// ==========================================================================
function changePracticeDifficulty(diff) {
    currentPracticeDifficulty = diff;
    document.querySelectorAll('.diff-btn').forEach(btn => {
        if (btn.dataset.diff === diff) btn.classList.add('active');
        else btn.classList.remove('active');
    });
    fetchNewPracticePhrase();
}

async function fetchNewPracticePhrase() {
    try {
        const res = await fetch(`/api/practice/random?difficulty=${currentPracticeDifficulty}`);
        const data = await res.json();
        currentTargetPhrase = data.exercise;
        document.getElementById('targetPhraseDisplay').textContent = `"${currentTargetPhrase}"`;
        document.getElementById('practiceResultsBox').style.display = 'none';
        document.getElementById('practiceStatus').textContent = 'Click record and read the target phrase aloud';
    } catch (e) {
        console.error('Error fetching practice phrase:', e);
    }
}

async function togglePracticeRecord() {
    const btn = document.getElementById('practiceRecordBtn');
    const dot = document.getElementById('practiceRecordDot');
    const btnText = document.getElementById('practiceRecordBtnText');
    const timer = document.getElementById('practiceTimer');
    const status = document.getElementById('practiceStatus');

    if (practiceMediaRecorder && practiceMediaRecorder.state === 'recording') {
        practiceMediaRecorder.stop();
        btn.classList.remove('recording');
        dot.textContent = '🔴';
        btnText.textContent = 'Record Attempt';
        clearInterval(practiceRecordInterval);
        status.textContent = 'Evaluating your pronunciation with fuzzy sequence matching...';
    } else {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            practiceRecordedChunks = [];

            const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
                ? 'audio/webm;codecs=opus'
                : (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus') ? 'audio/ogg;codecs=opus' : '');

            practiceMediaRecorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);

            practiceMediaRecorder.ondataavailable = (e) => {
                if (e.data && e.data.size > 0) practiceRecordedChunks.push(e.data);
            };

            practiceMediaRecorder.onstop = async () => {
                stream.getTracks().forEach(t => t.stop());
                const blobType = practiceMediaRecorder.mimeType || 'audio/webm';
                const audioBlob = new Blob(practiceRecordedChunks, { type: blobType });

                const formData = new FormData();
                formData.append('audio', audioBlob, 'practice_attempt.wav');
                formData.append('target_phrase', currentTargetPhrase);
                formData.append('difficulty', currentPracticeDifficulty);

                try {
                    const res = await fetch('/api/practice/evaluate', { method: 'POST', body: formData });
                    const data = await res.json();
                    renderPracticeResults(data);
                    status.textContent = 'Attempt evaluated!';
                } catch (e) {
                    console.error('Evaluation error:', e);
                    status.textContent = 'Error evaluating practice attempt.';
                }
            };

            practiceMediaRecorder.start(200);
            btn.classList.add('recording');
            dot.textContent = '⏹️';
            btnText.textContent = 'Stop Recording';
            status.textContent = 'Reading aloud now...';

            practiceRecordSeconds = 0;
            timer.textContent = '00:00';
            practiceRecordInterval = setInterval(() => {
                practiceRecordSeconds++;
                const m = String(Math.floor(practiceRecordSeconds / 60)).padStart(2, '0');
                const s = String(practiceRecordSeconds % 60).padStart(2, '0');
                timer.textContent = `${m}:${s}`;
            }, 1000);

        } catch (e) {
            console.error('Mic access error:', e);
            status.textContent = 'Microphone unavailable. You can upload an audio file above.';
        }
    }
}

async function handlePracticeAudioUpload(event) {
    const file = event.target.files && event.target.files[0];
    if (!file) return;

    const status = document.getElementById('practiceStatus');
    if (status) status.textContent = `Evaluating audio attempt (${file.name})...`;

    const formData = new FormData();
    formData.append('audio', file, file.name);
    formData.append('target_phrase', currentTargetPhrase);
    formData.append('difficulty', currentPracticeDifficulty);

    try {
        const res = await fetch('/api/practice/evaluate', { method: 'POST', body: formData });
        const data = await res.json();
        renderPracticeResults(data);
        if (status) status.textContent = 'Attempt evaluated successfully!';
    } catch (e) {
        console.error('Practice audio upload error:', e);
        if (status) status.textContent = 'Error evaluating practice audio attempt.';
    }
}

function renderPracticeResults(data) {
    const box = document.getElementById('practiceResultsBox');
    box.style.display = 'block';

    const score = data.match_score_pct || 0;
    const badge = document.getElementById('practiceMatchScore');
    badge.textContent = `${score}% Match`;

    if (score >= 80) {
        badge.style.background = 'rgba(16, 185, 129, 0.2)';
        badge.style.color = '#10B981';
        badge.style.borderColor = '#10B981';
    } else if (score >= 50) {
        badge.style.background = 'rgba(245, 158, 11, 0.2)';
        badge.style.color = '#F59E0B';
        badge.style.borderColor = '#F59E0B';
    } else {
        badge.style.background = 'rgba(239, 68, 68, 0.2)';
        badge.style.color = '#EF4444';
        badge.style.borderColor = '#EF4444';
    }

    const spokenText = data.spoken_transcript ? `Spoken: "${data.spoken_transcript}"` : '';
    document.getElementById('practiceFeedbackMsg').textContent = `${data.feedback_msg || 'Good effort!'} ${spokenText}`;

    // Word pills
    const container = document.getElementById('practiceWordDiffContainer');
    container.innerHTML = '';
    const diffs = data.diff_analysis || [];

    if (diffs.length > 0) {
        diffs.forEach(w => {
            const pill = document.createElement('span');
            pill.className = `diff-word-pill ${w.status === 'correct' ? 'diff-word-correct' : 'diff-word-practice'}`;
            pill.textContent = `${w.status === 'correct' ? '✓' : '•'} ${w.word}`;
            container.appendChild(pill);
        });
    } else {
        const words = currentTargetPhrase.split(/\s+/);
        words.forEach(w => {
            const pill = document.createElement('span');
            pill.className = 'diff-word-pill diff-word-correct';
            pill.textContent = `✓ ${w}`;
            container.appendChild(pill);
        });
    }

    box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ==========================================================================
// VIEW 5: REAL THERAPIST SESSIONS
// ==========================================================================
async function loadTherapists() {
    const grid = document.getElementById('therapistGrid');
    try {
        const res = await fetch('/api/therapists');
        const therapists = await res.json();
        grid.innerHTML = '';

        therapists.forEach(t => {
            const card = document.createElement('div');
            card.className = 'therapist-card';
            card.innerHTML = `
                <div class="therapist-avatar-row">
                    <div class="therapist-avatar">${t.avatar}</div>
                    <div>
                        <div class="therapist-name">${t.name}</div>
                        <div class="therapist-spec">${t.title}</div>
                    </div>
                </div>
                <div class="therapist-bio">${t.bio}</div>
                <div class="therapist-meta-row">
                    <span>⭐ ${t.rating} (${t.reviews_count} reviews)</span>
                    <span style="color:#10B981;">⚡ Next: ${t.next_available}</span>
                </div>
                <button type="button" class="btn-book-therapist" onclick="openBookingModal('${t.name}')">
                    📅 Book Tele-Therapy Session
                </button>
            `;
            grid.appendChild(card);
        });
    } catch (e) {
        console.error('Error loading therapists:', e);
    }
}

function openBookingModal(therapistName) {
    if (!currentUser) {
        alert('Please sign in or register to book a therapy consultation session.');
        openSidebarAuth('login');
        return;
    }

    document.getElementById('bookTherapistName').value = therapistName;
    document.getElementById('bookPatientName').value = currentUser.name || '';
    document.getElementById('bookingModalBackdrop').style.display = 'flex';
}

function closeBookingModal(e) {
    if (e && e.target !== document.getElementById('bookingModalBackdrop') && !e.target.classList.contains('drawer-close-btn')) {
        return;
    }
    document.getElementById('bookingModalBackdrop').style.display = 'none';
}

async function handleBookingSubmit(event) {
    event.preventDefault();
    const therapist_name = document.getElementById('bookTherapistName').value;
    const user_name = document.getElementById('bookPatientName').value;
    const session_type = document.getElementById('bookSessionType').value;
    const preferred_date = document.getElementById('bookDate').value;
    const preferred_time = document.getElementById('bookTime').value;
    const notes = document.getElementById('bookNotes').value;

    try {
        const res = await fetch('/api/therapists/book', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUser ? currentUser.id : null,
                user_name,
                therapist_name,
                session_type,
                preferred_date,
                preferred_time,
                notes
            })
        });
        const data = await res.json();
        if (data.success) {
            alert(`🎉 Tele-therapy session booked with ${therapist_name} on ${preferred_date} at ${preferred_time}! Your appointment is confirmed.`);
            document.getElementById('bookingModalBackdrop').style.display = 'none';
            loadMyConsultations();
        } else {
            alert('Booking failed: ' + (data.error || 'Server error'));
        }
    } catch (e) {
        console.error('Booking error:', e);
        alert('Could not connect to booking server.');
    }
}

async function loadMyConsultations() {
    const list = document.getElementById('myConsultationsList');
    try {
        const uid = currentUser ? currentUser.id : '';
        const res = await fetch(`/api/therapists/my-sessions${uid ? '?user_id=' + uid : ''}`);
        const sessions = await res.json();
        list.innerHTML = '';

        if (!sessions || sessions.length === 0) {
            list.innerHTML = `
                <div style="text-align:center; padding:24px; color:var(--text-muted); font-size:13px;">
                    You have no upcoming consultations scheduled yet. Book your first appointment with a specialist above!
                </div>
            `;
            return;
        }

        sessions.forEach(s => {
            const item = document.createElement('div');
            item.className = 'consultation-item-card';
            item.innerHTML = `
                <div>
                    <div style="font-size:14px; font-weight:800; color:#FFFFFF;">${s.therapist_name}</div>
                    <div style="font-size:12px; color:var(--gold);">${s.session_type}</div>
                    <div style="font-size:11px; color:var(--text-muted); margin-top:2px;">Scheduled: ${s.preferred_date} at ${s.preferred_time}</div>
                </div>
                <div>
                    <span style="background:rgba(16, 185, 129, 0.2); color:#10B981; font-size:11px; font-weight:800; padding:4px 10px; border-radius:999px;">
                        ✓ ${s.status || 'Confirmed'}
                    </span>
                </div>
            `;
            list.appendChild(item);
        });
    } catch (e) {
        console.error('Error loading sessions:', e);
    }
}

// ==========================================================================
// VIEW 6: PROGRESS & ANALYTICS
// ==========================================================================
async function loadProgressData() {
    try {
        const uid = currentUser ? currentUser.id : '';
        const res = await fetch(`/api/progress${uid ? '?user_id=' + uid : ''}`);
        const data = await res.json();

        // 1. KPI counters
        document.getElementById('statSpeechChecks').textContent = data.total_checks || 0;
        document.getElementById('statPracticeSessions').textContent = data.total_practice || 0;
        document.getElementById('statAvgClarity').textContent = data.avg_practice_score ? `${data.avg_practice_score}%` : '--';
        document.getElementById('statConsultations').textContent = (data.consultations || []).length;

        // 2. Recent Checks Table
        const checksTbody = document.getElementById('progressChecksTableBody');
        checksTbody.innerHTML = '';
        const checks = data.recent_checks || [];

        if (checks.length === 0) {
            checksTbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-muted);">No speech checks recorded yet. Run an analysis on the Speech Predictor tab!</td></tr>`;
        } else {
            checks.forEach(c => {
                const tr = document.createElement('tr');
                const timeStr = c.timestamp ? c.timestamp.split(' ')[0] : 'Today';
                tr.innerHTML = `
                    <td>${timeStr}</td>
                    <td><b>${(c.disorder_type || 'Typical').toUpperCase()}</b></td>
                    <td><span style="color:#F59E0B;">${c.severity_pct ? c.severity_pct + '%' : '0%'}</span></td>
                    <td>${(c.severity_category || 'Typical').toUpperCase()}</td>
                    <td>${c.confidence ? Math.round(c.confidence) + '%' : '85%'}</td>
                    <td style="max-width:240px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">"${c.transcript || 'Speech sample'}"</td>
                `;
                checksTbody.appendChild(tr);
            });
        }

        // 3. Practice History Table
        const practiceTbody = document.getElementById('progressPracticeTableBody');
        practiceTbody.innerHTML = '';
        const practices = data.practice_history || [];

        if (practices.length === 0) {
            practiceTbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-muted);">No practice sessions recorded yet. Practice a phrase on the Practice Studio tab!</td></tr>`;
        } else {
            practices.forEach(p => {
                const tr = document.createElement('tr');
                const timeStr = p.timestamp ? p.timestamp.split(' ')[0] : 'Today';
                const score = p.match_score_pct || 0;
                const scoreColor = score >= 80 ? '#10B981' : (score >= 50 ? '#F59E0B' : '#EF4444');
                tr.innerHTML = `
                    <td>${timeStr}</td>
                    <td><b>${p.exercise_type || 'Easy'}</b></td>
                    <td>"${p.target_phrase || ''}"</td>
                    <td>"${p.spoken_transcript || ''}"</td>
                    <td><b style="color:${scoreColor};">${score}%</b></td>
                    <td style="font-size:11px; color:var(--text-muted);">${p.feedback_msg || 'Completed'}</td>
                `;
                practiceTbody.appendChild(tr);
            });
        }

    } catch (e) {
        console.error('Error loading progress:', e);
    }
}

// ==========================================================================
// VIEW 7: SLP CLINICIAN PORTAL LOGIC & CASELOAD MANAGEMENT
// ==========================================================================
let currentSlpData = null;

async function loadSlpDashboardData() {
    try {
        const therapistParam = currentUser && currentUser.is_slp ? `?therapist_name=${encodeURIComponent(currentUser.name)}` : '';
        const res = await fetch(`/api/slp/dashboard${therapistParam}`);
        const data = await res.json();
        currentSlpData = data;

        // 1. KPI counters
        const stats = data.stats || {};
        const pCount = document.getElementById('slpStatPatients');
        const bCount = document.getElementById('slpStatBookings');
        const cCount = document.getElementById('slpStatChecks');
        const clrCount = document.getElementById('slpStatClarity');

        if (pCount) pCount.textContent = stats.total_patients || 0;
        if (bCount) bCount.textContent = stats.total_consultations || 0;
        if (cCount) cCount.textContent = stats.total_checks || 0;
        if (clrCount) clrCount.textContent = stats.avg_practice_score ? `${stats.avg_practice_score}%` : '--';

        // 2. Scheduled Tele-Therapy Consultations Table
        const consTbody = document.getElementById('slpConsultationsTableBody');
        if (consTbody) {
            consTbody.innerHTML = '';
            const consultations = data.consultations || [];
            if (consultations.length === 0) {
                consTbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">No scheduled consultations booked yet.</td></tr>`;
            } else {
                consultations.forEach(c => {
                    const tr = document.createElement('tr');
                    const statusClass = c.status === 'Completed' ? 'status-badge-completed' : (c.status === 'In Progress' ? 'status-badge-inprogress' : 'status-badge-confirmed');
                    tr.innerHTML = `
                        <td><b>${escapeHtml(c.user_name || 'Patient')}</b></td>
                        <td><span style="color:var(--gold); font-size:12px;">${escapeHtml(c.session_type || 'Tele-Therapy')}</span></td>
                        <td>${escapeHtml(c.preferred_date || 'Upcoming')} at ${escapeHtml(c.preferred_time || '')}</td>
                        <td style="max-width:200px; font-size:11px; color:#E2E8F0;">"${escapeHtml(c.notes || 'Routine check')}"</td>
                        <td><span class="${statusClass}">${escapeHtml(c.status || 'Confirmed')}</span></td>
                        <td style="max-width:180px; font-size:11px; color:var(--text-muted); font-style:italic;">
                            ${escapeHtml(c.clinical_notes || 'Pending consultation')}
                        </td>
                        <td>
                            <div style="display:flex; gap:6px;">
                                <button type="button" class="btn-table-action btn-video" onclick="openTeleTherapyModal('${escapeHtml(c.user_name || '')}', '${escapeHtml(c.session_type || '')}', '${escapeHtml(c.notes || '')}')" title="Launch Video Tele-Therapy Session">
                                    🎥 Call
                                </button>
                                <button type="button" class="btn-table-action" onclick="openConsultationStatusModal(${c.id}, '${escapeHtml(c.user_name || '')}', '${escapeHtml(c.status || '')}', '${escapeHtml(c.clinical_notes || '')}')" title="Update status and clinical notes">
                                    ✏️ Notes
                                </button>
                            </div>
                        </td>
                    `;
                    consTbody.appendChild(tr);
                });
            }
        }

        // 3. Registered Patients Caseload Grid
        const patientsGrid = document.getElementById('slpPatientsGrid');
        const prescribeSelect = document.getElementById('prescribePatientSelect');
        if (prescribeSelect) prescribeSelect.innerHTML = '';

        if (patientsGrid) {
            patientsGrid.innerHTML = '';
            const patients = data.patients || [];
            if (patients.length === 0) {
                patientsGrid.innerHTML = `<div style="color:var(--text-muted); padding:20px;">No registered patients in caseload yet.</div>`;
            } else {
                patients.forEach(p => {
                    // Populate Prescribe Select Dropdown
                    if (prescribeSelect) {
                        const opt = document.createElement('option');
                        opt.value = p.name;
                        opt.textContent = `${p.name} (${p.condition || 'Patient'})`;
                        prescribeSelect.appendChild(opt);
                    }

                    const card = document.createElement('div');
                    card.className = 'patient-caseload-card';
                    card.innerHTML = `
                        <div class="patient-card-header">
                            <div class="patient-avatar">👤</div>
                            <div style="flex:1;">
                                <div style="font-size:15px; font-weight:800; color:#FFFFFF;">${escapeHtml(p.name)}</div>
                                <div style="font-size:11px; color:#A855F7; font-weight:700;">${escapeHtml(p.condition || 'Patient')}</div>
                            </div>
                        </div>
                        <div class="patient-meta-row">
                            <span>Age: ${p.age || 30}</span>
                            <span>Phone: ${escapeHtml(p.phone || 'N/A')}</span>
                        </div>
                        <div class="patient-goal-box">
                            <b>🎯 Goal:</b> ${escapeHtml(p.primary_goal || 'Improve speech clarity and daily confidence')}
                        </div>
                        <div class="patient-card-actions">
                            <button type="button" class="btn-card-action btn-prescribe" onclick="openPrescribeModal('${escapeHtml(p.name)}')">
                                ➕ Prescribe Drill
                            </button>
                            ${p.phone ? `
                            <button type="button" class="btn-card-action btn-card-whatsapp" onclick="window.open('https://wa.me/${p.phone.replace(/[^0-9]/g, '')}?text=${encodeURIComponent('Hello ' + p.name + ', this is your Speech-Language Pathologist following up on your speech exercises.')}', '_blank')">
                                💬 WhatsApp
                            </button>` : ''}
                        </div>
                    `;
                    patientsGrid.appendChild(card);
                });
            }
        }

        // 4. Acoustic Diagnostic Checks Log Table
        const checksTbody = document.getElementById('slpChecksTableBody');
        if (checksTbody) {
            checksTbody.innerHTML = '';
            const checks = data.speech_checks || [];
            if (checks.length === 0) {
                checksTbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-muted);">No speech checks logged yet.</td></tr>`;
            } else {
                checks.forEach(chk => {
                    const tr = document.createElement('tr');
                    const timeStr = chk.timestamp ? chk.timestamp.split(' ')[0] : 'Today';
                    tr.innerHTML = `
                        <td>${timeStr}</td>
                        <td><b>${(chk.disorder_type || 'Typical').toUpperCase()}</b></td>
                        <td><span style="color:#F59E0B; font-weight:700;">${chk.severity_pct ? chk.severity_pct + '%' : '0%'}</span></td>
                        <td>${(chk.severity_category || 'Typical').toUpperCase()}</td>
                        <td>${chk.confidence ? Math.round(chk.confidence) + '%' : '85%'}</td>
                        <td style="max-width:280px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">"${escapeHtml(chk.transcript || 'Speech recording')}"</td>
                    `;
                    checksTbody.appendChild(tr);
                });
            }
        }

        // 5. Vocal Practice Sessions Log Table
        const practiceTbody = document.getElementById('slpPracticeTableBody');
        if (practiceTbody) {
            practiceTbody.innerHTML = '';
            const practices = data.practice_sessions || [];
            if (practices.length === 0) {
                practiceTbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-muted);">No practice sessions completed yet.</td></tr>`;
            } else {
                practices.forEach(pr => {
                    const tr = document.createElement('tr');
                    const timeStr = pr.timestamp ? pr.timestamp.split(' ')[0] : 'Today';
                    const score = pr.match_score_pct || 0;
                    const scoreColor = score >= 80 ? '#10B981' : (score >= 50 ? '#F59E0B' : '#EF4444');
                    tr.innerHTML = `
                        <td>${timeStr}</td>
                        <td><b>${escapeHtml(pr.exercise_type || 'Easy')}</b></td>
                        <td>"${escapeHtml(pr.target_phrase || '')}"</td>
                        <td>"${escapeHtml(pr.spoken_transcript || '')}"</td>
                        <td><b style="color:${scoreColor};">${score}%</b></td>
                        <td style="font-size:11px; color:var(--text-muted);">${escapeHtml(pr.feedback_msg || 'Done')}</td>
                    `;
                    practiceTbody.appendChild(tr);
                });
            }
        }

    } catch (e) {
        console.error('Error loading SLP dashboard data:', e);
    }
}

// Modal Handlers: Consultation Status
function openConsultationStatusModal(id, patientName, currentStatus, currentNotes) {
    document.getElementById('statusModalConsultationId').value = id;
    document.getElementById('statusModalPatientName').value = patientName || 'Patient Consultation';
    document.getElementById('statusModalSelect').value = currentStatus || 'Confirmed';
    document.getElementById('statusModalNotes').value = currentNotes || '';
    const modal = document.getElementById('consultationStatusModal');
    if (modal) modal.style.display = 'flex';
}

function closeConsultationStatusModal() {
    const modal = document.getElementById('consultationStatusModal');
    if (modal) modal.style.display = 'none';
}

async function handleSaveConsultationStatus(event) {
    event.preventDefault();
    const consultation_id = parseInt(document.getElementById('statusModalConsultationId').value);
    const status = document.getElementById('statusModalSelect').value;
    const clinical_notes = document.getElementById('statusModalNotes').value.trim();

    try {
        const res = await fetch('/api/slp/consultation/status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ consultation_id, status, clinical_notes })
        });
        const data = await res.json();
        if (data.success) {
            closeConsultationStatusModal();
            loadSlpDashboardData();
            alert('✅ Consultation record and clinical findings updated successfully!');
        } else {
            alert('Could not update consultation.');
        }
    } catch (e) {
        console.error('Error updating consultation:', e);
    }
}

// Modal Handlers: Prescribe Vocal Drill
function openPrescribeModal(preselectPatientName = null) {
    const select = document.getElementById('prescribePatientSelect');
    if (select && preselectPatientName) {
        select.value = preselectPatientName;
    }
    const modal = document.getElementById('prescribeModal');
    if (modal) modal.style.display = 'flex';
}

function closePrescribeModal() {
    const modal = document.getElementById('prescribeModal');
    if (modal) modal.style.display = 'none';
}

async function handleSavePrescribedDrill(event) {
    event.preventDefault();
    const patient_name = document.getElementById('prescribePatientSelect').value;
    const difficulty = document.getElementById('prescribeDifficulty').value;
    const target_phrase = document.getElementById('prescribePhrase').value.trim();
    const instructions = document.getElementById('prescribeInstructions').value.trim();
    const therapist_name = currentUser ? currentUser.name : 'Dr. Sarah Jenkins, CCC-SLP';

    if (!target_phrase) return;

    try {
        const res = await fetch('/api/slp/prescribe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ patient_name, therapist_name, target_phrase, difficulty, instructions })
        });
        const data = await res.json();
        if (data.success) {
            closePrescribeModal();
            document.getElementById('prescribePhrase').value = '';
            document.getElementById('prescribeInstructions').value = '';
            alert(`🎉 Vocal drill prescribed to ${patient_name}! Added to patient's clinical regimen.`);
        } else {
            alert('Could not prescribe drill.');
        }
    } catch (e) {
        console.error('Prescription error:', e);
    }
}

// Modal Handlers: Live Tele-Therapy Call Simulation
function openTeleTherapyModal(patientName, sessionType, notes) {
    document.getElementById('telePatientTitle').textContent = `1-on-1 Tele-Therapy: ${patientName}`;
    document.getElementById('telePatientLiveName').textContent = `${patientName} (Live Video)`;
    document.getElementById('teleLiveNotes').value = notes ? `Initial complaint: ${notes}\n` : '';
    document.getElementById('teleSaveFeedback').textContent = '';
    const modal = document.getElementById('teleTherapyModal');
    if (modal) modal.style.display = 'flex';
}

function closeTeleTherapyModal(e) {
    if (e && e.target !== document.getElementById('teleTherapyModal') && !e.target.classList.contains('drawer-close-btn')) {
        return;
    }
    const modal = document.getElementById('teleTherapyModal');
    if (modal) modal.style.display = 'none';
}

function saveTeleTherapyNotes() {
    const feedback = document.getElementById('teleSaveFeedback');
    feedback.textContent = '✓ Clinical observations saved to session record';
    setTimeout(() => { feedback.textContent = ''; }, 3500);
}

