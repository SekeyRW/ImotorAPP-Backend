import io
import os
import threading
import uuid
from datetime import datetime, timedelta

import requests
from PIL import Image
from flask import Blueprint, jsonify, request, send_from_directory, current_app, g
from flask_jwt_extended import jwt_required
from flask_mail import Message
from slugify import slugify
from sqlalchemy import or_, and_
from werkzeug.utils import secure_filename

from . import db, bcrypt, allowed_file, stripe, mail
from .decorators import current_user_required
from .models import Admin, Brand, Location, Community, Cars, Listings, ListingImage, SafetyFeatures, ListingAmenities, \
    User, Motorcycle, Boats, HeavyVehicles, Favorites, Make, Trim
from .schemas import BrandSchema, CommunitySchema, ListingsSchema, CarsSchema, UserSchema, ListingImageSchema, \
    FavoritesSchema, TrimSchema, MakeSchema

views = Blueprint('views', __name__)

# SCHEMAS
brand_schema = BrandSchema()
brands_schema = BrandSchema(many=True)

make_schema = MakeSchema()
makes_schema = MakeSchema(many=True)

trim_schema = TrimSchema()
trims_schema = TrimSchema(many=True)

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

favorite_schema = FavoritesSchema()
favorites_schema = FavoritesSchema(many=True)


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
    type = request.args.get('type', '', type=str)

    data = Brand.query

    if search or type:
        filter_conditions = []

        if search:
            search_conditions = Brand.name.ilike(f"%{search}%")
            filter_conditions.append(search_conditions)
        if type and type.lower() != 'all':
            type_conditions = Brand.type.ilike(f"%{type}%")
            filter_conditions.append(type_conditions)

        data = data.filter(and_(*filter_conditions))

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


# Make & Model View
@views.route('/admin/make-and-model-view/<int:id>', methods=['GET'])
@jwt_required()
@current_user_required
def make_and_model_view(id):
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    search = request.args.get('search', '', type=str)

    data = Make.query.filter_by(brand_id=id)

    if search:
        search_words = search.split(',')

        def search_filter(word):
            word = word.strip()
            return or_(
                Make.name.ilike(f"%{word}%"),
            )

        filter_conditions = [search_filter(word) for word in search_words]
        data = data.filter(*filter_conditions)

    data = data.order_by(Make.id.desc())

    data_paginated = data.limit(page_size).offset((page - 1) * page_size).all()

    result = makes_schema.dump(data_paginated)

    return jsonify({
        "data": result,
        "total": data.count()
    }), 200


# Make & Model Create
@views.route('/admin/make-and-model-create/<int:id>', methods=['POST'])
@jwt_required()
@current_user_required
def make_and_model_create(id):
    new_data = request.get_json()

    if new_data['checkbox'] == 0:
        brand = Brand.query.get(id)
        existing_data = Make.query.filter_by(name=brand.name + " " + new_data['name'].lower(), brand_id=id).first()

        if existing_data is not None:
            return jsonify({'message': 'Make & Model Already Exists!'}), 400

        new_data2 = Make(
            name=brand.name + " " + new_data['name'],
            brand_id=id,
            created_by=g.current_user['email']
        )

        db.session.add(new_data2)
        db.session.commit()

        new_added_data = make_schema.dump(new_data2)
        return jsonify({'message': 'Make & Model successfully added!', 'new_data': new_added_data}), 200
    else:
        brand = Brand.query.get(id)
        models = new_data['name'].split(', ')
        added_model_data = []
        for model in models:
            existing_data = Make.query.filter_by(name=brand.name + " " + model.lower(), brand_id=id).first()
            if existing_data:
                pass
            else:
                model_data = Make(name=brand.name + " " + model, brand_id=id, created_by=g.current_user['email'])
                db.session.add(model_data)
                db.session.commit()
                added_model_data.append(make_schema.dump(model_data))

        return jsonify({'message': 'Make & Model successfully added!', 'new_data': added_model_data}), 200


# Make & Model Update
@views.route('/admin/make-and-model-update/<int:id>', methods=['PUT'])
@jwt_required()
@current_user_required
def make_and_model_update(id):
    new_data = request.get_json()
    data = Make.query.get(id)
    if data:
        data.name = new_data['name']
        data.updated_by = g.current_user['email']
        data.updated_date = datetime.now()
        db.session.commit()
    else:
        return jsonify({'message': 'Make & Model not found!'}), 400

    updated_data = make_schema.dump(data)
    return jsonify({'message': 'Make & Model updated successfully!', 'updated_data': updated_data}), 200


# Make & Model Delete
@views.route('/admin/make-and-model-delete/<int:id>', methods=['DELETE'])
@jwt_required()
@current_user_required
def make_and_model_delete(id):
    data = Make.query.get(id)
    if data is None:
        return jsonify({'message': 'Make & Model not found.'}), 400

    db.session.delete(data)
    db.session.commit()
    return 'Success!', 200


# Trim View
@views.route('/admin/trim-view/<int:id>', methods=['GET'])
@jwt_required()
@current_user_required
def trim_view(id):
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    search = request.args.get('search', '', type=str)

    data = Trim.query.filter_by(make_id=id)

    if search:
        search_words = search.split(',')

        def search_filter(word):
            word = word.strip()
            return or_(
                Trim.name.ilike(f"%{word}%"),
            )

        filter_conditions = [search_filter(word) for word in search_words]
        data = data.filter(*filter_conditions)

    data = data.order_by(Trim.id.desc())

    data_paginated = data.limit(page_size).offset((page - 1) * page_size).all()

    result = trims_schema.dump(data_paginated)

    return jsonify({
        "data": result,
        "total": data.count()
    }), 200


# Trim Create
@views.route('/admin/trim-create/<int:id>', methods=['POST'])
@jwt_required()
@current_user_required
def trim_create(id):
    new_data = request.get_json()
    if new_data['checkbox'] == 0:
        existing_data = Trim.query.filter_by(name=new_data['name'].lower(), make_id=id).first()

        if existing_data is not None:
            return jsonify({'message': 'Trim Already Exists!'}), 400

        new_data2 = Trim(
            name=new_data['name'],
            make_id=id,
            created_by=g.current_user['email']
        )

        db.session.add(new_data2)
        db.session.commit()

        new_added_data = trim_schema.dump(new_data2)
        return jsonify({'message': 'Trim successfully added!', 'new_data': new_added_data}), 200
    else:
        trims = new_data['name'].split(', ')
        added_trim_data = []
        for trim in trims:
            existing_data = Trim.query.filter_by(name=trim.lower(), make_id=id).first()
            if existing_data:
                pass
            else:
                trim_data = Trim(name=trim, make_id=id, created_by=g.current_user['email'])
                db.session.add(trim_data)
                db.session.commit()
                added_trim_data.append(trim_schema.dump(trim_data))

        return jsonify({'message': 'Trims successfully added!', 'new_data': added_trim_data}), 200


