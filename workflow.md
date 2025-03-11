## **Workflows table system of PulsePoint**

### **PulsePoint OSINT Workflows and Combos Table**

| **Use Case**               | **Input**                 | **APIs/Tools to Add**                                                                                                                                                                                                                                                                                                                                                                                                                                                     | **Workflow Steps**                                                                                                                                                                                                  | **Output**                                                                  | **Status**  |
| -------------------------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- | ----------- |
| **Person of Interest**     | Name, Email, Phone        | - Hunter.io,<br/>- Pipl,<br/>- HIBP,<br/>- Truecaller,<br/>- [Twitter API](https://developer.x.com/en/portal/dashboard),<br/>- [TinEye](https://services.tineye.com/developers/tineyeapi/api_reference)                                                                                                                                                                                                                                                                   | 1. Use Hunter.io/Pipl to find emails and social profiles. <br> 2. Check emails with HIBP. <br> 3. Validate phone with Truecaller. <br> 4. Search Twitter for activity. <br> 5. Reverse image search with TinEye.    | Consolidated report with contact info, social profiles, and breach history. | Todo        |
| **Domain Analysis**        | Domain or URL             | - [WhoisXML](https://whois.whoisxmlapi.com/),<br/>- [SecurityTrails](https://securitytrails.com/corp/api),<br/>- BuiltWith,<br/>- [URLScan.io](https://urlscan.io/docs/api/),<br/>- [VirusTotal](https://docs.virustotal.com/reference/overview),<br/>- [Wayback Machine](https://archive.org/help/wayback_api.php)                                                                                                                                                       | 1. Get domain details with WhoisXML. <br> 2. Check DNS history with SecurityTrails. <br> 3. Identify tech stack with BuiltWith. <br> 4. Scan for threats with URLScan.io/VirusTotal. <br> 5. Check Wayback Machine. | Domain report with ownership, tech stack, threats, and historical data.     | Todo        |
| **Threat Intelligence**    | IP, Domain, File Hash     | - AlienVault OTX,<br/>- [VirusTotal](https://docs.virustotal.com/reference/overview),<br/>- Hybrid Analysis,<br/>- [Shodan](https://developer.shodan.io/api),<br/>- ThreatCrowd                                                                                                                                                                                                                                                                                           | 1. Check IP/Domain with AlienVault OTX. <br> 2. Analyze file hash with VirusTotal/Hybrid Analysis. <br> 3. Discover open ports with Shodan. <br> 4. Find related IOCs with ThreatCrowd.                             | Threat report with IOCs, malware analysis, and network details.             | Todo        |
| **Network Reconnaissance** | IP Range or Domain        | - [Shodan](https://developer.shodan.io/api),<br/>- Censys,<br/>- [IPinfo](https://ipinfo.io/products/ip-geolocation-api),<br/>- AbuseIPDB,<br/>- SecurityTrails                                                                                                                                                                                                                                                                                                           | 1. Discover devices with Shodan/Censys. <br> 2. Geolocate IPs with IPinfo. <br> 3. Check for abuse with AbuseIPDB. <br> 4. Gather DNS history with SecurityTrails.                                                  | Network map with device details, geolocation, and threat indicators.        | Todo        |
| **Social Media Analysis**  | Username or Keyword       | - [Twitter API](https://developer.x.com/en/portal/dashboard),<br/>- [Reddit API](https://www.reddit.com/dev/api/),<br/>- [Instagram Scraping (Unofficial)](https://github.com/drawrowfly/instagram-scraper),<br/>- [Facebook Graph API](https://developers.facebook.com/docs/graph-api/overview)                                                                                                                                                                          | 1. Search Twitter for posts/comments. <br> 2. Search Reddit for threads. <br> 3. Scrape Instagram for public posts. <br> 4. Use Facebook Graph API for public page data.                                            | Social media activity report with posts, comments, and trends.              | Todo        |
| **Image Analysis**         | Image File or URL         | - [TinEye](https://services.tineye.com/developers/tineyeapi/api_reference),<br/>- Google Reverse Image Search,<br/>- Yandex Image Search                                                                                                                                                                                                                                                                                                                                  | 1. Perform reverse image search with TinEye. <br> 2. Cross-check with Google/Yandex.                                                                                                                                | Image source and related information.                                       | Todo        |
| **Email Verification**     | Email Address             | - Hunter.io,<br/>- HIBP,<br/>- Pipl                                                                                                                                                                                                                                                                                                                                                                                                                                       | 1. Verify email with Hunter.io. <br> 2. Check for breaches with HIBP. <br> 3. Enrich with Pipl.                                                                                                                     | Email verification and enrichment report.                                   | Todo        |
| **Phone Number Lookup**    | Phone Number              | - Truecaller,<br/>- Whitepages,<br/>- NumVerify                                                                                                                                                                                                                                                                                                                                                                                                                           | 1. Validate phone with Truecaller. <br> 2. Get additional details with Whitepages/NumVerify.                                                                                                                        | Phone number details and associated information.                            | Todo        |
| **Geolocation**            | IP Address or Coordinates | - [IPinfo](https://ipinfo.io/products/ip-geolocation-api),<br/>- [OpenCage Geocoder](https://opencagedata.com/api),<br/>- [OpenStreetMap](https://wiki.openstreetmap.org/wiki/API) or [Google Maps API](https://developers.google.com/maps/documentation/javascript/get-api-key)                                                                                                                                                                                          | 1. Geolocate IP with IPinfo. <br> 2. Reverse geocode coordinates with OpenCage. <br> 3. Visualize on Maps.                                                                                                          | Geolocation data and map visualization.                                     | Todo        |
| **News Monitoring**        | Keyword or Topic          | - [NewsAPI](https://newsapi.org/),<br/>- [GDELT](http://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/),<br/>- [Google Trends API (scrapper)](https://colab.research.google.com/github/Tanu-N-Prabhu/Python/blob/master/Google_Trends_API.ipynb)                                                                                                                                                                                                                         | 1. Fetch news articles with News API. <br> 2. Analyze global trends with GDELT. <br> 3. Check search trends with Google Trends API.                                                                                 | News and trend analysis report.                                             | Todo        |
| **General Knowledge**      | Keyword or Topic          | - [Wikipedia API](https://en.wikipedia.org/api/rest_v1/),<br/>- [Google Search Engine API](https://developers.google.com/custom-search/),<br/>- [NewsAPI](https://newsapi.org/),<br/>- [Wolfram Alpha API](https://developer.wolframalpha.com/),<br/>- [Gemini Api](https://aistudio.google.com/app/apikey),<br/>- [OpenStreetMap](https://wiki.openstreetmap.org/wiki/API) or [Google Maps API](https://developers.google.com/maps/documentation/javascript/get-api-key) | 1. Fetch summary and details from Wikipedia API. <br> 2. Perform web searches with GSE. <br> 3. Fetch recent news articles with News API. <br> 4. Get factual data with Wolfram Alpha. <br> 5. Visualize locations. | Comprehensive report with summaries, web results, news, facts, and maps.    | on progress |

---

## **Detailed Workflow Explanation**

### **Person of Interest**

1. **Input**: Name, Email, or Phone Number.
2. **Steps**:
   - Use **Hunter.io** or **Pipl** to find associated emails and social profiles.
   - Check emails with **Have I Been Pwned (HIBP)** for breaches.
   - Validate phone numbers with **Truecaller** or **Whitepages**.
   - Search for social media activity using **Twitter API**.
   - Perform reverse image searches with **TinEye**.
3. **Output**: Consolidated report with contact info, social profiles, and breach history.

---

### **Domain Analysis**

1. **Input**: Domain or URL.
2. **Steps**:
   - Get domain details with **WhoisXML**.
   - Check DNS history with **SecurityTrails**.
   - Identify tech stack with **BuiltWith**.
   - Scan for threats with **URLScan.io** or **VirusTotal**.
   - View historical snapshots with **Wayback Machine**.
3. **Output**: Domain report with ownership, tech stack, threats, and historical data.

---

### **Threat Intelligence**

1. **Input**: IP, Domain, or File Hash.
2. **Steps**:
   - Check IP/Domain with **AlienVault OTX**.
   - Analyze file hash with **VirusTotal** or **Hybrid Analysis**.
   - Discover open ports with **Shodan**.
   - Find related IOCs with **ThreatCrowd**.
3. **Output**: Threat report with IOCs, malware analysis, and network details.

---

### **Network Reconnaissance**

1. **Input**: IP Range or Domain.
2. **Steps**:
   - Discover devices with **Shodan** or **Censys**.
   - Geolocate IPs with **IPinfo**.
   - Check for abuse with **AbuseIPDB**.
   - Gather DNS history with **SecurityTrails**.
3. **Output**: Network map with device details, geolocation, and threat indicators.

---

### **Social Media Analysis**

1. **Input**: Username or Keyword.
2. **Steps**:
   - Search **Twitter API** for posts/comments.
   - Search **Reddit API** for threads.
   - Scrape Instagram for public posts (unofficial tools).
   - Use **Facebook Graph API** for public page data.
3. **Output**: Social media activity report with posts, comments, and trends.

---

### **Image Analysis**

1. **Input**: Image File or URL.
2. **Steps**:
   - Perform reverse image search with **TinEye**.
   - Cross-check with **Google Reverse Image Search** or **Yandex Image Search**.
3. **Output**: Image source and related information.

---

### **Email Verification**

1. **Input**: Email Address.
2. **Steps**:
   - Verify email with **Hunter.io**.
   - Check for breaches with **Have I Been Pwned (HIBP)**.
   - Enrich with **Pipl**.
3. **Output**: Email verification and enrichment report.

---

### **Phone Number Lookup**

1. **Input**: Phone Number.
2. **Steps**:
   - Validate phone with **Truecaller**.
   - Get additional details with **Whitepages** or **NumVerify**.
3. **Output**: Phone number details and associated information.

---

### **Geolocation**

1. **Input**: IP Address or Coordinates.
2. **Steps**:
   - Geolocate IP with **IPinfo**.
   - Reverse geocode coordinates with **OpenCage Geocoder**.
   - Visualize on **Google Maps** or **OpenStreetMap**.
3. **Output**: Geolocation data and map visualization.

---

### **News Monitoring**

1. **Input**: Keyword or Topic.
2. **Steps**:
   - Fetch news articles with **News API**.
   - Analyze global trends with **GDELT**.
   - Check search trends with **Google Trends API**.
3. **Output**: News and trend analysis report.

---

### **General Knowledge**

1. **Input**: Keyword or Topic.
2. **Steps**:
   - Fetch summary and details from **Wikipedia API**.
   - Perform web searches with **Google Custom Search (GSE)**.
   - Fetch recent news articles with **News API**.
   - Get factual data with **Wolfram Alpha**.
   - Visualize locations with **OpenStreetMap** (if applicable).
3. **Output**: Comprehensive report with summaries, web results, news, facts, and maps.

---    

on some point this project will also using 3rd party api like :

- [apify](https://console.apify.com/store)

- [google trend](https://colab.research.google.com/github/Tanu-N-Prabhu/Python/blob/master/Google_Trends_API.ipynb)

- [Instagram Scraping](https://github.com/drawrowfly/instagram-scraper)
