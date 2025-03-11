from flask import current_app
from models import db, Query, Result, GeminiResponse
from collections import Counter

# Default source_control structure
DEFAULT_SOURCE_CONTROL = {
    "wikipedia": 0,
    "news_everything": 0,
    "news_top_headlines": 0,
    "google": 0,
    "wolfram_alpha": 0,
    "semantic_scholar": 0,
}


def update_missing_values():
    """
    Updates the source_control and gemini_processed columns with actual values from related tables.
    """
    with current_app.app_context():
        try:
            print("🔄 Running update_missing_values...")
            queries = Query.query.all()

            for query in queries:
                # Fetch all results related to this query
                results = (
                    db.session.query(Result).filter(Result.query_id == query.id).all()
                )

                # Count occurrences of each source
                source_counts = Counter(result.source for result in results)

                # Create source_control dictionary with actual counts
                source_control_data = DEFAULT_SOURCE_CONTROL.copy()
                for source, count in source_counts.items():
                    if source in source_control_data:
                        source_control_data[source] = count

                # Update query's source_control and Gemini processing status
                query.source_control = source_control_data
                query.gemini_processed = (
                    db.session.query(GeminiResponse)
                    .filter_by(query_id=query.id)
                    .first()
                    is not None
                )

            db.session.commit()
            print("✅ Successfully updated missing values.")

        except Exception as e:
            print(f"❌ Error updating values: {e}")
            db.session.rollback()
        finally:
            db.session.close()