# Trim Update
@views.route('/admin/trim-update/<int:id>', methods=['PUT'])
@jwt_required()
@current_user_required
def trim_update(id):
    new_data = request.get_json()
    data = Trim.query.get(id)
    if data:
        data.name = new_data['name']
        data.updated_by = g.current_user['email']
        data.updated_date = datetime.now()
        db.session.commit()
    else:
        return jsonify({'message': 'Trim not found!'}), 400

    updated_data = trim_schema.dump(data)
    return jsonify({'message': 'Trim updated successfully!', 'updated_data': updated_data}), 200


# Trim Delete
@views.route('/admin/trim-delete/<int:id>', methods=['DELETE'])
@jwt_required()
@current_user_required
def trim_delete(id):
    data = Trim.query.get(id)
    if data is None:
        return jsonify({'message': 'Trim not found.'}), 400

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


# Community Delete
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

    status = request.args.get('status', '', type=str)
    if status == "ALL":
        data = Listings.query.filter_by(vehicle_type='car')
    elif status == "IN REVIEW":
        data = Listings.query.filter_by(vehicle_type='car', publish_status=0)
    elif status == "NOT PUBLISHED":
        data = Listings.query.filter_by(vehicle_type='car', publish_status=2)
    elif status == "PUBLISHED":
        data = Listings.query.filter_by(vehicle_type='car', publish_status=1)

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


# UPDATE LISTING PUBLISH STATUS
@views.route('/admin/update/listing-status/<int:id>', methods=['PUT'])
@jwt_required()
@current_user_required
def listing_update_publish_status(id):
    new_data = request.get_json()

    data = Listings.query.get(id)

    data.publish_status = new_data['publish_status']
    data.updated_by = g.current_user['email']
    data.updated_date = datetime.now()

    db.session.commit()

    updated_data = listing_schema.dump(data)
    return jsonify({'message': f'Listing Publish Status updated successfully!', 'updated_data': updated_data}), 200


# Motorcycle LISTING INFORMATION
@views.route('/admin/motorcycle-listing-view', methods=['GET'])
@jwt_required()
@current_user_required
def motorcycle_listing_view():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    search = request.args.get('search', '', type=str)

    status = request.args.get('status', '', type=str)
    if status == "ALL":
        data = Listings.query.filter_by(vehicle_type='motorcycle')
    elif status == "IN REVIEW":
        data = Listings.query.filter_by(vehicle_type='motorcycle', publish_status=0)
    elif status == "NOT PUBLISHED":
        data = Listings.query.filter_by(vehicle_type='motorcycle', publish_status=2)
    elif status == "PUBLISHED":
        data = Listings.query.filter_by(vehicle_type='motorcycle', publish_status=1)

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
    status = request.args.get('status', '', type=str)

    search = request.args.get('search', '', type=str)

    if status == "ALL":
        data = Listings.query.filter_by(vehicle_type='boat')
    elif status == "IN REVIEW":
        data = Listings.query.filter_by(vehicle_type='boat', publish_status=0)
    elif status == "NOT PUBLISHED":
        data = Listings.query.filter_by(vehicle_type='boat', publish_status=2)
    elif status == "PUBLISHED":
        data = Listings.query.filter_by(vehicle_type='boat', publish_status=1)

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

    status = request.args.get('status', '', type=str)
    if status == "ALL":
        data = Listings.query.filter_by(vehicle_type='heavy vehicle')
    elif status == "IN REVIEW":
        data = Listings.query.filter_by(vehicle_type='heavy vehicle', publish_status=0)
    elif status == "NOT PUBLISHED":
        data = Listings.query.filter_by(vehicle_type='heavy vehicle', publish_status=2)
    elif status == "PUBLISHED":
        data = Listings.query.filter_by(vehicle_type='heavy vehicle', publish_status=1)

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


# Delete Listing
@views.route('/admin/delete-listing/<int:id>', methods=['DELETE'])
@jwt_required()
@current_user_required
def admin_delete_listing(id):
    admin = Admin.query.get(g.current_user['id'])
    if admin:
        listing_data = Listings.query.filter_by(id=id).first()
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

    data = Listings.query.filter_by(publish_status=1)

    if search:
        filter_conditions = []

        if search:
            search_conditions = or_(
                Listings.title.ilike(f"%{search}%"),
                Listings.brand.has(Brand.name.ilike(f"%{search}%"))
            )
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

#################### FAVORITES FUNCTION ENDPOINT ###############################
@views.route('/client/add-favorite/<int:id>', methods=['POST'])
@jwt_required()
@current_user_required
def add_favorite(id):
    faved = Favorites.query.filter_by(user_id=g.current_user['id'], listing_id=id).first()
    if faved is None:
        if g.current_user['id']:
            data = Favorites(user_id=g.current_user['id'], listing_id=id)
            db.session.add(data)
            db.session.commit()
        else:
            return jsonify({'message': 'Please log in to add favorite'}), 400
        return jsonify({'message': 'Listing added to favorites successfully'}), 200
    else:
        return jsonify({'message': 'Already added to favorites'}), 400


@views.route('/client/remove-favorite/<int:id>', methods=['DELETE'])
@jwt_required()
@current_user_required
def remove_favorite(id):
    if g.current_user['id']:
        favorite = Favorites.query.filter_by(user_id=g.current_user['id'], listing_id=id).first()
        if favorite:
            db.session.delete(favorite)
            db.session.commit()
            return jsonify({'message': 'Listing removed from favorites successfully'}), 200
        else:
            return jsonify({'message': 'Listing not found in favorites'}), 404
    else:
        return jsonify({'message': 'Please log in to add favorite'}), 400


@views.route('/client/favorite-listings/<int:id>', methods=['GET'])
@jwt_required()
@current_user_required
def get_favorite_listings(id):
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    data = Favorites.query.filter_by(user_id=id)

    data_paginated = data.limit(page_size).offset((page - 1) * page_size).all()

    result = favorites_schema.dump(data_paginated)
    return jsonify({
        "data": result,
        "total": data.count()
    }), 200


@views.route('/client/check-favorite/<int:id>', methods=['GET'])
@jwt_required()
@current_user_required
def check_favorite(id):
    if g.current_user['id']:
        favorite = Favorites.query.filter_by(user_id=g.current_user['id'], listing_id=id).first()
        if favorite:
            is_favorite = 1
        else:
            is_favorite = 0
    else:
        return jsonify({'message': 'Please log in to add favorite'}), 400
    return jsonify({'isFavorite': is_favorite})


