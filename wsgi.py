import os
from dotenv import load_dotenv
from app import create_app

# Load .env file (fallback if systemd EnvironmentFile fails)
load_dotenv()

# Determine environment from FLASK_ENV or default to production
config_name = os.environ.get('FLASK_ENV', 'production')
application = create_app(config_name)

if __name__ == '__main__':
    application.run()
