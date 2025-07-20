// Blurred Preview JavaScript
let previewMode = true;
let chartData = [];
let filteredData = [];

// Show loading screen initially
document.addEventListener('DOMContentLoaded', function() {
    showLoadingScreen();
    
    // Simulate loading time
    setTimeout(() => {
        hideLoadingScreen();
        loadPreviewChart();
    }, 3000);
});

function showLoadingScreen() {
    const loadingScreen = document.getElementById('loadingScreen');
    const main = document.getElementById('main');
    
    if (loadingScreen) {
        loadingScreen.classList.remove('export-loading-overlay-hidden');
        loadingScreen.style.display = 'flex';
    }
    
    if (main) {
        main.classList.add('main-container-hidden');
        main.style.display = 'none';
    }
    
    // Simulate loading progress
    simulateLoadingProgress();
}

function hideLoadingScreen() {
    const loadingScreen = document.getElementById('loadingScreen');
    const main = document.getElementById('main');
    
    if (loadingScreen) {
        loadingScreen.classList.add('export-loading-overlay-hidden');
        loadingScreen.style.display = 'none';
    }
    
    if (main) {
        main.classList.remove('main-container-hidden');
        main.style.display = 'block';
    }
}

function simulateLoadingProgress() {
    const statusElement = document.getElementById('loadingStatus');
    const progressFill = document.querySelector('.progress-fill');
    
    const stages = [
        { text: 'Establishing connection...', progress: 20 },
        { text: 'Retrieving organizational data...', progress: 40 },
        { text: 'Processing employee information...', progress: 60 },
        { text: 'Applying preview restrictions...', progress: 80 },
        { text: 'Finalizing chart structure...', progress: 100 }
    ];
    
    let currentStage = 0;
    
    const updateProgress = () => {
        if (currentStage < stages.length && statusElement && progressFill) {
            statusElement.textContent = stages[currentStage].text;
            progressFill.style.width = stages[currentStage].progress + '%';
            currentStage++;
            
            if (currentStage < stages.length) {
                setTimeout(updateProgress, 600);
            }
        }
    };
    
    updateProgress();
}