##################### FAVORITES FUNCTION ENDPOINT #################

############ VIEW ALL IMAGES IN A LISTING ############
@views.route('/client/single-listing-view/additional-images-view/<int:id>', methods=['GET'])
@jwt_required()
@current_user_required
def additiona_images(id):
    data = ListingImage.query.filter_by(listing_id=id)

    result = listing_images_schema.dump(data)
    return jsonify({"data": result})


##################END########################

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

    data = Listings.query.filter_by(vehicle_type='car', publish_status=1)

    if search or brand or (startPrice and endPrice) or (startMileage and endMileage) or (
            startModelYear and endModelYear):
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


# AUTH All Car View
@views.route('/client/auth-all-car-view', methods=['GET'])
@jwt_required()
@current_user_required
def auth_all_car_view():
    user_id = g.current_user['id']
    user_favorite_ids = [fav.listing_id for fav in Favorites.query.filter_by(user_id=user_id).all()]

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

    data = Listings.query.filter_by(vehicle_type='car', publish_status=1)

    if search or brand or (startPrice and endPrice) or (startMileage and endMileage) or (
            startModelYear and endModelYear):
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

    result = []
    for listing in data_paginated:
        listing_dict = listing_schema.dump(listing)
        listing_dict['is_favorite'] = int(listing.id in user_favorite_ids)
        result.append(listing_dict)

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
    user = User.query.get(g.current_user['id'])
    featured_as = new_data.get('featured_as', '').lower()
    if featured_as == 'standard':
        if user.count_standard_listings >= user.standard_listing:
            return jsonify({'message': f'Limit Standard Listing is {user.standard_listing}'}), 400
    elif featured_as == 'featured':
        if user.count_featured_listings >= user.featured_listing:
            return jsonify({'message': f'Limit Featured Listing is {user.featured_listing}'}), 400
    elif featured_as == 'premium':
        if user.count_premium_listings >= user.premium_listing:
            return jsonify({'message': f'Limit Premium Listing is {user.premium_listing}'}), 400
    else:
        return jsonify({'message': f'No Featured As'}), 400

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
        g_map_location=new_data['g_map_location'],
        vehicle_type='car',
        featured_as=new_data['featured_as'],
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
            listing_data.g_map_location = new_data['g_map_location']
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

    data = Listings.query.filter_by(vehicle_type='motorcycle', publish_status=1)

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


# AUTH All Motor View
@views.route('/client/auth-all-motorcylce-view', methods=['GET'])
@jwt_required()
@current_user_required
def auth_all_motorcycle_view():
    user_id = g.current_user['id']
    user_favorite_ids = [fav.listing_id for fav in Favorites.query.filter_by(user_id=user_id).all()]

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

    data = Listings.query.filter_by(vehicle_type='motorcycle', publish_status=1)

    if search or brand or (startPrice and endPrice) or (startMileage and endMileage) or (
            startModelYear and endModelYear):
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

    result = []
    for listing in data_paginated:
        listing_dict = listing_schema.dump(listing)
        listing_dict['is_favorite'] = int(listing.id in user_favorite_ids)
        result.append(listing_dict)

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
    user = User.query.get(g.current_user['id'])
    featured_as = new_data.get('featured_as', '').lower()
    if featured_as == 'standard':
        if user.count_standard_listings >= user.standard_listing:
            return jsonify({'message': f'Limit Standard Listing is {user.standard_listing}'}), 400
    elif featured_as == 'featured':
        if user.count_featured_listings >= user.featured_listing:
            return jsonify({'message': f'Limit Featured Listing is {user.featured_listing}'}), 400
    elif featured_as == 'premium':
        if user.count_premium_listings >= user.premium_listing:
            return jsonify({'message': f'Limit Premium Listing is {user.premium_listing}'}), 400
    else:
        return jsonify({'message': f'No Featured As'}), 400

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
        g_map_location=new_data['g_map_location'],
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
            listing_data.g_map_location = new_data['g_map_location']
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

    data = Listings.query.filter_by(vehicle_type='boat', publish_status=1)

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


# AUTH All Boat View
@views.route('/client/auth-all-boat-view', methods=['GET'])
@jwt_required()
@current_user_required
def auth_all_boat_view():
    user_id = g.current_user['id']
    user_favorite_ids = [fav.listing_id for fav in Favorites.query.filter_by(user_id=user_id).all()]

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

    data = Listings.query.filter_by(vehicle_type='boat', publish_status=1)

    if search or brand or (startPrice and endPrice) or (startMileage and endMileage) or (
            startModelYear and endModelYear):
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

    result = []
    for listing in data_paginated:
        listing_dict = listing_schema.dump(listing)
        listing_dict['is_favorite'] = int(listing.id in user_favorite_ids)
        result.append(listing_dict)

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
    user = User.query.get(g.current_user['id'])
    featured_as = new_data.get('featured_as', '').lower()
    if featured_as == 'standard':
        if user.count_standard_listings >= user.standard_listing:
            return jsonify({'message': f'Limit Standard Listing is {user.standard_listing}'}), 400
    elif featured_as == 'featured':
        if user.count_featured_listings >= user.featured_listing:
            return jsonify({'message': f'Limit Featured Listing is {user.featured_listing}'}), 400
    elif featured_as == 'premium':
        if user.count_premium_listings >= user.premium_listing:
            return jsonify({'message': f'Limit Premium Listing is {user.premium_listing}'}), 400
    else:
        return jsonify({'message': f'No Featured As'}), 400

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
        g_map_location=new_data['g_map_location'],
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
            listing_data.g_map_location = new_data['g_map_location']
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

    data = Listings.query.filter_by(vehicle_type='heavy vehicle', publish_status=1)

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


# AUTH All HV View
@views.route('/client/auth-all-heavy-vehicle-view', methods=['GET'])
@jwt_required()
@current_user_required
def auth_all_heavy_view():
    user_id = g.current_user['id']
    user_favorite_ids = [fav.listing_id for fav in Favorites.query.filter_by(user_id=user_id).all()]

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

    data = Listings.query.filter_by(vehicle_type='heavy vehicle', publish_status=1)

    if search or brand or (startPrice and endPrice) or (startMileage and endMileage) or (
            startModelYear and endModelYear):
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

    result = []
    for listing in data_paginated:
        listing_dict = listing_schema.dump(listing)
        listing_dict['is_favorite'] = int(listing.id in user_favorite_ids)
        result.append(listing_dict)

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
    user = User.query.get(g.current_user['id'])
    featured_as = new_data.get('featured_as', '').lower()
    if featured_as == 'standard':
        if user.count_standard_listings >= user.standard_listing:
            return jsonify({'message': f'Limit Standard Listing is {user.standard_listing}'}), 400
    elif featured_as == 'featured':
        if user.count_featured_listings >= user.featured_listing:
            return jsonify({'message': f'Limit Featured Listing is {user.featured_listing}'}), 400
    elif featured_as == 'premium':
        if user.count_premium_listings >= user.premium_listing:
            return jsonify({'message': f'Limit Premium Listing is {user.premium_listing}'}), 400
    else:
        return jsonify({'message': f'No Featured As'}), 400

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
        g_map_location=new_data['g_map_location'],
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
            listing_data.g_map_location = new_data['g_map_location']
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


