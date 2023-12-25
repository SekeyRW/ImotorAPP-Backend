import io
import os
import uuid
from datetime import datetime

from PIL import Image
from flask import Blueprint, jsonify, request, send_from_directory, current_app, g
from flask_jwt_extended import jwt_required
from slugify import slugify
from sqlalchemy import or_, and_
from werkzeug.utils import secure_filename

from . import db, bcrypt, allowed_file
from .decorators import current_user_required
from .models import Admin, Brand, Location, Community, Cars, Listings, ListingImage, SafetyFeatures, ListingAmenities, \
    User, Motorcycle, Boats, HeavyVehicles
from .schemas import BrandSchema, CommunitySchema, ListingsSchema, CarsSchema, UserSchema, ListingImageSchema

views = Blueprint('views', __name__)

# SCHEMAS
brand_schema = BrandSchema()
brands_schema = BrandSchema(many=True)

user_schema = UserSchema()
users_schema = UserSchema(many=True)

location_schema = BrandSchema()
locations_schema = BrandSchema(many=True)

community_schema = CommunitySchema()
communities_schema = CommunitySchema(many=True)

listing_schema = ListingsSchema()
listings_schema = ListingsSchema(many=True)

listing_image_schema = ListingImageSchema()
listing_images_schema = ListingImageSchema(many=True)

car_schema = CarsSchema()
cars_schema = CarsSchema(many=True)


####################################################################### ADMIN API ######################################
# Admin Credentials Initializer
@views.route('/admin/initializer', methods=['GET'])
def initializer():
    data = Admin.query.first()
    if not data:
        password = 'Imotor@37'
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        new_admin = Admin(email='imotorapp37@gmail.com', password=password_hash, first_name='Symon', last_name='Sitier')
        db.session.add(new_admin)
        db.session.commit()

    return jsonify(200)


# Serve Images to Frontend
@views.route('/uploaded_img/<path:filename>', methods=['GET'])
def serve_uploaded_image(filename):
    return send_from_directory(directory=current_app.config['UPLOAD_FOLDER'], path=filename)


# Image Resizer
def resize_image(image, max_size_kb):
    max_size_bytes = max_size_kb * 1024  # Convert KB to bytes

    # Open the image using PIL
    img = Image.open(image)

    # Convert the image to RGB mode if it's in RGBA mode (has an alpha channel)
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        img = img.convert('RGB')

    # Calculate current image size in bytes
    img_byte_array = io.BytesIO()
    img.save(img_byte_array, format='JPEG')  # Change format as required
    img_size = img_byte_array.tell()

    # Resize the image while keeping the aspect ratio
    if img_size > max_size_bytes:
        # Calculate the resize ratio to fit within the size limit
        resize_ratio = (max_size_bytes / img_size) ** 0.5  # square root to maintain aspect ratio

        # Calculate new dimensions
        new_width = int(img.width * resize_ratio)
        new_height = int(img.height * resize_ratio)

        # Resize the image
        img = img.resize((new_width, new_height))

    return img


############# Settings ################
# Brands View
@views.route('/admin/brand-view', methods=['GET'])
@jwt_required()
@current_user_required
def brands_view():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    search = request.args.get('search', '', type=str)

    data = Brand.query

    if search:
        search_words = search.split(',')

        def search_filter(word):
            word = word.strip()
            return or_(
                Brand.name.ilike(f"%{word}%"),
            )

        filter_conditions = [search_filter(word) for word in search_words]
        data = data.filter(*filter_conditions)

    data = data.order_by(Brand.id.desc())

    data_paginated = data.limit(page_size).offset((page - 1) * page_size).all()

    result = brands_schema.dump(data_paginated)

    return jsonify({
        "data": result,
        "total": data.count()
    }), 200


# Brands Create
@views.route('/admin/brand-create', methods=['POST'])
@jwt_required()
@current_user_required
def brand_create():
    new_data = request.form

    existing_data = Brand.query.filter_by(name=new_data['name'].lower(), type=new_data['type'].lower()).first()

    if existing_data is not None:
        return jsonify({'message': 'Brand Already Exists!'}), 400

    file_name = None
    file = request.files.get('image')

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_name = str(uuid.uuid1()) + '_' + filename
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], file_name))

    new_data2 = Brand(
        name=new_data['name'],
        type=new_data['type'],
        image=file_name,
        created_by=g.current_user['email']
    )
    db.session.add(new_data2)
    db.session.commit()

    new_added_data = brand_schema.dump(new_data2)
    return jsonify({'message': 'Brand successfully added!', 'new_data': new_added_data}), 200

# Brands Update
@views.route('/admin/brand-update/<int:id>', methods=['PUT'])
@jwt_required()
@current_user_required
def brand_update(id):
    new_data = request.form
    data = Brand.query.get(id)
    if data:
        if request.files.get('image'):
            file = request.files.get('image')
            file_name = None
            if data.image:
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], data.image)
                if os.path.exists(image_path):
                    os.remove(image_path)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_name = str(uuid.uuid1()) + '_' + filename
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], file_name))
            data.name = new_data['name']
            data.type = new_data['type']
            data.image = file_name
            data.updated_by = g.current_user['email']
            data.updated_date = datetime.now()
            db.session.commit()
        else:
            data.name = new_data['name']
            data.type = new_data['type']
            data.updated_by = g.current_user['email']
            data.updated_date = datetime.now()
            db.session.commit()
    else:
        return jsonify({'message': 'Brand not found!'}), 400

    updated_data = brand_schema.dump(data)
    return jsonify({'message': 'Brand updated successfully!', 'updated_data': updated_data}), 200

# Brands Delete
@views.route('/admin/brand-delete/<int:id>', methods=['DELETE'])
@jwt_required()
@current_user_required
def brand_delete(id):
    data = Brand.query.get(id)
    if data is None:
        return jsonify({'message': 'Brand not found.'}), 400
    image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], data.image)
    if os.path.exists(image_path):
        os.remove(image_path)

    db.session.delete(data)
    db.session.commit()
    return 'Success!', 200

# Locations View
@views.route('/admin/location-view', methods=['GET'])
@jwt_required()
@current_user_required
def location_view():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    search = request.args.get('search', '', type=str)

    data = Location.query

    if search:
        search_words = search.split(',')

        def search_filter(word):
            word = word.strip()
            return or_(
                Location.name.ilike(f"%{word}%"),
            )

        filter_conditions = [search_filter(word) for word in search_words]
        data = data.filter(*filter_conditions)

    data = data.order_by(Location.id.desc())

    data_paginated = data.limit(page_size).offset((page - 1) * page_size).all()

    result = locations_schema.dump(data_paginated)

    return jsonify({
        "data": result,
        "total": data.count()
    }), 200


# Location Create
@views.route('/admin/location-create', methods=['POST'])
@jwt_required()
@current_user_required
def location_create():
    new_data = request.form

    existing_data = Location.query.filter_by(name=new_data['name'].lower()).first()

    if existing_data is not None:
        return jsonify({'message': 'Location Already Exists!'}), 400

    file_name = None
    file = request.files.get('image')

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_name = str(uuid.uuid1()) + '_' + filename
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], file_name))

    new_data2 = Location(
        name=new_data['name'],
        image=file_name,
        created_by=g.current_user['email']
    )
    db.session.add(new_data2)
    db.session.commit()

    new_added_data = location_schema.dump(new_data2)
    return jsonify({'message': 'Location successfully added!', 'new_data': new_added_data}), 200

# Location Update
@views.route('/admin/location-update/<int:id>', methods=['PUT'])
@jwt_required()
@current_user_required
def location_update(id):
    new_data = request.form
    data = Location.query.get(id)
    if data:
        if request.files.get('image'):
            file = request.files.get('image')
            file_name = None
            if data.image:
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], data.image)
                if os.path.exists(image_path):
                    os.remove(image_path)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_name = str(uuid.uuid1()) + '_' + filename
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], file_name))
            data.name = new_data['name']
            data.image = file_name
            data.updated_by = g.current_user['email']
            data.updated_date = datetime.now()
            db.session.commit()
        else:
            data.name = new_data['name']
            data.updated_by = g.current_user['email']
            data.updated_date = datetime.now()
            db.session.commit()
    else:
        return jsonify({'message': 'Location not found!'}), 400

    updated_data = brand_schema.dump(data)
    return jsonify({'message': 'Location updated successfully!', 'updated_data': updated_data}), 200

# Location Delete
@views.route('/admin/location-delete/<int:id>', methods=['DELETE'])
@jwt_required()
@current_user_required
def location_delete(id):
    data = Location.query.get(id)
    if data is None:
        return jsonify({'message': 'Location not found.'}), 400
    image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], data.image)
    if os.path.exists(image_path):
        os.remove(image_path)

    db.session.delete(data)
    db.session.commit()
    return 'Success!', 200


# Community View
@views.route('/admin/community-view/<int:id>', methods=['GET'])
@jwt_required()
@current_user_required
def community_view(id):
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    search = request.args.get('search', '', type=str)

    data = Community.query.filter_by(location_id=id)

    if search:
        search_words = search.split(',')

        def search_filter(word):
            word = word.strip()
            return or_(
                Community.name.ilike(f"%{word}%"),
            )

        filter_conditions = [search_filter(word) for word in search_words]
        data = data.filter(*filter_conditions)

    data = data.order_by(Community.id.desc())

    data_paginated = data.limit(page_size).offset((page - 1) * page_size).all()

    result = communities_schema.dump(data_paginated)

    return jsonify({
        "data": result,
        "total": data.count()
    }), 200


