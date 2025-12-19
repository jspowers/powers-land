from flask import Blueprint

soty_bp = Blueprint('soty', __name__, template_folder='templates')

from app.blueprints.soty import routes