# Get Make Based on Brand
@views.route('/client/make-view', methods=['GET'])
def client_make_view():
    brand_id = request.args.get('brand_id', type=int)
    data = Make.query.filter_by(brand_id=brand_id)

    result = makes_schema.dump(data)

    return jsonify({
        "data": result,
        "total": data.count()
    }), 200


# Get Trim Based on Make
@views.route('/client/trim-view', methods=['GET'])
def client_trim_view():
    make_id = request.args.get('make_id', type=int)
    data = Trim.query.filter_by(make_id=make_id)

    result = trims_schema.dump(data)

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


############## ALL BRANDS ENDPOINT ################################
# Brands View
@views.route('/client/all-brand-view', methods=['GET'])
def client_brands_view():
    data = Brand.query

    result = brands_schema.dump(data)

    return jsonify({
        "data": result,
        "total": data.count()
    }), 200


############################# STRIPE INTEGERATION EMBEDED ######################
@views.route('/create-checkout-session', methods=['POST'])
@jwt_required()
@current_user_required
def create_checkout_session():
    new_data = request.get_json()
    try:
        stripe_customer_id = f'imotorV2_{g.current_user["id"]}'
        session = stripe.checkout.Session.create(
            ui_mode='embedded',
            line_items=[
                {
                    'price': new_data['price'],
                    'quantity': new_data['quantity'],
                },
            ],
            mode='subscription',
            customer=stripe_customer_id,
            metadata={
                'user_id': g.current_user['id'],
                'user_email': g.current_user['email']
            },
            return_url='https://imotor.app/return?session_id={CHECKOUT_SESSION_ID}',
        )
    except Exception as e:
        return str(e)

    return jsonify(clientSecret=session.client_secret)


@views.route('/create-checkout-session-native', methods=['POST'])
def create_checkout_session_native():
    new_data = request.get_json()
    try:
        stripe_customer_id = f'imotorV2_{new_data["user_id"]}'
        user_data = User.query.get(new_data["user_id"])
        session = stripe.checkout.Session.create(
            ui_mode='embedded',
            line_items=[
                {
                    'price': new_data['price'],
                    'quantity': new_data['quantity'],
                },
            ],
            mode='subscription',
            customer=stripe_customer_id,
            metadata={
                'user_id': user_data.id,
                'user_email': user_data.email
            },
            return_url='https://imotor.app/return-native?session_id={CHECKOUT_SESSION_ID}',
        )
    except Exception as e:
        return str(e)

    return jsonify(clientSecret=session.client_secret)

@views.route('/session-status-native', methods=['GET'])
def session_status_native():
    session = stripe.checkout.Session.retrieve(request.args.get('session_id'))
    return jsonify(status=session.status, billing_email=session.customer_details.email)

@views.route('/session-status', methods=['GET'])
@jwt_required()
@current_user_required
def session_status():
    session = stripe.checkout.Session.retrieve(request.args.get('session_id'))
    fullname = f"{g.current_user['first_name']} {g.current_user['last_name']}"

    return jsonify(status=session.status, customer_fullname=fullname, billing_email=session.customer_details.email)


