from flask import request, jsonify, render_template
from models import db, Query, Result, Tag, GeminiResponse, query_tag_association
from osint_helper import OSINTHelper
from sqlalchemy.exc import IntegrityError
import logging
import os
from dotenv import load_dotenv


def init_routes(app):
    # Load environment variables
    load_dotenv()

    # Initialize OSINT helper
    osint_helper = OSINTHelper()

    """
    General menu items
    """

    @app.route("/")
    def home():
        return render_template("dashboard.html")

    @app.route("/general_knowledge")
    def general_knowledge():
        return render_template("menu_items/general-knowledge.html")

    @app.route("/person_of_interest")
    def person_of_interest():
        return render_template("menu_items/person-of-interest.html")

    @app.route("/domain_analysis")
    def domain_analysis():
        return render_template("menu_items/domain-analysis.html")

    @app.route("/threat_intelligence")
    def threat_intelligence():
        return render_template("menu_items/threat-intelligence.html")

    @app.route("/network_recon")
    def network_recon():
        return render_template("menu_items/network-recon.html")

    @app.route("/social_media_analysis")
    def social_media_analysis():
        return render_template("menu_items/social-media-analysis.html")

    @app.route("/image_analysis")
    def image_analysis():
        return render_template("menu_items/image-analysis.html")

    @app.route("/email_verification")
    def email_verification():
        return render_template("menu_items/email-verification.html")

    @app.route("/phone_number_lookup")
    def phone_number_lookup():
        return render_template("menu_items/phone-number-lookup.html")

    @app.route("/geolocation")
    def geolocation():
        return render_template("menu_items/geolocation.html")

    @app.route("/news_monitoring")
    def news_monitoring():
        return render_template("menu_items/news-monitoring.html")

    """
    Api keys management
    """

    @app.route("/api_keys")
    def api_keys():
        # Read all API keys from .env file
        api_keys = {
            # General Knowledge APIs
            "NEWSAPI_KEY": os.getenv("NEWSAPI_KEY"),
            "GSE_API_KEY": os.getenv("GSE_API_KEY"),
            "GSE_ID": os.getenv("GSE_ID"),
            "WOLFRAM_ALPHA_APP_ID": os.getenv("WOLFRAM_ALPHA_APP_ID"),
            "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
            "WIKIPEDIA_API_KEY": os.getenv("WIKIPEDIA_API_KEY"),
            # Person of Interest APIs
            "HUNTER_API_KEY": os.getenv("HUNTER_API_KEY"),
            "PIPL_API_KEY": os.getenv("PIPL_API_KEY"),
            "HIBP_API_KEY": os.getenv("HIBP_API_KEY"),
            "TRUECALLER_API_KEY": os.getenv("TRUECALLER_API_KEY"),
            "TWITTER_API_KEY": os.getenv("TWITTER_API_KEY"),
            "TINEYE_API_KEY": os.getenv("TINEYE_API_KEY"),
            # Domain Analysis APIs
            "WHOISXML_API_KEY": os.getenv("WHOISXML_API_KEY"),
            "SECURITYTRAILS_API_KEY": os.getenv("SECURITYTRAILS_API_KEY"),
            "BUILTWITH_API_KEY": os.getenv("BUILTWITH_API_KEY"),
            "URLSCAN_API_KEY": os.getenv("URLSCAN_API_KEY"),
            "VIRUSTOTAL_API_KEY": os.getenv("VIRUSTOTAL_API_KEY"),
            "WAYBACK_MACHINE_API_KEY": os.getenv("WAYBACK_MACHINE_API_KEY"),
            # Threat Intelligence APIs
            "ALIENVAULT_OTX_API_KEY": os.getenv("ALIENVAULT_OTX_API_KEY"),
            "HYBRID_ANALYSIS_API_KEY": os.getenv("HYBRID_ANALYSIS_API_KEY"),
            "HYBRID_ANALYSIS_SECRET": os.getenv("HYBRID_ANALYSIS_SECRET"),
            "SHODAN_API_KEY": os.getenv("SHODAN_API_KEY"),
            "THREATCROWD_API_KEY": os.getenv("THREATCROWD_API_KEY"),
            # Network Recon APIs
            "CENSYS_API_KEY": os.getenv("CENSYS_API_KEY"),
            "IPINFO_API_KEY": os.getenv("IPINFO_API_KEY"),
            "ABUSEIPDB_API_KEY": os.getenv("ABUSEIPDB_API_KEY"),
            # Social Media Analysis APIs
            "REDDIT_API_KEY": os.getenv("REDDIT_API_KEY"),
            "INSTAGRAM_API_KEY": os.getenv("INSTAGRAM_API_KEY"),
            "FACEBOOK_GRAPH_API_KEY": os.getenv("FACEBOOK_GRAPH_API_KEY"),
            # Image Analysis APIs
            "GOOGLE_IMAGE_API_KEY": os.getenv("GOOGLE_IMAGE_API_KEY"),
            "YANDEX_IMAGE_API_KEY": os.getenv("YANDEX_IMAGE_API_KEY"),
            # Email Verification APIs
            "HUNTER_IO_API_KEY": os.getenv("HUNTER_IO_API_KEY"),
            "HIBP_API_KEY": os.getenv("HIBP_API_KEY"),
            "PIPL_API_KEY": os.getenv("PIPL_API_KEY"),
            # Phone Number Lookup APIs
            "TRUECALLER_API_KEY": os.getenv("TRUECALLER_API_KEY"),
            "WHITEPAGES_API_KEY": os.getenv("WHITEPAGES_API_KEY"),
            "NUMVERIFY_API_KEY": os.getenv("NUMVERIFY_API_KEY"),
            # Geolocation APIs
            "OPENCAGE_API_KEY": os.getenv("OPENCAGE_API_KEY"),
            "GOOGLE_MAPS_API_KEY": os.getenv("GOOGLE_MAPS_API_KEY"),
            # News Monitoring APIs
            "GDELT_API_KEY": os.getenv("GDELT_API_KEY"),
            "GOOGLE_TRENDS_API_KEY": os.getenv("GOOGLE_TRENDS_API_KEY"),
            # Other APIs
            "APIFY_API_KEY": os.getenv("APIFY_API_KEY"),
            "TAVILY_API_KEY": os.getenv("TAVILY_API_KEY"),
        }
        return render_template("api_keys.html", api_keys=api_keys)

    @app.route("/api/update_api_keys", methods=["POST"])
    def update_api_keys():
        try:
            data = request.json
            with open(".env", "w") as env_file:
                for key, value in data.items():
                    env_file.write(f"{key}={value}\n")
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    """
    Api Routes
    """

    @app.route("/search", methods=["POST"])
    def search():
        query = request.form.get("query")
        if not query or query.strip() == "":
            return jsonify({"error": "Query cannot be empty"}), 400

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
