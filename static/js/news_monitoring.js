const form = document.getElementById('search-form');
const resultsDiv = document.getElementById('results');
const loadingDiv = document.getElementById('loading');
const errorDiv = document.getElementById('error');
const errorMessage = document.getElementById('error-message');
const advancedToggle = document.getElementById('advanced-toggle');
const advancedFilters = document.getElementById('advanced-filters');
const toggleText = document.getElementById('toggle-text');
const toggleIcon = document.getElementById('toggle-icon');
const customDateRange = document.getElementById('custom-date-range');
const activeTimeFilters = document.getElementById('active-time-filters');
const activeFilterText = document.getElementById('active-filter-text');
const clearTimeFilters = document.getElementById('clear-time-filters');

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

// Handle form submission
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Show loading indicator and clear previous results/errors
    loadingDiv.classList.remove('hidden');
    resultsDiv.innerHTML = '';
    errorDiv.classList.add('hidden');

    // Get form data
    const query = document.getElementById('query').value;
    const negativeQuery = document.getElementById('negative_query').value;
    const fromDate = document.getElementById('from_date').value;
    const toDate = document.getElementById('to_date').value;
    const fromYear = document.getElementById('from_year').value;
    const toYear = document.getElementById('to_year').value;
    const language = document.getElementById('language').value;

    try {
        // Send search request to the news-specific endpoint
        const response = await fetch('/news_search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `query=${encodeURIComponent(query)}&negative_query=${encodeURIComponent(negativeQuery)}&from_date=${fromDate}&to_date=${toDate}&from_year=${fromYear}&to_year=${toYear}&language=${language}`
        });

        // Handle response
        if (!response.ok) {
            throw new Error('News search request failed: ' + response.statusText);
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

        // Display search results by source - prioritizing news sources
        if (data.results && Object.keys(data.results).length > 0) {
            resultsDiv.innerHTML += `<h2 class="text-2xl font-bold text-gray-800 mt-6 mb-4">
                <i class="fa-solid fa-newspaper text-blue-500 mr-2"></i>News Monitoring Results
            </h2>`;

            // Prioritize news sources first
            const prioritySources = [
                { key: "news_top_headlines", label: "Breaking News (Headlines)", icon: "fa-solid fa-bolt-lightning" },
                { key: "rss_news", label: "RSS News Feeds", icon: "fa-solid fa-rss" },
                { key: "gdelt", label: "GDELT Global Events", icon: "fa-solid fa-globe" },
                { key: "gnews", label: "Global News", icon: "fa-globe" },
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
                    // First two sources (news sources) are expanded by default, others are collapsed
                    const isExpanded = source.key === "news_top_headlines" || source.key === "news_everything";
                    
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
                                <i class="${source.icon} text-2xl mr-3 ${source.key.includes('news') ? 'text-blue-600' : 'text-gray-600'}"></i>
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
                                    
                                    return `
                                    <div class="result-item p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-all">
                                        <div class="flex justify-between items-start mb-2">
                                            <h4 class="text-lg font-semibold text-gray-800 flex-grow">${item.title}</h4>
                                            <span class="sentiment-badge ${sentimentClass} text-xs px-2 py-1 rounded-full ml-2 flex items-center whitespace-nowrap">
                                                <i class="fa-solid ${sentimentIcon} mr-1"></i>
                                                ${score.toFixed(2)}
                                            </span>
                                        </div>
                                        <p class="text-gray-600 mb-3">${item.snippet || "No description available."}</p>
                                        ${item.url ? `
                                        <a href="${item.url}" target="_blank" rel="noopener noreferrer" 
                                           class="inline-flex items-center text-blue-600 hover:text-blue-800">
                                            <i class="fa-solid fa-external-link-alt mr-1"></i> Read More
                                        </a>` : ''}
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

            // Add event listeners to tags for filtering
            addTagEventListeners();
        }

    } catch (error) {
        // Show error message
        loadingDiv.classList.add('hidden');
        errorDiv.classList.remove('hidden');
        errorMessage.textContent = error.message;
        console.error("Search error:", error);
    }
});

// Add click event listeners to tags
function addTagEventListeners() {
    document.querySelectorAll('.tag').forEach(tag => {
        tag.addEventListener('click', function() {
            const tagText = this.textContent.trim().substring(1); // Remove icon
            filterByTag(tagText);
        });
    });
}

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
    });
    
    // Remove any highlighting
    document.querySelectorAll('.highlight').forEach(highlight => {
        // Replace the highlight span with its text content
        const textNode = document.createTextNode(highlight.textContent);
        highlight.parentNode.replaceChild(textNode, highlight);
    });
}

// Generate sentiment badge based on score
function generateSentimentBadge(sentiment_score) {
    let badge_class, icon_class, text;
    
    if (sentiment_score > 0.05) {
        badge_class = "bg-green-100 text-green-800";
        icon_class = "fa-solid fa-smile";
        text = "Positive";
    } else if (sentiment_score < -0.05) {
        badge_class = "bg-red-100 text-red-800";
        icon_class = "fa-solid fa-frown";
        text = "Negative";
    } else {
        badge_class = "bg-gray-100 text-gray-800";
        icon_class = "fa-solid fa-meh";
        text = "Neutral";
    }
    
    return `
    <span class="inline-flex items-center ${badge_class} px-2 py-1 rounded-full text-xs">
        <i class="${icon_class} mr-1"></i>
        ${text} (${sentiment_score.toFixed(2)})
    </span>`;
} 