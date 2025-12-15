from datetime import datetime, date
from app import db
from app.models.base import Base

class Plant(Base):
    """Plant database model for Texas native plants"""
    __tablename__ = 'plants'

    # Core identification
    id = db.Column(db.Integer, primary_key=True)
    common_name = db.Column(db.String(100), nullable=False, index=True)
    scientific_name = db.Column(db.String(150), index=True)

    # Classification & characteristics
    plant_type = db.Column(db.String(50))
    native_region = db.Column(db.String(100))
    height_range = db.Column(db.String(50))
    spread_range = db.Column(db.String(50))

    # Growing conditions
    sun_exposure = db.Column(db.String(50))
    water_needs = db.Column(db.String(50))
    soil_type = db.Column(db.String(100))

    # Care & features
    bloom_season = db.Column(db.String(100))
    bloom_color = db.Column(db.String(100))
    wildlife_value = db.Column(db.String(200))
    drought_tolerant = db.Column(db.Boolean, default=False)
    deer_resistant = db.Column(db.Boolean, default=False)

    # Information & resources
    care_instructions = db.Column(db.Text)
    notes = db.Column(db.Text)
    image_url = db.Column(db.String(255))

    # Tracking (for "My Yard" feature)
    in_my_yard = db.Column(db.Boolean, default=False)
    date_planted = db.Column(db.Date, nullable=True)
    location_in_yard = db.Column(db.String(100))

    def __repr__(self):
        return f'<Plant {self.common_name}>'


class PlantResource(Base):
    """Plant resources - websites, guides, nurseries"""
    __tablename__ = 'plant_resources'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    resource_type = db.Column(db.String(50))
    is_favorite = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<PlantResource {self.title}>'


class CareLog(Base):
    """Care log for tracking plant maintenance"""
    __tablename__ = 'care_logs'

    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plants.id'), nullable=False)
    log_date = db.Column(db.Date, nullable=False, default=date.today)
    activity_type = db.Column(db.String(50))
    notes = db.Column(db.Text)

    plant = db.relationship('Plant', backref=db.backref('care_logs', lazy=True))

    def __repr__(self):
        return f'<CareLog {self.activity_type} on {self.log_date}>'
