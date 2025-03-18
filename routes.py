from flask import request, jsonify, render_template
from models import db, Query, Result, Tag, GeminiResponse, query_tag_association
from osint_helper import OSINTHelper
from sqlalchemy.exc import IntegrityError
import logging


def init_routes(app):
    # Initialize OSINT helper
    osint_helper = OSINTHelper()

    @app.route("/")
    def home():
        return render_template("index.html")
        # return render_template("dashboard.html")

    @app.route("/search", methods=["POST"])
    def search():
        query = request.form.get("query")
        if not query or query.strip() == "":
            return jsonify({"error": "Query cannot be empty"}), 400

        # normalized_query = OSINTHelper.normalize_query(query)  # ✅ Normalize query
        query = OSINTHelper.normalize_query(query)

        try:
            existing_query = (
                db.session.query(Query)
                .filter(Query.query_text == query.strip())
                .first()
            )
            if existing_query:
                stored_results = (
                    db.session.query(Result)
                    .filter(Result.query_id == existing_query.id)
                    .all()
                )
                stored_tags = (
                    db.session.query(Tag)
                    .join(query_tag_association)
                    .filter(query_tag_association.c.query_id == existing_query.id)
                    .all()
                )
                gemini_response = (
                    db.session.query(GeminiResponse)
                    .filter(GeminiResponse.query_id == existing_query.id)
                    .first()
                )

                osint_helper.apply_sentiment_analysis(stored_results)
                print(f"🔍 Query exists : using stored data for {query}")

                formatted_results = {}
                for res in stored_results:
                    if res.source not in formatted_results:
                        formatted_results[res.source] = []
                    formatted_results[res.source].append(
                        {
                            "title": res.title,
                            "snippet": res.snippet,
                            "url": res.url,
                            "sentiment_score": res.sentiment_score,
                        }
                    )

                return jsonify(
                    {
                        "results": formatted_results,
                        "summary": gemini_response.summary
                        if gemini_response
                        else "No summary available.",
                        "insights": gemini_response.insights
                        if gemini_response
                        else "No insights available.",
                        "cross_references": gemini_response.cross_references
                        if gemini_response
                        else "No cross-references available.",
                        "tags": [tag.tag for tag in stored_tags],
                    }
                )

            new_query = Query(query_text=query.strip())
            print(f"🔍 New Query : searcing for {query}")
            db.session.add(new_query)
            db.session.commit()

            results = osint_helper.perform_search(query)
            for source, data in results.items():
                if data:
                    osint_helper.save_results_to_db(new_query.id, source, data)

            new_results = (
                db.session.query(Result).filter(Result.query_id == new_query.id).all()
            )
            osint_helper.apply_sentiment_analysis(new_results)
            aggregated_results = osint_helper.aggregate_results(results)
            gemini_response = osint_helper.analyze_with_gemini(
                new_query, aggregated_results
            )

            return jsonify(
                {
                    "results": results,
                    "summary": gemini_response["summary"],
                    "insights": gemini_response["insights"],
                    "cross_references": gemini_response["cross_references"],
                    "tags": gemini_response["tags"],
                }
            )

        except IntegrityError:
            db.session.rollback()
            return jsonify({"error": "Query already exists."}), 200
        except Exception as e:
            logging.error(f"Error in search route: {str(e)}", exc_info=True)
            db.session.rollback()
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500
