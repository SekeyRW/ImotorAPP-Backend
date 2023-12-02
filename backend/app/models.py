import uuid
from datetime import datetime
from . import db


class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    created_by = db.Column(db.String(255))
    created_date = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_by = db.Column(db.String(255))
    updated_date = db.Column(db.DateTime(timezone=True))


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    contact_number = db.Column(db.String(255))
    whats_app_number = db.Column(db.String(255))
    viber_number = db.Column(db.String(255))
    profile_picture = db.Column(db.Text)
    status = db.Column(db.Integer, default=1)
    verified = db.Column(db.Integer, default=0)
    verification_code = db.Column(db.String(255))
    listings = db.relationship("Listings", backref="user", lazy='select', cascade="all, delete")
    reset_token = db.Column(db.Text)
    reset_token_timestamp = db.Column(db.DateTime(timezone=True))
    refresh_token = db.relationship('RefreshToken', backref='user', lazy='select', cascade='all, delete')
    created_by = db.Column(db.String(255))
    created_date = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_by = db.Column(db.String(255))
    updated_date = db.Column(db.DateTime(timezone=True))


class RefreshToken(db.Model):
    __tablename__ = 'refresh_tokens'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(512), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

class Brand(db.Model):
    __tablename__ = 'brand'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    type = db.Column(db.String(255))
    image = db.Column(db.Text)
    listings = db.relationship("Listings", backref="brand", lazy='select', cascade="all, delete")
    created_by = db.Column(db.String(255))
    created_date = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_by = db.Column(db.String(255))
    updated_date = db.Column(db.DateTime(timezone=True))


class Location(db.Model):
    __tablename__ = 'location'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    image = db.Column(db.Text)
    listings = db.relationship("Listings", backref="location", lazy='select', cascade="all, delete")
    community = db.relationship("Community", backref="location", lazy='select', cascade="all, delete")
    created_by = db.Column(db.String(255))
    created_date = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_by = db.Column(db.String(255))
    updated_date = db.Column(db.DateTime(timezone=True))


class Community(db.Model):
    __tablename__ = 'community'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    image = db.Column(db.Text)
    location_id = db.Column(db.Integer, db.ForeignKey("location.id", ondelete='CASCADE'), nullable=False)
    listings = db.relationship("Listings", backref="community", lazy='select', cascade="all, delete")
    created_by = db.Column(db.String(255))
    created_date = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_by = db.Column(db.String(255))
    updated_date = db.Column(db.DateTime(timezone=True))


class Listings(db.Model):
    __tablename__ = 'listings'
    id = db.Column(db.Integer, primary_key=True)
    vin = db.Column(db.String(255), unique=True)
    title = db.Column(db.String(255))
    slug = db.Column(db.Text)
    price = db.Column(db.String(255))
    description = db.Column(db.Text)
    model = db.Column(db.String(255))
    model_year = db.Column(db.String(255))
    variant = db.Column(db.String(255))
    mileage = db.Column(db.String(255))
    vehicle_type = db.Column(db.String(255))
    featured_as = db.Column(db.String(255))
    g_map_location = db.Column(db.Text)
    featured_image = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete='CASCADE'), nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey("brand.id", ondelete='CASCADE'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey("location.id", ondelete='CASCADE'), nullable=False)
    community_id = db.Column(db.Integer, db.ForeignKey("community.id", ondelete='CASCADE'), nullable=False)
    listing_amenities = db.relationship("ListingAmenities", backref="listing", lazy='select', cascade="all, delete")
    safety_features = db.relationship("SafetyFeatures", backref="listing", lazy='select', cascade="all, delete")
    listing_image = db.relationship("ListingImage", backref="listing", lazy='select', cascade="all, delete")
    cars = db.relationship("Cars", uselist=False,backref="listing", lazy='select', cascade="all, delete")
    motorcycle = db.relationship("Motorcycle", backref="listing", lazy='select', cascade="all, delete")
    boats = db.relationship("Boats", backref="listing", lazy='select', cascade="all, delete")
    heavy_vehicles = db.relationship("HeavyVehicles", backref="listing", lazy='select', cascade="all, delete")
    created_by = db.Column(db.String(255))
    created_date = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_by = db.Column(db.String(255))
    updated_date = db.Column(db.DateTime(timezone=True))