# Community Create
@views.route('/admin/community-create/<int:id>', methods=['POST'])
@jwt_required()
@current_user_required
def community_create(id):
    new_data = request.form

    existing_data = Community.query.filter_by(name=new_data['name'].lower(), location_id=id).first()

    if existing_data is not None:
        return jsonify({'message': 'Community Already Exists!'}), 400

    file = request.files.get('image')

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_name = str(uuid.uuid1()) + '_' + filename
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], file_name))

        new_data2 = Community(
            name=new_data['name'],
            location_id=id,
            created_by=g.current_user['email'],
            image=file_name
        )
    else:
        new_data2 = Community(
            name=new_data['name'],
            location_id=id,
            created_by=g.current_user['email']
        )

    db.session.add(new_data2)
    db.session.commit()

    new_added_data = community_schema.dump(new_data2)
    return jsonify({'message': 'Community successfully added!', 'new_data': new_added_data}), 200

# Community Update
@views.route('/admin/community-update/<int:id>', methods=['PUT'])
@jwt_required()
@current_user_required
def community_update(id):
    new_data = request.form
    data = Community.query.get(id)
    if data:
        if request.files.get('image'):
            file = request.files.get('image')
            file_name = None
            if data.image:
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], data.image)
                if os.path.exists(image_path):
                    os.remove(image_path)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_name = str(uuid.uuid1()) + '_' + filename
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], file_name))
            data.name = new_data['name']
            data.image = file_name
            data.updated_by = g.current_user['email']
            data.updated_date = datetime.now()
            db.session.commit()
        else:
            data.name = new_data['name']
            data.updated_by = g.current_user['email']
            data.updated_date = datetime.now()
            db.session.commit()
    else:
        return jsonify({'message': 'Community not found!'}), 400

    updated_data = brand_schema.dump(data)
    return jsonify({'message': 'Community updated successfully!', 'updated_data': updated_data}), 200

# Location Delete
@views.route('/admin/community-delete/<int:id>', methods=['DELETE'])
@jwt_required()
@current_user_required
def community_delete(id):
    data = Community.query.get(id)
    if data is None:
        return jsonify({'message': 'Community not found.'}), 400
    image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], data.image)
    if os.path.exists(image_path):
        os.remove(image_path)

    db.session.delete(data)
    db.session.commit()
    return 'Success!', 200


############## END OF SETTINGS ##################################

################ LISTINGS ########################################
# CAR LISTING INFORMATION
@views.route('/admin/car-listing-view', methods=['GET'])
@jwt_required()
@current_user_required
def car_listing_view():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    search = request.args.get('search', '', type=str)

    data = Listings.query.filter_by(vehicle_type='car')

    if search:
        search_words = search.split(',')

        def search_filter(word):
            word = word.strip()
            return or_(
                Listings.title.ilike(f"%{word}%"),
            )

        filter_conditions = [search_filter(word) for word in search_words]
        data = data.filter(*filter_conditions)

    data = data.order_by(Listings.id.desc())

    data_paginated = data.limit(page_size).offset((page - 1) * page_size).all()

    result = listings_schema.dump(data_paginated)

    return jsonify({
        "data": result,
        "total": data.count()
    }), 200

# Motorcycle LISTING INFORMATION
@views.route('/admin/motorcycle-listing-view', methods=['GET'])
@jwt_required()
@current_user_required
def motorcycle_listing_view():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    search = request.args.get('search', '', type=str)

    data = Listings.query.filter_by(vehicle_type='motorcycle')

    if search:
        search_words = search.split(',')

        def search_filter(word):
            word = word.strip()
            return or_(
                Listings.title.ilike(f"%{word}%"),
            )

        filter_conditions = [search_filter(word) for word in search_words]
        data = data.filter(*filter_conditions)

    data = data.order_by(Listings.id.desc())

    data_paginated = data.limit(page_size).offset((page - 1) * page_size).all()

    result = listings_schema.dump(data_paginated)

    return jsonify({
        "data": result,
        "total": data.count()
    }), 200

# boat LISTING INFORMATION
@views.route('/admin/boat-listing-view', methods=['GET'])
@jwt_required()
@current_user_required
def boat_listing_view():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    search = request.args.get('search', '', type=str)

    data = Listings.query.filter_by(vehicle_type='boat')

    if search:
        search_words = search.split(',')

        def search_filter(word):
            word = word.strip()
            return or_(
                Listings.title.ilike(f"%{word}%"),
            )

        filter_conditions = [search_filter(word) for word in search_words]
        data = data.filter(*filter_conditions)

    data = data.order_by(Listings.id.desc())

    data_paginated = data.limit(page_size).offset((page - 1) * page_size).all()

    result = listings_schema.dump(data_paginated)

    return jsonify({
        "data": result,
        "total": data.count()
    }), 200

# CAR LISTING INFORMATION
@views.route('/admin/heavy-vehicle-listing-view', methods=['GET'])
@jwt_required()
@current_user_required
def heavy_vehicle_listing_view():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    search = request.args.get('search', '', type=str)

    data = Listings.query.filter_by(vehicle_type='heavy vehicle')

    if search:
        search_words = search.split(',')

        def search_filter(word):
            word = word.strip()
            return or_(
                Listings.title.ilike(f"%{word}%"),
            )

        filter_conditions = [search_filter(word) for word in search_words]
        data = data.filter(*filter_conditions)

    data = data.order_by(Listings.id.desc())

    data_paginated = data.limit(page_size).offset((page - 1) * page_size).all()

    result = listings_schema.dump(data_paginated)

    return jsonify({
        "data": result,
        "total": data.count()
    }), 200


############### END OF LISTINGS ##################################
# USER INFORMATION
@views.route('/admin/users-view', methods=['GET'])
@jwt_required()
@current_user_required
def users_view():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    search = request.args.get('search', '', type=str)

    data = User.query

    if search:
        search_words = search.split(',')

        def search_filter(word):
            word = word.strip()
            return or_(
                User.email.ilike(f"%{word}%"),
            )

        filter_conditions = [search_filter(word) for word in search_words]
        data = data.filter(*filter_conditions)

    data = data.order_by(User.id.desc())

    data_paginated = data.limit(page_size).offset((page - 1) * page_size).all()

    result = users_schema.dump(data_paginated)

    return jsonify({
        "data": result,
        "total": data.count()
    }), 200



############################################################## CLIENT SIDE #############################################

###################### SEARCH ALL LISTING ENDPOINT ####################
@views.route('/client/all-listing-search', methods=['GET'])
def all_listing_search():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    search = request.args.get('search', '', type=str)

    data = Listings.query

    if search:
        filter_conditions = []

        if search:
            search_conditions = Listings.title.ilike(f"%{search}%")
            filter_conditions.append(search_conditions)

        data = data.filter(and_(*filter_conditions))

    data = data.order_by(Listings.id.desc())

    data_paginated = data.limit(page_size).offset((page - 1) * page_size).all()

    result = listings_schema.dump(data_paginated)

    return jsonify({
        "data": result,
        "total": data.count()
    }), 200

##################### END SEARCH ALL LISTING ENDPOINT #################

###################### CAR LISTING ENDPOINT ###########################
# All Car View
@views.route('/client/all-car-view', methods=['GET'])
def all_car_view():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    search = request.args.get('search', '', type=str)
    brand = request.args.get('brand', type=str)
    startPrice = request.args.get('startPrice', '', type=str)
    endPrice = request.args.get('endPrice', '', type=str)
    startModelYear = request.args.get('startModelYear', '', type=str)
    endModelYear = request.args.get('endModelYear', '', type=str)
    startMileage = request.args.get('startMileage', '', type=str)
    endMileage = request.args.get('endMileage', '', type=str)

    data = Listings.query.filter_by(vehicle_type='car')

    if search or brand or (startPrice and endPrice) or (startMileage and endMileage) or (startModelYear and endModelYear):
        filter_conditions = []

        if search:
            search_conditions = Listings.title.ilike(f"%{search}%")
            filter_conditions.append(search_conditions)
        if brand:
            brand = int(brand)
            brand_conditions = Listings.brand_id == brand
            filter_conditions.append(brand_conditions)
        if startPrice and endPrice:
            price_condition = Listings.price.between(startPrice, endPrice)
            filter_conditions.append(price_condition)
        if startMileage and endMileage:
            mileage_condition = Listings.mileage.between(startMileage, endMileage)
            filter_conditions.append(mileage_condition)
        if startModelYear and endModelYear:
            modelYear_condition = Listings.model_year.between(startModelYear, endModelYear)
            filter_conditions.append(modelYear_condition)

        data = data.filter(and_(*filter_conditions))

    data = data.order_by(Listings.id.desc())

    data_paginated = data.limit(page_size).offset((page - 1) * page_size).all()

    result = listings_schema.dump(data_paginated)

    return jsonify({
        "data": result,
        "total": data.count()
    }), 200


# User Car View
@views.route('/client/user-car-view/<int:id>', methods=['GET'])
def user_car_view(id):
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    search = request.args.get('search', '', type=str)

    data = Listings.query.filter_by(vehicle_type='car', user_id=id)


    user = User.query.get(id)
    if not user:
        return jsonify({
            "message": 'User not found',
        }), 400

    if search:
        search_words = search.split(',')

        def search_filter(word):
            word = word.strip()
            return or_(
                Listings.title.ilike(f"%{word}%"),
            )

        filter_conditions = [search_filter(word) for word in search_words]
        data = data.filter(*filter_conditions)

    data = data.order_by(Listings.id.desc())

    data_paginated = data.limit(page_size).offset((page - 1) * page_size).all()

    result = listings_schema.dump(data_paginated)

    return jsonify({
        "data": result,
        "total": data.count()
    }), 200


