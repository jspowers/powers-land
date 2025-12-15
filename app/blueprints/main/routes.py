from flask import render_template
from app.blueprints.main import main_bp

@main_bp.route('/')
def index():
    """Homepage with bio, hobbies, and background"""
    return render_template('main/index.html')

@main_bp.route('/about')
def about():
    """Extended bio and background page"""
    return render_template('main/about.html')