class Cars(db.Model):
    __tablename__ = 'cars'
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("listings.id", ondelete='CASCADE'), nullable=False)
    fuel_type = db.Column(db.String(255))
    exterior_color = db.Column(db.String(255))
    interior_color = db.Column(db.String(255))
    warranty = db.Column(db.String(255))
    doors = db.Column(db.String(255))
    no_of_cylinders = db.Column(db.String(255))
    transmission_type = db.Column(db.String(255))
    body_type = db.Column(db.String(255))
    seating_capacity = db.Column(db.String(255))
    horse_power = db.Column(db.String(255))
    engine_capacity = db.Column(db.String(255))
    steering_hand = db.Column(db.String(255))
    trim = db.Column(db.String(255))
    insured_uae = db.Column(db.String(255))
    regional_spec = db.Column(db.String(255))
    created_by = db.Column(db.String(255))
    created_date = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_by = db.Column(db.String(255))
    updated_date = db.Column(db.DateTime(timezone=True))


class Motorcycle(db.Model):
    __tablename__ = 'motorcycle'
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("listings.id", ondelete='CASCADE'), nullable=False)
    type = db.Column(db.String(255))
    usage = db.Column(db.String(255))
    warranty = db.Column(db.String(255))
    wheels = db.Column(db.String(255))
    seller_type = db.Column(db.String(255))
    final_drive_system = db.Column(db.String(255))
    engine_size = db.Column(db.String(255))
    created_by = db.Column(db.String(255))
    created_date = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_by = db.Column(db.String(255))
    updated_date = db.Column(db.DateTime(timezone=True))


class Boats(db.Model):
    __tablename__ = 'boats'
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("listings.id", ondelete='CASCADE'), nullable=False)
    type_1 = db.Column(db.String(255))
    type_2 = db.Column(db.String(255))
    usage = db.Column(db.String(255))
    warranty = db.Column(db.String(255))
    age = db.Column(db.String(255))
    seller_type = db.Column(db.String(255))
    length = db.Column(db.String(255))
    condition = db.Column(db.String(255))
    created_by = db.Column(db.String(255))
    created_date = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_by = db.Column(db.String(255))
    updated_date = db.Column(db.DateTime(timezone=True))

class HeavyVehicles(db.Model):
    __tablename__ = 'heavy_vehicles'
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("listings.id", ondelete='CASCADE'), nullable=False)
    type_1 = db.Column(db.String(255))
    type_2 = db.Column(db.String(255))
    fuel_type = db.Column(db.String(255))
    no_of_cylinders = db.Column(db.String(255))
    body_condition = db.Column(db.String(255))
    mechanical_condition = db.Column(db.String(255))
    capacity_weight = db.Column(db.String(255))
    horse_condition = db.Column(db.String(255))
    created_by = db.Column(db.String(255))
    created_date = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_by = db.Column(db.String(255))
    updated_date = db.Column(db.DateTime(timezone=True))

class ListingAmenities(db.Model):
    __tablename__ = 'listing_amenities'
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("listings.id", ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(255))
    created_by = db.Column(db.String(255))
    created_date = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_by = db.Column(db.String(255))
    updated_date = db.Column(db.DateTime(timezone=True))


class SafetyFeatures(db.Model):
    __tablename__ = 'safety_features'
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("listings.id", ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(255))
    created_by = db.Column(db.String(255))
    created_date = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_by = db.Column(db.String(255))
    updated_date = db.Column(db.DateTime(timezone=True))


class ListingImage(db.Model):
    __tablename__ = 'listing_image'
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("listings.id", ondelete='CASCADE'), nullable=False)
    image = db.Column(db.Text)
    created_by = db.Column(db.String(255))
    created_date = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_by = db.Column(db.String(255))
    updated_date = db.Column(db.DateTime(timezone=True))
