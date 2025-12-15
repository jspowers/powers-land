from flask import Blueprint

landscaping_bp = Blueprint('landscaping', __name__, template_folder='templates')

from app.blueprints.landscaping import routes
