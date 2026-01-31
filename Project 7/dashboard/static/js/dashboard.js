// Quantum-Safe Communication Suite Dashboard JavaScript

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Fetch dashboard data
    fetchDashboardData();
});

// Function to fetch dashboard data from the API
function fetchDashboardData() {
    fetch('/api/stats')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            updateDashboard(data);
        })
        .catch(error => {
            console.error('Error fetching dashboard data:', error);
        });
}

// Function to update the dashboard with the fetched data
function updateDashboard(data) {
    // Update statistics
    document.getElementById('emails-sent').textContent = data.emails_sent;
    document.getElementById('pdfs-signed').textContent = data.pdfs_signed;
    document.getElementById('receipts-generated').textContent = data.receipts_generated;
    
    // Update service statuses
    updateServiceStatus('gateway', data.services.gateway.status);
    updateServiceStatus('signer', data.services.signer.status);
    updateServiceStatus('receipts', data.services.receipts.status);
    
    // Update last updated timestamp
    document.getElementById('last-updated').textContent = data.timestamp;
    
    // Add animation to the updated values
    animateValueChanges();
}

// Function to update service status indicators
function updateServiceStatus(service, status) {
    const statusElement = document.getElementById(`${service}-status`);
    const statusTextElement = statusElement.querySelector('.status-text');
    
    // Remove existing status classes
    statusElement.classList.remove('status-up', 'status-down');
    
    if (status === 'up') {
        statusElement.classList.add('status-up');
        statusTextElement.textContent = 'Running';
    } else {
        statusElement.classList.add('status-down');
        statusTextElement.textContent = 'Down';
    }
}

// Function to add animation to value changes
function animateValueChanges() {
    const statValues = document.querySelectorAll('.stat-value');
    
    statValues.forEach(value => {
        value.classList.add('highlight');
        
        setTimeout(() => {
            value.classList.remove('highlight');
        }, 1000);
    });
}

// Add a CSS class for the highlight animation
const style = document.createElement('style');
style.textContent = `
    @keyframes highlight {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
    
    .highlight {
        animation: highlight 1s ease;
    }
`;
document.head.appendChild(style);