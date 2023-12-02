from marshmallow import fields
from . import ma
from .models import User, Admin, Brand, Listings, Cars, ListingAmenities, SafetyFeatures, ListingImage, Location, \
    Community, Motorcycle


class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True


class AdminSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Admin
        load_instance = True


class BrandSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Brand
        load_instance = True


class LocationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Location
        load_instance = True

class CommunitySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Community
        load_instance = True

class ListingsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Listings
        load_instance = True

    cars = fields.Nested('CarsSchema')
    safety_features = fields.Nested('SafetyFeaturesSchema', many=True)
    listing_amenities = fields.Nested('ListingAmenitiesSchema', many=True)
    listing_image = fields.Nested('ListingImageSchema', many=True)

class CarsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Cars
        load_instance = True

class MotorcycleSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Motorcycle
        load_instance = True

class ListingAmenitiesSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ListingAmenities
        load_instance = True

class SafetyFeaturesSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = SafetyFeatures
        load_instance = True


class ListingImageSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ListingImage
        load_instance = True