function closePreviewOverlay() {
    const overlay = document.getElementById('previewOverlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
    
    // Remove blur from content
    const container = document.querySelector('.container');
    if (container) {
        container.classList.remove('content-blurred');
    }
}

function loadPreviewChart() {
    // Generate sample organization chart data for preview
    const sampleData = generateSampleChartData();
    
    // Render the blurred chart
    renderBlurredChart(sampleData);
    
    // Apply preview restrictions
    applyPreviewRestrictions();
}

function generateSampleChartData() {
    // Sample organization data for preview (limited and anonymized)
    return [
        {
            id: 'ceo-1',
            name: 'C*** E*** O***',
            title: 'Chief Executive Officer',
            department: 'Executive',
            level: 1,
            parentId: null,
            email: 'c**@company.com',
            phone: '+1 ***-***-****',
            location: 'New York',
            directReports: 3,
            isBlurred: true
        },
        {
            id: 'cto-1',
            name: 'J*** S***',
            title: 'Chief Technology Officer',
            department: 'Technology',
            level: 2,
            parentId: 'ceo-1',
            email: 'j***@company.com',
            phone: '+1 ***-***-****',
            location: 'San Francisco',
            directReports: 5,
            isBlurred: true
        },
        {
            id: 'cfo-1',
            name: 'S*** M***',
            title: 'Chief Financial Officer',
            department: 'Finance',
            level: 2,
            parentId: 'ceo-1',
            email: 's***@company.com',
            phone: '+1 ***-***-****',
            location: 'New York',
            directReports: 3,
            isBlurred: true
        },
        {
            id: 'cmo-1',
            name: 'A*** R***',
            title: 'Chief Marketing Officer',
            department: 'Marketing',
            level: 2,
            parentId: 'ceo-1',
            email: 'a***@company.com',
            phone: '+1 ***-***-****',
            location: 'Los Angeles',
            directReports: 4,
            isBlurred: true
        },
        {
            id: 'eng-mgr-1',
            name: 'M*** D***',
            title: 'Engineering Manager',
            department: 'Technology',
            level: 3,
            parentId: 'cto-1',
            email: 'm***@company.com',
            phone: '+1 ***-***-****',
            location: 'San Francisco',
            directReports: 8,
            isBlurred: true
        },
        {
            id: 'dev-1',
            name: 'Developer 1',
            title: 'Senior Software Engineer',
            department: 'Technology',
            level: 4,
            parentId: 'eng-mgr-1',
            email: '***@company.com',
            phone: '+1 ***-***-****',
            location: 'San Francisco',
            directReports: 0,
            isBlurred: true
        },
        {
            id: 'dev-2',
            name: 'Developer 2',
            title: 'Software Engineer',
            department: 'Technology',
            level: 4,
            parentId: 'eng-mgr-1',
            email: '***@company.com',
            phone: '+1 ***-***-****',
            location: 'Remote',
            directReports: 0,
            isBlurred: true
        }
    ];
}

function renderBlurredChart(data) {
    const chartContainer = document.querySelector('.org-chart');
    if (!chartContainer) return;
    
    // Clear existing content
    chartContainer.innerHTML = '';
    
    // Generate HTML for the organization chart
    const chartHTML = generateBlurredChartHTML(data);
    chartContainer.innerHTML = chartHTML;
    
    // Add click event listeners (non-functional)
    addNonFunctionalListeners();
}

function generateBlurredChartHTML(data) {
    // Build hierarchy
    const hierarchy = buildHierarchy(data);
    
    // Generate HTML structure
    let html = '<div class="chart-wrapper">';
    
    // Render each level
    const levels = organizeByLevel(hierarchy);
    
    levels.forEach((level, index) => {
        html += `<div class="chart-level level-${index + 1}">`;
        
        level.forEach(person => {
            html += generatePersonCard(person);
        });
        
        html += '</div>';
        
        // Add connecting lines if not the last level
        if (index < levels.length - 1) {
            html += '<div class="connecting-lines"></div>';
        }
    });
    
    html += '</div>';
    
    return html;
}

function buildHierarchy(data) {
    const map = {};
    const roots = [];
    
    // Create a map of all people
    data.forEach(person => {
        map[person.id] = { ...person, children: [] };
    });
    
    // Build the hierarchy
    data.forEach(person => {
        if (person.parentId && map[person.parentId]) {
            map[person.parentId].children.push(map[person.id]);
        } else {
            roots.push(map[person.id]);
        }
    });
    
    return roots;
}

function organizeByLevel(hierarchy) {
    const levels = [];
    
    function traverseLevel(nodes, level = 0) {
        if (!levels[level]) {
            levels[level] = [];
        }
        
        nodes.forEach(node => {
            levels[level].push(node);
            if (node.children && node.children.length > 0) {
                traverseLevel(node.children, level + 1);
            }
        });
    }
    
    traverseLevel(hierarchy);
    return levels;
}

function generatePersonCard(person) {
    const isManager = person.directReports > 0;
    const cardClass = `person-card ${isManager ? 'manager-card' : 'employee-card'} preview-org-node`;
    
    return `
        <div class="${cardClass}" data-person-id="${person.id}">
            <div class="person-avatar">
                <span class="person-initials">?</span>
            </div>
            <div class="person-info">
                <h3 class="person-name">${person.name}</h3>
                <p class="person-title">${person.title}</p>
                <p class="person-department">${person.department}</p>
                <div class="person-meta">
                    <span class="location-badge">
                        <i class="fas fa-map-marker-alt"></i>
                        ${person.location}
                    </span>
                    ${person.directReports > 0 ? `<span class="reports-badge">${person.directReports} reports</span>` : ''}
                </div>
                <div class="preview-limitation-badge">🔒</div>
            </div>
        </div>
    `;
}

function addNonFunctionalListeners() {
    // Add click listeners to person cards to show blurred details
    document.querySelectorAll('.person-card').forEach(card => {
        card.addEventListener('click', (e) => {
            e.preventDefault();
            showBlurredPersonDetails(card);
        });
    });
    
    // Disable export functions only
    document.querySelectorAll('.export-controls button, .export-option').forEach(element => {
        element.addEventListener('click', (e) => {
            e.preventDefault();
            showPreviewLimitation('Export features require purchase for full access');
        });
    });
    
    // Disable search functionality
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            e.preventDefault();
            e.target.value = '';
            showPreviewLimitation('Search functionality is disabled in preview mode');
        });
    }
}

