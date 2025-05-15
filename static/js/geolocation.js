const form = document.getElementById('search-form');
const resultsDiv = document.getElementById('results');
const loadingDiv = document.getElementById('loading');
const errorDiv = document.getElementById('error');
const errorMessage = document.getElementById('error-message');
const mapContainer = document.getElementById('map-container');
const advancedToggle = document.getElementById('advanced-toggle');
const advancedFilters = document.getElementById('advanced-filters');
const toggleText = document.getElementById('toggle-text');
const toggleIcon = document.getElementById('toggle-icon');
const customDateRange = document.getElementById('custom-date-range');
const activeTimeFilters = document.getElementById('active-time-filters');
const activeFilterText = document.getElementById('active-filter-text');
const clearTimeFilters = document.getElementById('clear-time-filters');

// Map related variables
let map = null;
let markers = [];
let markerLayer = null;

// Toggle advanced filters visibility
advancedToggle.addEventListener('click', () => {
    advancedFilters.classList.toggle('hidden');

    if (advancedFilters.classList.contains('hidden')) {
        toggleText.textContent = 'Show Advanced Search';
        toggleIcon.className = 'fa-solid fa-chevron-down ml-1';
    } else {
        toggleText.textContent = 'Hide Advanced Search';
        toggleIcon.className = 'fa-solid fa-chevron-up ml-1';
    }
});

// Initialize Flatpickr date range picker
const dateRangePicker = flatpickr("#date-range-picker", {
    mode: "range",
    dateFormat: "Y-m-d",
    maxDate: "today",
    onChange: function(selectedDates, dateStr) {
        if (selectedDates.length === 2) {
            const [start, end] = selectedDates;
            document.getElementById('from_date').value = formatDate(start);
            document.getElementById('to_date').value = formatDate(end);
            updateActiveFilters();
        }
    }
});

// Format date as YYYY-MM-DD
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// Time range pill selection
const timeRangePills = document.querySelectorAll('.time-range-pill');
timeRangePills.forEach(pill => {
    pill.addEventListener('click', function() {
        // Remove active class from all pills
        timeRangePills.forEach(p => p.classList.remove('active'));

        // Add active class to clicked pill
        this.classList.add('active');

        const range = this.getAttribute('data-range');
        if (range === 'custom') {
            // Show custom date range selector
            customDateRange.classList.remove('hidden');
        } else if (range === 'none') {
            // Clear all date filters
            document.getElementById('from_date').value = '';
            document.getElementById('to_date').value = '';
            document.getElementById('from_year').value = '';
            document.getElementById('to_year').value = '';
            dateRangePicker.clear();
            activeTimeFilters.classList.add('hidden');
            customDateRange.classList.add('hidden');
        } else {
            // Set predefined range
            customDateRange.classList.add('hidden');
            setDateRange(range);
        }
    });
});

// Set date range based on predefined option
function setDateRange(range) {
    const today = new Date();
    let fromDate, toDate;

    switch(range) {
        case 'today':
            fromDate = today;
            toDate = today;
            break;
        case 'past-week':
            fromDate = new Date(today);
            fromDate.setDate(today.getDate() - 7);
            toDate = today;
            break;
        case 'past-month':
            fromDate = new Date(today);
            fromDate.setMonth(today.getMonth() - 1);
            toDate = today;
            break;
        case 'past-year':
            fromDate = new Date(today);
            fromDate.setFullYear(today.getFullYear() - 1);
            toDate = today;
            break;
        default:
            return;
    }

    // Set date values in hidden fields
    document.getElementById('from_date').value = formatDate(fromDate);
    document.getElementById('to_date').value = formatDate(toDate);

    // Update active filters display
    updateActiveFilters();
}