# Car Create
@views.route('/client/car-create', methods=['POST'])
@jwt_required()
@current_user_required
def car_create():
    new_data = request.form

    file_name = None
    file = request.files.get('featured_image')

    if file and allowed_file(file.filename):
        resize_file = resize_image(file, max_size_kb=1024)
        filename = secure_filename(file.filename)
        file_name = str(uuid.uuid1()) + '_' + filename
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file_name)
        resize_file.save(filepath, format='JPEG')

    title = f"{new_data['model']} {new_data['model_year']}"
    slug = slugify(title)

    listing_data = Listings(
        vin=new_data['vin'],
        title=title,
        slug=slug,
        price=new_data['price'],
        description=new_data['description'],
        model=new_data['model'],
        model_year=new_data['model_year'],
        variant=new_data['variant'],
        mileage=new_data['mileage'],
        vehicle_type='car',
        featured_as='standard',
        user_id=new_data['user_id'],
        brand_id=new_data['brand_id'],
        location_id=new_data['location_id'],
        community_id=new_data['community_id'],
        featured_image=file_name,
        created_by=g.current_user['email']
    )
    db.session.add(listing_data)
    db.session.commit()

    images = request.files.getlist('images')
    for image in images:
        if image and allowed_file(image.filename):
            resized_img = resize_image(image, max_size_kb=1024)
            filename = str(uuid.uuid1()) + '_' + secure_filename(image.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            resized_img.save(filepath, format='JPEG')

            images_data = ListingImage(image=filename, listing_id=listing_data.id, created_by=g.current_user['email'])
            db.session.add(images_data)
            db.session.commit()

    safety_features = new_data['safety_features'].split(',')
    for features in safety_features:
        features_data = SafetyFeatures(name=features, listing_id=listing_data.id)
        db.session.add(features_data)
        db.session.commit()

    amenities = new_data['amenities'].split(',')
    for amenity in amenities:
        amenity_data = ListingAmenities(name=amenity, listing_id=listing_data.id)
        db.session.add(amenity_data)
        db.session.commit()

    car_data = Cars(
        listing_id=listing_data.id,
        fuel_type=new_data['fuel_type'],
        exterior_color=new_data['exterior_color'],
        interior_color=new_data['interior_color'],
        warranty=new_data['warranty'],
        doors=new_data['doors'],
        no_of_cylinders=new_data['no_of_cylinders'],
        transmission_type=new_data['transmission_type'],
        body_type=new_data['body_type'],
        seating_capacity=new_data['seating_capacity'],
        horse_power=new_data['horse_power'],
        engine_capacity=new_data['engine_capacity'],
        steering_hand=new_data['steering_hand'],
        trim=new_data['trim'],
        insured_uae=new_data['insured_uae'],
        regional_spec=new_data['regional_spec'],
        created_by=g.current_user['email']
    )
    db.session.add(car_data)
    db.session.commit()

    new_added_data = listing_schema.dump(listing_data)
    return jsonify({'message': 'Car successfully listed!', 'new_data': new_added_data}), 200


# Single Car View
@views.route('/client/single-car-view/<int:id>', methods=['GET'])
def single_car_view(id):
    data = Listings.query.filter_by(id=id, vehicle_type='car').first()
    if data is None:
        return jsonify({'message': 'Car not found.'}), 400
    result = listing_schema.dump(data)

    return jsonify({
        "data": result,
    }), 200


# Single Car Update Information
@views.route('/client/single-car-view/update-information/<int:id>', methods=['PUT'])
@jwt_required()
@current_user_required
def update_car(id):
    new_data = request.get_json()
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='car').first()
        if listing_data:
            title = f"{new_data['model']} {new_data['model_year']}"
            slug = slugify(title)
            listing_data.title = title
            listing_data.slug = slug
            listing_data.price = new_data['price']
            listing_data.description = new_data['description']
            listing_data.model = new_data['model']
            listing_data.model_year = new_data['model_year']
            listing_data.variant = new_data['variant']
            listing_data.mileage = new_data['mileage']
            listing_data.updated_by = g.current_user['email']
            listing_data.updated_date = datetime.now()
            db.session.commit()

            car_data = Cars.query.filter_by(listing_id=listing_data.id).first()
            car_data.fuel_type = new_data['fuel_type']
            car_data.exterior_color = new_data['exterior_color']
            car_data.interior_color = new_data['interior_color']
            car_data.warranty = new_data['warranty']
            car_data.doors = new_data['doors']
            car_data.no_of_cylinders = new_data['no_of_cylinders']
            car_data.transmission_type = new_data['transmission_type']
            car_data.body_type = new_data['body_type']
            car_data.seating_capacity = new_data['seating_capacity']
            car_data.horse_power = new_data['horse_power']
            car_data.engine_capacity = new_data['engine_capacity']
            car_data.steering_hand = new_data['steering_hand']
            car_data.trim = new_data['trim']
            car_data.insured_uae = new_data['insured_uae']
            car_data.regional_spec = new_data['regional_spec']
            car_data.updated_by = g.current_user['email']
            car_data.updated_date = datetime.now()
            db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    updated_data = listing_schema.dump(listing_data)
    return jsonify({'message': f'Listing updated successfully!', 'updated_data': updated_data}), 200


# Car update featured image
@views.route('/client/single-car-view/update-featured-image/<int:id>', methods=['PUT'])
@jwt_required()
@current_user_required
def update_car_featured_img(id):
    image = request.files.get('featured_image')
    if not image:
        return jsonify({'message': 'No image file provided'}), 400

    if not allowed_file(image.filename):
        return jsonify({'message': 'Invalid image file format'}), 400

    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='car').first()
        if listing_data:
            if listing_data.featured_image:
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], listing_data.featured_image)
                if os.path.exists(image_path):
                    os.remove(image_path)

            resized_img = resize_image(image, max_size_kb=1024)
            filename = str(uuid.uuid1()) + '_' + secure_filename(image.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            resized_img.save(filepath, format='JPEG')

            listing_data.featured_image = filename
            listing_data.updated_by = g.current_user['email']
            listing_data.updated_date = datetime.now()
            db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    updated_data = listing_schema.dump(listing_data)
    return jsonify({'message': f'Listing Featured Image updated successfully!', 'updated_data': updated_data}), 200


# Car Add Images
@views.route('/client/single-car-view/add-images/<int:id>', methods=['POST'])
@jwt_required()
@current_user_required
def car_add_images(id):
    images = request.files.getlist('images')
    if not images:
        return jsonify({'message': 'No image files provided'}), 400

    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()

    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='car').first()
        if listing_data:
            for image in images:
                if image and allowed_file(image.filename):
                    resized_img = resize_image(image, max_size_kb=1024)
                    filename = str(uuid.uuid1()) + '_' + secure_filename(image.filename)
                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    resized_img.save(filepath, format='JPEG')

                    new_data = ListingImage(image=filename, listing_id=listing_data.id,
                                            created_by=g.current_user['email'])
                    db.session.add(new_data)
                    db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    updated_data = listing_schema.dump(listing_data)
    return jsonify({'message': f'Images successfully added!', 'updated_data': updated_data}), 200


# Delete Car Images
@views.route('/client/single-car-view/delete-images/<int:id>', methods=['DELETE'])
@jwt_required()
@current_user_required
def delete_car_images(id):
    image_ids = request.get_json().get('image_ids')
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='car').first()
        if listing_data:
            for image_id in image_ids:
                image = ListingImage.query.get(image_id)
                if image:
                    image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image.image)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                db.session.delete(image)
                db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    return 'Success!', 200


# Car Add Safety Features
@views.route('/client/single-car-view/add-safety-features/<int:id>', methods=['POST'])
@jwt_required()
@current_user_required
def car_add_safety_features(id):
    features = request.get_json().get('features')
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='car').first()
        if listing_data:
            for feature in features:
                existing_feature = SafetyFeatures.query.filter_by(name=feature.lower(), listing_id=id).first()
                if existing_feature:
                    pass
                else:
                    new_data = SafetyFeatures(name=feature, listing_id=listing_data.id,
                                              created_by=g.current_user['email'])
                    db.session.add(new_data)
                    db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    updated_data = listing_schema.dump(listing_data)
    return jsonify({'message': f'Safety Features added successfully!', 'updated_data': updated_data}), 200


# Delete Car Safety Features
@views.route('/client/single-car-view/delete-safety-features/<int:id>', methods=['DELETE'])
@jwt_required()
@current_user_required
def delete_car_safety_features(id):
    feature_ids = request.get_json().get('feature_ids')
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='car').first()
        if listing_data:
            for feature_id in feature_ids:
                feature = SafetyFeatures.query.get(feature_id)
                db.session.delete(feature)
                db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    return 'Success!', 200


