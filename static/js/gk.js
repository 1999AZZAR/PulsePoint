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
        // Send search request to the backend
        const response = await fetch('/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `query=${encodeURIComponent(query)}&negative_query=${encodeURIComponent(negativeQuery)}&from_date=${fromDate}&to_date=${toDate}&from_year=${fromYear}&to_year=${toYear}&language=${language}`
        });

        // Handle response
        if (!response.ok) {
            throw new Error('Search request failed: ' + response.statusText);
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

        // Display search results by source
        if (data.results && Object.keys(data.results).length > 0) {
            resultsDiv.innerHTML += `<h2 class="text-2xl font-bold text-gray-800 mt-6 mb-4">
                <i class="fa-solid fa-list-ul text-blue-500 mr-2"></i>Search Results
            </h2>`;

            const sources = [
                { key: "wikipedia", label: "Wikipedia", icon: "fa-brands fa-wikipedia-w" },
                { key: "google", label: "Google Search", icon: "fa-brands fa-google" },
                { key: "news_everything", label: "News (Everything)", icon: "fa-regular fa-newspaper" },
                { key: "news_top_headlines", label: "News (Top Headlines)", icon: "fa-solid fa-newspaper" },
                { key: "semantic_scholar", label: "Semantic Scholar", icon: "fa-solid fa-graduation-cap" },
                { key: "wolfram_alpha", label: "Wolfram Alpha", icon: "fa-solid fa-calculator" }
            ];

            sources.forEach(source => {
                if (data.results[source.key] && data.results[source.key].length > 0) {
                    const contentId = `content-${source.key}`;

                    resultsDiv.innerHTML += `
                        <div class="bg-gray-200 text-gray-800 p-4 rounded-md font-semibold mt-4 cursor-pointer flex justify-between items-center source-header" data-target="${contentId}">
                            <div>
                                <i class="${source.icon} mr-2"></i>${source.label} <span class="text-gray-600">(${data.results[source.key].length} results)</span>
                            </div>
                            <i class="fa-solid fa-chevron-down transition-transform duration-200"></i>
                        </div>
                        <div id="${contentId}" class="source-content results-grid py-2">
                        </div>
                    `;

                    const contentContainer = document.getElementById(contentId);
                    data.results[source.key].forEach((item, index) => {
                        const sentimentBadge = generateSentimentBadge(item.sentiment_score);

                        const resultElement = document.createElement('div');
                        resultElement.className = 'result-item bg-white p-4 rounded-lg shadow result-card';

                        resultElement.innerHTML = `
                            <h3 class="text-lg font-semibold flex justify-between items-center mb-2">
                                <span class="truncate">${index + 1}. ${item.title || "No title available"}</span>
                                ${sentimentBadge}
                            </h3>
                            <div class="result-content custom-scrollbar content-fade">
                                <p class="text-gray-700">${item.snippet || "No description available"}</p>
                            </div>
                            <div class="result-footer">
                                ${item.url ? `<a href="${item.url}" target="_blank" class="text-blue-500 hover:underline inline-block"><i class="fa-solid fa-external-link mr-1"></i>View Source</a>` : ""}
                            </div>
                        `;

                        contentContainer.appendChild(resultElement);
                    });
                }
            });
        } else {
            resultsDiv.innerHTML += `
                <div class="text-gray-500 mt-6 flex items-center">
                    <i class="fa-solid fa-info-circle mr-2 text-blue-500"></i>
                    <p>No search results found.</p>
                </div>
            `;
        }

        // Initialize UI interactions after content is added to the DOM
        initializeResultsUi();
    } catch (error) {
        // Handle errors
        loadingDiv.classList.add('hidden');
        errorMessage.textContent = 'An error occurred: ' + error.message;
        errorDiv.classList.remove('hidden');
        console.error('Search error:', error);
    }
});

// Handle source toggling - improved version
function setupSourceToggling() {
    document.querySelectorAll('.source-header').forEach(header => {
        header.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const targetContent = document.getElementById(targetId);
            const icon = this.querySelector('.fa-chevron-down');

            if (targetContent) {
                // Toggle the display of content
                if (targetContent.style.display === 'none' || targetContent.style.display === '') {
                    targetContent.style.display = 'grid';
                    icon.style.transform = 'rotate(180deg)';
                } else {
                    targetContent.style.display = 'none';
                    icon.style.transform = 'rotate(0deg)';
                }
            }
        });
    });
}

// Function to add event listeners to tags
function addTagEventListeners() {
    document.querySelectorAll('.tag').forEach(tag => {
        tag.addEventListener('click', function() {
            filterByTag(this.textContent);
        });
    });
}

