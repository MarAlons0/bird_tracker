// Load AI analysis when the page loads
document.addEventListener('DOMContentLoaded', function() {
    const analysisContent = document.getElementById('analysisContent');
    
    // Show loading message with spinner
    analysisContent.innerHTML = `
        <div class="text-center p-4">
            <div class="spinner-border text-primary mb-3" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="text-muted">Generating AI analysis of recent bird sightings...</p>
        </div>
    `;
    
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
                // Create a pre element to preserve whitespace and line breaks
                const preElement = document.createElement('pre');
                preElement.style.whiteSpace = 'pre-wrap';
                preElement.style.fontFamily = 'inherit';
                preElement.style.margin = '0';
                preElement.style.padding = '1rem';
                preElement.style.backgroundColor = '#f8f9fa';
                preElement.style.borderRadius = '8px';
                
                // Set the content
                preElement.textContent = data.analysis;
                
                // Clear the analysis content and append the pre element
                analysisContent.innerHTML = '';
                analysisContent.appendChild(preElement);
            } else {
                analysisContent.innerHTML = '<div class="alert alert-warning">No analysis available.</div>';
            }
        })
        .catch(error => {
            console.error('Error fetching analysis:', error);
            analysisContent.innerHTML = '<div class="alert alert-danger">Error loading analysis. Please try again later.</div>';
        });
});

// Listen for location changes
window.addEventListener('locationChanged', function(event) {
    const newLocation = event.detail.location;
    const analysisContent = document.getElementById('analysisContent');
    
    // Show loading message with new location
    analysisContent.innerHTML = `
        <div class="text-center p-4">
            <div class="spinner-border text-primary mb-3" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="text-muted">Generating AI analysis for ${newLocation.name}...</p>
        </div>
    `;
    
    // Fetch new analysis with cache-busting
    fetch('/api/analysis?' + new Date().getTime())
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.analysis) {
                // Create a pre element to preserve whitespace and line breaks
                const preElement = document.createElement('pre');
                preElement.style.whiteSpace = 'pre-wrap';
                preElement.style.fontFamily = 'inherit';
                preElement.style.margin = '0';
                preElement.style.padding = '1rem';
                preElement.style.backgroundColor = '#f8f9fa';
                preElement.style.borderRadius = '8px';
                
                // Set the content
                preElement.textContent = data.analysis;
                
                // Clear the analysis content and append the pre element
                analysisContent.innerHTML = '';
                analysisContent.appendChild(preElement);
            } else {
                analysisContent.innerHTML = '<div class="alert alert-warning">No analysis available for this location.</div>';
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