# Car Add Amenities
@views.route('/client/single-car-view/add-amenities/<int:id>', methods=['POST'])
@jwt_required()
@current_user_required
def car_add_amenities(id):
    amenities = request.get_json().get('amenities')
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='car').first()
        if listing_data:
            for amenity in amenities:
                existing_data = ListingAmenities.query.filter_by(name=amenity.lower(), listing_id=id).first()
                if existing_data:
                    pass
                else:
                    new_data = ListingAmenities(name=amenity, listing_id=listing_data.id,
                                                created_by=g.current_user['email'])
                    db.session.add(new_data)
                    db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    updated_data = listing_schema.dump(listing_data)
    return jsonify({'message': f'Amenities added successfully!', 'updated_data': updated_data}), 200


# Delete Car Amenities
@views.route('/client/single-car-view/delete-amenities/<int:id>', methods=['DELETE'])
@jwt_required()
@current_user_required
def delete_car_amenities(id):
    amenity_ids = request.get_json().get('amenity_ids')
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='car').first()
        if listing_data:
            for amenity_id in amenity_ids:
                amenity = ListingAmenities.query.get(amenity_id)
                db.session.delete(amenity)
                db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    return 'Success!', 200


# Delete Car Listing
@views.route('/client/single-car-view/delete-listing/<int:id>', methods=['DELETE'])
@jwt_required()
@current_user_required
def delete_car_listing(id):
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='car').first()
        if listing_data:
            listing = Listings.query.get(id)
            if listing_data.featured_image:
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], listing_data.featured_image)
                if os.path.exists(image_path):
                    os.remove(image_path)
            for image in listing_data.listing_image:
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image.image)
                if os.path.exists(image_path):
                    os.remove(image_path)
            db.session.delete(listing)
            db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    return 'Success!', 200


############## END OF CAR LISTING ENDPOINT ###############

############## MOTORCYCLE LISTING ENDPOINT ###################

# All Motorcycle View
@views.route('/client/all-motorcycle-view', methods=['GET'])
def all_motorcycle_view():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    search = request.args.get('search', '', type=str)
    brand = request.args.get('brand', type=str)
    startPrice = request.args.get('startPrice', '', type=str)
    endPrice = request.args.get('endPrice', '', type=str)
    startModelYear = request.args.get('startModelYear', '', type=str)
    endModelYear = request.args.get('endModelYear', '', type=str)
    startMileage = request.args.get('startMileage', '', type=str)
    endMileage = request.args.get('endMileage', '', type=str)

    data = Listings.query.filter_by(vehicle_type='motorcycle')

    if search or brand or (startPrice and endPrice) or (startMileage and endMileage) or (
            startModelYear and endModelYear):
        filter_conditions = []

        if search:
            search_conditions = Listings.title.ilike(f"%{search}%")
            filter_conditions.append(search_conditions)
        if brand:
            brand_conditions = Listings.brand_id.ilike(f"%{brand}")
            filter_conditions.append(brand_conditions)
        if startPrice and endPrice:
            price_condition = Listings.price.between(startPrice, endPrice)
            filter_conditions.append(price_condition)
        if startMileage and endMileage:
            mileage_condition = Listings.mileage.between(startMileage, endMileage)
            filter_conditions.append(mileage_condition)
        if startModelYear and endModelYear:
            modelYear_condition = Listings.model_year.between(startModelYear, endModelYear)
            filter_conditions.append(modelYear_condition)

        data = data.filter(and_(*filter_conditions))

    data = data.order_by(Listings.id.desc())

    data_paginated = data.limit(page_size).offset((page - 1) * page_size).all()

    result = listings_schema.dump(data_paginated)

    return jsonify({
        "data": result,
        "total": data.count()
    }), 200


# User Motorcycle View
@views.route('/client/user-motorcycle-view/<int:id>', methods=['GET'])
def user_motorcycle_view(id):
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    search = request.args.get('search', '', type=str)

    data = Listings.query.filter_by(vehicle_type='motorcycle', user_id=id)

    user = User.query.get(id)
    if not user:
        return jsonify({
            "message": 'User not found',
        }), 400

    if search:
        search_words = search.split(',')

        def search_filter(word):
            word = word.strip()
            return or_(
                Listings.title.ilike(f"%{word}%"),
            )

        filter_conditions = [search_filter(word) for word in search_words]
        data = data.filter(*filter_conditions)

    data = data.order_by(Listings.id.desc())

    data_paginated = data.limit(page_size).offset((page - 1) * page_size).all()

    result = listings_schema.dump(data_paginated)

    return jsonify({
        "data": result,
        "total": data.count()
    }), 200


# Motorcycle Create
@views.route('/client/motorcycle-create', methods=['POST'])
@jwt_required()
@current_user_required
def motorcycle_create():
    new_data = request.form

    file_name = None
    file = request.files.get('featured_image')

    if file and allowed_file(file.filename):
        resize_file = resize_image(file, max_size_kb=1024)
        filename = secure_filename(file.filename)
        file_name = str(uuid.uuid1()) + '_' + filename
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file_name)
        resize_file.save(filepath, format='JPEG')

    title = f"{new_data['model']} {new_data['model_year']}"
    slug = slugify(title)

    listing_data = Listings(
        vin=new_data['vin'],
        title=title,
        slug=slug,
        price=new_data['price'],
        description=new_data['description'],
        model=new_data['model'],
        model_year=new_data['model_year'],
        variant=new_data['variant'],
        mileage=new_data['mileage'],
        vehicle_type='motorcycle',
        featured_as='standard',
        user_id=new_data['user_id'],
        brand_id=new_data['brand_id'],
        location_id=new_data['location_id'],
        community_id=new_data['community_id'],
        featured_image=file_name,
        created_by=g.current_user['email']
    )
    db.session.add(listing_data)
    db.session.commit()

    images = request.files.getlist('images')
    for image in images:
        if image and allowed_file(image.filename):
            resized_img = resize_image(image, max_size_kb=1024)
            filename = str(uuid.uuid1()) + '_' + secure_filename(image.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            resized_img.save(filepath, format='JPEG')

            images_data = ListingImage(image=filename, listing_id=listing_data.id, created_by=g.current_user['email'])
            db.session.add(images_data)
            db.session.commit()

    safety_features = new_data['safety_features'].split(',')
    for features in safety_features:
        features_data = SafetyFeatures(name=features, listing_id=listing_data.id)
        db.session.add(features_data)
        db.session.commit()

    amenities = new_data['amenities'].split(',')
    for amenity in amenities:
        amenity_data = ListingAmenities(name=amenity, listing_id=listing_data.id)
        db.session.add(amenity_data)
        db.session.commit()

    motorcycle_data = Motorcycle(
        listing_id=listing_data.id,
        type=new_data['type'],
        usage=new_data['usage'],
        warranty=new_data['warranty'],
        wheels=new_data['wheels'],
        seller_type=new_data['seller_type'],
        final_drive_system=new_data['final_drive_system'],
        engine_size=new_data['engine_size'],
        created_by=g.current_user['email']
    )
    db.session.add(motorcycle_data)
    db.session.commit()

    new_added_data = listing_schema.dump(listing_data)
    return jsonify({'message': 'Motorcycle successfully listed!', 'new_data': new_added_data}), 200


# Single Motorcycle View
@views.route('/client/single-motorcycle-view/<int:id>', methods=['GET'])
def single_motorcycle_view(id):
    data = Listings.query.filter_by(id=id, vehicle_type='motorcycle').first()
    if data is None:
        return jsonify({'message': 'Motorcycle not found.'}), 400
    result = listing_schema.dump(data)

    return jsonify({
        "data": result,
    }), 200


# Single Motorcycle Update Information
@views.route('/client/single-motorcycle-view/update-information/<int:id>', methods=['PUT'])
@jwt_required()
@current_user_required
def update_motorcycle(id):
    new_data = request.get_json()
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='motorcycle').first()
        if listing_data:
            title = f"{new_data['model']} {new_data['model_year']}"
            slug = slugify(title)
            listing_data.title = title
            listing_data.slug = slug
            listing_data.price = new_data['price']
            listing_data.description = new_data['description']
            listing_data.model = new_data['model']
            listing_data.model_year = new_data['model_year']
            listing_data.variant = new_data['variant']
            listing_data.mileage = new_data['mileage']
            listing_data.updated_by = g.current_user['email']
            listing_data.updated_date = datetime.now()
            db.session.commit()

            motorcycle_data = Motorcycle.query.filter_by(listing_id=listing_data.id).first()
            motorcycle_data.type = new_data['type']
            motorcycle_data.usage = new_data['usage']
            motorcycle_data.warranty = new_data['warranty']
            motorcycle_data.wheels = new_data['wheels']
            motorcycle_data.seller_type = new_data['seller_type']
            motorcycle_data.final_drive_system = new_data['final_drive_system']
            motorcycle_data.engine_size = new_data['engine_size']
            motorcycle_data.updated_by = g.current_user['email']
            motorcycle_data.updated_date = datetime.now()
            db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    updated_data = listing_schema.dump(listing_data)
    return jsonify({'message': f'Listing updated successfully!', 'updated_data': updated_data}), 200