// Update active filters display
function updateActiveFilters() {
    const fromDate = document.getElementById('from_date').value;
    const toDate = document.getElementById('to_date').value;
    const fromYear = document.getElementById('from_year').value;
    const toYear = document.getElementById('to_year').value;

    let filterText = [];

    if (fromDate && toDate) {
        if (fromDate === toDate) {
            filterText.push(`Date: ${fromDate}`);
        } else {
            filterText.push(`Date range: ${fromDate} to ${toDate}`);
        }
    }

    if (fromYear && toYear) {
        filterText.push(`Year range: ${fromYear} to ${toYear}`);
    } else if (fromYear) {
        filterText.push(`From year: ${fromYear}`);
    } else if (toYear) {
        filterText.push(`To year: ${toYear}`);
    }

    if (filterText.length > 0) {
        activeFilterText.textContent = filterText.join(' • ');
        activeTimeFilters.classList.remove('hidden');
    } else {
        activeTimeFilters.classList.add('hidden');
    }
}

// Clear time filters
clearTimeFilters.addEventListener('click', function() {
    document.getElementById('from_date').value = '';
    document.getElementById('to_date').value = '';
    document.getElementById('from_year').value = '';
    document.getElementById('to_year').value = '';
    dateRangePicker.clear();

    // Hide active filters display
    activeTimeFilters.classList.add('hidden');

    // Deselect all pills
    timeRangePills.forEach(pill => pill.classList.remove('active'));
});

// Update active filters when year inputs change
document.getElementById('from_year').addEventListener('change', updateActiveFilters);
document.getElementById('to_year').addEventListener('change', updateActiveFilters);

// Initialize the map
function initMap() {
    if (map !== null) return; // Map already initialized
    
    // Create a map centered on the world
    map = L.map('map-container').setView([20, 0], 2);
    
    // Add the OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    
    // Create a layer group for markers
    markerLayer = L.layerGroup().addTo(map);
}

// Add a marker to the map
function addMarker(lat, lng, title, description, source, url) {
    const marker = L.marker([lat, lng]).addTo(markerLayer);
    
    // Prepare popup content
    let popupContent = `
        <div class="popup-content">
            <h3 class="font-bold">${title}</h3>
            <p>${description}</p>
            ${source ? `<p class="text-sm text-gray-600">Source: ${source}</p>` : ''}
            ${url ? `<a href="${url}" target="_blank" class="text-blue-600 hover:text-blue-800">Read more</a>` : ''}
        </div>
    `;
    
    marker.bindPopup(popupContent);
    markers.push(marker);
    
    return marker;
}

// Clear all markers from the map
function clearMarkers() {
    markerLayer.clearLayers();
    markers = [];
}

// Extract locations from GDELT data
function extractLocationsFromGDELT(gdeltData) {
    const locations = [];
    
    gdeltData.forEach(item => {
        if (item.location && Array.isArray(item.location)) {
            item.location.forEach(loc => {
                if (loc.lat && loc.lng) {
                    locations.push({
                        lat: loc.lat,
                        lng: loc.lng,
                        title: item.title,
                        description: item.snippet || item.description,
                        source: item.source,
                        url: item.url
                    });
                }
            });
        }
    });
    
    return locations;
}

