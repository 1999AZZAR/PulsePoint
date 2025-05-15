from flask import current_app
from models import db, Query, Result, GeminiResponse
from collections import Counter
import sqlite3
import os
from flask import Flask

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

def setup_db(app):
    """Initialize the SQLite database with the required tables."""
    with app.app_context():
        # Create all tables defined in models.py
        db.create_all()
        
        # Apply migrations
        apply_migrations(app)
        
        print("Database setup complete.")

def apply_migrations(app):
    """Apply any necessary migrations to the database schema."""
    # Get the database URI from the app config
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    
    # For SQLite, the URI starts with 'sqlite:///'
    if db_uri.startswith('sqlite:///'):
        # Extract the path to the SQLite database file
        db_path = db_uri[10:]  # Remove 'sqlite:///'
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Migration 1: Add sentiment_score column to results table if it doesn't exist
        try:
            # Check if the column exists
            cursor.execute("PRAGMA table_info(results)")
            columns = [info[1] for info in cursor.fetchall()]
            
            if 'sentiment_score' not in columns:
                print("Applying migration: Add sentiment_score column to results table")
                cursor.execute("ALTER TABLE results ADD COLUMN sentiment_score REAL")
                conn.commit()
        except Exception as e:
            print(f"Error applying migration 1: {e}")
            
        # Migration 2: Add source_control column to queries table if it doesn't exist
        try:
            # Check if the column exists
            cursor.execute("PRAGMA table_info(queries)")
            columns = [info[1] for info in cursor.fetchall()]
            
            if 'source_control' not in columns:
                print("Applying migration: Add source_control column to queries table")
                cursor.execute("ALTER TABLE queries ADD COLUMN source_control JSON")
                conn.commit()
        except Exception as e:
            print(f"Error applying migration 2: {e}")
            
        # Migration 3: Add gemini_processed column to queries table if it doesn't exist
        try:
            # Check if the column exists
            cursor.execute("PRAGMA table_info(queries)")
            columns = [info[1] for info in cursor.fetchall()]
            
            if 'gemini_processed' not in columns:
                print("Applying migration: Add gemini_processed column to queries table")
                cursor.execute("ALTER TABLE queries ADD COLUMN gemini_processed BOOLEAN DEFAULT 0")
                conn.commit()
        except Exception as e:
            print(f"Error applying migration 3: {e}")
            
        # Migration 4: Add data column to results table if it doesn't exist
        try:
            # Check if the column exists
            cursor.execute("PRAGMA table_info(results)")
            columns = [info[1] for info in cursor.fetchall()]
            
            if 'data' not in columns:
                print("Applying migration: Add data column to results table")
                cursor.execute("ALTER TABLE results ADD COLUMN data JSON")
                conn.commit()
        except Exception as e:
            print(f"Error applying migration 4: {e}")
            
        # Close the connection
        conn.close()

def init_app():
    """Initialize the Flask application."""
    app = Flask(__name__)
    
    # Get absolute path to the instance folder
    instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
    db_path = os.path.join(instance_path, 'osint.db')
    
    # Make sure instance directory exists
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    
    # Configure SQLAlchemy with absolute path
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the database
    db.init_app(app)
    
    # Setup database and apply migrations
    setup_db(app)
    
    return app

if __name__ == "__main__":
    app = init_app()