# Motorcycle update featured image
@views.route('/client/single-motorcycle-view/update-featured-image/<int:id>', methods=['PUT'])
@jwt_required()
@current_user_required
def update_motorcycle_featured_img(id):
    image = request.files.get('featured_image')
    if not image:
        return jsonify({'message': 'No image file provided'}), 400

    if not allowed_file(image.filename):
        return jsonify({'message': 'Invalid image file format'}), 400

    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='motorcycle').first()
        if listing_data:
            if listing_data.featured_image:
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], listing_data.featured_image)
                if os.path.exists(image_path):
                    os.remove(image_path)

            resized_img = resize_image(image, max_size_kb=1024)
            filename = str(uuid.uuid1()) + '_' + secure_filename(image.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            resized_img.save(filepath, format='JPEG')

            listing_data.featured_image = filename
            listing_data.updated_by = g.current_user['email']
            listing_data.updated_date = datetime.now()
            db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    updated_data = listing_schema.dump(listing_data)
    return jsonify({'message': f'Listing Featured Image updated successfully!', 'updated_data': updated_data}), 200


# Motorcycle Add Images
@views.route('/client/single-motorcycle-view/add-images/<int:id>', methods=['POST'])
@jwt_required()
@current_user_required
def motorcycle_add_images(id):
    images = request.files.getlist('images')
    if not images:
        return jsonify({'message': 'No image files provided'}), 400

    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()

    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='motorcycle').first()
        if listing_data:
            for image in images:
                if image and allowed_file(image.filename):
                    resized_img = resize_image(image, max_size_kb=1024)
                    filename = str(uuid.uuid1()) + '_' + secure_filename(image.filename)
                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    resized_img.save(filepath, format='JPEG')

                    new_data = ListingImage(image=filename, listing_id=listing_data.id,
                                            created_by=g.current_user['email'])
                    db.session.add(new_data)
                    db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    updated_data = listing_schema.dump(listing_data)
    return jsonify({'message': f'Images successfully added!', 'updated_data': updated_data}), 200


# Delete Motor Images
@views.route('/client/single-motorcycle-view/delete-images/<int:id>', methods=['DELETE'])
@jwt_required()
@current_user_required
def delete_motor_images(id):
    image_ids = request.get_json().get('image_ids')
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='motorcycle').first()
        if listing_data:
            for image_id in image_ids:
                image = ListingImage.query.get(image_id)
                if image:
                    image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image.image)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                db.session.delete(image)
                db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    return 'Success!', 200


# Motorcycle Add Safety Features
@views.route('/client/single-motorcycle-view/add-safety-features/<int:id>', methods=['POST'])
@jwt_required()
@current_user_required
def motorcycle_add_safety_features(id):
    features = request.get_json().get('features')
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='motorcycle').first()
        if listing_data:
            for feature in features:
                existing_feature = SafetyFeatures.query.filter_by(name=feature.lower(), listing_id=id).first()
                if existing_feature:
                    pass
                else:
                    new_data = SafetyFeatures(name=feature, listing_id=listing_data.id,
                                              created_by=g.current_user['email'])
                    db.session.add(new_data)
                    db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    updated_data = listing_schema.dump(listing_data)
    return jsonify({'message': f'Safety Features added successfully!', 'updated_data': updated_data}), 200


# Delete Motorcycle Safety Features
@views.route('/client/single-motorcycle-view/delete-safety-features/<int:id>', methods=['DELETE'])
@jwt_required()
@current_user_required
def delete_motorcycle_safety_features(id):
    feature_ids = request.get_json().get('feature_ids')
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='motorcycle').first()
        if listing_data:
            for feature_id in feature_ids:
                feature = SafetyFeatures.query.get(feature_id)
                db.session.delete(feature)
                db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    return 'Success!', 200


# Motorcycle Add Amenities
@views.route('/client/single-motorcycle-view/add-amenities/<int:id>', methods=['POST'])
@jwt_required()
@current_user_required
def motorcycle_add_amenities(id):
    amenities = request.get_json().get('amenities')
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='motorcycle').first()
        if listing_data:
            for amenity in amenities:
                existing_data = ListingAmenities.query.filter_by(name=amenity.lower(), listing_id=id).first()
                if existing_data:
                    pass
                else:
                    new_data = ListingAmenities(name=amenity, listing_id=listing_data.id,
                                                created_by=g.current_user['email'])
                    db.session.add(new_data)
                    db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    updated_data = listing_schema.dump(listing_data)
    return jsonify({'message': f'Amenities added successfully!', 'updated_data': updated_data}), 200


# Delete Motor Amenities
@views.route('/client/single-motorcycle-view/delete-amenities/<int:id>', methods=['DELETE'])
@jwt_required()
@current_user_required
def delete_motorcycle_amenities(id):
    amenity_ids = request.get_json().get('amenity_ids')
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='motorcycle').first()
        if listing_data:
            for amenity_id in amenity_ids:
                amenity = ListingAmenities.query.get(amenity_id)
                db.session.delete(amenity)
                db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    return 'Success!', 200


# Delete Motorcycle Listing
@views.route('/client/single-motorcycle-view/delete-listing/<int:id>', methods=['DELETE'])
@jwt_required()
@current_user_required
def delete_motorcycle_listing(id):
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='motorcycle').first()
        if listing_data:
            listing = Listings.query.get(id)
            if listing_data.featured_image:
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], listing_data.featured_image)
                if os.path.exists(image_path):
                    os.remove(image_path)
            for image in listing_data.listing_image:
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image.image)
                if os.path.exists(image_path):
                    os.remove(image_path)
            db.session.delete(listing)
            db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    return 'Success!', 200


########## END OF MOTORCYCLE LISTING ENDPOINT ###########

########### BOAT LISTING ENDPOINT ################

# All Boat View
@views.route('/client/all-boat-view', methods=['GET'])
def all_boat_view():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    search = request.args.get('search', '', type=str)
    brand = request.args.get('brand', type=str)
    startPrice = request.args.get('startPrice', '', type=str)
    endPrice = request.args.get('endPrice', '', type=str)
    startModelYear = request.args.get('startModelYear', '', type=str)
    endModelYear = request.args.get('endModelYear', '', type=str)
    startMileage = request.args.get('startMileage', '', type=str)
    endMileage = request.args.get('endMileage', '', type=str)

    data = Listings.query.filter_by(vehicle_type='boat')

    if search or brand or (startPrice and endPrice) or (startMileage and endMileage) or (
            startModelYear and endModelYear):
        filter_conditions = []

        if search:
            search_conditions = Listings.title.ilike(f"%{search}%")
            filter_conditions.append(search_conditions)
        if brand:
            brand_conditions = Listings.brand_id.ilike(f"%{brand}")
            filter_conditions.append(brand_conditions)
        if startPrice and endPrice:
            price_condition = Listings.price.between(startPrice, endPrice)
            filter_conditions.append(price_condition)
        if startMileage and endMileage:
            mileage_condition = Listings.mileage.between(startMileage, endMileage)
            filter_conditions.append(mileage_condition)
        if startModelYear and endModelYear:
            modelYear_condition = Listings.model_year.between(startModelYear, endModelYear)
            filter_conditions.append(modelYear_condition)

        data = data.filter(and_(*filter_conditions))

    data = data.order_by(Listings.id.desc())

    data_paginated = data.limit(page_size).offset((page - 1) * page_size).all()

    result = listings_schema.dump(data_paginated)

    return jsonify({
        "data": result,
        "total": data.count()
    }), 200


# User Boat View
@views.route('/client/user-boat-view/<int:id>', methods=['GET'])
def user_boat_view(id):
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    search = request.args.get('search', '', type=str)

    data = Listings.query.filter_by(vehicle_type='boat', user_id=id)

    user = User.query.get(id)
    if not user:
        return jsonify({
            "message": 'User not found',
        }), 400

    if search:
        search_words = search.split(',')

        def search_filter(word):
            word = word.strip()
            return or_(
                Listings.title.ilike(f"%{word}%"),
            )

        filter_conditions = [search_filter(word) for word in search_words]
        data = data.filter(*filter_conditions)

    data = data.order_by(Listings.id.desc())

    data_paginated = data.limit(page_size).offset((page - 1) * page_size).all()

    result = listings_schema.dump(data_paginated)

    return jsonify({
        "data": result,
        "total": data.count()
    }), 200


