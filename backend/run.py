#!/usr/bin/env python3
"""
Application entry point for the Automated Reporting and Insight Generation Tool
Team: W10A_DONUT
"""

import os
import sys
from app import create_app

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Main application entry point"""
    # Get configuration from environment
    config_name = os.environ.get('FLASK_ENV', 'development')
    
    # Create Flask application
    app = create_app(config_name)
    
    # Get host and port from environment variables
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5050))
    debug = config_name == 'development'
    
    print(f"Starting Reporting Service...")
    print(f"Environment: {config_name}")
    print(f"Running on: http://{host}:{port}")
    print(f"Debug mode: {debug}")
    
    # Run the Flask development server
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True,
        use_reloader = False
    )


if __name__ == '__main__':
    main()