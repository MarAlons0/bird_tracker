function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (!message) return;

    // Add user message
    addMessage(message, 'user');
    input.value = '';

    // Send to backend and get response
    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        addMessage(data.response, 'bot');
    })
    .catch(error => {
        console.error('Error:', error);
        addMessage('Sorry, there was an error processing your request.', 'bot');
    });
}

function addMessage(text, type) {
    const messagesDiv = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    messageDiv.textContent = text;
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Handle Enter key in chat input
document.getElementById('chatInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

async function loadAnalysis() {
    try {
        const analysisContent = document.getElementById('analysisContent');
        
        // Show loading state
        analysisContent.innerHTML = `
            <div class="alert alert-info">
                <div class="spinner-border spinner-border-sm" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                Generating AI analysis... This may take up to 30 seconds.
                <div class="progress mt-2">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" 
                         role="progressbar" style="width: 0%"></div>
                </div>
            </div>`;
        
        // First get basic stats
        console.log('Fetching basic analysis...');
        const basicResponse = await fetch('/api/analysis/basic');
        const basicData = await basicResponse.json();
        
        // Show basic stats while waiting for AI
        analysisContent.innerHTML = basicData.analysis;
        
        // Then get AI analysis
        console.log('Fetching AI analysis...');
        const response = await fetch('/api/analysis');
        console.log('AI analysis response received:', response.status);
        
        if (!response.ok) {
            throw new Error(`Server responded with status ${response.status}`);
        }
        
        const data = await response.json();
        console.log('AI analysis data:', {
            hasAnalysis: !!data.analysis,
            length: data.analysis ? data.analysis.length : 0,
            content: data.analysis
        });
        
        if (!data.analysis) {
            throw new Error('No analysis content received');
        }
        
        // Update the content with the AI analysis
        analysisContent.innerHTML = data.analysis;
        console.log('Analysis displayed successfully');
    } catch (error) {
        console.error('Error loading analysis:', error);
        document.getElementById('analysisContent').innerHTML = `
            <div class="alert alert-danger">
                <h4>Error Loading Analysis</h4>
                <p>${error.message || 'An unexpected error occurred'}</p>
                <button class="btn btn-outline-danger mt-2" onclick="loadAnalysis()">
                    <i class="fas fa-sync-alt"></i> Try Again
                </button>
            </div>`;
    }
}

// Start loading analysis when page loads
document.addEventListener('DOMContentLoaded', loadAnalysis); 