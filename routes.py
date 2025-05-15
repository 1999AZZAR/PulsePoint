from flask import request, jsonify, render_template
from models import db, Query, Result, Tag, GeminiResponse, query_tag_association
from osint_helper import OSINTHelper
from sqlalchemy.exc import IntegrityError
import logging
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import re


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

    @app.route("/news_search", methods=["POST"])
    def news_search():
        """
        Endpoint specifically for news monitoring searches.
        Prioritizes news sources and can include additional news-specific parameters.
        """
        query = request.form.get("query")
        if not query or query.strip() == "":
            return jsonify({"error": "Query cannot be empty"}), 400

        query = OSINTHelper.normalize_query(query)
        
        # Get additional parameters
        negative_query = request.form.get("negative_query", "")
        from_date = request.form.get("from_date", "")
        to_date = request.form.get("to_date", "")
        language = request.form.get("language", "en")
        
        try:
            # Check for existing query in database
            existing_query = (
                db.session.query(Query)
                .filter(Query.query_text == query.strip())
                .first()
            )
            
            if existing_query:
                # Retrieve stored results with focus on news sources
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
                print(f"🔍 News search: using stored data for {query}")

                # Format results with news sources first
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
                        "summary": gemini_response.summary if gemini_response else "No summary available.",
                        "insights": gemini_response.insights if gemini_response else "No insights available.",
                        "cross_references": gemini_response.cross_references if gemini_response else "No cross-references available.",
                        "tags": [tag.tag for tag in stored_tags],
                    }
                )

            # Create new query and perform search
            new_query = Query(query_text=query.strip())
            print(f"🔍 New news search: searching for {query}")
            db.session.add(new_query)
            db.session.commit()

            # For news monitoring, we prioritize news sources
            news_results = {
                "news_top_headlines": osint_helper.fetch_news(
                    query, 
                    endpoint="top-headlines", 
                    negative_query=negative_query.split(",") if negative_query else None,
                    language=language,
                    from_date=from_date,
                    to_date=to_date,
                    page_size=15
                ) or [],
                
                "news_everything": osint_helper.fetch_news(
                    query, 
                    endpoint="everything", 
                    negative_query=negative_query.split(",") if negative_query else None,
                    language=language,
                    from_date=from_date,
                    to_date=to_date,
                    page_size=15
                ) or [],
                
                # Add RSS feeds - completely free, no API key required
                "rss_news": osint_helper.fetch_rss_news(
                    query,
                    negative_query=negative_query.split(",") if negative_query else None,
                    max_results=20
                ) or [],
                
                # Add GNews results if API key is available
                "gnews": osint_helper.fetch_gnews(
                    query,
                    negative_query=negative_query.split(",") if negative_query else None,
                    language=language,
                    from_date=from_date,
                    to_date=to_date,
                    max_results=10
                ) or [],
                
                # Add MediaStack results if API key is available
                "mediastack": osint_helper.fetch_mediastack(
                    query,
                    negative_query=negative_query.split(",") if negative_query else None,
                    language=language,
                    from_date=from_date,
                    to_date=to_date,
                    max_results=10
                ) or [],
                
                # Add Current News API results (free and doesn't require API key)
                "current_news": osint_helper.fetch_current_news(
                    query,
                    language=language,
                    max_results=10
                ) or [],
            }
            
            # Also include other sources but with lower priority
            other_results = {
                "google": osint_helper.fetch_gse_results(
                    query, 
                    negative_query=negative_query.split(",") if negative_query else None,
                    exclude_keyword="wikipedia",
                    num_results=5
                ) or [],
                
                "wikipedia": osint_helper.search_wikipedia(
                    query, 
                    negative_query=negative_query.split(",") if negative_query else None,
                    num_results=3
                ) or [],
                
                "semantic_scholar": osint_helper.fetch_semantic_scholar(
                    query, 
                    negative_query=negative_query.split(",") if negative_query else None,
                    num_results=3
                ) or [],
                
                "wolfram_alpha": osint_helper.fetch_wolfram_alpha(query) or [],
            }
            
            # Combine results with news sources first
            results = {**news_results, **other_results}
            
            # Save results to database
            for source, data in results.items():
                if data:
                    osint_helper.save_results_to_db(new_query.id, source, data)

            # Apply sentiment analysis and generate insights
            new_results = (
                db.session.query(Result).filter(Result.query_id == new_query.id).all()
            )
            osint_helper.apply_sentiment_analysis(new_results)
            
            # Generate analysis with special focus on news
            aggregated_results = osint_helper.aggregate_results(results)
            gemini_response = osint_helper.analyze_with_gemini(
                new_query, aggregated_results, language, analysis_focus="news"
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
            logging.error(f"Error in news search route: {str(e)}", exc_info=True)
            db.session.rollback()
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500

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

    @app.route("/geo_search", methods=["POST"])
    def geo_search():
        """
        Endpoint for geolocation-focused searches.
        Handles three types of input:
        1. Regular text queries (e.g. "earthquakes in California")
        2. IP addresses (e.g. "8.8.8.8")
        3. Coordinates (e.g. "37.7749,-122.4194" or "37.7749, -122.4194")
        
        Prioritizes sources with geographic data, especially GDELT.
        """
        query = request.form.get("query")
        if not query or query.strip() == "":
            return jsonify({"error": "Query cannot be empty"}), 400
            
        # Get additional parameters
        negative_query = request.form.get("negative_query", "")
        from_date = request.form.get("from_date", "")
        to_date = request.form.get("to_date", "")
        from_year = request.form.get("from_year", "")
        to_year = request.form.get("to_year", "")
        language = request.form.get("language", "en")
        
        # Detect input type (IP, coordinates, or regular query)
        input_type = "query"  # Default
        ip_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        coord_pattern = r"^(-?\d+\.?\d*),\s*(-?\d+\.?\d*)$"
        
        location_data = None
        
        # Initialize OSINT helper
        osint_helper = OSINTHelper()
        
        # Check if it's an IP address
        if re.match(ip_pattern, query.strip()):
            input_type = "ip"
            ip_address = query.strip()
            print(f"🌎 Detected IP address: {ip_address}")
            location_data = osint_helper.geolocate_ip(ip_address)
            
        # Check if it's coordinates
        elif re.match(coord_pattern, query.strip()):
            input_type = "coordinates"
            coords = re.match(coord_pattern, query.strip())
            lat = float(coords.group(1))
            lon = float(coords.group(2))
            print(f"🌎 Detected coordinates: {lat}, {lon}")
            location_data = osint_helper.reverse_geocode(lat, lon)
            
            # Create a more descriptive query for regular search
            if location_data and location_data.get("formatted"):
                query = location_data.get("formatted")
                print(f"🌎 Using location name: {query}")
        
        # Normalize the query for database lookup
        normalized_query = OSINTHelper.normalize_query(query)
        
        try:
            # For direct IP or coordinate lookups, don't use cached results
            if input_type in ["ip", "coordinates"] and location_data:
                # Create new query for database storage
                new_query = Query(query_text=query.strip())
                print(f"🗺️ New geo search: {input_type} lookup for {query}")
                db.session.add(new_query)
                db.session.commit()
                
                # Format the direct location result
                results = {
                    "geo_direct_lookup": [{
                        "title": f"Location information for {query}",
                        "snippet": location_data.get("formatted", "Location information"),
                        "url": "",
                        "data": {
                            "location": {
                                "lat": location_data.get("coordinates", {}).get("lat"),
                                "lon": location_data.get("coordinates", {}).get("lon"),
                                "formatted": location_data.get("formatted"),
                                "country": location_data.get("country"),
                                "region": location_data.get("region") or location_data.get("state"),
                                "city": location_data.get("city")
                            },
                            "location_data": location_data
                        }
                    }]
                }
                
                # Save direct lookup result to database
                osint_helper.save_results_to_db(new_query.id, "geo_direct_lookup", results["geo_direct_lookup"])
                
                # For IPs and coordinates, also fetch context information
                if input_type == "ip":
                    # For IP addresses, add relevant network information
                    additional_query = f"information about {location_data.get('org', 'this network')} {location_data.get('country', '')}"
                    print(f"🔍 Adding context: {additional_query}")
                    
                    # Get some general information about this location
                    geo_results = {
                        "gdelt": osint_helper.fetch_gdelt(
                            location_data.get("city", "") or location_data.get("region", "") or location_data.get("country", ""),
                            max_results=10,
                            timespan="1month"
                        ) or []
                    }
                    
                    # Save these additional results
                    for source, data in geo_results.items():
                        if data:
                            osint_helper.save_results_to_db(new_query.id, source, data)
                    
                    # Combine results
                    results.update(geo_results)
                
                elif input_type == "coordinates":
                    # For coordinates, add information about the area
                    area_name = location_data.get("city", "") or location_data.get("region", "") or location_data.get("country", "")
                    if area_name:
                        print(f"🔍 Getting info about area: {area_name}")
                        geo_results = {
                            "gdelt": osint_helper.fetch_gdelt(
                                area_name,
                                max_results=15,
                                timespan="1month"
                            ) or []
                        }
                        
                        # Save these additional results
                        for source, data in geo_results.items():
                            if data:
                                osint_helper.save_results_to_db(new_query.id, source, data)
                        
                        # Combine results
                        results.update(geo_results)
                
                # Generate analysis with special focus on geolocation
                osint_helper.apply_sentiment_analysis(
                    db.session.query(Result).filter(Result.query_id == new_query.id).all()
                )
                
                # Prepare results for Gemini
                aggregated_results = osint_helper.aggregate_results(results)
                gemini_response = osint_helper.analyze_with_gemini(
                    new_query, aggregated_results, language, analysis_focus="geolocation"
                )
                
                return jsonify(
                    {
                        "results": results,
                        "location_data": location_data,
                        "input_type": input_type,
                        "summary": gemini_response["summary"],
                        "insights": gemini_response["insights"],
                        "cross_references": gemini_response["cross_references"],
                        "tags": gemini_response["tags"],
                    }
                )
            
            # For regular text queries or if location lookup failed, use normal process
            # Check for existing query in database
            existing_query = (
                db.session.query(Query)
                .filter(Query.query_text == normalized_query)
                .first()
            )
            
            if existing_query:
                # Retrieve stored results with focus on location-enabled sources
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
                print(f"🗺️ Geo search: using stored data for {query}")

                # Format results with geo-enabled sources first
                formatted_results = {}
                for res in stored_results:
                    if res.source not in formatted_results:
                        formatted_results[res.source] = []
                    
                    # Parse the JSON data fields if they exist
                    location = None
                    themes = None
                    
                    try:
                        # Try to extract location and themes if available
                        result_data = json.loads(res.data) if res.data else {}
                        location = result_data.get("location")
                        themes = result_data.get("themes")
                    except:
                        pass
                    
                    formatted_results[res.source].append(
                        {
                            "title": res.title,
                            "snippet": res.snippet,
                            "url": res.url,
                            "sentiment_score": res.sentiment_score,
                            "location": location,
                            "themes": themes
                        }
                    )

                return jsonify(
                    {
                        "results": formatted_results,
                        "summary": gemini_response.summary if gemini_response else "No summary available.",
                        "insights": gemini_response.insights if gemini_response else "No insights available.",
                        "cross_references": gemini_response.cross_references if gemini_response else "No cross-references available.",
                        "tags": [tag.tag for tag in stored_tags],
                    }
                )

            # Create new query and perform search
            new_query = Query(query_text=query.strip())
            print(f"🗺️ New geo search: searching for {query}")
            db.session.add(new_query)
            db.session.commit()

            # For geolocation, we prioritize GDELT which has location data
            # Set a longer timespan for GDELT to capture more geo-data
            gdelt_timespan = "1month"
            if from_date and to_date:
                # If date range is specified, adjust the timespan accordingly
                try:
                    from_date_obj = datetime.strptime(from_date, "%Y-%m-%d")
                    to_date_obj = datetime.strptime(to_date, "%Y-%m-%d")
                    date_diff = (to_date_obj - from_date_obj).days
                    
                    if date_diff <= 1:
                        gdelt_timespan = "1day"
                    elif date_diff <= 3:
                        gdelt_timespan = "3days"
                    elif date_diff <= 7:
                        gdelt_timespan = "1week"
                    elif date_diff <= 14:
                        gdelt_timespan = "2weeks"
                    elif date_diff <= 30:
                        gdelt_timespan = "1month"
                    elif date_diff <= 60:
                        gdelt_timespan = "2months"
                    elif date_diff <= 180:
                        gdelt_timespan = "6months"
                    else:
                        gdelt_timespan = "1year"
                except:
                    # If there's an error parsing dates, use default timespan
                    pass

            geo_results = {
                # GDELT is the primary data source for geolocation
                "gdelt": osint_helper.fetch_gdelt(
                    query, 
                    negative_query=negative_query.split(",") if negative_query else None,
                    max_results=30,  # Fetch more results for better geo-coverage
                    timespan=gdelt_timespan
                ) or [],
                
                # Add other news sources that might have location data
                "news_top_headlines": osint_helper.fetch_news(
                    query, 
                    endpoint="top-headlines", 
                    negative_query=negative_query.split(",") if negative_query else None,
                    language=language,
                    from_date=from_date,
                    to_date=to_date,
                    page_size=10
                ) or [],
                
                "rss_news": osint_helper.fetch_rss_news(
                    query,
                    negative_query=negative_query.split(",") if negative_query else None,
                    max_results=15
                ) or [],
            }
            
            # Include other sources as well, but with lower priority
            other_results = {
                "gnews": osint_helper.fetch_gnews(
                    query,
                    negative_query=negative_query.split(",") if negative_query else None,
                    language=language,
                    from_date=from_date,
                    to_date=to_date,
                    max_results=5
                ) or [],
                
                "mediastack": osint_helper.fetch_mediastack(
                    query,
                    negative_query=negative_query.split(",") if negative_query else None,
                    language=language,
                    from_date=from_date,
                    to_date=to_date,
                    max_results=5
                ) or [],
                
                "current_news": osint_helper.fetch_current_news(
                    query,
                    language=language,
                    max_results=5
                ) or [],
                
                "google": osint_helper.fetch_gse_results(
                    query, 
                    negative_query=negative_query.split(",") if negative_query else None,
                    exclude_keyword="wikipedia",
                    num_results=3
                ) or [],
                
                "wikipedia": osint_helper.search_wikipedia(
                    query, 
                    negative_query=negative_query.split(",") if negative_query else None,
                    num_results=3
                ) or [],
            }
            
            # Combine results with geo-enabled sources first
            results = {**geo_results, **other_results}
            
            # Save results to database with full data including location information
            for source, data in results.items():
                if data:
                    # For GDELT results, ensure location data is saved
                    if source == "gdelt":
                        for item in data:
                            if "location" in item or "themes" in item:
                                # Store the additional data in the data field
                                item["data"] = json.dumps({
                                    "location": item.get("location"),
                                    "themes": item.get("themes")
                                })
                    
                    osint_helper.save_results_to_db(new_query.id, source, data)

            # Apply sentiment analysis and generate insights
            new_results = (
                db.session.query(Result).filter(Result.query_id == new_query.id).all()
            )
            osint_helper.apply_sentiment_analysis(new_results)
            
            # Generate analysis with special focus on geolocation
            aggregated_results = osint_helper.aggregate_results(results)
            gemini_response = osint_helper.analyze_with_gemini(
                new_query, aggregated_results, language, analysis_focus="geolocation"
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
            logging.error(f"Error in geo search route: {str(e)}", exc_info=True)
            db.session.rollback()
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500
