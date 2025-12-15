import os
from app import create_app

# Determine environment from FLASK_ENV or default to production
config_name = os.environ.get('FLASK_ENV', 'development')
application = create_app(config_name)

if __name__ == '__main__':
    application.run()  # or any other port number
