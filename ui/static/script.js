const triggerBtn = document.getElementById('triggerBtn');
const triggerStatus = document.getElementById('triggerStatus');
const currentStateLabel = document.getElementById('currentStateLabel');
const errorLogs = document.getElementById('errorLogs');
const dataPreview = document.getElementById('dataPreview');
const itemCount = document.getElementById('itemCount');

// Node mapping from backend status to DOM ID
const statusMap = {
    "init": "node-init",
    "run_parsing": "node-parsing",
    "parsed": "node-parsing",
    "parsing_failed": "node-parsing",
    "run_bdd_tests": "node-bdd",
    "bdd_passed": "node-bdd",
    "bdd_failed": "node-bdd",
    "run_mcp_validation": "node-validation",
    "validated": "node-validation",
    "validation_failed": "node-validation",
    "self_heal": "node-heal",
    "healed": "node-heal",
    "failed_max_retries": "node-heal",
    "sync_to_ion": "node-sync",
    "synced": "node-sync",
    "sync_failed": "node-sync"
};

// Polling state
async function fetchStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        updateUI(data.pipeline, data.parsed_items, data.preview);
    } catch (e) {
        console.error("Error fetching status:", e);
    }
}

function updateUI(pipeline, parsedItems, preview) {
    const status = pipeline.status;
    const logs = pipeline.error_logs;
    
    currentStateLabel.innerText = status;
    
    // Reset nodes
    document.querySelectorAll('.node').forEach(n => {
        n.classList.remove('active', 'error', 'success');
    });
    
    // Set active node
    const activeNodeId = statusMap[status];
    if (activeNodeId) {
        const node = document.getElementById(activeNodeId);
        node.classList.add('active');
        
        if (status.includes('fail')) {
            node.classList.add('error');
            node.classList.remove('active');
        }
        if (status === 'validated' || status === 'healed' || status === 'synced') {
            node.classList.add('success');
            node.classList.remove('active');
        }
    }
    
    // Logs
    if (logs) {
        errorLogs.innerText = logs;
        errorLogs.style.color = '#ff7b72';
    } else {
        errorLogs.innerText = 'No critical errors. Pipeline healthy.';
        errorLogs.style.color = '#8b949e';
    }
    
    // Data Preview
    itemCount.innerText = `${parsedItems} items`;
    if (preview && preview.length > 0) {
        dataPreview.innerText = JSON.stringify(preview, null, 2);
    } else {
        dataPreview.innerText = 'No data available.';
    }
}

// Trigger attack
triggerBtn.addEventListener('click', async () => {
    triggerBtn.disabled = true;
    triggerBtn.innerText = 'Injecting...';
    try {
        const res = await fetch('/api/trigger_attack', { method: 'POST' });
        const result = await res.json();
        triggerStatus.innerText = result.message;
    } catch(e) {
        triggerStatus.innerText = "Error triggering attack.";
    }
    setTimeout(() => {
        triggerBtn.disabled = false;
        triggerBtn.innerText = 'Inject Slop Squatting Attack (Red Team)';
        triggerStatus.innerText = '';
    }, 5000);
});

// Start polling
setInterval(() => {
    fetchStatus();
    fetchIONInbox();
}, 1000);
fetchStatus();
fetchIONInbox();

// Poll ION Inbox
let currentBODs = [];
let activeBOD = null;

async function fetchIONInbox() {
    try {
        const response = await fetch('/api/ion_inbox');
        const data = await response.json();
        
        document.getElementById('ionBODCount').innerText = `${data.files.length} BODs`;
        
        if (JSON.stringify(data.files) !== JSON.stringify(currentBODs)) {
            currentBODs = data.files;
            renderInboxList(data.files);
        }
    } catch(e) {
        console.error("Error fetching ION inbox:", e);
    }
}

function renderInboxList(files) {
    const list = document.getElementById('inboxFileList');
    if (files.length === 0) {
        list.innerHTML = '<p style="color: #8b949e; font-size: 0.85rem; text-align: center;">No BODs received yet.</p>';
        return;
    }
    
    list.innerHTML = '';
    files.forEach(file => {
        const btn = document.createElement('button');
        btn.style.width = '100%';
        btn.style.padding = '0.6rem 0.75rem';
        btn.style.background = file === activeBOD ? 'rgba(59, 130, 246, 0.2)' : 'rgba(255, 255, 255, 0.03)';
        btn.style.border = file === activeBOD ? '1px solid var(--accent)' : '1px solid rgba(255, 255, 255, 0.1)';
        btn.style.borderRadius = '6px';
        btn.style.cursor = 'pointer';
        btn.style.color = '#c9d1d9';
        btn.style.textAlign = 'left';
        btn.style.fontSize = '0.8rem';
        btn.style.transition = 'all 0.2s ease';
        btn.innerHTML = `📄 ${file}`;
        
        btn.addEventListener('click', () => loadBOD(file));
        list.appendChild(btn);
    });
}

async function loadBOD(filename) {
    activeBOD = filename;
    document.getElementById('activeBODName').innerText = filename;
    
    // Update button background styling locally for responsiveness
    document.querySelectorAll('#inboxFileList button').forEach(btn => {
        if (btn.innerText.includes(filename)) {
            btn.style.background = 'rgba(59, 130, 246, 0.2)';
            btn.style.borderColor = 'var(--accent)';
        } else {
            btn.style.background = 'rgba(255, 255, 255, 0.03)';
            btn.style.borderColor = 'rgba(255, 255, 255, 0.1)';
        }
    });
    
    try {
        const response = await fetch(`/api/ion_inbox/${filename}`);
        const data = await response.json();
        
        const preview = document.getElementById('bodPreview');
        if (data.content) {
            preview.textContent = data.content;
        } else {
            preview.textContent = "Error loading content.";
        }
    } catch(e) {
        console.error("Error loading BOD:", e);
    }
}

// Chat UI Logic
const chatInput = document.getElementById('chatInput');
const sendChatBtn = document.getElementById('sendChatBtn');
const chatHistory = document.getElementById('chatHistory');

function addChatMessage(role, text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-msg ${role}`;
    msgDiv.innerHTML = `<strong>${role === 'user' ? 'You' : 'Orchestrator'}:</strong> ${text}`;
    chatHistory.appendChild(msgDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

async function sendChatMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    // Add user message
    addChatMessage('user', text);
    chatInput.value = '';

    // Typing indicator
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-msg system';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = 'Orchestrator is typing...';
    chatHistory.appendChild(typingDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        });
        const data = await response.json();
        
        // Remove typing
        document.getElementById('typingIndicator')?.remove();
        
        // Add agent response
        addChatMessage('agent', data.response);
    } catch (e) {
        document.getElementById('typingIndicator')?.remove();
        addChatMessage('system', 'Error communicating with Orchestrator backend.');
    }
}

sendChatBtn.addEventListener('click', sendChatMessage);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendChatMessage();
});