function showPreviewLimitation(message) {
    // Create a temporary notification
    const notification = document.createElement('div');
    notification.className = 'preview-notification';
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-lock"></i>
            <span>${message}</span>
        </div>
    `;
    
    // Add notification styles
    notification.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(0, 0, 0, 0.9);
        color: white;
        padding: 1rem 2rem;
        border-radius: 12px;
        z-index: 10001;
        animation: fadeInOut 2s ease-in-out;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    `;
    
    // Add animation CSS
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeInOut {
            0%, 100% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
            50% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
        }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(notification);
    
    // Remove after animation
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
        if (style.parentNode) {
            style.parentNode.removeChild(style);
        }
    }, 2000);
}

// Prevent right-click context menu in preview mode
document.addEventListener('contextmenu', function(e) {
    if (previewMode) {
        e.preventDefault();
        showPreviewLimitation('Right-click is disabled in preview mode');
    }
});

// Prevent text selection in preview mode
document.addEventListener('selectstart', function(e) {
    if (previewMode && e.target.closest('.person-card')) {
        e.preventDefault();
    }
});

// Disable keyboard shortcuts
document.addEventListener('keydown', function(e) {
    if (previewMode) {
        // Disable common shortcuts
        if (e.ctrlKey && (e.key === 's' || e.key === 'p' || e.key === 'c' || e.key === 'v' || e.key === 'a')) {
            e.preventDefault();
            showPreviewLimitation('Keyboard shortcuts are disabled in preview mode');
        }
        
        // Disable F12 (dev tools)
        if (e.key === 'F12') {
            e.preventDefault();
        }
    }
});

// Add watermark interaction
document.addEventListener('DOMContentLoaded', function() {
    const watermark = document.querySelector('.preview-watermark');
    if (watermark) {
        watermark.addEventListener('click', function() {
            window.location.href = '/marketplace/';
        });
        
        // Make watermark slightly interactive
        watermark.style.cursor = 'pointer';
        watermark.title = 'Click to return to marketplace';
    }
});

// Simulate network latency for preview authenticity
function simulateNetworkDelay(callback, delay = 1000) {
    setTimeout(callback, delay);
}

// Export disabled functionality
window.exportChart = function(format) {
    showPreviewLimitation(`Export to ${format.toUpperCase()} is only available in the full version`);
};

// Search disabled functionality
window.performSearch = function(query) {
    showPreviewLimitation('Search functionality requires full access');
    return [];
};

// Filter disabled functionality
window.applyFilters = function(filters) {
    showPreviewLimitation('Advanced filtering is only available in the full version');
    return [];
};

// Helper function to apply preview restrictions
function applyPreviewRestrictions() {
    // Add preview mode class to body
    document.body.classList.add('preview-mode');
    
    // Disable all interactive elements
    const interactiveElements = document.querySelectorAll(
        'button:not(.preview-btn), input, select, textarea, a:not(.preview-btn)'
    );
    
    interactiveElements.forEach(element => {
        element.disabled = true;
        element.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
    });
    
    // Add visual indicators
    document.querySelectorAll('.preview-disabled').forEach(element => {
        element.style.position = 'relative';
    });
}

// Initialize preview mode
function initializePreview() {
    console.log('Organization Chart Preview Mode Initialized');
    
    // Track preview interactions for analytics (mock)
    window.trackPreviewInteraction = function(action) {
        console.log(`Preview interaction: ${action}`);
    };
    
    // Show preview notice after a delay
    setTimeout(() => {
        const overlay = document.getElementById('previewOverlay');
        if (overlay && overlay.style.display !== 'none') {
            // Keep overlay visible until user decides
        }
    }, 5000);
}

