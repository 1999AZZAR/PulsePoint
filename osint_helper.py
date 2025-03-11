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

    def perform_search(self, query):
        """
        Performs search using OSINT tools and returns results.
        """
        return {
            "wikipedia": self.search_wikipedia(query) or [],
            "news_everything": self.fetch_news(query, endpoint="everything") or [],
            "news_top_headlines": self.fetch_news(query, endpoint="top-headlines")
            or [],
            "google": self.fetch_gse_results(query) or [],
            "wolfram_alpha": self.fetch_wolfram_alpha(query) or [],
            "semantic_scholar": self.fetch_semantic_scholar(query) or [],
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

    def analyze_with_gemini(self, query, text, language="en"):
        """
        Analyze text using Gemini, save the response, and return structured JSON.

        Args:
            query (Query): The query object (needed for saving results).
            text (str): The input text to analyze.
            language (str): Language preference ("en" for English, "id" for Indonesian).

        Returns:
            dict: Structured JSON containing 'summary', 'insights', 'cross_references', and 'tags'.
        """
        gemini_text = "No summary available."

        try:
            # Define the strict JSON format expected from Gemini
            prompt_template = {
                "id": """
                    Anda adalah asisten AI yang mengekstrak informasi terstruktur dari teks.
                    Harap kembalikan respons **dalam format JSON yang ketat**.

                    **Format JSON yang Diharapkan:**
                    ```json
                    {{
                        "summary": "Ringkasan singkat dari teks.",
                        "insights": "Informasi penting atau wawasan yang ditemukan dalam teks.",
                        "cross_references": "hubungan antar referensi (dalam bentuk paragraf)",
                        "tags": ["tag1", "tag2", "tag3"]
                    }}
                    ```

                    **Teks yang akan dianalisis:** {text}
                """,
                "en": """
                    You are an AI assistant that extracts structured information from text.
                    Return a response **strictly in JSON format**.

                    **Expected JSON Format:**
                    ```json
                    {{
                        "summary": "A brief summary of the text.",
                        "insights": "Key information or insights extracted from the text.",
                        "cross_references":"relationships between references (in a paragraph form)",
                        "tags": ["tag1", "tag2", "tag3"]
                    }}
                    ```

                    **Text to analyze:** {text}
                """,
            }

            # Send request to Gemini API
            detailed_prompt = prompt_template.get(
                language, prompt_template["en"]
            ).format(text=text)
            response = self.gemini_model.generate_content(detailed_prompt)

            if not response or not hasattr(response, "text"):
                raise ValueError("Empty or invalid response from Gemini API.")

            gemini_text = response.text.strip()

            # Extract JSON response
            cleaned_text = re.sub(
                r"```json\n(.*?)\n```", r"\1", gemini_text, flags=re.DOTALL
            ).strip()
            cleaned_text = re.sub(
                r"```\n(.*?)\n```", r"\1", cleaned_text, flags=re.DOTALL
            ).strip()
            if "{" in cleaned_text:
                cleaned_text = cleaned_text[cleaned_text.find("{") :]
            if "}" in cleaned_text:
                cleaned_text = cleaned_text[: cleaned_text.rfind("}") + 1]

            # ✅ Attempt JSON parsing
            parsed_response = json.loads(cleaned_text)

            # ✅ Extract values properly
            gemini_data = {
                "summary": parsed_response.get("summary", "No summary available."),
                "insights": parsed_response.get("insights", "No insights available."),
                "cross_references": parsed_response.get("cross_references", []),
                "tags": parsed_response.get("tags", []),
            }

            # ✅ Automatically save response to database
            self.save_gemini_response(
                query.query_text, gemini_data
            )  # Pass query_text instead of query object

            return gemini_data  # Return structured data

        except json.JSONDecodeError:
            print(f"   ❌ Error: Gemini response is not valid JSON.")
            return {
                "summary": gemini_text,
                "insights": "No insights available.",
                "cross_references": "",
                "tags": "",
            }

        except Exception as e:
            print(f"   ❌ ERROR: Gemini API response processing failed: {e}")
            return {
                "summary": gemini_text,
                "insights": "No insights available.",
                "cross_references": "",
                "tags": "",
            }

    def save_gemini_response(self, query_text, gemini_data):
        """
        Saves or updates the Gemini response for a given query.
        Uses the proven method of fetching query ID properly.
        """
        try:
            # 🔹 Step 1: Use the WORKING method to fetch query ID
            query = (
                db.session.query(Query).filter(Query.query_text == query_text).first()
            )

            if not query:
                print(f"   ❌ ERROR: No matching query found for '{query_text}'.")
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
