# Geolocation Feature Implementation

The geolocation feature adds location-based analysis capabilities to the PulsePoint OSINT tool. This document outlines the implementation details for both frontend and backend components.

## Overview

The geolocation system consists of:

1. A dedicated `/geo_search` endpoint in the backend
2. A specialized analysis focus for Gemini AI model to analyze geographic data
3. An interactive map visualization using Leaflet.js
4. Database storage for location information
5. An intuitive user interface for location-based searches
6. Support for direct IP address and coordinate inputs

## Backend Implementation

### 1. Routes (`routes.py`)

Added a new `/geo_search` endpoint that:
- Accepts POST requests with search criteria
- Detects and handles three types of input:
  - Regular text queries (e.g., "earthquakes in California")
  - IP addresses (e.g., "8.8.8.8")
  - Coordinates (e.g., "37.7749,-122.4194")
- Prioritizes sources with geographic data (especially GDELT)
- Uses specialized API services for IP geolocation and reverse geocoding
- Returns results with location information

### 2. OSINT Helper (`osint_helper.py`)

Enhanced the OSINTHelper class with:
- IP geolocation using IPinfo API
- Coordinate reverse geocoding using OpenCage API
- Integration with GDELT data source for location-enriched results
- Uses specialized geolocation prompts for AI analysis

### 3. Database (`models.py`)

Modified the Result model to include:
- A `data` JSON column to store location information, including:
  - Latitude and longitude coordinates
  - Location names
  - Country, region and city information
  - Additional geographic metadata

## Frontend Implementation

### 1. User Interface (`geolocation.html`)

- Created a dedicated geolocation page with map visualization
- Added control panel for search options
- Added explanatory information about the geolocation feature

### 2. JavaScript Integration (`geolocation.js`)

- Implemented interactive map using Leaflet.js
- Created marker system for displaying location-based results
- Added popup information windows for geographic data points
- Enhanced the search form to target the geolocation endpoint
- Applied specialized styling for geolocation-specific results

## Data Flow

The geolocation feature works as follows:

1. User submits a search query from the geolocation page
   - Can input regular text, IP address, or coordinates
2. The query is processed by the `/geo_search` endpoint
3. For IP addresses: IPinfo API retrieves location data
4. For coordinates: OpenCage API performs reverse geocoding
5. GDELT and other sources are queried for location-related information
6. AI analysis is performed with a geolocation focus
7. Results are returned to the frontend
8. The JS code renders markers on the map for each location point
9. Users can interact with the map to explore results

## Testing

To test the geolocation feature:
1. Navigate to the Geolocation page
2. Enter a search query related to a location (e.g., "earthquakes in Japan")
   - Or enter an IP address (e.g., "8.8.8.8")
   - Or enter coordinates (e.g., "37.7749,-122.4194")
3. Submit the search
4. Observe the results displayed on the map
5. Click on markers to view detailed information
6. Verify that the AI analysis focuses on geographic aspects

## API Keys

This feature requires the following API keys:
- IPinfo API key for IP geolocation
- OpenCage API key for reverse geocoding

These can be configured in the API Keys section of the application.

## Key Features

- **Location Markers**: Interactive markers show where events are taking place
- **Popup Details**: Clicking on markers reveals additional information
- **Geographic AI Analysis**: Specialized AI prompts for geospatial intelligence
- **Location Tags**: Geographic tags help categorize and filter results
- **Prioritized Sources**: Sources with location data are emphasized

## Future Enhancements

Potential future improvements:
- Heat maps for showing concentration of events
- Timeline visualization of geographic data
- Regional filtering options
- Custom map styles
- Additional location data sources beyond GDELT 