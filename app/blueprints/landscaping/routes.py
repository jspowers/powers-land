from flask import render_template
from app.blueprints.landscaping import landscaping_bp

@landscaping_bp.route('/')
def index():
    """Landscaping showcase homepage"""
    return render_template('landscaping/index.html')

@landscaping_bp.route('/resources')
def resources():
    """Favorite plant resources"""
    return render_template('landscaping/resources.html')

# Future routes (ready to activate):
# @landscaping_bp.route('/plants')
# def plants():
#     """Interactive plant database with filtering"""
#     from app.blueprints.landscaping.models import Plant
#     plants = Plant.query.all()
#     return render_template('landscaping/plants.html', plants=plants)

# @landscaping_bp.route('/plants/<int:plant_id>')
# def plant_detail(plant_id):
#     """Individual plant detail page"""
#     from app.blueprints.landscaping.models import Plant
#     plant = Plant.query.get_or_404(plant_id)
#     return render_template('landscaping/plant_detail.html', plant=plant)