# Boat Create
@views.route('/client/boat-create', methods=['POST'])
@jwt_required()
@current_user_required
def boat_create():
    new_data = request.form

    file_name = None
    file = request.files.get('featured_image')

    if file and allowed_file(file.filename):
        resize_file = resize_image(file, max_size_kb=1024)
        filename = secure_filename(file.filename)
        file_name = str(uuid.uuid1()) + '_' + filename
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file_name)
        resize_file.save(filepath, format='JPEG')

    title = f"{new_data['model']} {new_data['model_year']}"
    slug = slugify(title)

    listing_data = Listings(
        vin=new_data['vin'],
        title=title,
        slug=slug,
        price=new_data['price'],
        description=new_data['description'],
        model=new_data['model'],
        model_year=new_data['model_year'],
        variant=new_data['variant'],
        mileage=new_data['mileage'],
        vehicle_type='boat',
        featured_as='standard',
        user_id=new_data['user_id'],
        brand_id=new_data['brand_id'],
        location_id=new_data['location_id'],
        community_id=new_data['community_id'],
        featured_image=file_name,
        created_by=g.current_user['email']
    )
    db.session.add(listing_data)
    db.session.commit()

    images = request.files.getlist('images')
    for image in images:
        if image and allowed_file(image.filename):
            resized_img = resize_image(image, max_size_kb=1024)
            filename = str(uuid.uuid1()) + '_' + secure_filename(image.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            resized_img.save(filepath, format='JPEG')

            images_data = ListingImage(image=filename, listing_id=listing_data.id, created_by=g.current_user['email'])
            db.session.add(images_data)
            db.session.commit()

    safety_features = new_data['safety_features'].split(',')
    for features in safety_features:
        features_data = SafetyFeatures(name=features, listing_id=listing_data.id)
        db.session.add(features_data)
        db.session.commit()

    amenities = new_data['amenities'].split(',')
    for amenity in amenities:
        amenity_data = ListingAmenities(name=amenity, listing_id=listing_data.id)
        db.session.add(amenity_data)
        db.session.commit()

    boat_data = Boats(
        listing_id=listing_data.id,
        type_1=new_data['type_1'],
        type_2=new_data['type_2'],
        usage=new_data['usage'],
        warranty=new_data['warranty'],
        age=new_data['age'],
        seller_type=new_data['seller_type'],
        length=new_data['length'],
        condition=new_data['condition'],
        created_by=g.current_user['email']
    )
    db.session.add(boat_data)
    db.session.commit()

    new_added_data = listing_schema.dump(listing_data)
    return jsonify({'message': 'Boat successfully listed!', 'new_data': new_added_data}), 200

# Single Boat Update Information
@views.route('/client/single-boat-view/update-information/<int:id>', methods=['PUT'])
@jwt_required()
@current_user_required
def update_boat(id):
    new_data = request.get_json()
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='boat').first()
        if listing_data:
            title = f"{new_data['model']} {new_data['model_year']}"
            slug = slugify(title)
            listing_data.title = title
            listing_data.slug = slug
            listing_data.price = new_data['price']
            listing_data.description = new_data['description']
            listing_data.model = new_data['model']
            listing_data.model_year = new_data['model_year']
            listing_data.variant = new_data['variant']
            listing_data.mileage = new_data['mileage']
            listing_data.updated_by = g.current_user['email']
            listing_data.updated_date = datetime.now()
            db.session.commit()

            boat_data = Boats.query.filter_by(listing_id=listing_data.id).first()
            boat_data.type_1 = new_data['type_1']
            boat_data.type_2 = new_data['type_2']
            boat_data.usage = new_data['usage']
            boat_data.warranty = new_data['warranty']
            boat_data.age = new_data['age']
            boat_data.seller_type = new_data['seller_type']
            boat_data.length = new_data['length']
            boat_data.condition = new_data['condition']
            boat_data.updated_by = g.current_user['email']
            boat_data.updated_date = datetime.now()
            db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    updated_data = listing_schema.dump(listing_data)
    return jsonify({'message': f'Listing updated successfully!', 'updated_data': updated_data}), 200


# Single Boat View
@views.route('/client/single-boat-view/<int:id>', methods=['GET'])
def single_boat_view(id):
    data = Listings.query.filter_by(id=id, vehicle_type='boat').first()
    if data is None:
        return jsonify({'message': 'Boat not found.'}), 400
    result = listing_schema.dump(data)

    return jsonify({
        "data": result,
    }), 200


# Boat update featured image
@views.route('/client/single-boat-view/update-featured-image/<int:id>', methods=['PUT'])
@jwt_required()
@current_user_required
def update_boat_featured_img(id):
    image = request.files.get('featured_image')
    if not image:
        return jsonify({'message': 'No image file provided'}), 400

    if not allowed_file(image.filename):
        return jsonify({'message': 'Invalid image file format'}), 400

    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='boat').first()
        if listing_data:
            if listing_data.featured_image:
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], listing_data.featured_image)
                if os.path.exists(image_path):
                    os.remove(image_path)

            resized_img = resize_image(image, max_size_kb=1024)
            filename = str(uuid.uuid1()) + '_' + secure_filename(image.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            resized_img.save(filepath, format='JPEG')

            listing_data.featured_image = filename
            listing_data.updated_by = g.current_user['email']
            listing_data.updated_date = datetime.now()
            db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    updated_data = listing_schema.dump(listing_data)
    return jsonify({'message': f'Listing Featured Image updated successfully!', 'updated_data': updated_data}), 200


# Boat Add Images
@views.route('/client/single-boat-view/add-images/<int:id>', methods=['POST'])
@jwt_required()
@current_user_required
def boat_add_images(id):
    images = request.files.getlist('images')
    if not images:
        return jsonify({'message': 'No image files provided'}), 400

    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()

    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='boat').first()
        if listing_data:
            for image in images:
                if image and allowed_file(image.filename):
                    resized_img = resize_image(image, max_size_kb=1024)
                    filename = str(uuid.uuid1()) + '_' + secure_filename(image.filename)
                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    resized_img.save(filepath, format='JPEG')

                    new_data = ListingImage(image=filename, listing_id=listing_data.id,
                                            created_by=g.current_user['email'])
                    db.session.add(new_data)
                    db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    updated_data = listing_schema.dump(listing_data)
    return jsonify({'message': f'Images successfully added!', 'updated_data': updated_data}), 200


# Delete Boat Images
@views.route('/client/single-boat-view/delete-images/<int:id>', methods=['DELETE'])
@jwt_required()
@current_user_required
def delete_boat_images(id):
    image_ids = request.get_json().get('image_ids')
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='boat').first()
        if listing_data:
            for image_id in image_ids:
                image = ListingImage.query.get(image_id)
                if image:
                    image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image.image)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                db.session.delete(image)
                db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    return 'Success!', 200


# Boat Add Safety Features
@views.route('/client/single-boat-view/add-safety-features/<int:id>', methods=['POST'])
@jwt_required()
@current_user_required
def boat_add_safety_features(id):
    features = request.get_json().get('features')
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='boat').first()
        if listing_data:
            for feature in features:
                existing_feature = SafetyFeatures.query.filter_by(name=feature.lower(), listing_id=id).first()
                if existing_feature:
                    pass
                else:
                    new_data = SafetyFeatures(name=feature, listing_id=listing_data.id,
                                              created_by=g.current_user['email'])
                    db.session.add(new_data)
                    db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    updated_data = listing_schema.dump(listing_data)
    return jsonify({'message': f'Safety Features added successfully!', 'updated_data': updated_data}), 200


# Delete Boat Safety Features
@views.route('/client/single-boat-view/delete-safety-features/<int:id>', methods=['DELETE'])
@jwt_required()
@current_user_required
def delete_boat_safety_features(id):
    feature_ids = request.get_json().get('feature_ids')
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='boat').first()
        if listing_data:
            for feature_id in feature_ids:
                feature = SafetyFeatures.query.get(feature_id)
                db.session.delete(feature)
                db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    return 'Success!', 200


# Boat Add Amenities
@views.route('/client/single-boat-view/add-amenities/<int:id>', methods=['POST'])
@jwt_required()
@current_user_required
def boat_add_amenities(id):
    amenities = request.get_json().get('amenities')
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='boat').first()
        if listing_data:
            for amenity in amenities:
                existing_data = ListingAmenities.query.filter_by(name=amenity.lower(), listing_id=id).first()
                if existing_data:
                    pass
                else:
                    new_data = ListingAmenities(name=amenity, listing_id=listing_data.id,
                                                created_by=g.current_user['email'])
                    db.session.add(new_data)
                    db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    updated_data = listing_schema.dump(listing_data)
    return jsonify({'message': f'Amenities added successfully!', 'updated_data': updated_data}), 200

# Delete Boat Amenities
@views.route('/client/single-boat-view/delete-amenities/<int:id>', methods=['DELETE'])
@jwt_required()
@current_user_required
def delete_boat_amenities(id):
    amenity_ids = request.get_json().get('amenity_ids')
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='boat').first()
        if listing_data:
            for amenity_id in amenity_ids:
                amenity = ListingAmenities.query.get(amenity_id)
                db.session.delete(amenity)
                db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    return 'Success!', 200

# Delete Boat Listing
@views.route('/client/single-boat-view/delete-listing/<int:id>', methods=['DELETE'])
@jwt_required()
@current_user_required
def delete_boat_listing(id):
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='boat').first()
        if listing_data:
            listing = Listings.query.get(id)
            if listing_data.featured_image:
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], listing_data.featured_image)
                if os.path.exists(image_path):
                    os.remove(image_path)
            for image in listing_data.listing_image:
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image.image)
                if os.path.exists(image_path):
                    os.remove(image_path)
            db.session.delete(listing)
            db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    return 'Success!', 200


############## END OF BOAT LISTING ENDPOINT ###############

################# HEAVY VEHICLE LISTING ENDPOINT ###############

# All Heavy Vehicle View
@views.route('/client/all-heavy-vehicle-view', methods=['GET'])
def all_heavy_vehicle_view():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    search = request.args.get('search', '', type=str)
    brand = request.args.get('brand', type=str)
    startPrice = request.args.get('startPrice', '', type=str)
    endPrice = request.args.get('endPrice', '', type=str)
    startModelYear = request.args.get('startModelYear', '', type=str)
    endModelYear = request.args.get('endModelYear', '', type=str)
    startMileage = request.args.get('startMileage', '', type=str)
    endMileage = request.args.get('endMileage', '', type=str)

    data = Listings.query.filter_by(vehicle_type='heavy vehicle')

    if search or brand or (startPrice and endPrice) or (startMileage and endMileage) or (
            startModelYear and endModelYear):
        filter_conditions = []

        if search:
            search_conditions = Listings.title.ilike(f"%{search}%")
            filter_conditions.append(search_conditions)
        if brand:
            brand_conditions = Listings.brand_id.ilike(f"%{brand}")
            filter_conditions.append(brand_conditions)
        if startPrice and endPrice:
            price_condition = Listings.price.between(startPrice, endPrice)
            filter_conditions.append(price_condition)
        if startMileage and endMileage:
            mileage_condition = Listings.mileage.between(startMileage, endMileage)
            filter_conditions.append(mileage_condition)
        if startModelYear and endModelYear:
            modelYear_condition = Listings.model_year.between(startModelYear, endModelYear)
            filter_conditions.append(modelYear_condition)

        data = data.filter(and_(*filter_conditions))

    data = data.order_by(Listings.id.desc())

    data_paginated = data.limit(page_size).offset((page - 1) * page_size).all()

    result = listings_schema.dump(data_paginated)

    return jsonify({
        "data": result,
        "total": data.count()
    }), 200

