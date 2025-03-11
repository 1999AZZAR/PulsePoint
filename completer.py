from flask import current_app
from models import db, Query, Result, GeminiResponse
from osint_helper import OSINTHelper
import logging
import time
from typing import Dict, List, Any
import threading
from sqlalchemy.sql.expression import func

# Global lock to prevent duplicate runs
query_processing_lock = threading.Lock()


class GK_Completer:
    def __init__(self, app=None, api_call_delay: float = 2.0):
        """
        Initialize the GK_Completer with an OSINT helper and configurable API call delay.

        Args:
            app: Flask application instance (optional)
            api_call_delay: Delay in seconds between API calls to avoid rate limiting.
        """
        self.osint_helper = OSINTHelper()
        self.api_call_delay = api_call_delay
        self.app = app
        self.sources = [
            "wikipedia",
            "news_everything",
            "news_top_headlines",
            "google",
            "wolfram_alpha",
            "semantic_scholar",
        ]
        self.logger = logging.getLogger(__name__)

    def check_all_queries_per_source(
        self, min_results_per_source=4, max_queries_per_run=1
    ):
        """
        Check all queries and re-search sources that have insufficient results.
        Prevents duplicate execution by ensuring only one process runs at a time.
        """
        if not query_processing_lock.acquire(blocking=False):
            print("⚠️ Another instance is already running. Skipping this run...")
            return  # Prevent duplicate runs

        try:
            with current_app.app_context():
                queries = (
                    db.session.query(Query)
                    .filter(Query.gemini_processed == False)
                    .order_by(func.random())  # ✅ Select random queries
                    .limit(max_queries_per_run)
                    .all()
                )

                for query in queries:
                    query_id = query.id
                    query_text = query.query_text
                    print(
                        f"\n🔍 Performing Research and completion process for query {query_id}: {query_text}"
                    )

                    try:
                        # Fetch all results for this query
                        all_results = (
                            db.session.query(Result)
                            .filter(Result.query_id == query_id)
                            .all()
                        )
                        results_by_source = {}

                        for result in all_results:
                            if result.source not in results_by_source:
                                results_by_source[result.source] = []
                            results_by_source[result.source].append(
                                {
                                    "title": result.title,
                                    "snippet": result.snippet,
                                    "url": result.url,
                                }
                            )

                        if query.source_control is None:
                            query.source_control = {
                                source: 0 for source in self.sources
                            }

                        # 🔹 Step 1: Fetch missing results
                        for source in self.sources:
                            old_count = len(results_by_source.get(source, []))

                            if old_count < min_results_per_source:
                                print(
                                    f"   🔄 Source {source} has {old_count} results (insufficient). Re-searching..."
                                )
                                fresh_results = self._fetch_results_for_source(
                                    query_text, source
                                )

                                if fresh_results:
                                    self.osint_helper.save_results_to_db(
                                        query_id, source, fresh_results
                                    )
                                    new_count = old_count + len(fresh_results)
                                    print(
                                        f"   ✅ New results: {len(fresh_results)} | Total: {new_count}"
                                    )
                                else:
                                    new_count = old_count
                                    print(f"   ❌ No new results found.")

                                query.source_control[source] = new_count
                                time.sleep(self.api_call_delay)
                            else:
                                print(
                                    f"   ✅ Source {source} already has {old_count} results (sufficient)."
                                )

                        # 🔹 Step 2: Check and regenerate Gemini response if needed
                        gemini_response = (
                            db.session.query(GeminiResponse)
                            .filter_by(query_id=query_id)
                            .first()
                        )

                        if (
                            query.gemini_processed == False
                            or not gemini_response
                            or gemini_response.summary
                            in [
                                "❌ Gemini API quota exceeded.",
                                "No summary available.",
                            ]
                        ):
                            print("   🔄 Regenerating Gemini response...")

                            aggregated_results = self.osint_helper.aggregate_results(
                                results_by_source
                            )
                            gemini_data = self.osint_helper.analyze_with_gemini(
                                query, aggregated_results
                            )

                        # 🔹 Step 3: Mark query as fully processed
                        if all(
                            query.source_control[source] >= min_results_per_source
                            for source in self.sources
                        ):
                            query.gemini_processed = True

                        db.session.commit()

                    except Exception as e:
                        print(f"   ⚠️ Error processing query {query_id}: {str(e)}")
                        db.session.rollback()

                print("\n✅ Research and completion process finished!")

        finally:
            query_processing_lock.release()  # ✅ Release lock after completion

    def _fetch_results_for_source(
        self, query_text: str, source: str
    ) -> List[Dict[str, Any]]:
        """
        Fetch results for a specific source using the OSINTHelper.

        Args:
            query_text: The query text to search for.
            source: The source to fetch results from.
        """
        try:
            source_handlers = {
                "wikipedia": lambda: self.osint_helper.search_wikipedia(query_text, []),
                "news_everything": lambda: self.osint_helper.fetch_news(
                    query_text, endpoint="everything", negative_query=[], language="en"
                ),
                "news_top_headlines": lambda: self.osint_helper.fetch_news(
                    query_text,
                    endpoint="top-headlines",
                    negative_query=[],
                    language="en",
                ),
                "google": lambda: self.osint_helper.fetch_gse_results(query_text, []),
                "wolfram_alpha": lambda: self.osint_helper.fetch_wolfram_alpha(
                    query_text
                ),
                "semantic_scholar": lambda: self.osint_helper.fetch_semantic_scholar(
                    query_text, [], None, None
                ),
            }

            return source_handlers[source]() or []
        except Exception as e:
            print(f"   ⚠️ Error fetching results from {source}: {str(e)}")
            return []