// Function to show blurred person details
function showBlurredPersonDetails(card) {
    const personId = card.dataset.personId;
    
    // Generate blurred employee details
    const blurredDetails = generateBlurredPersonDetails(personId);
    
    // Show the right panel with blurred details
    const rightPanel = document.getElementById('rightPanel');
    if (rightPanel) {
        rightPanel.classList.add('active');
        rightPanel.innerHTML = `
            <div class="right-panel-content">
                <div class="profile-header">
                    <div class="profile-photo">
                        <div class="profile-initials" style="background: #4A90E2;">
                            ${blurredDetails.initials}
                        </div>
                    </div>
                    <div class="profile-title">
                        <h3>${blurredDetails.name}</h3>
                        <p>${blurredDetails.title}</p>
                    </div>
                    <button class="close-panel" onclick="document.getElementById('rightPanel').classList.remove('active')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="profile-details">
                    <div class="contact-icons">
                        <div class="contact-icon web" title="Website">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
                            </svg>
                        </div>
                        <div class="contact-icon email" title="Email">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/>
                            </svg>
                        </div>
                        <div class="contact-icon phone" title="Phone">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"/>
                            </svg>
                        </div>
                        <div class="contact-icon location" title="Location">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                            </svg>
                        </div>
                    </div>
                    <div class="detail-item">
                        <label>FULL NAME</label>
                        <span class="blurred-text">${blurredDetails.name}</span>
                    </div>
                    <div class="detail-item">
                        <label>DESIGNATION</label>
                        <span class="blurred-text">${blurredDetails.title}</span>
                    </div>
                    <div class="detail-item">
                        <label>EMAIL ADDRESS</label>
                        <span class="blurred-text">${blurredDetails.email}</span>
                    </div>
                    <div class="detail-item">
                        <label>BOARDLINE NUMBER</label>
                        <span class="blurred-text">${blurredDetails.phone}</span>
                    </div>
                    <div class="detail-item">
                        <label>DEPARTMENT NAME</label>
                        <span class="blurred-text">${blurredDetails.department}</span>
                    </div>
                    <div class="detail-item">
                        <label>ORGANIZATION NAME</label>
                        <span class="blurred-text">${blurredDetails.organization}</span>
                    </div>
                    <div class="detail-item">
                        <label>CITY/TOWN</label>
                        <span class="blurred-text">${blurredDetails.city}</span>
                    </div>
                    <div class="detail-item">
                        <label>STATE/PROVINCE</label>
                        <span class="blurred-text">${blurredDetails.state}</span>
                    </div>
                    <div class="detail-item">
                        <label>COUNTRY/REGION</label>
                        <span class="blurred-text">${blurredDetails.country}</span>
                    </div>
                    <div class="detail-item">
                        <label>POSTAL CODE</label>
                        <span class="blurred-text">${blurredDetails.postal}</span>
                    </div>
                    <div class="detail-item">
                        <label>PRIMARY ADDRESS</label>
                        <span class="blurred-text">${blurredDetails.address}</span>
                    </div>
                </div>
            </div>
        `;
    }
}

// Function to generate blurred person details
function generateBlurredPersonDetails(personId) {
    const blurredNames = ["J*** S****", "A*** P****", "R*** K****", "M*** T****", "S*** R****"];
    const blurredEmails = ["j***.s***@company.com", "a***.p***@company.com", "r***.k***@company.com"];
    const blurredPhones = ["(+**) *** *** ****", "(+**) *** *** ****", "(+**) *** *** ****"];
    const blurredAddresses = ["GHAR NO *, *-**, **** ****** ******* **", "FLAT NO *, *-**, **** ****** ******* **"];
    
    const blurredDepartments = ["S****", "M*******", "I*", "H*", "F******", "O*********"];
    const blurredOrganizations = ["T*******", "I*******", "S*******", "G*******", "P*******"];
    const blurredCities = ["M*****", "D****", "B*******", "C******", "P***", "H*******"];
    const blurredStates = ["M*********", "D****", "K*******", "T*** N***", "T*******"];
    const blurredCountries = ["I****", "U**", "U*", "C*****", "A*******"];
    const blurredPostalCodes = ["4****1", "1****1", "5****1", "6****1", "5****1"];
    
    const randomIndex = Math.floor(Math.random() * blurredNames.length);
    const name = blurredNames[randomIndex];
    
    return {
        initials: name.charAt(0) + name.split(' ')[1].charAt(0),
        name: name,
        title: "S**** E*******", // Also blur job titles
        email: blurredEmails[randomIndex] || "***@company.com",
        phone: blurredPhones[randomIndex] || "(+**) *** *** ****",
        department: blurredDepartments[Math.floor(Math.random() * blurredDepartments.length)],
        organization: blurredOrganizations[Math.floor(Math.random() * blurredOrganizations.length)],
        city: blurredCities[Math.floor(Math.random() * blurredCities.length)],
        state: blurredStates[Math.floor(Math.random() * blurredStates.length)],
        country: blurredCountries[Math.floor(Math.random() * blurredCountries.length)],
        postal: blurredPostalCodes[Math.floor(Math.random() * blurredPostalCodes.length)],
        address: blurredAddresses[Math.floor(Math.random() * blurredAddresses.length)]
    };
}

// Call initialization when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializePreview);
} else {
    initializePreview();
}
