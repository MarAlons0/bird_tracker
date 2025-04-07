// Debug logs for localStorage
console.log('Report page loaded');
console.log('localStorage available:', !!localStorage);

// Get current location from localStorage if available
const storedLocation = localStorage.getItem('currentLocation');
console.log('Stored location on report page:', storedLocation);

// Function to load AI analysis
function loadAIAnalysis() {
    console.log('Loading AI analysis');
    const analysisContent = document.getElementById('analysisContent');
    analysisContent.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div><p>Loading AI analysis...</p></div>';
    
    // Get current location from localStorage
    const location = JSON.parse(localStorage.getItem('currentLocation')) || {
        name: 'Cincinnati, OH',
        latitude: 39.1031,
        longitude: -84.5120,
        radius: 10
    };
    
    console.log('Using location for analysis:', location);
    
    // Add cache-busting query parameter
    const timestamp = new Date().getTime();
    fetch(`/api/analysis?t=${timestamp}`)
        .then(response => response.json())
        .then(data => {
            console.log('AI analysis response:', data);
            if (data.analysis) {
                analysisContent.innerHTML = data.analysis;
            } else {
                analysisContent.innerHTML = `<div class="alert alert-info">No analysis available for ${location.name}. Please check back later.</div>`;
            }
        })
        .catch(error => {
            console.error('Error loading AI analysis:', error);
            analysisContent.innerHTML = '<div class="alert alert-danger">Error loading AI analysis. Please try again later.</div>';
        });
}

// Listen for location changes
window.addEventListener('locationChanged', function(event) {
    console.log('Location change event received in report:', event.detail);
    const newLocation = event.detail.location;
    
    // Update loading message with new location
    const analysisContent = document.getElementById('analysisContent');
    analysisContent.innerHTML = `<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div><p>Loading AI analysis for ${newLocation.name}...</p></div>`;
    
    // Add cache-busting query parameter
    const timestamp = new Date().getTime();
    fetch(`/api/analysis?t=${timestamp}`)
        .then(response => response.json())
        .then(data => {
            console.log('AI analysis response after location change:', data);
            if (data.analysis) {
                analysisContent.innerHTML = data.analysis;
            } else {
                analysisContent.innerHTML = `<div class="alert alert-info">No analysis available for ${newLocation.name}. Please check back later.</div>`;
            }
        })
        .catch(error => {
            console.error('Error loading AI analysis after location change:', error);
            analysisContent.innerHTML = '<div class="alert alert-danger">Error loading AI analysis. Please try again later.</div>';
        });
});

// Load initial analysis
loadAIAnalysis();

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