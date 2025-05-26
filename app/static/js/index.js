// Function to load bird observations
function loadBirdObservations(location) {
    console.log('Loading bird observations for location:', location);
    const observationsContainer = document.getElementById('observationsContainer');
    if (!observationsContainer) return;

    // Show loading state
    observationsContainer.innerHTML = `
        <div class="text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Loading bird observations...</p>
        </div>
    `;

    // Make the API request
    fetch('/api/observations', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            location: location,
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
            observationsContainer.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        } else if (data.observations && data.observations.length > 0) {
            console.log('Observations received, updating content...');
            
            // Store observations in localStorage
            localStorage.setItem('birdObservations', JSON.stringify(data.observations));
            
            // Update the UI
            observationsContainer.innerHTML = data.observations.map(observation => `
                <div class="card mb-3">
                    <div class="card-body">
                        <h5 class="card-title">${observation.species}</h5>
                        <p class="card-text">
                            <strong>Location:</strong> ${observation.location}<br>
                            <strong>Date:</strong> ${observation.date}<br>
                            <strong>Count:</strong> ${observation.count}
                        </p>
                    </div>
                </div>
            `).join('');
        } else {
            console.warn('No observations in response');
            observationsContainer.innerHTML = `<div class="alert alert-info">No observations found for ${location.name} in the last 7 days.</div>`;
        }
    })
    .catch(error => {
        console.error('Error in observations request:', error);
        observationsContainer.innerHTML = `<div class="alert alert-danger">Error loading observations: ${error.message}</div>`;
    });
}

// Function to get current location based on priority
function getCurrentLocation() {
    // 1. Check for new location selected during session
    const newLocation = JSON.parse(localStorage.getItem('selectedLocation'));
    if (newLocation) {
        return newLocation;
    }

    // 2. Check for last location from previous session
    const lastLocation = JSON.parse(localStorage.getItem('lastLocation'));
    if (lastLocation) {
        return lastLocation;
    }

    // 3. Default to Cincinnati, OH
    return {
        name: 'Cincinnati, OH',
        latitude: 39.1031,
        longitude: -84.5120,
        radius: 25
    };
}

// Function to update current location display
function updateCurrentLocation() {
    const locationSpan = document.getElementById('currentLocation');
    if (!locationSpan) return;

    const location = getCurrentLocation();
    locationSpan.textContent = location.name;
    return location;
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing...');
    
    // Update current location display
    const location = updateCurrentLocation();
    
    // Load initial observations
    loadBirdObservations(location);
});

// Listen for location changes
window.addEventListener('locationChanged', function(event) {
    console.log('Location change event received:', event.detail);
    const newLocation = event.detail.location;
    
    // Store the new location
    localStorage.setItem('selectedLocation', JSON.stringify(newLocation));
    localStorage.setItem('lastLocation', JSON.stringify(newLocation));
    
    // Update location display
    const locationSpan = document.getElementById('currentLocation');
    if (locationSpan) {
        locationSpan.textContent = newLocation.name;
    }
    
    // Reload observations with new location
    loadBirdObservations(newLocation);
}); 