@views.route('/webhook', methods=['POST'])
def stripe_webhook():
    global plan_id, quantity
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    # whsec_oqxVEZ8EYHv6QGk5dkBkn1h6UK2tXZUv for deployment
    #whsec_ae47c490c311e3e7eda01bf4ca663cce37e42577fc004f4915c828229bad849f
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, 'whsec_oqxVEZ8EYHv6QGk5dkBkn1h6UK2tXZUv'
        )
    except ValueError as e:
        # Invalid payload
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return 'Invalid signature', 400

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_id = session['customer']
        customer_details = session['customer_details']
        customer_email = customer_details['email']
        subscription_id = session.get('subscription')
        if subscription_id:
            subscription = stripe.Subscription.retrieve(subscription_id)
            plan_id = subscription.plan.id
            quantity = subscription.quantity
        parts = customer_id.split("_")
        if len(parts) == 2 and parts[0] == "imotorV2":
            user_id = parts[1]
            user_data = User.query.get(user_id)
            if user_data:
                if plan_id == 'price_1OmCRADvpPWaX3mF1CHQIjph':
                    # price_1OrYWIDvpPWaX3mFsWNweyeK
                    plan_name = 'PREMIUM PACKAGE'
                    quantity = 1
                    user_data.standard_listing = user_data.standard_listing + 13
                    user_data.featured_listing = user_data.featured_listing + 5
                    user_data.premium_listing = user_data.premium_listing + 2
                    user_data.is_subscribe_to_package = 1
                    db.session.commit()

                    invoice = stripe.Invoice.list(customer=f'{customer_id}', limit=1)['data'][0]
                    invoice_url = invoice.hosted_invoice_url

                    thread = threading.Thread(target=send_confirmation_email,
                                              args=(customer_email, plan_name, quantity, invoice_url,
                                                    current_app._get_current_object()))
                    thread.start()
                elif plan_id == 'price_1OmCRvDvpPWaX3mFKHD2Ugel':
                    # price_1OrYWFDvpPWaX3mFQKEQ2HGD
                    plan_name = 'ADDITIONAL STANDARD LISTING'
                    user_data.standard_listing = user_data.standard_listing + int(quantity)
                    db.session.commit()

                    invoice = stripe.Invoice.list(customer=f'{customer_id}', limit=1)['data'][0]
                    invoice_url = invoice.hosted_invoice_url

                    thread = threading.Thread(target=send_confirmation_email,
                                              args=(customer_email, plan_name, quantity, invoice_url,
                                                    current_app._get_current_object()))
                    thread.start()
                elif plan_id == 'price_1OmCPfDvpPWaX3mFCTdaJdr0':
                    # price_1OrYWKDvpPWaX3mFEXsKyKkv
                    plan_name = 'ADDITIONAL FEATURED LISTING'
                    user_data.featured_listing = user_data.featured_listing + int(quantity)
                    db.session.commit()

                    invoice = stripe.Invoice.list(customer=f'{customer_id}', limit=1)['data'][0]
                    invoice_url = invoice.hosted_invoice_url

                    thread = threading.Thread(target=send_confirmation_email,
                                              args=(customer_email, plan_name, quantity, invoice_url,
                                                    current_app._get_current_object()))
                    thread.start()
                elif plan_id == 'price_1OmCTUDvpPWaX3mFB6skAGpQ':
                    # price_1OrYVtDvpPWaX3mFm5djUTrr
                    plan_name = 'ADDITIONAL PREMIUM LISTING'
                    user_data.premium_listing = user_data.premium_listing + int(quantity)
                    db.session.commit()

                    invoice = stripe.Invoice.list(customer=f'{customer_id}', limit=1)['data'][0]
                    invoice_url = invoice.hosted_invoice_url

                    thread = threading.Thread(target=send_confirmation_email,
                                              args=(customer_email, plan_name, quantity, invoice_url,
                                                    current_app._get_current_object()))
                    thread.start()

        else:
            print('NO USER DATA: checkout.session.completed')

    # Handle the event
    if event['type'] == 'customer.subscription.deleted':
        print('Delete Subscription')
        subscription = event['data']['object']
        subscription_id = subscription['id']
        customer_id = subscription['customer']
        product_id = subscription['plan']['product']
        print(customer_id)

        parts = customer_id.split("_")
        if len(parts) == 2 and parts[0] == "imotorV2":
            user_id = parts[1]
            user_data = User.query.get(user_id)
            if product_id == 'prod_PbPGcIZ8mGDgKt':
                # prod_PgwPGPw7ro44tD
                if user_data.is_subscribe_to_package == 1:
                    old_user_data = user_data.standard_listing
                    limitation = abs(16 - old_user_data)
                    user_data.standard_listing = 16
                    listings = Listings.query.filter_by(user_id=user_data.id, featured_as='standard').order_by(
                        Listings.created_date.asc()).limit(limitation).all()
                    for listing in listings:
                        listing.publish_status = 2
                        db.session.commit()
                else:
                    old_user_data = user_data.standard_listing
                    limitation = abs(3 - old_user_data)
                    user_data.standard_listing = 3
                    listings = Listings.query.filter_by(user_id=user_data.id, featured_as='standard').order_by(
                        Listings.created_date.asc()).limit(limitation).all()
                    for listing in listings:
                        listing.publish_status = 2
                        db.session.commit()
            elif product_id == 'prod_PbPEwLQCcVKadd':
                # prod_PgwPWCQ4vqJCLI
                if user_data.is_subscribe_to_package == 1:
                    old_user_data = user_data.featured_listing
                    limitation = abs(5 - old_user_data)
                    user_data.featured_listing = 5
                    listings = Listings.query.filter_by(user_id=user_data.id, featured_as='featured').order_by(
                        Listings.created_date.asc()).limit(limitation).all()
                    for listing in listings:
                        listing.publish_status = 2
                        db.session.commit()
                else:
                    old_user_data = user_data.featured_listing
                    limitation = abs(0 - old_user_data)
                    user_data.featured_listing = 0
                    listings = Listings.query.filter_by(user_id=user_data.id, featured_as='featured').order_by(
                        Listings.created_date.asc()).limit(limitation).all()
                    for listing in listings:
                        listing.publish_status = 2
                        db.session.commit()
            elif product_id == 'prod_PbPInhDd5zE2d5':
                # prod_PgwOWe6kwz1agd
                if user_data.is_subscribe_to_package == 1:
                    old_user_data = user_data.premium_listing
                    limitation = abs(2 - old_user_data)
                    user_data.premium_listing = 2
                    listings = Listings.query.filter_by(user_id=user_data.id, featured_as='premium').order_by(
                        Listings.created_date.asc()).limit(limitation).all()
                    for listing in listings:
                        listing.publish_status = 2
                        db.session.commit()
                else:
                    old_user_data = user_data.premium_listing
                    limitation = abs(0 - old_user_data)
                    user_data.premium_listing = 0
                    listings = Listings.query.filter_by(user_id=user_data.id, featured_as='premium').order_by(
                        Listings.created_date.asc()).limit(limitation).all()
                    for listing in listings:
                        listing.publish_status = 2
                        db.session.commit()
            elif product_id == 'prod_PbPFZ2qSaqQFS5':
                print('Delete Subscription: Premium Package')
                # prod_PgwPz8DTwFRMOp
                if user_data.standard_listing == 16:
                    old_user_data = user_data.standard_listing
                    limitation = abs(3 - old_user_data)
                    user_data.standard_listing = 3
                    listings = Listings.query.filter_by(user_id=user_data.id, featured_as='standard').order_by(
                        Listings.created_date.asc()).limit(limitation).all()
                    for listing in listings:
                        listing.publish_status = 2
                        db.session.commit()
                else:
                    limitation = abs(13)
                    user_data.standard_listing = abs(user_data.standard_listing - 16 + 3)
                    listings = Listings.query.filter_by(user_id=user_data.id, featured_as='standard').order_by(
                        Listings.created_date.asc()).limit(limitation).all()
                    for listing in listings:
                        listing.publish_status = 2
                        db.session.commit()

                if user_data.featured_listing == 5:
                    old_user_data = user_data.featured_listing
                    limitation = abs(0 - old_user_data)
                    user_data.featured_listing = 0
                    listings = Listings.query.filter_by(user_id=user_data.id, featured_as='featured').order_by(
                        Listings.created_date.asc()).limit(limitation).all()
                    for listing in listings:
                        listing.publish_status = 2
                        db.session.commit()
                else:
                    limitation = abs(5)
                    user_data.featured_listing = abs(user_data.featured_listing - 5)
                    listings = Listings.query.filter_by(user_id=user_data.id, featured_as='featured').order_by(
                        Listings.created_date.asc()).limit(limitation).all()
                    for listing in listings:
                        listing.publish_status = 2
                        db.session.commit()

                if user_data.premium_listing == 2:
                    old_user_data = user_data.premium_listing
                    limitation = abs(0 - old_user_data)
                    user_data.premium_listing = 0
                    listings = Listings.query.filter_by(user_id=user_data.id, featured_as='premium').order_by(
                        Listings.created_date.asc()).limit(limitation).all()
                    for listing in listings:
                        listing.publish_status = 2
                        db.session.commit()
                else:
                    limitation = abs(2)
                    user_data.premium_listing = abs(user_data.premium_listing - 2)
                    listings = Listings.query.filter_by(user_id=user_data.id, featured_as='premium').order_by(
                        Listings.created_date.asc()).limit(limitation).all()
                    for listing in listings:
                        listing.publish_status = 2
                        db.session.commit()

                user_data.is_subscribe_to_package = 0
            db.session.commit()
        return '', 200

    if event['type'] == 'invoice.payment_failed':
        invoice_data = event['data']['object']

        # Extracting information
        invoice_id = invoice_data['id']
        customer_id = invoice_data['customer']
        hosted_invoice_url = invoice_data['hosted_invoice_url']
        customer_email = invoice_data['customer_email']
        subscription_id = invoice_data['subscription']

        product_id = None
        plan_name = None
        lines = invoice_data.get('lines', {}).get('data', [])
        if lines:
            product_id = lines[0].get('price', {}).get('product')

        parts = customer_id.split("_")
        if len(parts) == 2 and parts[0] == "imotorV2":
            user_id = parts[1]
            user_data = User.query.get(user_id)
            if user_data:
                if product_id == 'prod_PbPGcIZ8mGDgKt':
                    # prod_PgwPGPw7ro44tD
                    plan_name = 'Additional Standard Listing'
                    if user_data.standard_listing_desc:
                        pass
                    else:
                        # Current date and time
                        dateNow = datetime.now()

                        # Date and time seven days from now
                        dateInSevenDays = dateNow + timedelta(days=7)

                        # Format the dates as strings
                        dateNowFormatted = dateNow.strftime("%Y-%m-%d %H:%M:%S")
                        dateInSevenDaysFormatted = dateInSevenDays.strftime("%Y-%m-%d %H:%M:%S")

                        user_data.standard_listing_desc = f'Sent First Email on Payment Failed in {dateNowFormatted}, Manual Cancellation will be on {dateInSevenDaysFormatted}'
                        db.session.commit()
                elif product_id == 'prod_PbPEwLQCcVKadd':
                    # prod_PgwPWCQ4vqJCLI
                    plan_name = 'Additional Featured Listing'
                    if user_data.featured_listing_desc:
                        pass
                    else:
                        # Current date and time
                        dateNow = datetime.now()

                        # Date and time seven days from now
                        dateInSevenDays = dateNow + timedelta(days=7)

                        # Format the dates as strings
                        dateNowFormatted = dateNow.strftime("%Y-%m-%d %H:%M:%S")
                        dateInSevenDaysFormatted = dateInSevenDays.strftime("%Y-%m-%d %H:%M:%S")

                        user_data.featured_listing_desc = f'Sent First Email on Payment Failed in {dateNowFormatted}, Manual Cancellation will be on {dateInSevenDaysFormatted}'
                        db.session.commit()
                elif product_id == 'prod_PbPInhDd5zE2d5':
                    # prod_PgwOWe6kwz1agd
                    plan_name = 'Additional Premium Listing'
                    if user_data.premium_listing_desc:
                        pass
                    else:
                        # Current date and time
                        dateNow = datetime.now()

                        # Date and time seven days from now
                        dateInSevenDays = dateNow + timedelta(days=7)

                        # Format the dates as strings
                        dateNowFormatted = dateNow.strftime("%Y-%m-%d %H:%M:%S")
                        dateInSevenDaysFormatted = dateInSevenDays.strftime("%Y-%m-%d %H:%M:%S")

                        user_data.premium_listing_desc = f'Sent First Email on Payment Failed in {dateNowFormatted}, Manual Cancellation will be on {dateInSevenDaysFormatted}'
                        db.session.commit()
                elif product_id == 'prod_PbPFZ2qSaqQFS5':
                    # prod_PgwPz8DTwFRMOp
                    plan_name = 'Premium Package'
                    if user_data.premium_package_desc:
                        pass
                    else:
                        # Current date and time
                        dateNow = datetime.now()

                        # Date and time seven days from now
                        dateInSevenDays = dateNow + timedelta(days=7)

                        # Format the dates as strings
                        dateNowFormatted = dateNow.strftime("%Y-%m-%d %H:%M:%S")
                        dateInSevenDaysFormatted = dateInSevenDays.strftime("%Y-%m-%d %H:%M:%S")

                        user_data.premium_package_desc = f'Sent First Email on Payment Failed in {dateNowFormatted}, Manual Cancellation will be on {dateInSevenDaysFormatted}'
                        db.session.commit()
                fullname = f'{user_data.first_name} {user_data.last_name}'
                thread = threading.Thread(target=send_payment_failed,
                                          args=(customer_email, fullname, plan_name, hosted_invoice_url,
                                                current_app._get_current_object()))
                thread.start()

    if event['type'] == 'invoice.payment_succeeded':
        invoice_data = event['data']['object']

        # Extracting information
        invoice_id = invoice_data['id']
        customer_id = invoice_data['customer']
        hosted_invoice_url = invoice_data['hosted_invoice_url']
        customer_email = invoice_data['customer_email']
        subscription_id = invoice_data['subscription']

        product_id = None
        plan_name = None
        lines = invoice_data.get('lines', {}).get('data', [])
        if lines:
            product_id = lines[0].get('price', {}).get('product')

        parts = customer_id.split("_")
        if len(parts) == 2 and parts[0] == "imotorV2":
            user_id = parts[1]
            user_data = User.query.get(user_id)
            if user_data:
                if product_id == 'prod_PbPGcIZ8mGDgKt':
                    # prod_PgwPGPw7ro44tD
                    plan_name = 'Additional Standard Listing'
                elif product_id == 'prod_PbPEwLQCcVKadd':
                    # prod_PgwPWCQ4vqJCLI
                    plan_name = 'Additional Featured Listing'
                elif product_id == 'prod_PbPInhDd5zE2d5':
                    # prod_PgwOWe6kwz1agd
                    plan_name = 'Additional Premium Listing'
                elif product_id == 'prod_PbPFZ2qSaqQFS5':
                    # prod_PgwPz8DTwFRMOp
                    plan_name = 'Premium Package'
                fullname = f'{user_data.first_name} {user_data.last_name}'
                thread = threading.Thread(target=send_payment_success,
                                          args=(customer_email, fullname, plan_name, hosted_invoice_url,
                                                current_app._get_current_object()))
                thread.start()

    return '', 200