# User Heavy Vehicle View
@views.route('/client/user-heavy-vehicle-view/<int:id>', methods=['GET'])
def user_heavy_vehicle_view(id):
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    search = request.args.get('search', '', type=str)

    data = Listings.query.filter_by(vehicle_type='heavy vehicle', user_id=id)

    user = User.query.get(id)
    if not user:
        return jsonify({
            "message": 'User not found',
        }), 400

    if search:
        search_words = search.split(',')

        def search_filter(word):
            word = word.strip()
            return or_(
                Listings.title.ilike(f"%{word}%"),
            )

        filter_conditions = [search_filter(word) for word in search_words]
        data = data.filter(*filter_conditions)

    data = data.order_by(Listings.id.desc())

    data_paginated = data.limit(page_size).offset((page - 1) * page_size).all()

    result = listings_schema.dump(data_paginated)

    return jsonify({
        "data": result,
        "total": data.count()
    }), 200

# Heavy Vehicle Create
@views.route('/client/heavy-vehicle-create', methods=['POST'])
@jwt_required()
@current_user_required
def heavy_vehicle_create():
    new_data = request.form

    file_name = None
    file = request.files.get('featured_image')

    if file and allowed_file(file.filename):
        resize_file = resize_image(file, max_size_kb=1024)
        filename = secure_filename(file.filename)
        file_name = str(uuid.uuid1()) + '_' + filename
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file_name)
        resize_file.save(filepath, format='JPEG')

    title = f"{new_data['model']} {new_data['model_year']}"
    slug = slugify(title)

    listing_data = Listings(
        vin=new_data['vin'],
        title=title,
        slug=slug,
        price=new_data['price'],
        description=new_data['description'],
        model=new_data['model'],
        model_year=new_data['model_year'],
        variant=new_data['variant'],
        mileage=new_data['mileage'],
        vehicle_type='heavy vehicle',
        featured_as='standard',
        user_id=new_data['user_id'],
        brand_id=new_data['brand_id'],
        location_id=new_data['location_id'],
        community_id=new_data['community_id'],
        featured_image=file_name,
        created_by=g.current_user['email']
    )
    db.session.add(listing_data)
    db.session.commit()

    images = request.files.getlist('images')
    for image in images:
        if image and allowed_file(image.filename):
            resized_img = resize_image(image, max_size_kb=1024)
            filename = str(uuid.uuid1()) + '_' + secure_filename(image.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            resized_img.save(filepath, format='JPEG')

            images_data = ListingImage(image=filename, listing_id=listing_data.id, created_by=g.current_user['email'])
            db.session.add(images_data)
            db.session.commit()

    safety_features = new_data['safety_features'].split(',')
    for features in safety_features:
        features_data = SafetyFeatures(name=features, listing_id=listing_data.id)
        db.session.add(features_data)
        db.session.commit()

    amenities = new_data['amenities'].split(',')
    for amenity in amenities:
        amenity_data = ListingAmenities(name=amenity, listing_id=listing_data.id)
        db.session.add(amenity_data)
        db.session.commit()

    heavy_vehicle_data = HeavyVehicles(
        listing_id=listing_data.id,
        type_1=new_data['type_1'],
        type_2=new_data['type_2'],
        fuel_type=new_data['fuel_type'],
        no_of_cylinders=new_data['no_of_cylinders'],
        body_condition=new_data['body_condition'],
        mechanical_condition=new_data['mechanical_condition'],
        capacity_weight=new_data['capacity_weight'],
        seller_type=new_data['seller_type'],
        warranty=new_data['warranty'],
        horse_power=new_data['horse_power'],
        created_by=g.current_user['email']
    )
    db.session.add(heavy_vehicle_data)
    db.session.commit()

    new_added_data = listing_schema.dump(listing_data)
    return jsonify({'message': 'Heavy Vehicle successfully listed!', 'new_data': new_added_data}), 200

# Single Heavy Vehicle Update Information
@views.route('/client/single-heavy-vehicle-view/update-information/<int:id>', methods=['PUT'])
@jwt_required()
@current_user_required
def update_heavy_vehicle(id):
    new_data = request.get_json()
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='heavy vehicle').first()
        if listing_data:
            title = f"{new_data['model']} {new_data['model_year']}"
            slug = slugify(title)
            listing_data.title = title
            listing_data.slug = slug
            listing_data.price = new_data['price']
            listing_data.description = new_data['description']
            listing_data.model = new_data['model']
            listing_data.model_year = new_data['model_year']
            listing_data.variant = new_data['variant']
            listing_data.mileage = new_data['mileage']
            listing_data.updated_by = g.current_user['email']
            listing_data.updated_date = datetime.now()
            db.session.commit()

            heavy_vehicle_data = HeavyVehicles.query.filter_by(listing_id=listing_data.id).first()
            heavy_vehicle_data.type_1 = new_data['type_1']
            heavy_vehicle_data.type_2 = new_data['type_2']
            heavy_vehicle_data.fuel_type = new_data['fuel_type']
            heavy_vehicle_data.no_of_cylinders = new_data['no_of_cylinders']
            heavy_vehicle_data.body_condition = new_data['body_condition']
            heavy_vehicle_data.mechanical_condition = new_data['mechanical_condition']
            heavy_vehicle_data.capacity_weight = new_data['capacity_weight']
            heavy_vehicle_data.seller_type = new_data['seller_type']
            heavy_vehicle_data.warranty = new_data['warranty']
            heavy_vehicle_data.horse_power = new_data['horse_power']
            heavy_vehicle_data.updated_by = g.current_user['email']
            heavy_vehicle_data.updated_date = datetime.now()
            db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    updated_data = listing_schema.dump(listing_data)
    return jsonify({'message': f'Listing updated successfully!', 'updated_data': updated_data}), 200

# Single Heavy Vehicle View
@views.route('/client/single-heavy-vehicle-view/<int:id>', methods=['GET'])
def single_heavy_vehicle_view(id):
    data = Listings.query.filter_by(id=id, vehicle_type='heavy vehicle').first()
    if data is None:
        return jsonify({'message': 'Heavy Vehicle not found.'}), 400
    result = listing_schema.dump(data)

    return jsonify({
        "data": result,
    }), 200

# Heavy Vehicle update featured image
@views.route('/client/single-heavy-vehicle-view/update-featured-image/<int:id>', methods=['PUT'])
@jwt_required()
@current_user_required
def update_heavy_vehicle_featured_img(id):
    image = request.files.get('featured_image')
    if not image:
        return jsonify({'message': 'No image file provided'}), 400

    if not allowed_file(image.filename):
        return jsonify({'message': 'Invalid image file format'}), 400

    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='heavy vehicle').first()
        if listing_data:
            if listing_data.featured_image:
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], listing_data.featured_image)
                if os.path.exists(image_path):
                    os.remove(image_path)

            resized_img = resize_image(image, max_size_kb=1024)
            filename = str(uuid.uuid1()) + '_' + secure_filename(image.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            resized_img.save(filepath, format='JPEG')

            listing_data.featured_image = filename
            listing_data.updated_by = g.current_user['email']
            listing_data.updated_date = datetime.now()
            db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    updated_data = listing_schema.dump(listing_data)
    return jsonify({'message': f'Listing Featured Image updated successfully!', 'updated_data': updated_data}), 200

# Heavy Vehicle Add Images
@views.route('/client/single-heavy-vehicle-view/add-images/<int:id>', methods=['POST'])
@jwt_required()
@current_user_required
def heavy_vehicle_add_images(id):
    images = request.files.getlist('images')
    if not images:
        return jsonify({'message': 'No image files provided'}), 400

    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()

    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='heavy vehicle').first()
        if listing_data:
            for image in images:
                if image and allowed_file(image.filename):
                    resized_img = resize_image(image, max_size_kb=1024)
                    filename = str(uuid.uuid1()) + '_' + secure_filename(image.filename)
                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    resized_img.save(filepath, format='JPEG')

                    new_data = ListingImage(image=filename, listing_id=listing_data.id,
                                            created_by=g.current_user['email'])
                    db.session.add(new_data)
                    db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    updated_data = listing_schema.dump(listing_data)
    return jsonify({'message': f'Images successfully added!', 'updated_data': updated_data}), 200

# Delete Heavy Vehicle Images
@views.route('/client/single-heavy-vehicle-view/delete-images/<int:id>', methods=['DELETE'])
@jwt_required()
@current_user_required
def delete_heavy_vehicle_images(id):
    image_ids = request.get_json().get('image_ids')
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='heavy vehicle').first()
        if listing_data:
            for image_id in image_ids:
                image = ListingImage.query.get(image_id)
                if image:
                    image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image.image)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                db.session.delete(image)
                db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    return 'Success!', 200


