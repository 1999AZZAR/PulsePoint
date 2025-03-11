from flask import current_app
from models import db, Query, Tag, GeminiResponse
from osint_helper import OSINTHelper
from datetime import datetime
from completer import query_processing_lock  # Import the lock

# Initialize OSINT helper
osint_helper = OSINTHelper()


def automatic_search():
    if not query_processing_lock.acquire(blocking=False):
        print("⚠️ Another instance is already running. Skipping automatic search...")
        return  # Prevent duplicate execution

    try:
        with current_app.app_context():
            # Find a tag that hasn't been used as a query yet
            unused_tag = (
                db.session.query(Tag)
                .filter(
                    ~db.session.query(Query)
                    .filter(Query.query_text == Tag.tag)
                    .exists()
                )
                .first()
            )

            if unused_tag:
                print(f"\n🔍 Performing automatic search for tag: {unused_tag.tag}")

                # Create a new Query entry
                query = OSINTHelper.normalize_query(unused_tag.tag)
                new_query = Query(query_text=query)
                db.session.add(new_query)
                db.session.commit()

                # Fetch results using OSINTHelper
                results = osint_helper.perform_search(query)

                # Save results to the database
                for source, data in results.items():
                    if data:  # Only save if data exists
                        osint_helper.save_results_to_db(new_query.id, source, data)

                # Aggregate results for Gemini analysis
                aggregated_results = osint_helper.aggregate_results(results)

                # Generate Gemini response
                print("   🔄 Generating Gemini response...")
                gemini_data = osint_helper.analyze_with_gemini(
                    new_query, aggregated_results
                )

            print("\n✅ Automatic search completed.")

    finally:
        query_processing_lock.release()  # Release lock after execution
