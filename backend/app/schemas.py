from marshmallow import fields
from . import ma
from .models import User, Admin, Brand, Listings, Cars, ListingAmenities, SafetyFeatures, ListingImage, Location, \
    Community, Motorcycle, Boats, HeavyVehicles, Favorites, Make, Trim


class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True

    verified_name = fields.String(attribute='verified_name')
    standard_listings_count = fields.Method("get_standard_listings_count")
    featured_listings_count = fields.Method("get_featured_listings_count")
    premium_listings_count = fields.Method("get_premium_listings_count")

    def get_standard_listings_count(self, obj):
        return obj.count_standard_listings

    def get_featured_listings_count(self, obj):
        return obj.count_featured_listings

    def get_premium_listings_count(self, obj):
        return obj.count_premium_listings

class AdminSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Admin
        load_instance = True


class BrandSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Brand
        load_instance = True

class MakeSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Make
        load_instance = True

class TrimSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Trim
        load_instance = True

class FavoritesSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Favorites
        load_instance = True

    listing = fields.Nested('ListingsSchema')

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
    motorcycle = fields.Nested('MotorcycleSchema')
    boats = fields.Nested('BoatsSchema')
    heavy_vehicles = fields.Nested('HeavyVehiclesSchema')
    safety_features = fields.Nested('SafetyFeaturesSchema', many=True)
    listing_amenities = fields.Nested('ListingAmenitiesSchema', many=True)
    listing_image = fields.Nested('ListingImageSchema', many=True)
    user = fields.Nested('UserSchema')
    brand = fields.Nested('BrandSchema')
    location = fields.Nested('LocationSchema')
    community = fields.Nested('CommunitySchema')
    publish_status_name = fields.String(attribute='publish_status_name')

class CarsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Cars
        load_instance = True

class MotorcycleSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Motorcycle
        load_instance = True
class BoatsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Boats
        load_instance = True


class HeavyVehiclesSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = HeavyVehicles
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