# Heavy Vehicle Add Safety Features
@views.route('/client/single-heavy-vehicle-view/add-safety-features/<int:id>', methods=['POST'])
@jwt_required()
@current_user_required
def heavy_vehicle_add_safety_features(id):
    features = request.get_json().get('features')
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='heavy vehicle').first()
        if listing_data:
            for feature in features:
                existing_feature = SafetyFeatures.query.filter_by(name=feature.lower(), listing_id=id).first()
                if existing_feature:
                    pass
                else:
                    new_data = SafetyFeatures(name=feature, listing_id=listing_data.id,
                                              created_by=g.current_user['email'])
                    db.session.add(new_data)
                    db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    updated_data = listing_schema.dump(listing_data)
    return jsonify({'message': f'Safety Features added successfully!', 'updated_data': updated_data}), 200


# Delete Heavy Vehicle Safety Features
@views.route('/client/single-heavy-vehicle-view/delete-safety-features/<int:id>', methods=['DELETE'])
@jwt_required()
@current_user_required
def delete_heavy_vehicle_safety_features(id):
    feature_ids = request.get_json().get('feature_ids')
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='heavy vehicle').first()
        if listing_data:
            for feature_id in feature_ids:
                feature = SafetyFeatures.query.get(feature_id)
                db.session.delete(feature)
                db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    return 'Success!', 200


# Heavy Vehicle Add Amenities
@views.route('/client/single-heavy-vehicle-view/add-amenities/<int:id>', methods=['POST'])
@jwt_required()
@current_user_required
def heavy_vehicle_add_amenities(id):
    amenities = request.get_json().get('amenities')
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='heavy vehicle').first()
        if listing_data:
            for amenity in amenities:
                existing_data = ListingAmenities.query.filter_by(name=amenity.lower(), listing_id=id).first()
                if existing_data:
                    pass
                else:
                    new_data = ListingAmenities(name=amenity, listing_id=listing_data.id,
                                                created_by=g.current_user['email'])
                    db.session.add(new_data)
                    db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    updated_data = listing_schema.dump(listing_data)
    return jsonify({'message': f'Amenities added successfully!', 'updated_data': updated_data}), 200


# Delete Heavy Vehicle Amenities
@views.route('/client/single-heavy-vehicle-view/delete-amenities/<int:id>', methods=['DELETE'])
@jwt_required()
@current_user_required
def delete_heavy_vehicle_amenities(id):
    amenity_ids = request.get_json().get('amenity_ids')
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='heavy vehicle').first()
        if listing_data:
            for amenity_id in amenity_ids:
                amenity = ListingAmenities.query.get(amenity_id)
                db.session.delete(amenity)
                db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    return 'Success!', 200


# Delete Heavy Vehicle Listing
@views.route('/client/single-heavy-vehicle-view/delete-listing/<int:id>', methods=['DELETE'])
@jwt_required()
@current_user_required
def delete_heavy_vehicle_listing(id):
    data = User.query.get(g.current_user['id'])
    data_listing = Listings.query.filter_by(id=id, user_id=data.id).first()
    if data_listing:
        listing_data = Listings.query.filter_by(id=id, vehicle_type='heavy vehicle').first()
        if listing_data:
            listing = Listings.query.get(id)
            if listing_data.featured_image:
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], listing_data.featured_image)
                if os.path.exists(image_path):
                    os.remove(image_path)
            for image in listing_data.listing_image:
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image.image)
                if os.path.exists(image_path):
                    os.remove(image_path)
            db.session.delete(listing)
            db.session.commit()
        else:
            return jsonify({'message': 'Listing not found.'}), 400
    else:
        return jsonify({'message': 'You are not allowed to update other users listing.'}), 400

    return 'Success!', 200


############## END OF HEAVY VEHICLE LISTING ENDPOINT ###############

######### BRANDS ENDPOINT ######################

# Get All Car Brands
@views.route('/client/car-brand-view', methods=['GET'])
def client_car_brands_view():
    data = Brand.query.filter_by(type='car')

    result = brands_schema.dump(data)

    return jsonify({
        "data": result,
        "total": data.count()
    }), 200


# Get All Motorcycle Brands
@views.route('/client/motorcycle-brand-view', methods=['GET'])
def client_motorcycle_brand_view():
    data = Brand.query.filter_by(type='motorcycle')

    result = brands_schema.dump(data)

    return jsonify({
        "data": result,
        "total": data.count()
    }), 200


# Get All Boats Brands
@views.route('/client/boats-brand-view', methods=['GET'])
def client_boats_brand_view():
    data = Brand.query.filter_by(type='boat')

    result = brands_schema.dump(data)

    return jsonify({
        "data": result,
        "total": data.count()
    }), 200


# Get All Heavy Vehicle Brands
@views.route('/client/heavy-vehicle-brand-view', methods=['GET'])
def client_heavy_vehicle_brand_view():
    data = Brand.query.filter_by(type='heavy vehicle')

    result = brands_schema.dump(data)

    return jsonify({
        "data": result,
        "total": data.count()
    }), 200


########### END OF BRANDS  ENDPOINT#########################

############# LOCATION AND COMMUNITY ENDPOINTS ####################
# Get All Location
@views.route('/client/location-view', methods=['GET'])
def client_location_view():
    data = Location.query

    result = locations_schema.dump(data)

    return jsonify({
        "data": result,
        "total": data.count()
    }), 200


# Get Community Based on location
@views.route('/client/community-view', methods=['GET'])
def client_community_view():
    location_id = request.args.get('location_id', type=int)
    data = Community.query.filter_by(location_id=location_id)

    result = communities_schema.dump(data)

    return jsonify({
        "data": result,
        "total": data.count()
    }), 200


############# END OF LOCATION AND COMMUNITY ENDPOINTS####################

############## USER PROFILE ENDPOINTS #######################
# User Profile View
@views.route('/user-profile/<int:id>', methods=['GET'])
def user_profile(id):
    data = User.query.get(id)
    if data:
        result = user_schema.dump(data)
    else:
        return jsonify({'message': 'User not found.'}), 400

    return jsonify({"data": result})


# User Update Profile
@views.route('/update/user/profile/<int:id>', methods=['PUT'])
@jwt_required()
@current_user_required
def update_user_profile(id):
    new_data = request.get_json()
    data = User.query.get(id)

    if data:
        data.first_name = new_data['first_name']
        data.last_name = new_data['last_name']
        data.contact_number = new_data['contact_number']
        data.whats_app_number = new_data['whats_app_number']
        data.viber_number = new_data['viber_number']
        data.updated_by = g.current_user['email']
        data.updated_date = datetime.now()
        db.session.commit()
    else:
        return jsonify({'message': 'User not found.'}), 400

    updated_data = user_schema.dump(data)
    return jsonify({'message': f'Profile updated successfully!', 'updated_data': updated_data}), 200


# User update password
@views.route('/update/user/profile-password/<int:id>', methods=['PUT'])
@jwt_required()
@current_user_required
def update_profile_password(id):
    new_data = request.get_json()

    data = User.query.get(id)
    if data:
        old_password = new_data['old_password']
        if not bcrypt.check_password_hash(data.password, old_password):
            return jsonify({'message': 'Invalid old password.'}), 400

        new_password = new_data['new_password']
        password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        data.password = password_hash
        data.updated_by = g.current_user['email']
        data.updated_date = datetime.now()
        db.session.commit()
    else:
        return jsonify({'message': 'User not found.'}), 400

    return jsonify({'message': f'Password updated successfully!'}), 200


# User update profile picture
@views.route('/update/user/profile-picture/<int:id>', methods=['PUT'])
@jwt_required()
@current_user_required
def update_profile_picture(id):
    image = request.files.get('image')
    if not image:
        return jsonify({'message': 'No image file provided'}), 400

    if not allowed_file(image.filename):
        return jsonify({'message': 'Invalid image file format'}), 400

    data = User.query.get(id)
    if data:
        if data.profile_picture != 'default_profile_picture.jpg':
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], data.profile_picture)
            if os.path.exists(image_path):
                os.remove(image_path)

        resized_img = resize_image(image, max_size_kb=1024)
        filename = str(uuid.uuid1()) + '_' + secure_filename(image.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        resized_img.save(filepath, format='JPEG')

        data.profile_picture = filename
        data.updated_by = g.current_user['email']
        data.updated_date = datetime.now()
        db.session.commit()
    else:
        return jsonify({'message': 'User not found.'}), 400

    updated_data = user_schema.dump(data)

    return jsonify({'message': f'Profile Picture updated successfully!', 'updated_data': updated_data}), 200

@views.route('/delete/user/<int:id>', methods=['DELETE'])
@jwt_required()
@current_user_required
def delete_user(id):
    data = User.query.get(id)
    if data is None:
        return jsonify({'message': 'User not found.'}), 400

    listing_data = Listings.query.filter_by(user_id=id)
    for listing in listing_data:
        listing_feature_image = listing.featured_image
        if listing_feature_image:
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], listing_feature_image)
            if os.path.exists(image_path):
                os.remove(image_path)
        listing_image_data = ListingImage.query.filter_by(listing_id=listing.id)
        for images in listing_image_data:
            image_data = images.image
            if image_data:
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image_data)
                if os.path.exists(image_path):
                    os.remove(image_path)

    db.session.delete(data)
    db.session.commit()

    return 'Success!', 200


############## END OF USER PROFILE ENDPOINTS #######################

# FOR TESTING DATA
@views.route('/test', methods=['POST'])
def test():
    new_data = request.form
    print(new_data['safety_features'])
    safety_features = new_data['safety_features'].split(', ')
    print(safety_features)

    return jsonify({
        "Success": '200',
    }), 200
