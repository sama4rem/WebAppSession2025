# -*- coding: utf-8 -*-
from app import create_app
import os
from dotenv import load_dotenv

# Load environment variables from .env file for local development
# This must be done BEFORE the app instance is created.
load_dotenv()

# Create the Flask application instance
app = create_app()

if __name__ == '__main__':
    # Get the port from the environment variable (e.g., set by Cloud Run)
    # The default port is 8080, which is the standard for Cloud Run.
    port = int(os.environ.get("PORT", 8080))
    
    # Run the application on 0.0.0.0 to accept external requests
    app.run(host="0.0.0.0", port=port, debug=True)