def send_payment_success(user_mail, user_fullname, plan_name, invoice_url, app):
    with app.app_context():
        msg = Message(f'Subscription Payment Successful', recipients=[f'{user_mail}'])
        msg.html = f"""
                <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                    </head>
                    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px;">
                        <div style="max-width: 600px; margin: 0 auto; background-color: #fff; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <div style="text-align: center; margin-bottom: 20px;">
                                <h2>Subscription Payment Successful</h2>
                            </div>
                            <div style="text-align: left; margin-top: 10px;">
                                Dear {user_fullname},
                            </div>
                            <br/>
                            <div style="text-align: left">
                                We are pleased to inform you that your payment for the {plan_name} plan subscription has been successfully processed.
                            </div>
                            <br/>
                            <div style="text-align: left">
                                You can view your invoice details at the following link: <a href="{invoice_url}">{invoice_url}</a>
                            </div>
                            <br/>
                            <div style="text-align: left">
                                Thank you for your continued support.
                            </div>
                            <br/>
                            <div style="text-align: left">
                                Best regards,
                            </div>
                            <div style="text-align: left">
                                Imotor Team
                            </div>
                        </div>
                    </body>
                </html>
        """
        msg.mimetype = 'text/html'
        mail.send(msg)


def send_payment_failed(user_mail, user_fullname, plan_name, invoice_url, app):
    with app.app_context():
        msg = Message(f'Subscription Payment Failed', recipients=[f'{user_mail}'])
        msg.html = f"""
                <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                    </head>
                    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px;">
                        <div style="max-width: 600px; margin: 0 auto; background-color: #fff; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <div style="text-align: center; margin-bottom: 20px;">
                                <h2>Subscription Payment Failed</h2>
                            </div>
                            <div style="text-align: left; margin-top: 10px;">
                                Dear {user_fullname},
                            </div>
                            <br/>
                            <div style="text-align: left">
                                We noticed that there was an issue processing your payment for the {plan_name} plan subscription.
                                To avoid interruption of your service, please update your payment information within the next 7 days.
                            </div>
                            <br/>
                            <div style="text-align: left">
                                Please find your invoice details at the following link: <a href="{invoice_url}">{invoice_url}</a>
                            </div>
                            <br/>
                            <div style="text-align: left">
                                Best regards,
                            </div>
                            <div style="text-align: left">
                                Imotor Team
                            </div>
                        </div>
                    </body>
                </html>
        """
        msg.mimetype = 'text/html'
        mail.send(msg)


