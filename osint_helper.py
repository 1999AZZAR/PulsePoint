import requests
import wikipediaapi
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import re
from models import db, Query, Result, Tag, GeminiResponse
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from collections import Counter
import time
import google.api_core.exceptions
from datetime import datetime
import urllib.parse
from bs4 import BeautifulSoup
import html

# Try to import feedparser, but continue if it's not available
try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    print("Warning: feedparser module not available. Using requests-html fallback for RSS feeds.")
    FEEDPARSER_AVAILABLE = False
    # Import requests-html as a fallback
    try:
        from requests_html import HTMLSession
    except ImportError:
        print("Warning: requests-html not available. RSS feeds will be completely disabled.")

# Load environment variables
load_dotenv()

# Default source control structure
DEFAULT_SOURCE_CONTROL = {
    "wikipedia": 0,
    "news_everything": 0,
    "news_top_headlines": 0,
    "google": 0,
    "wolfram_alpha": 0,
    "semantic_scholar": 0,
}


class OSINTHelper:
    def __init__(self):
        # Initialize Wikipedia API
        self.user_agent = "PulsePoint/1.0 (azzarmrzs@gmail.com)"
        self.wikipedia = wikipediaapi.Wikipedia(
            language="en", user_agent=self.user_agent
        )

        # Load API keys
        self.newsapi_key = os.getenv("NEWSAPI_KEY")
        self.gse_api_key = os.getenv("GSE_API_KEY")
        self.gse_id = os.getenv("GSE_ID")
        self.wolfram_alpha_app_id = os.getenv("WOLFRAM_ALPHA_APP_ID")

        # Initialize Gemini
        # Set up the model
        self.generation_config = {
            "temperature": 0.75,
            "top_p": 0.65,
            "top_k": 35,
            "max_output_tokens": 2048,
            "stop_sequences": [],
        }

        # Safety settings
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        # Model settings
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=self.generation_config,
            safety_settings=self.safety_settings,
        )

        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=self.gemini_api_key)
        self.gemini_model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=self.generation_config,
            safety_settings=self.safety_settings,
        )

        # Initialize VADER sentiment analyzer
        self.sentiment_analyzer = SentimentIntensityAnalyzer()

        # Add new API keys and RSS feed URLs
        self.gnews_api_key = os.getenv("GNEWS_API_KEY")
        self.mediastack_api_key = os.getenv("MEDIASTACK_API_KEY")
        
        # List of major news RSS feeds
        self.rss_feeds = {
            "reuters": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
            "bbc": "http://feeds.bbci.co.uk/news/world/rss.xml",
            "cnn": "http://rss.cnn.com/rss/edition_world.rss",
            "nyt": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
            "guardian": "https://www.theguardian.com/world/rss",
            "ap": "https://www.ap.org/rss-feeds/",
            "npr": "https://feeds.npr.org/1001/rss.xml"
        }

    @staticmethod
    def normalize_query(query: str) -> str:
        """
        Normalize the query by:
        - Converting to lowercase
        - Removing special characters (#, @, !, etc.)
        - Stripping leading/trailing whitespace

        Args:
            query (str): The input query.

        Returns:
            str: The normalized query.
        """
        if not query:
            return ""

        # Convert to lowercase
        query = query.lower()

        # Remove special characters (keep alphanumeric + spaces)
        query = re.sub(r"[^\w\s]", "", query)

        # Strip leading/trailing whitespace
        return query.strip()

    def analyze_sentiment(self, text):
        """
        Analyze the sentiment of the given text using VADER.
        Returns a sentiment score between -1 (negative) and 1 (positive).
        """
        sentiment = self.sentiment_analyzer.polarity_scores(text)
        return sentiment["compound"]

    def apply_sentiment_analysis(self, results):
        """
        Apply sentiment analysis to a list of results and update the database.
        """
        for result in results:
            if (
                result.sentiment_score is None
            ):  # Only analyze if sentiment_score is not set
                sentiment_score = self.analyze_sentiment(result.snippet or "")
                result.sentiment_score = sentiment_score
                db.session.commit()

    def save_results_to_db(self, query_id, source, results):
        """
        Save results from a specific source to the database.
        Ensures `source_control` accumulates values correctly.
        """
        try:
            saved_count = 0  # Track number of results saved

            # Ensure results is a list
            if not isinstance(results, list):
                print(
                    f"   ⚠ Warning: Expected list, got {type(results)} for {source}. Skipping..."
                )
                return

            for item in results:
                if not isinstance(item, dict):
                    print(
                        f"   ⚠ Warning: Skipping invalid result from {source}: {item}"
                    )
                    continue

                # 🔹 Determine correct fields based on source
                if source == "wikipedia":
                    title = item.get("title", "Untitled")
                    snippet = item.get("summary", "")
                    url = item.get("url", "")

                elif source in ["news_everything", "news_top_headlines"]:
                    title = item.get("title", "Untitled")
                    snippet = item.get("description", "")
                    url = item.get("url", "")

                elif source == "gse":
                    title = item.get("title", "Untitled")
                    snippet = item.get("snippet", "")
                    url = item.get("link", "")

                elif source == "semantic_scholar":
                    title = item.get("title", "Untitled")
                    snippet = item.get("abstract", "")
                    url = item.get("url", "")

                elif source == "wolfram_alpha":
                    title = item.get("title", "Untitled")
                    snippet = item.get("snippet", "")
                    url = ""  # Wolfram Alpha does not provide URLs

                else:  # Default case for unknown sources
                    title = item.get("title", "Untitled")
                    snippet = item.get(
                        "snippet", item.get("description", item.get("abstract", ""))
                    )
                    url = item.get("url", item.get("link", ""))

                # 🔹 Add result to database
                db.session.add(
                    Result(
                        query_id=query_id,
                        source=source,
                        title=title,
                        snippet=snippet,
                        url=url,
                        data=item.get("data", None),  # Store additional data like location information
                    )
                )
                saved_count += 1

            db.session.commit()

            print(
                f"   ✅ Successfully saved {saved_count} results from {source} to database."
            )

            # 🔹 **Ensure `source_control` updates persistently**
            query = db.session.query(Query).filter(Query.id == query_id).first()
            if query:
                # Initialize if `source_control` is missing
                if query.source_control is None:
                    query.source_control = DEFAULT_SOURCE_CONTROL.copy()

                # 🔥 FIX: Merge existing values instead of overwriting
                updated_source_control = {
                    **query.source_control,
                    source: query.source_control.get(source, 0) + saved_count,
                }
                query.source_control = updated_source_control

                db.session.commit()

        except Exception as e:
            print(f"   ❌ Error saving results from {source} to database: {e}")
            db.session.rollback()

    def search_wikipedia(self, query, negative_query=None, num_results=10):
        """
        Search Wikipedia for a given query, excluding negative keywords.
        Supports special characters and hashtags.
        """
        try:
            # Encode the query to handle special characters
            encoded_query = requests.utils.quote(query)
            search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded_query}&format=json&srlimit={num_results}"
            headers = {"User-Agent": self.user_agent}
            response = requests.get(search_url, headers=headers)

            # Check if the response is valid JSON
            if response.status_code != 200:
                print(
                    f"   ❌ Wikipedia API request failed with status code: {response.status_code}"
                )
                return []

            search_results = response.json().get("query", {}).get("search", [])

            results = []
            for result in search_results:
                title = result["title"]
                snippet = result.get("snippet", "")

                # Skip results containing negative keywords
                if negative_query and any(
                    keyword.lower() in title.lower()
                    or keyword.lower() in snippet.lower()
                    for keyword in negative_query
                    if keyword.strip()
                ):
                    continue

                page = self.wikipedia.page(title)
                if page.exists():
                    results.append(
                        {
                            "title": page.title,
                            "summary": page.summary[
                                :500
                            ],  # First 500 characters of the summary
                            "url": page.fullurl,
                        }
                    )
            return results
        except Exception as e:
            print(f"   ❌ Error searching Wikipedia: {e}")
            return []

    def fetch_news(
        self,
        query,
        endpoint="everything",  # Default to "everything"
        negative_query=None,
        language="en",  # Default to English
        page_size=10,
        from_date=None,
        to_date=None,
    ):
        """
        Fetch news articles from NewsAPI using the specified endpoint.
        Supports both "everything" and "top-headlines" endpoints.
        """
        url = f"https://newsapi.org/v2/{endpoint}"
        params = {
            "q": query,
            "language": language,  # Use the language parameter
            "pageSize": page_size,
            "apiKey": self.newsapi_key,
        }

        # Add time filter if provided (only for "everything" endpoint)
        if endpoint == "everything":
            if from_date:
                params["from"] = from_date
            if to_date:
                params["to"] = to_date
        elif endpoint == "top-headlines":
            # Top headlines endpoint does not support date filters
            pass

        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            articles = data.get("articles", [])

            # Filter out articles containing negative keywords
            if negative_query:
                articles = [
                    article
                    for article in articles
                    if not any(
                        keyword.lower() in article.get("title", "").lower()
                        or keyword.lower() in article.get("description", "").lower()
                        for keyword in negative_query
                        if keyword.strip()
                    )
                ]

            # Format the results to include title, description, URL, and published date
            formatted_articles = []
            for article in articles:
                formatted_articles.append(
                    {
                        "title": article.get("title", "No title available"),
                        "description": article.get(
                            "description", "No description available"
                        ),
                        "url": article.get("url", ""),
                        "publishedAt": article.get("publishedAt", ""),
                    }
                )

            return formatted_articles
        return []

    def fetch_gse_results(
        self, query, negative_query=None, exclude_keyword="wikipedia", num_results=10
    ):
        """
        Fetch results from Google Custom Search Engine, excluding negative keywords.
        Supports special characters and hashtags.
        """
        try:
            # Encode the query to handle special characters
            encoded_query = requests.utils.quote(query)
            url = "https://www.googleapis.com/customsearch/v1/"
            params = {
                "q": encoded_query,
                "key": self.gse_api_key,
                "cx": self.gse_id,
                "safe": "off",
                "num": num_results,
                "filter": 0,
                "cr": f"-{exclude_keyword}",
            }
            response = requests.get(url, params=params)

            # Check if the response is valid JSON
            if response.status_code != 200:
                print(
                    f"   ❌ Google Custom Search API request failed with status code: {response.status_code}"
                )
                return []

            # data = response.json()
            data = (
                self.fetch_with_retry(url, params) or {}
            )  # Ensure data is always a dict
            items = data.get("items", [])  # Safely access "items"

            # Filter out results containing negative keywords
            if negative_query:
                items = [
                    item
                    for item in items
                    if not any(
                        keyword.lower() in item.get("title", "").lower()
                        or keyword.lower() in item.get("snippet", "").lower()
                        for keyword in negative_query
                        if keyword.strip()
                    )
                ]
            return items
            # return data.get("items", []) if data else []
        except Exception as e:
            print(f"   ❌ Error fetching Google Custom Search results: {e}")
            return []

    def fetch_wolfram_alpha(self, query):
        """
        Fetch results from Wolfram Alpha.
        Supports special characters and hashtags.
        Ensures results are always returned in a uniform format.
        """
        try:
            # Encode the query to handle special characters
            encoded_query = requests.utils.quote(query)
            url = "http://api.wolframalpha.com/v2/query"
            params = {
                "input": encoded_query,
                "format": "plaintext",
                "output": "json",
                "appid": self.wolfram_alpha_app_id,
            }

            response = requests.get(url, params=params, timeout=10)
            if response.status_code != 200:
                print(
                    f"   ⚠ Wolfram Alpha API request failed with status code: {response.status_code}"
                )
                return []

            data = response.json()

            # Ensure queryresult exists
            query_result = data.get("queryresult", {})
            if not query_result or not isinstance(query_result, dict):
                print(f"   ⚠ Unexpected response format from Wolfram Alpha: {data}")
                return []

            # Extract relevant information
            results = []
            pods = query_result.get("pods", [])
            if not isinstance(pods, list):
                print(
                    f"   ⚠ Warning: Expected list, got {type(pods)} for wolfram_alpha. Skipping..."
                )
                return []

            for pod in pods:
                title = pod.get("title", "Untitled")
                subpods = pod.get("subpods", [])

                if isinstance(subpods, list) and subpods:
                    for subpod in subpods:
                        plaintext = subpod.get("plaintext", "").strip()
                        if plaintext:
                            results.append(
                                {
                                    "title": title,
                                    "snippet": plaintext,
                                    "url": "",  # Wolfram Alpha does not provide direct URLs
                                }
                            )

            if not results:
                print("   ⚠ Wolfram Alpha returned no usable results.")
            else:
                print(
                    f"   ✅ Successfully fetched {len(results)} results from Wolfram Alpha."
                )

            return results

        except requests.exceptions.Timeout:
            print("   ❌ Error: Wolfram Alpha request timed out.")
            return []

        except json.JSONDecodeError:
            print("   ❌ Error: Failed to parse Wolfram Alpha response as JSON.")
            return []

        except Exception as e:
            print(f"   ❌ Error fetching Wolfram Alpha results: {e}")
            return []

    def fetch_semantic_scholar(
        self, query, negative_query=None, num_results=5, from_year=None, to_year=None
    ):
        """
        Fetch academic papers from Semantic Scholar, excluding negative keywords and applying time filters.
        Supports special characters and hashtags.
        """
        try:
            # Encode the query to handle special characters
            encoded_query = requests.utils.quote(query)
            url = "https://api.semanticscholar.org/graph/v1/paper/search"
            params = {
                "query": encoded_query,
                "limit": num_results,
                "fields": "title,abstract,url",
            }

            # Add time filter if provided
            if from_year or to_year:
                params["year"] = f"{from_year or ''}-{to_year or ''}"

            response = requests.get(url, params=params)

            # Check if the response is valid JSON
            if response.status_code != 200:
                print(
                    f"   ❌ Semantic Scholar API request failed with status code: {response.status_code}"
                )
                return []

            # data = response.json()
            data = (
                self.fetch_with_retry(url, params) or {}
            )  # Ensure data is always a dict
            papers = data.get("data", [])  # Safely access "data"

            # Filter out papers containing negative keywords
            if negative_query:
                papers = [
                    paper
                    for paper in papers
                    if not any(
                        keyword.lower() in paper.get("title", "").lower()
                        or keyword.lower() in paper.get("abstract", "").lower()
                        for keyword in negative_query
                        if keyword.strip()
                    )
                ]

            # Format the results to include title, abstract snippet, and link
            formatted_papers = []
            for paper in papers:
                title = paper.get("title", "No title available")
                abstract = paper.get("abstract", "") or ""  # Handle None case
                url = paper.get("url", "")

                # Extract the first 500 characters of the abstract
                abstract_snippet = (
                    abstract[:500] + "..." if len(abstract) > 500 else abstract
                )

                formatted_papers.append(
                    {
                        "title": title,
                        "snippet": abstract_snippet,  # Use the snippet for display
                        "abstract": abstract,  # Keep the full abstract if needed
                        "url": url,
                    }
                )

            return formatted_papers
        except Exception as e:
            print(f"   ❌ Error fetching Semantic Scholar results: {e}")
            return []

    def fetch_with_retry(self, url, params, retries=3, delay=2):
        """
        Fetch data with retry logic to handle 429 rate limits.
        """
        for attempt in range(retries):
            response = requests.get(url, params=params)

            if response.status_code == 200:
                return response.json()  # ✅ Ensure only JSON data is returned

            elif response.status_code == 429:  # Rate limited
                wait_time = delay * (2**attempt)  # Exponential backoff
                print(
                    f"   🔄 Rate limit exceeded (429). Retrying in {wait_time} seconds..."
                )
                time.sleep(wait_time)

            else:
                print(
                    f"   ❌ API request failed with status {response.status_code}: {response.text}"
                )
                break  # Stop retrying if it's another error

        return {}  # ✅ Return an empty dict instead of None

    def fetch_rss_news(self, query, negative_query=None, max_results=15):
        """
        Fetch news from various RSS feeds based on the query.
        
        Args:
            query: The search query.
            negative_query: Keywords to exclude from results.
            max_results: Maximum number of results to return.
            
        Returns:
            List of news items from RSS feeds.
        """
        all_results = []
        query_terms = query.lower().split()
        
        print(f"   🔍 Searching RSS feeds for: {query}")
        
        # If feedparser is not available, use requests-html as fallback
        if not FEEDPARSER_AVAILABLE:
            try:
                session = HTMLSession()
                print("   ℹ️ Using requests-html fallback for RSS feeds")
                
                # Parse each RSS feed
                for source, feed_url in self.rss_feeds.items():
                    try:
                        # Fetch the RSS feed content
                        r = session.get(feed_url)
                        
                        # Find all items/entries in the RSS feed
                        items = r.html.xpath('//item') or r.html.xpath('//entry')
                        
                        for item in items[:10]:  # Limit to first 10 items for performance
                            # Extract data using XPath
                            title_elem = item.xpath('.//title')
                            description_elem = item.xpath('.//description') or item.xpath('.//content') or item.xpath('.//summary')
                            link_elem = item.xpath('.//link')
                            
                            title = title_elem[0].text if title_elem else "No title"
                            
                            # Extract description - might be in CDATA or as text
                            description = ""
                            if description_elem:
                                description = description_elem[0].text or "".join(description_elem[0].xpath('.//text()'))
                            
                            # Clean up the description (remove HTML)
                            if description:
                                soup = BeautifulSoup(description, 'html.parser')
                                description = soup.get_text()
                                
                            # Get link - might be as attribute or as text
                            link = ""
                            if link_elem:
                                link = link_elem[0].attrs.get('href', '') or link_elem[0].text
                            
                            # Check if the item matches the query
                            full_text = f"{title} {description}".lower()
                            if any(term in full_text for term in query_terms):
                                # Check for negative query terms
                                if negative_query and any(
                                    neg_term.lower() in full_text 
                                    for neg_term in negative_query 
                                    if neg_term.strip()
                                ):
                                    continue
                                    
                                # Add to results
                                all_results.append({
                                    'title': title,
                                    'description': description[:300] + ('...' if len(description) > 300 else ''),
                                    'url': link,
                                    'publishedAt': '',  # No reliable way to get this without full parsing
                                    'source': source
                                })
                                
                    except Exception as e:
                        print(f"   ⚠ Error processing RSS feed {source} with fallback method: {str(e)}")
                
                session.close()
                        
            except Exception as e:
                print(f"   ❌ Failed to use requests-html fallback for RSS feeds: {str(e)}")
                return all_results
        else:
            # Original implementation using feedparser
            for source, feed_url in self.rss_feeds.items():
                try:
                    # Parse the feed
                    feed = feedparser.parse(feed_url)
                    
                    # Check each entry in the feed
                    for entry in feed.entries[:50]:  # Limit to first 50 entries for performance
                        title = entry.get('title', '')
                        description = entry.get('description', '')
                        summary = entry.get('summary', description)
                        
                        # Clean up HTML from description/summary
                        if summary:
                            try:
                                soup = BeautifulSoup(summary, 'html.parser')
                                summary = soup.get_text()
                            except:
                                # If BeautifulSoup fails, try basic HTML unescape
                                summary = html.unescape(summary)
                        
                        # Create a combined text for matching
                        full_text = f"{title} {summary}".lower()
                        
                        # Check if query terms match
                        if any(term in full_text for term in query_terms):
                            # Check for negative query terms
                            if negative_query and any(
                                neg_term.lower() in full_text 
                                for neg_term in negative_query 
                                if neg_term.strip()
                            ):
                                continue
                                
                            # Get publish date if available
                            published = entry.get('published', '')
                            published_parsed = entry.get('published_parsed')
                            if published_parsed:
                                # Convert to ISO format string
                                dt = datetime(*published_parsed[:6])
                                published = dt.isoformat()
                                
                            # Get URL
                            url = entry.get('link', '')
                            
                            # Add to results
                            all_results.append({
                                'title': title,
                                'description': summary[:300] + ('...' if len(summary) > 300 else ''),
                                'url': url,
                                'publishedAt': published,
                                'source': source
                            })
                    
                except Exception as e:
                    print(f"   ⚠ Error processing RSS feed {source}: {str(e)}")
        
        # Sort by date if possible, newest first
        all_results = sorted(
            all_results, 
            key=lambda x: x.get('publishedAt', ''), 
            reverse=True
        )
        
        # Return only up to max_results
        return all_results[:max_results]

    def fetch_gnews(self, query, negative_query=None, language="en", max_results=10, from_date=None, to_date=None):
        """
        Fetch news from GNews API.
        
        Args:
            query: The search query.
            negative_query: Keywords to exclude from results.
            language: The language code.
            max_results: Maximum number of results to return.
            from_date: Start date for results (YYYY-MM-DD).
            to_date: End date for results (YYYY-MM-DD).
            
        Returns:
            List of news articles from GNews.
        """
        if not self.gnews_api_key:
            print("   ⚠ GNews API key not found")
            return []
            
        # Base URL for GNews API - updated to v4
        url = "https://gnews.io/api/v4/search"
        
        # Build query parameters
        params = {
            "q": query,
            "lang": language,
            "max": max_results,
            "apikey": self.gnews_api_key,
            "sortby": "publishedAt"  # Sort by publication date
        }
        
        # Add date parameters if provided
        if from_date:
            params["from"] = from_date + "T00:00:00Z"
        if to_date:
            params["to"] = to_date + "T23:59:59Z"
            
        try:
            # Set up headers with user agent to avoid some 401 errors
            headers = {
                "User-Agent": self.user_agent,
                "Accept": "application/json"
            }
            
            # Make the request
            print(f"   🔍 Calling GNews API with key: {self.gnews_api_key[:5]}...")
            response = requests.get(url, params=params, headers=headers)
            
            # Debug the response
            print(f"   ℹ️ GNews API response status: {response.status_code}")
            if response.status_code != 200:
                print(f"   ❌ GNews API error response: {response.text[:100]}...")
                
                # Try alternative approach - some implementations require the key in the URL
                alt_url = f"https://gnews.io/api/v4/search?apikey={self.gnews_api_key}&q={urllib.parse.quote(query)}&lang={language}&max={max_results}"
                print(f"   🔄 Trying alternative GNews API approach...")
                response = requests.get(alt_url, headers=headers)
                
                if response.status_code != 200:
                    print(f"   ❌ Alternative GNews approach also failed: {response.status_code}")
                    return []
                else:
                    print(f"   ✅ Alternative GNews approach succeeded!")
                
            # Parse response
            data = response.json()
            articles = data.get("articles", [])
            
            # Filter by negative query if provided
            if negative_query:
                articles = [
                    article
                    for article in articles
                    if not any(
                        keyword.lower() in article.get("title", "").lower()
                        or keyword.lower() in article.get("description", "").lower()
                        for keyword in negative_query
                        if keyword.strip()
                    )
                ]
                
            # Format results
            formatted_articles = []
            for article in articles:
                formatted_articles.append({
                    "title": article.get("title", "No title available"),
                    "description": article.get("description", "No description available"),
                    "url": article.get("url", ""),
                    "publishedAt": article.get("publishedAt", ""),
                    "source": article.get("source", {}).get("name", "GNews")
                })
            
            print(f"   ✅ Successfully fetched {len(formatted_articles)} articles from GNews API")    
            return formatted_articles
                
        except Exception as e:
            print(f"   ❌ Error fetching GNews results: {str(e)}")
            return []

    def fetch_mediastack(self, query, negative_query=None, language="en", max_results=10, from_date=None, to_date=None):
        """
        Fetch news from MediaStack API.
        
        Args:
            query: The search query.
            negative_query: Keywords to exclude from results.
            language: The language code.
            max_results: Maximum number of results to return.
            from_date: Start date for results (YYYY-MM-DD).
            to_date: End date for results (YYYY-MM-DD).
            
        Returns:
            List of news articles from MediaStack.
        """
        if not self.mediastack_api_key:
            print("   ⚠ MediaStack API key not found")
            return []
            
        # Base URL for MediaStack API
        url = "http://api.mediastack.com/v1/news"
        
        # Build query parameters
        params = {
            "access_key": self.mediastack_api_key,
            "keywords": query,
            "languages": language,
            "limit": max_results,
            "sort": "published_desc",
        }
        
        # Add date parameters if provided
        if from_date:
            params["date"] = from_date
            if to_date:
                params["date"] += "," + to_date
            
        try:
            # Make the request
            response = requests.get(url, params=params)
            
            # Check response status
            if response.status_code != 200:
                print(f"   ❌ MediaStack API request failed with status code: {response.status_code}")
                return []
                
            # Parse response
            data = response.json()
            articles = data.get("data", [])
            
            # Filter by negative query if provided
            if negative_query:
                articles = [
                    article
                    for article in articles
                    if not any(
                        keyword.lower() in article.get("title", "").lower()
                        or keyword.lower() in article.get("description", "").lower()
                        for keyword in negative_query
                        if keyword.strip()
                    )
                ]
                
            # Format results
            formatted_articles = []
            for article in articles:
                formatted_articles.append({
                    "title": article.get("title", "No title available"),
                    "description": article.get("description", "No description available"),
                    "url": article.get("url", ""),
                    "publishedAt": article.get("published_at", ""),
                    "source": article.get("source", "MediaStack")
                })
                
            return formatted_articles
                
        except Exception as e:
            print(f"   ❌ Error fetching MediaStack results: {str(e)}")
            return []

    def fetch_current_news(self, query, language="en", max_results=10):
        """
        Fetch news from Current News API (free and open).
        This API doesn't require authentication.
        
        Args:
            query: The search query.
            language: The language code.
            max_results: Maximum number of results to return.
            
        Returns:
            List of news articles from Current News API.
        """
        # Base URL for Current News API
        url = "https://api.currentsapi.services/v1/search"
        
        # Build query parameters
        params = {
            "keywords": query,
            "language": language,
            "page_size": max_results,
        }
        
        try:
            # Make the request
            response = requests.get(url, params=params)
            
            # Check response status
            if response.status_code != 200:
                print(f"   ❌ Current News API request failed with status code: {response.status_code}")
                return []
                
            # Parse response
            data = response.json()
            articles = data.get("news", [])
            
            # Format results
            formatted_articles = []
            for article in articles:
                formatted_articles.append({
                    "title": article.get("title", "No title available"),
                    "description": article.get("description", "No description available"),
                    "url": article.get("url", ""),
                    "publishedAt": article.get("published", ""),
                    "source": article.get("source", "Current News")
                })
                
            return formatted_articles
                
        except Exception as e:
            print(f"   ❌ Error fetching Current News results: {str(e)}")
            return []

    def fetch_gdelt(self, query, negative_query=None, max_results=15, timespan="1week", sort_by="tone"):
        """
        Fetch data from the GDELT Global Knowledge Graph API.
        Returns results with location information, themes, and more.
        
        Args:
            query (str): The search query.
            negative_query (list, optional): List of terms to exclude. Defaults to None.
            max_results (int, optional): Maximum number of results to return. Defaults to 15.
            timespan (str, optional): Time range for results - options: 1day, 3days, 1week, 2weeks, 
                                      1month, 2months, 6months, 1year. Defaults to "1week".
            sort_by (str, optional): Sort results by - options: date, tone, relevance. Defaults to "tone".
            
        Returns:
            list: List of dictionaries containing GDELT results.
        """
        # GDELT only supports timespan in certain formats
        valid_timespans = ["1day", "3days", "1week", "2weeks", "1month", "2months", "6months", "1year"]
        if timespan not in valid_timespans:
            timespan = "1week"  # Default fallback
            
        # GDELT v2 GKG API URL
        url = "https://api.gdeltproject.org/api/v2/doc/doc"
        
        # Format query and negative terms for GDELT
        formatted_query = query.replace(" ", "%20")
        if negative_query:
            if isinstance(negative_query, list):
                negative_terms = "%20".join([f"-{term.replace(' ', '%20')}" for term in negative_query if term.strip()])
                if negative_terms:
                    formatted_query = f"{formatted_query}%20{negative_terms}"
            else:
                formatted_query = f"{formatted_query}%20-{negative_query.replace(' ', '%20')}"
        
        # Build parameters
        params = {
            "query": formatted_query,
            "mode": "artlist",
            "format": "json",
            "maxrecords": max_results,
            "timespan": timespan,
            "sort": sort_by
        }
        
        try:
            print(f"   🔍 Searching GDELT for: {query}")
            # GDELT expects parameters in the URL rather than as query params
            param_string = "&".join([f"{k}={v}" for k, v in params.items()])
            full_url = f"{url}?{param_string}"
            
            # Make the request with a proper user agent to avoid blocks
            headers = {"User-Agent": self.user_agent}
            response = requests.get(full_url, headers=headers)
            
            if response.status_code != 200:
                print(f"   ❌ GDELT API request failed with status code: {response.status_code}")
                return []
                
            # Parse response - GDELT returns a list of articles
            data = response.json()
            articles = data.get("articles", [])
            
            # Format results
            formatted_articles = []
            for article in articles:
                # GDELT provides sentiment scores in "tone" field
                sentiment_score = None
                if "tone" in article:
                    # GDELT tone ranges from -100 to +100, normalize to -1 to +1
                    sentiment_score = float(article["tone"]) / 100
                
                # Format the item
                formatted_articles.append({
                    "title": article.get("title", "No title available"),
                    "description": article.get("seendate", "") + " - " + article.get("sourcecountry", "") + " - " + article.get("domain", ""),
                    "snippet": article.get("snippet", "No description available"),
                    "url": article.get("url", ""),
                    "publishedAt": article.get("seendate", ""),
                    "source": article.get("domain", "GDELT"),
                    "sentiment_score": sentiment_score,
                    "location": article.get("locations", []),
                    "themes": article.get("themes", [])
                })
            
            print(f"   ✅ Successfully fetched {len(formatted_articles)} items from GDELT")
            return formatted_articles
            
        except Exception as e:
            print(f"   ❌ Error fetching GDELT results: {str(e)}")
            return []

    def geolocate_ip(self, ip_address):
        """
        Geolocate an IP address using IPinfo API.
        
        Args:
            ip_address (str): The IP address to geolocate.
            
        Returns:
            dict: Dictionary with location information or None if failed.
        """
        api_key = os.getenv("IPINFO_API_KEY")
        if not api_key:
            print("   ⚠ Warning: IPinfo API key not found.")
            return None
            
        try:
            url = f"https://ipinfo.io/{ip_address}/json"
            response = requests.get(url, headers={
                "Authorization": f"Bearer {api_key}"
            })
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract location coordinates if available
                coordinates = None
                if "loc" in data and data["loc"]:
                    try:
                        lat, lon = data["loc"].split(",")
                        coordinates = {
                            "lat": float(lat),
                            "lon": float(lon)
                        }
                    except (ValueError, TypeError):
                        pass
                
                return {
                    "ip": data.get("ip"),
                    "hostname": data.get("hostname"),
                    "city": data.get("city"),
                    "region": data.get("region"),
                    "country": data.get("country"),
                    "coordinates": coordinates,
                    "org": data.get("org"),
                    "postal": data.get("postal"),
                    "timezone": data.get("timezone"),
                    "raw_data": data
                }
            else:
                print(f"   ⚠ IPinfo API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"   ⚠ Error geolocating IP address: {str(e)}")
            return None
    
    def reverse_geocode(self, lat, lon):
        """
        Perform reverse geocoding on coordinates using OpenCage API.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            
        Returns:
            dict: Dictionary with location information or None if failed.
        """
        api_key = os.getenv("OPENCAGE_API_KEY")
        if not api_key:
            print("   ⚠ Warning: OpenCage API key not found.")
            return None
            
        try:
            url = "https://api.opencagedata.com/geocode/v1/json"
            params = {
                "q": f"{lat},{lon}",
                "key": api_key,
                "language": "en",
                "pretty": 1
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data["results"] and len(data["results"]) > 0:
                    result = data["results"][0]
                    
                    # Extract components for easier access
                    components = result.get("components", {})
                    
                    return {
                        "formatted": result.get("formatted"),
                        "name": components.get("name"),
                        "road": components.get("road"),
                        "neighbourhood": components.get("neighbourhood"),
                        "city": components.get("city") or components.get("town") or components.get("village"),
                        "county": components.get("county"),
                        "state": components.get("state"),
                        "country": components.get("country"),
                        "country_code": components.get("country_code"),
                        "postal_code": components.get("postcode"),
                        "coordinates": {
                            "lat": result.get("geometry", {}).get("lat"),
                            "lon": result.get("geometry", {}).get("lng")
                        },
                        "raw_data": result
                    }
                else:
                    print("   ⚠ No results found for the given coordinates.")
                    return None
            else:
                print(f"   ⚠ OpenCage API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"   ⚠ Error reverse geocoding coordinates: {str(e)}")
            return None
            
    def perform_search(self, query):
        """
        Perform a comprehensive search across multiple sources.
        """
        return {
            "wikipedia": self.search_wikipedia(query) or [],
            "news_everything": self.fetch_news(query, endpoint="everything") or [],
            "news_top_headlines": self.fetch_news(query, endpoint="top-headlines") or [],
            "rss_news": self.fetch_rss_news(query) or [],
            "gnews": self.fetch_gnews(query) or [],
            "mediastack": self.fetch_mediastack(query) or [],
            "current_news": self.fetch_current_news(query) or [],
            "google": self.fetch_gse_results(query) or [],
            "wolfram_alpha": self.fetch_wolfram_alpha(query) or [],
            "semantic_scholar": self.fetch_semantic_scholar(query) or [],
            "gdelt": self.fetch_gdelt(query) or [],
        }

    def aggregate_results(self, results):
        """
        Combines search results into a formatted text block for AI processing.
        """
        aggregated_results = ""
        for source, data in results.items():
            if data:
                aggregated_results += f"=== {source.upper()} ===\n"
                for item in data:
                    if isinstance(item, dict):
                        aggregated_results += f"Title: {item.get('title', '')}\n"
                        aggregated_results += f"Content: {item.get('snippet', '')}\n"
                        aggregated_results += f"URL: {item.get('url', '')}\n\n"
        return aggregated_results

    def analyze_with_gemini(self, query, text, language="en", analysis_focus=None):
        """
        Use Gemini model to analyze search results.

        Args:
            query: The search query.
            text: The text to analyze.
            language: The language of the text.
            analysis_focus: Optional focus area for analysis (e.g., "news", "academic", etc.)
        """
        try:
            # Get query text for the prompt
            query_text = query.query_text if hasattr(query, "query_text") else query

            # Create a prompt based on analysis focus
            if analysis_focus == "news":
                prompt = f"""
                You are an expert news analyst and journalist. Analyze the following search results about "{query_text}".
                Focus on extracting relevant news information, identifying media trends, detecting bias, and highlighting key events.

                For breaking news, emphasize timeliness and impact. For ongoing stories, highlight developments and changes.
                Be particularly attentive to information from credible news sources.

                Search results:
                {text}

                Provide the following:

                1. SUMMARY: A concise, factual summary of the information (3-5 sentences max).
                
                2. INSIGHTS: Key observations about the news coverage, including:
                   - Identify any media bias or slant in the reporting
                   - Note the recency and currency of the information
                   - Highlight consensus vs. conflicting viewpoints
                   - Provide context on how this news fits into broader narratives
                   
                3. CROSS-REFERENCES: Connections between different sources, contradictions, or corroborations.
                
                4. TAGS: Generate 5-10 relevant tags for categorizing this topic, including geographic locations, key figures, organizations, themes, and events. Format as a simple list of single words or short phrases.
                """
            elif analysis_focus == "geolocation":
                prompt = f"""
                You are an expert geographic analyst specializing in geospatial intelligence. Analyze the following search results about "{query_text}" with a focus on geographic and location-based information.

                Pay special attention to:
                - Specific locations mentioned (cities, countries, regions)
                - Geographic patterns and trends
                - Regional connections to global events
                - Spatial relationships between events and entities

                Search results:
                {text}

                Provide the following:

                1. SUMMARY: A concise, factual summary of the information with emphasis on geographic aspects (3-5 sentences max).
                
                2. INSIGHTS: Key observations about the geographic patterns, including:
                   - Identify patterns in the spatial distribution of events
                   - Note any regional concentrations of activity
                   - Highlight connections between locations
                   - Suggest how geography influences the topic
                   
                3. CROSS-REFERENCES: Geographic connections between different sources, contradictions in location data, or corroborations of regional trends.
                
                4. TAGS: Generate 5-10 relevant tags with emphasis on geographic locations, regions, countries, and location-related concepts. Format as a simple list of single words or short phrases.
                """
            else:
                # Default prompt
                prompt = f"""
                You are a digital research assistant. Analyze these search results for "{query_text}".
                Search results: {text}

                Provide the following:
                1. SUMMARY: A concise, factual summary of the information (3-5 sentences max).
                2. INSIGHTS: Key observations, patterns, contradictions, or unique perspectives from the results.
                3. CROSS-REFERENCES: Connections between different sources, contradictions, or corroborations.
                4. TAGS: Generate 5-10 relevant tags for categorizing this topic. Format as a simple list of single words or short phrases.
                """

            # Adjust prompt for language if not English
            if language != "en":
                prompt += f"\nRespond in {language}."

            prompt_parts = [prompt]

            # Use the Gemini API to generate a response
            response = self.gemini_model.generate_content(prompt_parts)
            response_text = response.text

            # Extract each section
            summary_pattern = r"(?:SUMMARY:|1\.)[^\n]*\n(.*?)(?:\n\s*\n|\n\s*INSIGHTS:|\n\s*2\.)"
            insights_pattern = r"(?:INSIGHTS:|2\.)[^\n]*\n(.*?)(?:\n\s*\n|\n\s*CROSS-REFERENCES:|\n\s*3\.)"
            cross_references_pattern = r"(?:CROSS-REFERENCES:|3\.)[^\n]*\n(.*?)(?:\n\s*\n|\n\s*TAGS:|\n\s*4\.)"
            tags_pattern = r"(?:TAGS:|4\.)[^\n]*\n(.*?)(?:\n\s*\n|$)"

            summary_match = re.search(summary_pattern, response_text, re.DOTALL)
            insights_match = re.search(insights_pattern, response_text, re.DOTALL)
            cross_references_match = re.search(
                cross_references_pattern, response_text, re.DOTALL
            )
            tags_match = re.search(tags_pattern, response_text, re.DOTALL)

            # Extract and clean up each section
            summary = (
                summary_match.group(1).strip()
                if summary_match
                else "No summary available."
            )
            insights = (
                insights_match.group(1).strip()
                if insights_match
                else "No insights available."
            )
            cross_references = (
                cross_references_match.group(1).strip()
                if cross_references_match
                else "No cross-references available."
            )

            # For tags, extract individual tags
            tags_text = tags_match.group(1).strip() if tags_match else ""
            # Clean up the tags (remove numbers, bullets, etc.)
            tags = []
            for line in tags_text.split("\n"):
                # Remove leading numbers, bullets, dashes, etc.
                clean_line = re.sub(r"^\s*[\d\-\*\•\-]+\s*", "", line).strip()
                if clean_line and ":" not in clean_line:  # Skip likely headers
                    tags.append(clean_line.strip())

            # Save the Gemini response to the database
            gemini_data = {
                "summary": summary,
                "insights": insights,
                "cross_references": cross_references,
                "tags": tags,
            }

            # If the query is an object with an ID, save the response to the database
            if hasattr(query, "id"):
                self.save_gemini_response(query, gemini_data)

            return gemini_data

        except google.api_core.exceptions.GoogleAPIError as e:
            print(f"   ❌ Error generating Gemini analysis: {e}")
            # Return empty data in case of error
            return {
                "summary": "Error generating summary.",
                "insights": "Error generating insights.",
                "cross_references": "Error generating cross-references.",
                "tags": [],
            }
        except Exception as e:
            print(f"   ❌ Unexpected error in Gemini analysis: {e}")
            return {
                "summary": "Error generating summary.",
                "insights": "Error generating insights.",
                "cross_references": "Error generating cross-references.",
                "tags": [],
            }

    def save_gemini_response(self, query, gemini_data):
        """
        Saves or updates the Gemini response for a given query.
        Uses the proven method of fetching query ID properly.
        """
        try:
            # 🔹 Step 1: Use the WORKING method to fetch query ID
            query = (
                db.session.query(Query).filter(Query.query_text == query.query_text).first()
            )

            if not query:
                print(f"   ❌ ERROR: No matching query found for '{query.query_text}'.")
                return

            # 🔹 Step 2: Get the ID using the known working method
            query_id = query.id

            print(f"   🔍 Fetched Query ID: {query_id}")

            # 🔹 Step 3: Ensure 'cross_references' and 'tags' are properly formatted
            cross_references = gemini_data.get("cross_references", "")
            if isinstance(cross_references, list):
                cross_references = ", ".join(
                    str(ref).strip() for ref in cross_references if ref
                )

            tags = gemini_data.get("tags", [])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(",") if tag.strip()]

            # 🔹 Step 4: Check if Gemini response already exists
            existing_response = (
                db.session.query(GeminiResponse)
                .filter(GeminiResponse.query_id == query_id)
                .first()
            )

            if existing_response:
                # ✅ Update existing response
                existing_response.summary = gemini_data.get(
                    "summary", "No summary available."
                )
                existing_response.insights = gemini_data.get(
                    "insights", "No insights available."
                )
                existing_response.cross_references = cross_references
                existing_response.tags = ", ".join(tags)
                print("   🔄 Existing Gemini response updated.")
            else:
                # ✅ Insert new response
                new_gemini_response = GeminiResponse(
                    query_id=query_id,  # This is now 100% a valid integer
                    summary=gemini_data.get("summary", "No summary available."),
                    insights=gemini_data.get("insights", "No insights available."),
                    cross_references=cross_references,
                    tags=", ".join(tags),
                )
                db.session.add(new_gemini_response)
                print("   ✅ Gemini response saved.")

            # 🔹 Step 5: Handle tags
            for tag_name in tags:
                tag = db.session.query(Tag).filter(Tag.tag == tag_name).first()
                if not tag:
                    tag = Tag(tag=tag_name)
                    db.session.add(tag)
                    db.session.commit()

                # Associate the tag with the query
                if tag not in query.tags:
                    query.tags.append(tag)

            db.session.commit()

        except Exception as e:
            print(f"   ❌ Error saving Gemini response: {e}")
            db.session.rollback()
