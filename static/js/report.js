// Debug logs for localStorage
console.log('Report page loaded');
console.log('localStorage available:', !!localStorage);

// Get current location from localStorage if available
const storedLocation = localStorage.getItem('currentLocation');
console.log('Stored location on report page:', storedLocation);

// Function to update current location display
function updateCurrentLocation() {
    const locationSpan = document.getElementById('currentLocation');
    if (!locationSpan) return;

    const location = JSON.parse(localStorage.getItem('currentLocation')) || {
        name: 'Cincinnati, OH',
        latitude: 39.1031,
        longitude: -84.5120,
        radius: 10
    };
    
    locationSpan.textContent = location.name;
    return location;
}

// Function to load AI analysis
function loadAIAnalysis() {
    console.log('Starting AI analysis request...');
    const analysisContent = document.getElementById('analysisContent');
    if (!analysisContent) {
        console.error('Analysis content element not found!');
        return;
    }
    
    // Show loading state
    analysisContent.innerHTML = `
        <div class="text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Generating analysis...</p>
        </div>
    `;
    
    // Get current location
    const location = updateCurrentLocation();
    console.log('Using location for analysis:', location);
    
    // Make the analysis request
    console.log('Sending analysis request to server...');
    fetch('/api/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            location: location.name,
            timeframe: 7  // Always use 7 days for consistency
        })
    })
    .then(response => {
        console.log('Received response from server:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Parsed response data:', data);
        if (data.error) {
            console.error('Server returned error:', data.error);
            analysisContent.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        } else if (data.analysis) {
            console.log('Analysis received, updating content...');
            analysisContent.innerHTML = data.analysis;
            // Add initial chat message
            addMessage("I've analyzed the recent bird sightings in your area. What would you like to know more about?", 'bot');
        } else {
            console.warn('No analysis data in response');
            analysisContent.innerHTML = `<div class="alert alert-info">No analysis available for ${location.name}. Please check back later.</div>`;
        }
    })
    .catch(error => {
        console.error('Error in analysis request:', error);
        analysisContent.innerHTML = `<div class="alert alert-danger">Error loading AI analysis: ${error.message}</div>`;
    });
}

// Function to handle chat messages
function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (!message) return;

    // Add user message
    addMessage(message, 'user');
    input.value = '';

    // Show typing indicator
    const typingIndicator = addMessage('...', 'bot');
    
    // Send to backend and get response
    fetch('/main/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            message: message,
            location: updateCurrentLocation().name
        })
    })
    .then(response => response.json())
    .then(data => {
        // Remove typing indicator
        typingIndicator.remove();
        // Add bot response
        addMessage(data.response, 'bot');
    })
    .catch(error => {
        console.error('Error:', error);
        typingIndicator.remove();
        addMessage('Sorry, there was an error processing your request.', 'bot');
    });
}

// Function to handle suggested questions
function askQuestion(question) {
    const input = document.getElementById('chatInput');
    input.value = question;
    sendMessage();
}

// Function to handle Enter key in chat input
function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

// Function to add a message to the chat
function addMessage(text, type) {
    const messagesDiv = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    messageDiv.textContent = text;
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return messageDiv;
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing...');
    
    // Update current location display
    updateCurrentLocation();
    
    // Load initial analysis
    loadAIAnalysis();
});

// Listen for location changes
window.addEventListener('locationChanged', function(event) {
    console.log('Location change event received in report:', event.detail);
    const newLocation = event.detail.location;
    
    // Update location display
    const locationSpan = document.getElementById('currentLocation');
    if (locationSpan) {
        locationSpan.textContent = newLocation.name;
    }
    
    // Reload analysis with new location
    loadAIAnalysis();
}); 