def send_confirmation_email(user_email, plan_name, quantity, invoice_url, app):
    with app.app_context():
        msg = Message(f'Subscription Confirmation', recipients=[f'{user_email}'])
        if plan_name == 'PREMIUM PACKAGE':
            msg.html = f"""
                    <html lang="en">
                        <head>
                            <meta charset="UTF-8">
                        </head>
                        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px;">
                            <div style="max-width: 600px; margin: 0 auto; background-color: #fff; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                <div style="text-align: center; margin-bottom: 20px;">
                                    <h2>Subscription Confirmation</h2>
                                </div>
                                <div style="text-align: left; margin-top: 10px;">
                                    Dear User,
                                </div>
                                <br/>
                                <div style="text-align: left">
                                    Thank you for your subscription to our service. You have successfully subscribed to the {plan_name} plan.
                                </div>
                                <br/>
                                <div style="text-align: left">
                                    Please find your invoice details at the following link: <a href="{invoice_url}">{invoice_url}</a>
                                </div>
                                <br/>
                                <div style="text-align: left">
                                    Best regards,
                                </div>
                                <div style="text-align: left">
                                    Imotor Team
                                </div>
                            </div>
                        </body>
                    </html>
            """
        else:
            msg.html = f"""
                               <html lang="en">
                                   <head>
                                       <meta charset="UTF-8">
                                   </head>
                                   <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px;">
                                       <div style="max-width: 600px; margin: 0 auto; background-color: #fff; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                           <div style="text-align: center; margin-bottom: 20px;">
                                               <h2>Subscription Confirmation</h2>
                                           </div>
                                           <div style="text-align: left; margin-top: 10px;">
                                               Dear User,
                                           </div>
                                                 <br/>
                                           <div style="text-align: left">
                                               Thank you for your subscription to our service. You have successfully subscribed to the {plan_name} plan with a quantity of {quantity}.
                                           </div>
                                           <br/>
                                            <div style="text-align: left">
                                                Please find your invoice details at the following link: <a href="{invoice_url}">{invoice_url}</a>
                                            </div>
                                           <br/>
                                           <div style="text-align: left">
                                               Best regards,
                                           </div>
                                           <div style="text-align: left">
                                               Imotor Team
                                           </div>
                                       </div>
                                   </body>
                               </html>
                       """
        msg.mimetype = 'text/html'
        mail.send(msg)


@views.route('/import-all-user-to-stripe', methods=['POST'])
def import_users_to_stripe():
    # Retrieve users from your database
    users = User.query.all()  # Assuming User is your SQLAlchemy model

    for user in users:
        try:
            # Create a customer in Stripe using the user's ID as the customer ID
            stripe.Customer.create(
                id=f'imotorV2_{user.id}',
                name=f'{user.first_name} {user.last_name}'
                # Add other optional parameters as needed
            )
            print(f"Imported user {user.id} to Stripe.")
        except stripe.error.StripeError as e:
            # Handle any errors
            print(f"Error importing user {user.id} to Stripe: {e}")
    return '', 200