// Handle form submission
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Show loading indicator and clear previous results/errors
    loadingDiv.classList.remove('hidden');
    resultsDiv.innerHTML = '';
    errorDiv.classList.add('hidden');
    mapContainer.classList.add('hidden');
    
    // Clear existing markers if any
    if (markerLayer) {
        clearMarkers();
    }

    // Get form data
    const query = document.getElementById('query').value;
    const negativeQuery = document.getElementById('negative_query').value;
    const fromDate = document.getElementById('from_date').value;
    const toDate = document.getElementById('to_date').value;
    const fromYear = document.getElementById('from_year').value;
    const toYear = document.getElementById('to_year').value;
    const language = document.getElementById('language').value;

    try {
        // Send search request to the geolocation endpoint
        const response = await fetch('/geo_search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `query=${encodeURIComponent(query)}&negative_query=${encodeURIComponent(negativeQuery)}&from_date=${fromDate}&to_date=${toDate}&from_year=${fromYear}&to_year=${toYear}&language=${language}`
        });

        // Handle response
        if (!response.ok) {
            throw new Error('Geolocation search request failed: ' + response.statusText);
        }

        const data = await response.json();
        console.log("Backend response:", data); // Debugging: Log the backend response
        loadingDiv.classList.add('hidden');

        // Display summary, insights, cross-references, and tags
        resultsDiv.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div class="bg-white p-6 rounded-lg shadow result-card">
                    <h2 class="text-xl font-semibold mb-2">
                        <i class="fa-solid fa-file-lines text-blue-500 mr-2"></i>Summary
                    </h2>
                    <div class="result-content custom-scrollbar content-fade">
                        <p class="text-gray-700">${data.summary || "No summary available."}</p>
                    </div>
                </div>

                <div class="bg-white p-6 rounded-lg shadow result-card">
                    <h2 class="text-xl font-semibold mb-2">
                        <i class="fa-solid fa-lightbulb text-yellow-500 mr-2"></i>Insights
                    </h2>
                    <div class="result-content custom-scrollbar content-fade">
                        <p class="text-gray-700">${data.insights || "No insights available."}</p>
                    </div>
                </div>

                <div class="bg-white p-6 rounded-lg shadow result-card">
                    <h2 class="text-xl font-semibold mb-2">
                        <i class="fa-solid fa-link text-purple-500 mr-2"></i>Cross-References
                    </h2>
                    <div class="result-content custom-scrollbar content-fade">
                        <p class="text-gray-700">${data.cross_references || "No cross-references available."}</p>
                    </div>
                </div>

                <div class="bg-white p-6 rounded-lg shadow result-card tags-card">
                    <h2 class="text-xl font-semibold mb-2">
                        <i class="fa-solid fa-tags text-green-500 mr-2"></i>Tags
                    </h2>
                    <div class="result-content custom-scrollbar">
                        <div class="flex flex-wrap gap-2">
                            ${Array.isArray(data.tags) && data.tags.length > 0
                                ? data.tags.map(tag => `<span class="tag bg-gray-200 text-gray-700 px-3 py-1 rounded-full text-sm cursor-pointer hover:bg-gray-300 mb-2"><i class="fa-solid fa-tag mr-1"></i>${tag}</span>`).join("")
                                : "<p class='text-gray-500'>No tags available.</p>"}
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Display the map if we have location data
        let hasLocationData = false;
        
        // Check if we have GDELT data with locations
        if (data.results && data.results.gdelt && data.results.gdelt.length > 0) {
            const locationData = extractLocationsFromGDELT(data.results.gdelt);
            
            if (locationData.length > 0) {
                hasLocationData = true;
                
                // Initialize the map
                mapContainer.classList.remove('hidden');
                initMap();
                
                // Add markers for each location
                locationData.forEach(loc => {
                    addMarker(
                        loc.lat, 
                        loc.lng, 
                        loc.title, 
                        loc.description, 
                        loc.source,
                        loc.url
                    );
                });
                
                // Fit the map to show all markers
                if (markers.length > 0) {
                    const bounds = L.featureGroup(markers).getBounds();
                    map.fitBounds(bounds, { padding: [50, 50] });
                }
            }
        }
        
        // Display geolocation results
        if (hasLocationData) {
            resultsDiv.innerHTML += `
                <h2 class="text-2xl font-bold text-gray-800 mt-6 mb-4">
                    <i class="fa-solid fa-map-location-dot text-blue-500 mr-2"></i>Geolocation Analysis
                </h2>
                <div class="bg-white p-6 rounded-lg shadow mb-6">
                    <p class="mb-4">
                        <i class="fa-solid fa-circle-info text-blue-500 mr-2"></i>
                        The map above shows locations mentioned in news and events related to your search.
                        Click on the markers to see details about each location.
                    </p>
                    <p>
                        <strong>${markers.length}</strong> locations identified from ${data.results.gdelt ? data.results.gdelt.length : 0} GDELT events.
                    </p>
                </div>
            `;
        } else {
            resultsDiv.innerHTML += `
                <div class="bg-gray-100 p-6 rounded-lg text-center mt-6">
                    <i class="fa-solid fa-map-location-dot text-gray-400 text-5xl mb-4"></i>
                    <h3 class="text-xl font-semibold mb-2">No Location Data Found</h3>
                    <p class="text-gray-600">
                        We couldn't find any geographic data related to your search. 
                        Try broadening your search terms or searching for topics with stronger geographic connections.
                    </p>
                </div>
            `;
        }

        // Display search results by source
        if (data.results && Object.keys(data.results).length > 0) {
            resultsDiv.innerHTML += `<h2 class="text-2xl font-bold text-gray-800 mt-6 mb-4">
                <i class="fa-solid fa-list-ul text-blue-500 mr-2"></i>Search Results
            </h2>`;

            // Prioritize GDELT and location-oriented sources
            const prioritySources = [
                { key: "gdelt", label: "GDELT Global Events", icon: "fa-solid fa-globe" },
                { key: "news_top_headlines", label: "Breaking News (Headlines)", icon: "fa-solid fa-bolt-lightning" },
                { key: "rss_news", label: "RSS News Feeds", icon: "fa-solid fa-rss" },
                { key: "gnews", label: "Global News", icon: "fa-regular fa-newspaper" },
                { key: "mediastack", label: "MediaStack News", icon: "fa-solid fa-newspaper" },
                { key: "current_news", label: "Current News", icon: "fa-solid fa-hourglass-half" },
                { key: "news_everything", label: "Comprehensive News Coverage", icon: "fa-regular fa-newspaper" },
                { key: "wikipedia", label: "Wikipedia", icon: "fa-brands fa-wikipedia-w" },
                { key: "google", label: "Google Search", icon: "fa-brands fa-google" },
                { key: "semantic_scholar", label: "Semantic Scholar", icon: "fa-solid fa-graduation-cap" },
                { key: "wolfram_alpha", label: "Wolfram Alpha", icon: "fa-solid fa-calculator" }
            ];

            // Accordion container for all sources
            resultsDiv.innerHTML += `<div class="accordion space-y-4" id="results-accordion"></div>`;
            const accordionContainer = document.getElementById('results-accordion');

            // Create sections for each source
            prioritySources.forEach(source => {
                if (data.results[source.key] && data.results[source.key].length > 0) {
                    // GDELT is expanded by default for geolocation
                    const isExpanded = source.key === "gdelt";
                    
                    // Calculate the sentiment distribution for the current source
                    const sentiments = data.results[source.key].map(item => item.sentiment_score || 0);
                    const positiveCount = sentiments.filter(score => score > 0.05).length;
                    const negativeCount = sentiments.filter(score => score < -0.05).length;
                    const neutralCount = sentiments.filter(score => score >= -0.05 && score <= 0.05).length;
                    
                    // Calculate percentages
                    const total = sentiments.length;
                    const positivePercent = Math.round((positiveCount / total) * 100);
                    const negativePercent = Math.round((negativeCount / total) * 100);
                    const neutralPercent = Math.round((neutralCount / total) * 100);
                    
                    // Create accordion item
                    const sourceSection = document.createElement('div');
                    sourceSection.className = "bg-white rounded-lg shadow-md overflow-hidden";
                    sourceSection.innerHTML = `
                        <div class="source-header cursor-pointer p-4 flex justify-between items-center border-b border-gray-200" 
                             data-toggle="collapse" data-target="#${source.key}-content">
                            <div class="flex items-center">
                                <i class="${source.icon} text-2xl mr-3 ${source.key === 'gdelt' ? 'text-blue-600' : (source.key.includes('news') ? 'text-green-600' : 'text-gray-600')}"></i>
                                <div>
                                    <h3 class="text-lg font-semibold">${source.label}</h3>
                                    <p class="text-sm text-gray-500">${data.results[source.key].length} results</p>
                                </div>
                            </div>
                            <div class="flex items-center">
                                <!-- Sentiment distribution badges -->
                                <div class="hidden md:flex mr-4 items-center">
                                    <span class="px-2 py-1 rounded-full bg-green-100 text-green-800 text-xs mr-1">
                                        <i class="fa-solid fa-smile mr-1"></i>${positivePercent}%
                                    </span>
                                    <span class="px-2 py-1 rounded-full bg-red-100 text-red-800 text-xs mr-1">
                                        <i class="fa-solid fa-frown mr-1"></i>${negativePercent}%
                                    </span>
                                    <span class="px-2 py-1 rounded-full bg-gray-100 text-gray-800 text-xs">
                                        <i class="fa-solid fa-meh mr-1"></i>${neutralPercent}%
                                    </span>
                                </div>
                                <i class="fa-solid ${isExpanded ? 'fa-chevron-up' : 'fa-chevron-down'} text-gray-400"></i>
                            </div>
                        </div>
                        <div id="${source.key}-content" class="source-content ${isExpanded ? '' : 'hidden'} p-4">
                            <div class="space-y-4">
                                ${data.results[source.key].map((item, index) => {
                                    // Determine sentiment class and icon
                                    let sentimentClass, sentimentIcon;
                                    const score = item.sentiment_score || 0;
                                    
                                    if (score > 0.05) {
                                        sentimentClass = "bg-green-100 text-green-800";
                                        sentimentIcon = "fa-smile";
                                    } else if (score < -0.05) {
                                        sentimentClass = "bg-red-100 text-red-800";
                                        sentimentIcon = "fa-frown";
                                    } else {
                                        sentimentClass = "bg-gray-100 text-gray-800";
                                        sentimentIcon = "fa-meh";
                                    }
                                    
                                    // Check if this item has location data
                                    const hasLocation = item.location && Array.isArray(item.location) && item.location.length > 0;
                                    const locationBadge = hasLocation ? 
                                        `<span class="ml-2 px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs flex items-center">
                                            <i class="fa-solid fa-map-pin mr-1"></i>Has Location
                                        </span>` : '';
                                    
                                    return `
                                    <div class="result-item p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-all ${hasLocation ? 'border-blue-200' : ''}">
                                        <div class="flex justify-between items-start mb-2">
                                            <h4 class="text-lg font-semibold text-gray-800 flex-grow">${item.title}</h4>
                                            <div class="flex items-center">
                                                ${locationBadge}
                                                <span class="sentiment-badge ${sentimentClass} text-xs px-2 py-1 rounded-full ml-2 flex items-center whitespace-nowrap">
                                                    <i class="fa-solid ${sentimentIcon} mr-1"></i>
                                                    ${score.toFixed(2)}
                                                </span>
                                            </div>
                                        </div>
                                        <p class="text-gray-600 mb-3">${item.snippet || item.description || "No description available."}</p>
                                        ${item.url ? `
                                        <a href="${item.url}" target="_blank" rel="noopener noreferrer" 
                                           class="inline-flex items-center text-blue-600 hover:text-blue-800">
                                            <i class="fa-solid fa-external-link-alt mr-1"></i> Read More
                                        </a>` : ''}
                                        ${hasLocation ? `
                                        <button class="inline-flex items-center text-blue-600 hover:text-blue-800 ml-4 locate-on-map" 
                                               data-lat="${item.location[0].lat}" data-lng="${item.location[0].lng}">
                                            <i class="fa-solid fa-map-marker-alt mr-1"></i> Show on Map
                                        </button>` : ''}
                                    </div>
                                    `;
                                }).join('')}
                            </div>
                        </div>
                    `;
                    accordionContainer.appendChild(sourceSection);
                }
            });

            // Add event listeners for toggling accordions
            document.querySelectorAll('.source-header').forEach(header => {
                header.addEventListener('click', function() {
                    const targetId = this.getAttribute('data-target');
                    const content = document.querySelector(targetId);
                    content.classList.toggle('hidden');
                    
                    // Toggle chevron icon
                    const icon = this.querySelector('.fa-chevron-up, .fa-chevron-down');
                    if (content.classList.contains('hidden')) {
                        icon.classList.replace('fa-chevron-up', 'fa-chevron-down');
                    } else {
                        icon.classList.replace('fa-chevron-down', 'fa-chevron-up');
                    }
                });
            });

            // Add event listeners to "Show on Map" buttons
            document.querySelectorAll('.locate-on-map').forEach(button => {
                button.addEventListener('click', function() {
                    const lat = parseFloat(this.getAttribute('data-lat'));
                    const lng = parseFloat(this.getAttribute('data-lng'));
                    
                    if (map && !isNaN(lat) && !isNaN(lng)) {
                        map.setView([lat, lng], 10);
                        
                        // Find and open the corresponding marker popup
                        markers.forEach(marker => {
                            const markerLatLng = marker.getLatLng();
                            if (markerLatLng.lat === lat && markerLatLng.lng === lng) {
                                marker.openPopup();
                            }
                        });
                        
                        // Scroll to the map
                        mapContainer.scrollIntoView({ behavior: 'smooth' });
                    }
                });
            });

            // Add event listeners to tags for filtering
            document.querySelectorAll('.tag').forEach(tag => {
                tag.addEventListener('click', function() {
                    const tagText = this.textContent.trim().substring(1); // Remove icon
                    filterByTag(tagText);
                });
            });
        } else {
            resultsDiv.innerHTML += `
                <div class="text-gray-500 mt-6 flex items-center">
                    <i class="fa-solid fa-info-circle mr-2 text-blue-500"></i>
                    <p>No search results found.</p>
                </div>
            `;
        }
    } catch (error) {
        // Handle errors
        loadingDiv.classList.add('hidden');
        errorMessage.textContent = 'An error occurred: ' + error.message;
        errorDiv.classList.remove('hidden');
        console.error('Search error:', error);
    }
});

