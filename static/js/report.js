// Load AI analysis when the page loads
document.addEventListener('DOMContentLoaded', function() {
    const analysisContent = document.getElementById('analysisContent');
    
    // Show loading message
    analysisContent.innerHTML = '<div class="alert alert-info">Loading analysis...</div>';
    
    // Fetch analysis from the API
    fetch('/api/analysis')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.analysis) {
                analysisContent.innerHTML = data.analysis;
            } else {
                analysisContent.innerHTML = '<div class="alert alert-warning">No analysis available.</div>';
            }
        })
        .catch(error => {
            console.error('Error fetching analysis:', error);
            analysisContent.innerHTML = '<div class="alert alert-danger">Error loading analysis. Please try again later.</div>';
        });
});

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