@views.route('/get-user-subscription', methods=['GET'])
@jwt_required()
@current_user_required
def get_subscriptions():
    customer_id = f'imotorV2_{g.current_user["id"]}'
    # Make a request to the Stripe API endpoint
    url = f'https://api.stripe.com/v1/subscriptions?customer={customer_id}'
    headers = {
        'Authorization': f'Bearer {stripe.api_key}',
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        subscriptions = response.json()
        return jsonify(subscriptions), 200
    else:
        return jsonify({'error': 'Failed to fetch subscriptions'}), 500


@views.route('/upgrade-subscription', methods=['POST'])
@jwt_required()
@current_user_required
def upgrade_subscription():
    # Get the subscription ID and new quantity from the request
    subscription_id = request.json.get('subscriptionId')
    product_id = request.json.get('productId')
    new_quantity = request.json.get('newQuantity')
    print(subscription_id, product_id, new_quantity)
    try:
        print("entering TRY")
        # Retrieve the subscription from Stripe
        subscription = stripe.Subscription.retrieve(subscription_id)

        # Update the subscription quantity
        subscription.quantity = new_quantity
        subscription.save()
        print("SAVED")
        user_data = User.query.get(g.current_user["id"])
        print(user_data)
        if product_id == 'prod_PbPGcIZ8mGDgKt':
            # prod_PgwPGPw7ro44tD
            if user_data.is_subscribe_to_package == 0:
                user_data.standard_listing = 3 + int(new_quantity)
                db.session.commit()
            elif user_data.is_subscribe_to_package == 1:
                user_data.standard_listing = 16 + int(new_quantity)
                db.session.commit()
        elif product_id == 'prod_PbPEwLQCcVKadd':
            # prod_PgwPWCQ4vqJCLI
            if user_data.is_subscribe_to_package == 0:
                user_data.featured_listing = 0 + int(new_quantity)
                db.session.commit()
            elif user_data.is_subscribe_to_package == 1:
                user_data.featured_listing = 5 + int(new_quantity)
                db.session.commit()
        elif product_id == 'prod_PbPInhDd5zE2d5':
            # prod_PgwOWe6kwz1agd
            if user_data.is_subscribe_to_package == 0:
                user_data.premium_listing = 0 + int(new_quantity)
                db.session.commit()
            elif user_data.is_subscribe_to_package == 1:
                user_data.premium_listing = 2 + int(new_quantity)
                db.session.commit()

        return jsonify({'message': 'Subscription upgraded successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@views.route('/cancel-subscription/<subscription_id>', methods=['POST'])
@jwt_required()
@current_user_required
def cancel_subscription(subscription_id):
    try:
        # Retrieve the subscription from Stripe
        subscription = stripe.Subscription.retrieve(subscription_id)

        # Schedule the subscription for cancellation at the end of the current billing period
        subscription.cancel_at_period_end = True
        subscription.save()

        return jsonify({'message': 'Subscription scheduled for cancellation at the end of the billing period'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@views.route('/products', methods=['GET'])
def get_products():
    try:
        products = stripe.Product.list(limit=10)  # Fetch up to 10 products (adjust limit as needed)
        active_products = []
        for product in products.data:
            if product.active:  # Check if the product is active
                default_price_id = product.default_price
                if default_price_id:  # Check if default_price_id is not None
                    try:
                        default_price = stripe.Price.retrieve(default_price_id)
                        product_info = {
                            "product_id": product.id,
                            "price_id": product.default_price,
                            "description": product.description,
                            "name": product.name,
                            "unit_amount": default_price.unit_amount_decimal,
                        }
                        active_products.append(product_info)
                    except stripe.error.StripeError as e:
                        print(f"Error retrieving price for product {product.id}: {e}")
        return jsonify({"data": active_products})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@views.route('/add_payment_method', methods=['POST'])
@jwt_required()
@current_user_required
def add_payment_method():
    # Assuming the payment information is sent in the request body as JSON
    payment_info = request.json

    customer = stripe.Customer.retrieve(f"imotorV2_{g.current_user['id']}")

    # Create a PaymentMethod from the token
    payment_method = stripe.PaymentMethod.create(
        type='card',
        card={
            'token': payment_info['token'],  # Use the token to create the PaymentMethod
        }
    )

    # Attach the PaymentMethod to the customer
    stripe.PaymentMethod.attach(payment_method.id, customer=customer.id)

    # Update the PaymentMethod to include billing details
    payment_method = stripe.PaymentMethod.modify(
        payment_method.id,
        billing_details={
            'name': payment_info['cardholder_name']  # Include the cardholder's name
        }
    )

    # Set the new PaymentMethod as the default for the customer
    customer.invoice_settings.default_payment_method = payment_method.id
    customer.save()

    # Return success response to the frontend
    return jsonify({'message': 'Payment method added successfully'})


@views.route('/update_payment_method', methods=['POST'])
@jwt_required()
@current_user_required
def update_payment_method():
    # Assuming the updated payment information is sent in the request body as JSON
    updated_payment_info = request.json

    pm_id = updated_payment_info['pmId']
    token = updated_payment_info['token']

    # Detach the existing payment method
    stripe.PaymentMethod.detach(pm_id)

    # Retrieve the Stripe customer object associated with the currently logged-in user
    customer = stripe.Customer.retrieve(f"imotorV2_{g.current_user['id']}")

    # Create a new PaymentMethod from the token
    new_payment_method = stripe.PaymentMethod.create(
        type='card',
        card={
            'token': token,
        }
    )

    # Attach the new PaymentMethod to the customer
    stripe.PaymentMethod.attach(new_payment_method.id, customer=customer.id)

    # Set the new PaymentMethod as the default for the customer
    customer.invoice_settings.default_payment_method = new_payment_method.id
    customer.save()

    # Return success response to the frontend
    return jsonify({'message': 'Payment method updated successfully'})


# Endpoint to retrieve the user's default payment method
@views.route('/get_default_payment_method', methods=['GET'])
@jwt_required()
@current_user_required
def get_default_payment_method():
    # Retrieve the Stripe customer object associated with the currently logged-in user
    customer = stripe.Customer.retrieve(f"imotorV2_{g.current_user['id']}")

    # Retrieve the default payment method from the invoice settings
    invoice_settings = customer.get('invoice_settings', {})
    default_payment_method_id = invoice_settings.get('default_payment_method')

    if default_payment_method_id:
        # Retrieve the details of the default payment method
        payment_method = stripe.PaymentMethod.retrieve(default_payment_method_id)

        # Return the payment method details to the frontend
        return jsonify(payment_method)
    else:
        return jsonify({'error': 'Default payment method not found'}), 400


@views.route('/get_payment_methods', methods=['GET'])
@jwt_required()
@current_user_required
def get_payment_methods():
    try:
        # Retrieve the Stripe customer object associated with the currently logged-in user
        customer = stripe.Customer.retrieve(f"imotorV2_{g.current_user['id']}")

        # Retrieve all payment methods associated with the customer
        payment_methods = stripe.PaymentMethod.list(customer=customer.id)

        # Convert payment methods to JSON and return to the frontend
        return jsonify(payment_methods.data)
    except stripe.error.StripeError as e:
        return jsonify({'error': str(e)}), 500


# Endpoint to update the default payment method of the user
@views.route('/update_default_payment_method', methods=['POST'])
@jwt_required()
@current_user_required
def update_default_payment_method():
    try:
        # Retrieve the payment method ID from the request body
        data = request.json
        payment_method_id = data.get('payment_method_id')

        if not payment_method_id:
            return jsonify({'error': 'Payment method ID is required'}), 400

        # Retrieve the Stripe customer object associated with the currently logged-in user
        customer = stripe.Customer.retrieve(f"imotorV2_{g.current_user['id']}")

        # Update the default payment method for the customer
        customer.default_payment_method = payment_method_id
        customer.save()

        return jsonify({'message': 'Default payment method updated successfully'})
    except stripe.error.StripeError as e:
        return jsonify({'error': str(e)}), 500


@views.route('/delete_payment_method', methods=['POST'])
@jwt_required()
@current_user_required
def delete_payment_method():
    print("initialize delete")
    try:
        # Retrieve the payment method ID from the request body
        data = request.json
        print(data)
        payment_method_id = data.get('payment_method_id')
        print(payment_method_id)

        if not payment_method_id:
            print('Payment not found')
            return jsonify({'error': 'Payment method ID is required'}), 400

        # Detach (delete) the payment method
        stripe.PaymentMethod.detach(payment_method_id)

        return jsonify({'message': 'Payment method deleted successfully'})
    except stripe.error.StripeError as e:
        print(e)
        return jsonify({'error': str(e)}), 500


############################# END OF BRANDS ENDPOINT ####################

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