// Filter results by tag
function filterByTag(tag) {
    // First, check if we already have an active filter pill
    let filterPill = document.getElementById('active-filter-pill');
    
    // If we don't have a filter pill, create one
    if (!filterPill) {
        filterPill = document.createElement('div');
        filterPill.id = 'active-filter-pill';
        filterPill.className = 'fixed bottom-4 right-4 bg-blue-600 text-white px-4 py-2 rounded-full shadow-lg z-50 flex items-center';
        
        const closeBtn = document.createElement('button');
        closeBtn.className = 'ml-2 text-white hover:text-red-200';
        closeBtn.innerHTML = '<i class="fa-solid fa-times"></i>';
        closeBtn.onclick = clearFilter;
        
        filterPill.appendChild(document.createElement('span'));
        filterPill.appendChild(closeBtn);
        document.body.appendChild(filterPill);
    }
    
    // Update the filter pill text
    filterPill.querySelector('span').textContent = `Filter: ${tag}`;
    filterPill.classList.remove('hidden');
    
    // Loop through all result items and filter them
    document.querySelectorAll('.result-item').forEach(item => {
        const itemText = item.textContent.toLowerCase();
        if (itemText.includes(tag.toLowerCase())) {
            item.style.display = '';
            // Highlight the matching parts
            highlightMatches(item, tag);
        } else {
            item.style.display = 'none';
        }
    });
}

