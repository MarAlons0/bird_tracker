// Newsletter subscription handling
function updateNewsletterSubscription(subscribe) {
    fetch('/api/update-newsletter', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ subscribe: subscribe })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update UI to reflect subscription status
            const newsletterToggle = document.getElementById('newsletter-toggle');
            if (newsletterToggle) {
                newsletterToggle.checked = data.subscribed;
            }
        } else {
            console.error('Failed to update newsletter subscription:', data.error);
        }
    })
    .catch(error => {
        console.error('Error updating newsletter subscription:', error);
    });
}

// Check newsletter subscription status on page load
function checkNewsletterSubscription() {
    fetch('/api/check-newsletter')
        .then(response => response.json())
        .then(data => {
            if (data.subscribed !== undefined) {
                const newsletterToggle = document.getElementById('newsletter-toggle');
                if (newsletterToggle) {
                    newsletterToggle.checked = data.subscribed;
                }
            }
        })
        .catch(error => {
            console.error('Error checking newsletter subscription:', error);
        });
}

// Add event listener for newsletter toggle
document.addEventListener('DOMContentLoaded', function() {
    const newsletterToggle = document.getElementById('newsletter-toggle');
    if (newsletterToggle) {
        newsletterToggle.addEventListener('change', function() {
            updateNewsletterSubscription(this.checked);
        });
        checkNewsletterSubscription();
    }
}); 