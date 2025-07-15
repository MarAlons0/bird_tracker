// Debug logs for localStorage
console.log('Analysis page loaded');

// Get current location from localStorage if available
const storedLocation = localStorage.getItem('currentLocation');
console.log('Stored location on analysis page:', storedLocation);

// Function to get current location from localStorage or default to Cincinnati
function getCurrentLocation() {
    const storedLocation = localStorage.getItem('currentLocation');
    if (storedLocation) {
        return JSON.parse(storedLocation);
    }
    
    // Default to Cincinnati, OH
    return {
        name: 'Cincinnati, OH',
        lat: 39.1031,
        lng: -84.5120,
        radius: 25
    };
}

// Function to update the current location display
function updateCurrentLocation() {
    const location = getCurrentLocation();
    document.getElementById('currentLocation').textContent = location.name;
    return location;
}

// Function to load AI analysis
async function loadAIAnalysis() {
    const analysisContent = document.getElementById('analysisContent');
    const loadingSpinner = document.getElementById('loading-spinner');
    const initialMessage = analysisContent.querySelector('.alert');
    
    try {
        // Show loading state
        if (initialMessage) {
            initialMessage.style.display = 'none';
        }
        loadingSpinner.style.display = 'block';
        
        // Get current location
        const location = getCurrentLocation();
        console.log('Loading analysis for location:', location);
        
        // Fetch observations from API
        const params = new URLSearchParams({
            lat: location.lat,
            lng: location.lng,
            radius: location.radius
        });
        
        const response = await fetch(`/api/sightings?${params.toString()}`);
        if (!response.ok) {
            throw new Error('Failed to fetch observations');
        }
        
        const observations = await response.json();
        console.log('Fetched observations:', observations);
        
        // Store observations for chat
        window.analysisObservations = observations;
        console.log('Stored observations for chat:', window.analysisObservations);
        
        if (!observations || observations.length === 0) {
            analysisContent.innerHTML = `
                <div class="alert alert-warning">
                    No bird observations found for ${location.name}. Please try a different location or check back later.
                </div>
            `;
            loadingSpinner.style.display = 'none';
            return;
        }
        
        // Make API request to analyze the data
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        const analysisResponse = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({
                location: location,
                observations: observations,
                timeframe: 7  // Last 7 days
            })
        });
        
        if (!analysisResponse.ok) {
            throw new Error('Failed to analyze data');
        }
        
        const data = await analysisResponse.json();
        
        if (data.error) {
            analysisContent.innerHTML = `
                <div class="alert alert-danger">
                    ${data.error}
                </div>
            `;
        } else if (data.analysis) {
            analysisContent.innerHTML = data.analysis;
            // Add initial chat message
            addMessage("I've analyzed the recent bird sightings in your area. What would you like to know more about?", 'bot');
        } else {
            analysisContent.innerHTML = `
                <div class="alert alert-info">
                    No analysis available for ${location.name}. Please check back later.
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading analysis:', error);
        analysisContent.innerHTML = `
            <div class="alert alert-danger">
                Error loading analysis: ${error.message}
            </div>
        `;
    } finally {
        loadingSpinner.style.display = 'none';
    }
}

// Function to add a message to the chat
function addMessage(text, sender) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    messageDiv.textContent = text;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Function to send a message
async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessage(message, 'user');
    input.value = '';
    
    // Retrieve the observations that were fetched for the AI analysis
    const observations = window.analysisObservations || [];
    console.log('Using observations for chat:', observations);
    
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({ 
                message: message,
                observations: observations
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to get response');
        }
        
        const data = await response.json();
        
        if (data.error) {
            addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        } else {
            addMessage(data.response, 'bot');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        addMessage('Sorry, I encountered an error. Please try again.', 'bot');
    }
}

// Handle Enter key in message input
document.getElementById('chatInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Load initial analysis
    loadAIAnalysis();
    
    // Listen for location changes
    window.addEventListener('storage', function(e) {
        if (e.key === 'currentLocation') {
            loadAIAnalysis();
        }
    });
}); 