// Function to filter results by tag
function filterByTag(tag) {
    // Get all result items
    const items = document.querySelectorAll('.result-item');

    // Remove existing filter indicator if present
    const existingIndicator = document.querySelector('.filter-indicator');
    if (existingIndicator) {
        existingIndicator.remove();
    }

    // Remove any "no matches" message
    const noMatchesMsg = document.querySelector('.no-matches');
    if (noMatchesMsg) {
        noMatchesMsg.remove();
    }

    // Create filter indicator
    const filterIndicator = document.createElement('div');
    filterIndicator.className = 'filter-indicator bg-blue-100 text-blue-800 p-3 rounded-md mb-4 flex justify-between items-center';
    filterIndicator.innerHTML = `
        <span><i class="fa-solid fa-filter mr-2"></i>Filtering by tag: <strong>${tag}</strong></span>
        <button id="clear-filter" class="text-blue-600 hover:text-blue-800">
            <i class="fa-solid fa-times"></i> Clear filter
        </button>
    `;

    // Insert the filter indicator right after the tags card
    const tagsCard = document.querySelector('.tags-card');
    if (tagsCard) {
        tagsCard.parentNode.insertBefore(filterIndicator, tagsCard.nextSibling);
    }

    // Add event listener to clear filter button
    document.getElementById('clear-filter').addEventListener('click', clearFilter);

    // Loop through items and show/hide based on tag
    let anyVisible = false;
    items.forEach(item => {
        if (item.textContent.toLowerCase().includes(tag.toLowerCase())) {
            item.style.display = 'block';
            anyVisible = true;

            // Also ensure the parent source section is visible
            const parentContent = item.closest('.source-content');
            if (parentContent) {
                parentContent.style.display = 'block';

                // Update the toggle icon
                const header = document.querySelector(`[data-target="${parentContent.id}"]`);
                if (header) {
                    const icon = header.querySelector('.fa-chevron-down');
                    if (icon) {
                        icon.style.transform = 'rotate(180deg)';
                    }
                }
            }
        } else {
            item.style.display = 'none';
        }
    });

    // Show a "no matches" message if no items match the tag
    if (!anyVisible) {
        const noMatchesMsg = document.createElement('div');
        noMatchesMsg.className = 'no-matches bg-gray-100 p-4 rounded-md text-gray-600 mt-4';
        noMatchesMsg.innerHTML = `<i class="fa-solid fa-info-circle mr-2"></i>No results match the tag "${tag}".`;

        const filterIndicator = document.querySelector('.filter-indicator');
        if (filterIndicator) {
            filterIndicator.parentNode.insertBefore(noMatchesMsg, filterIndicator.nextSibling);
        }
    }
}

// Function to clear filters and show all results
function clearFilter() {
    // Show all result items
    const items = document.querySelectorAll('.result-item');
    items.forEach(item => {
        item.style.display = 'block';
    });

    // Remove the filter indicator
    const filterIndicator = document.querySelector('.filter-indicator');
    if (filterIndicator) {
        filterIndicator.remove();
    }

    // Remove any "no matches" message
    const noMatchesMsg = document.querySelector('.no-matches');
    if (noMatchesMsg) {
        noMatchesMsg.remove();
    }
}

// Function to generate sentiment badge
function generateSentimentBadge(sentiment_score) {
    if (sentiment_score === null || sentiment_score === undefined) {
        return ""; // Return an empty string if sentiment is null
    }

    let sentimentText = "";
    let sentimentColor = "";
    let sentimentIcon = "";

    if (sentiment_score >= 0.5) {
        sentimentText = "Positive";
        sentimentColor = "bg-green-500";
        sentimentIcon = "fa-solid fa-face-smile";
    } else if (sentiment_score > 0) {
        sentimentText = "Slightly Positive";
        sentimentColor = "bg-green-300";
        sentimentIcon = "fa-solid fa-face-smile-slight";
    } else if (sentiment_score === 0) {
        sentimentText = "Neutral";
        sentimentColor = "bg-gray-400";
        sentimentIcon = "fa-solid fa-face-meh";
    } else if (sentiment_score >= -0.5) {
        sentimentText = "Slightly Negative";
        sentimentColor = "bg-red-300";
        sentimentIcon = "fa-solid fa-face-frown-slight";
    } else {
        sentimentText = "Negative";
        sentimentColor = "bg-red-500";
        sentimentIcon = "fa-solid fa-face-frown";
    }

    return `<span class="ml-2 px-3 py-1 text-sm font-medium text-white ${sentimentColor} rounded-full flex items-center"><i class="${sentimentIcon} mr-1"></i>${sentimentText}</span>`;
}

function initializeResultsUi() {
    addTagEventListeners();
    setupSourceToggling();
}