// Highlight matching text
function highlightMatches(element, searchText) {
    // This is a simplified version - in a real app, you'd need a more robust implementation
    const regex = new RegExp(`(${searchText})`, 'gi');
    
    // Only apply to text elements, not to elements with children
    const textNodes = [];
    const walk = document.createTreeWalker(
        element,
        NodeFilter.SHOW_TEXT,
        null,
        false
    );
    
    let node;
    while (node = walk.nextNode()) {
        // Skip if parent has a highlight class already
        if (node.parentNode.classList && node.parentNode.classList.contains('highlight')) {
            continue;
        }
        
        if (node.textContent.match(regex)) {
            textNodes.push(node);
        }
    }
    
    // Replace matching text with highlighted version
    textNodes.forEach(node => {
        const highlightedText = node.textContent.replace(
            regex,
            '<span class="bg-yellow-200 highlight">$1</span>'
        );
        
        // Create a temporary element to hold our HTML
        const temp = document.createElement('div');
        temp.innerHTML = highlightedText;
        
        // Replace the text node with our new nodes
        const fragment = document.createDocumentFragment();
        while (temp.firstChild) {
            fragment.appendChild(temp.firstChild);
        }
        
        node.parentNode.replaceChild(fragment, node);
    });
}

// Clear the tag filter
function clearFilter() {
    // Remove filter pill
    const filterPill = document.getElementById('active-filter-pill');
    if (filterPill) {
        filterPill.classList.add('hidden');
    }
    
    // Show all result items
    document.querySelectorAll('.result-item').forEach(item => {
        item.style.display = '';
        
        // Remove highlight spans
        item.querySelectorAll('.highlight').forEach(highlighted => {
            const parent = highlighted.parentNode;
            const text = document.createTextNode(highlighted.textContent);
            parent.replaceChild(text, highlighted);
        });
    });
} 