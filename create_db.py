from flask import Flask
from models import db, Query, Result, GeminiResponse, Tag
import sqlite3
import os

# Create a Flask app
app = Flask(__name__)

# Get absolute path to the instance folder
instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
db_path = os.path.join(instance_path, 'osint.db')

# Make sure instance directory exists
if not os.path.exists(instance_path):
    os.makedirs(instance_path)
    print(f"Created instance directory at {instance_path}")

# Configure SQLAlchemy with absolute path
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the database
db.init_app(app)

def ensure_instance_dir():
    """Make sure the instance directory exists."""
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
        print(f"Created instance directory at {instance_path}")

def create_tables():
    """Create all tables defined in models."""
    with app.app_context():
        db.create_all()
        print("Created all database tables")

def add_data_column():
    """Add the data column to the results table if it doesn't exist."""
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the column exists
        cursor.execute("PRAGMA table_info(results)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'data' not in columns:
            print("Adding data column to results table")
            cursor.execute("ALTER TABLE results ADD COLUMN data JSON")
            conn.commit()
            print("Successfully added data column")
        else:
            print("Data column already exists")
            
        # Close the connection
        conn.close()
    except Exception as e:
        print(f"Error adding data column: {e}")

if __name__ == "__main__":
    # Ensure instance directory exists
    ensure_instance_dir()
    
    # Create tables
    create_tables()
    
    # Add data column
    add_data_column()
    
    print(f"Database setup complete at {db_path}") 