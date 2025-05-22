from flask import Flask
from routes import init_routes
from models import db
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import atexit
from auto_search import automatic_search
from completer import GK_Completer
from mig import update_missing_values, apply_migrations
import os


# Initialize Flask app
app = Flask(__name__)

# Get absolute path to the instance folder
instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
db_path = os.path.join(instance_path, 'osint.db')

# Make sure instance directory exists
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

# Configure SQLAlchemy database with absolute path
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
db.init_app(app)

# Create database tables (if they don't exist) and apply migrations
with app.app_context():
    db.create_all()
    apply_migrations(app)  # Apply any pending migrations

# Initialize General Knowledge Completer
completer = GK_Completer()


# Wrapper function to ensure the application context is available
def run_with_app_context(func):
    def wrapper():
        with app.app_context():
            func()

    return wrapper


# Initialize the scheduler
scheduler = BackgroundScheduler()

# Schedule periodic checks with app context
# scheduler.add_job(
#     func=run_with_app_context(completer.check_all_queries_per_source),
#     trigger="interval",
#     seconds=80,
#     # next_run_time=datetime.now(),
#     misfire_grace_time=27,
# )

# scheduler.add_job(
#     func=run_with_app_context(automatic_search),
#     trigger="interval",
#     seconds=241,
#     # next_run_time=datetime.now(),
#     misfire_grace_time=81,
# )

# scheduler.add_job(
#     func=run_with_app_context(update_missing_values),
#     trigger="interval",
#     seconds=483,
#     # next_run_time=datetime.now(),
#     misfire_grace_time=163,
# )

# Start the scheduler
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

# Register routes
init_routes(app)

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
