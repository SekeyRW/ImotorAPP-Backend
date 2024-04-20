import random
import string
import threading
from datetime import datetime, timedelta

import jwt as pyjwt
from flask import Blueprint, request, jsonify, current_app, redirect, json
from flask_jwt_extended import create_access_token, create_refresh_token
from flask_mail import Message

from . import db, bcrypt, mail, stripe
from .models import User, Admin, RefreshToken

auth = Blueprint('auth', __name__)

#Create Stripe Customer
def create_stripe_customer(user_id):
    user = User.query.get(user_id)
    try:
        # Create a customer in Stripe with your own unique identifier
        stripe.Customer.create(
            id=f'imotorV2_{user.id}',  # Use the user's ID from your database
            name=f'{user.first_name} {user.last_name}'
            # Add other optional parameters as needed
        )
        return None
    except stripe.error.StripeError as e:
        # Handle any errors
        print(f"Error creating Stripe customer: {e}")
        return None

# ADMIN LOGIN
@auth.route('/admin/login', methods=['POST'])
def login():
    logging_user = request.get_json()

    email = logging_user['email']
    password = logging_user['password']

    user = Admin.query.filter_by(email=email.lower()).first()

    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({"message": "Invalid credentials"}), 401

    access_token = create_access_token(
        identity={"email": user.email, "id": user.id, "first_name": user.first_name, "last_name": user.last_name, })
    return jsonify(access_token=access_token), 200


# GOOGLE LOGIN (CLIENT SIDE)
@auth.route('/google/callback', methods=['POST'])
def google_auth_callback():
    if 'email' not in request.json:
        return jsonify({'message': 'Error Occurred!'}), 400
    user = User.query.filter_by(email=request.json['email'].lower()).first()
    if not user:
        if request.json['is_verified'] == True:
            isverified = 1
        else:
            isverified = 0
        new_user = User(
            email=request.json['email'],
            first_name=request.json['first_name'],
            last_name=request.json['last_name'],
            verified=isverified,
            profile_picture='default_profile_picture.jpg'
            # You might want to fetch and store more user information here
        )
        db.session.add(new_user)
        db.session.commit()
        create_stripe_customer(new_user.id)
        user = new_user

        access_token = create_access_token(identity={
            "email": user.email,
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
        })
        refresh_token_exp = datetime.utcnow() + timedelta(days=30)
        refresh_token_duration = refresh_token_exp - datetime.utcnow()
        refresh_token = create_refresh_token(identity={"user_id": user.id}, expires_delta=refresh_token_duration)
        new_refresh_token = RefreshToken(token=refresh_token, user_id=user.id, expires_at=refresh_token_exp)
        db.session.add(new_refresh_token)
        db.session.commit()

        return jsonify(
            {"access_token": access_token, 'refresh_token': refresh_token, 'message': 'Logged in successfully'}), 200
    else:
        access_token = create_access_token(identity={
            "email": user.email,
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
        })
        refresh_token_exp = datetime.utcnow() + timedelta(days=30)
        refresh_token_duration = refresh_token_exp - datetime.utcnow()
        refresh_token = create_refresh_token(identity={"user_id": user.id}, expires_delta=refresh_token_duration)
        new_refresh_token = RefreshToken(token=refresh_token, user_id=user.id, expires_at=refresh_token_exp)
        db.session.add(new_refresh_token)
        db.session.commit()
        return jsonify(
            {"access_token": access_token, 'refresh_token': refresh_token, 'message': 'Logged in successfully'}), 200


# APPLE LOGIN (CLIENT SIDE) NATIVE
@auth.route('/apple/native/callback', methods=['POST'])
def apple_auth_native_callback():
    json_data = request.json
    email = json_data.get('email')
    family_name = json_data.get('fullName', {}).get('familyName')
    given_name = json_data.get('fullName', {}).get('givenName')
    identity_token = json_data.get('identityToken')

    if email:
        user = User.query.filter_by(email=email.lower()).first()
        if not user:
            new_user = User(
                email=email,
                first_name=given_name,
                last_name=family_name,
                verified=1,
                profile_picture='default_profile_picture.jpg'
            )
            db.session.add(new_user)
            db.session.commit()
            create_stripe_customer(new_user.id)
            user = new_user

        access_token = create_access_token(identity={
            "email": user.email,
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
        })
        refresh_token_exp = datetime.utcnow() + timedelta(days=30)
        refresh_token_duration = refresh_token_exp - datetime.utcnow()
        refresh_token = create_refresh_token(identity={"user_id": user.id}, expires_delta=refresh_token_duration)
        new_refresh_token = RefreshToken(token=refresh_token, user_id=user.id, expires_at=refresh_token_exp)
        db.session.add(new_refresh_token)
        db.session.commit()

        return jsonify(
            {"access_token": access_token, 'refresh_token': refresh_token, 'message': 'Logged in successfully'}), 200
    else:
        decoded_token = pyjwt.decode(identity_token, options={"verify_signature": False})
        user = User.query.filter_by(email=decoded_token.get('email').lower()).first()
        if user is None:
            return jsonify({'message': 'User is not registered'}), 400

        access_token = create_access_token(identity={
            "email": user.email,
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
        })
        refresh_token_exp = datetime.utcnow() + timedelta(days=30)
        refresh_token_duration = refresh_token_exp - datetime.utcnow()
        refresh_token = create_refresh_token(identity={"user_id": user.id}, expires_delta=refresh_token_duration)
        new_refresh_token = RefreshToken(token=refresh_token, user_id=user.id, expires_at=refresh_token_exp)
        db.session.add(new_refresh_token)
        db.session.commit()
        return jsonify(
            {"access_token": access_token, 'refresh_token': refresh_token, 'message': 'Logged in successfully'}), 200


# APPLE LOGIN (CLIENT SIDE)
@auth.route('/apple/callback', methods=['POST'])
def apple_auth_callback():
    form_data = request.form
    user_info = form_data.get('user')
    if user_info:
        user_json = json.loads(user_info)  # Parse the 'user' JSON string
        first_name = user_json.get('name', {}).get('firstName')
        last_name = user_json.get('name', {}).get('lastName')
        email = user_json.get('email')

        user = User.query.filter_by(email=email.lower()).first()
        if not user:
            new_user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                verified=1,
                profile_picture='default_profile_picture.jpg'
            )
            db.session.add(new_user)
            db.session.commit()
            create_stripe_customer(new_user.id)
            user = new_user

        access_token = create_access_token(identity={
            "email": user.email,
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
        })
        refresh_token_exp = datetime.utcnow() + timedelta(days=30)
        refresh_token_duration = refresh_token_exp - datetime.utcnow()
        refresh_token = create_refresh_token(identity={"user_id": user.id}, expires_delta=refresh_token_duration)
        new_refresh_token = RefreshToken(token=refresh_token, user_id=user.id, expires_at=refresh_token_exp)
        db.session.add(new_refresh_token)
        db.session.commit()
        return redirect(
            f'{current_app.config["FRONTEND_URL"]}/validating-token?access_token={access_token}&refresh_token={refresh_token}')
    else:
        id_token = form_data.get('id_token')
        if id_token is None:
            return jsonify({'message': 'ID token not found in request data'}), 400

        # Decode and verify the 'id_token' received from Apple
        decoded_token = pyjwt.decode(id_token, options={"verify_signature": False})

        user = User.query.filter_by(email=decoded_token.get('email').lower()).first()

        if user is None:
            return jsonify({'message': 'User is not registered'}), 400

        access_token = create_access_token(identity={
            "email": user.email,
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
        })
        refresh_token_exp = datetime.utcnow() + timedelta(days=30)
        refresh_token_duration = refresh_token_exp - datetime.utcnow()
        refresh_token = create_refresh_token(identity={"user_id": user.id}, expires_delta=refresh_token_duration)
        new_refresh_token = RefreshToken(token=refresh_token, user_id=user.id, expires_at=refresh_token_exp)
        db.session.add(new_refresh_token)
        db.session.commit()
        return redirect(
            f'{current_app.config["FRONTEND_URL"]}/validating-token?access_token={access_token}&refresh_token={refresh_token}')


# CODE GENERATOR
def generate_verification_code():
    # Generate a 6-digit random code
    return ''.join(random.choices(string.digits, k=6))


# Manual Sign up (Client Side)
@auth.route('/client/signup', methods=['POST'])
def client_signup():
    new_data = request.get_json()
    user = User.query.filter_by(email=new_data['email'].lower()).first()
    if not user:
        password = new_data['password']
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(
            email=new_data['email'],
            first_name=new_data['first_name'],
            last_name=new_data['last_name'],
            password=password_hash,
            profile_picture='default_profile_picture.jpg',
            verification_code=generate_verification_code(),
        )
        db.session.add(new_user)
        db.session.commit()
        create_stripe_customer(new_user.id)
        user = new_user

        access_token = create_access_token(identity={
            "email": user.email,
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
        })
        refresh_token_exp = datetime.utcnow() + timedelta(days=30)
        refresh_token_duration = refresh_token_exp - datetime.utcnow()
        refresh_token = create_refresh_token(identity={"user_id": user.id}, expires_delta=refresh_token_duration)
        new_refresh_token = RefreshToken(token=refresh_token, user_id=user.id, expires_at=refresh_token_exp)
        db.session.add(new_refresh_token)
        db.session.commit()

        # Here, you'd send an email to the user with the verification code
        # Use your email service/API to send the verification code to the user's email
        thread = threading.Thread(target=send_verification_code,
                                  args=(new_user.verification_code, new_user.email, current_app._get_current_object()))
        thread.start()

        return jsonify({"access_token": access_token, 'refresh_token': refresh_token,
                        'message': 'User registered successfully. Check your email for verification code.'}), 200
    else:
        return jsonify({'message': 'Email already exists!'}), 401


def send_verification_code(verification_code, user_email, app):
    with app.app_context():
        msg = Message(f'Email Verification Code', recipients=[f'{user_email}'])
        msg.html = f"""
                <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                    </head>
                    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px;">
                        <div style="max-width: 600px; margin: 0 auto; background-color: #fff; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <div style="text-align: center; margin-bottom: 20px;">
                                <h2>Email Verification</h2>
                            </div>
                            <div style="font-size: 24px; font-weight: bold; text-align: center; padding: 15px; border: 2px dashed #ccc; border-radius: 5px; background-color: #f9f9f9;">
                                Your verification code is: <span> {verification_code}</span>
                            </div>
                            <div style="text-align: center; margin-top: 20px;">
                                Please use the above verification code to verify your email address.
                            </div>
                        </div>
                    </body>
                </html>
        """
        msg.mimetype = 'text/html'
        mail.send(msg)


# CODE VERIFIER
@auth.route('/verify_code', methods=['POST'])
def verify_code():
    data = request.json
    email = data.get('email')
    verification_code = data.get('verification_code')

    user = User.query.filter_by(email=email).first()
    if user:
        if user.verification_code == verification_code:
            user.verified = 1
            db.session.commit()
            return jsonify({'message': 'Verification successful. User is verified.'})
        else:
            return jsonify({'error': 'Invalid verification code.'}), 400
    else:
        return jsonify({'error': 'User not found.'}), 404


# USER CHECKER IF VERIFIED
@auth.route('/check_verification', methods=['GET'])
def check_verification():
    email = request.args.get('email')

    user = User.query.filter_by(email=email).first()
    if user:
        verified_status = bool(user.verified)
        return jsonify({'verified': verified_status})
    else:
        return jsonify({'error': 'User not found.'}), 404


# Manual Login (Client Side)
@auth.route('/client/login', methods=['POST'])
def client_login():
    logging_user = request.get_json()

    email = logging_user['email']
    password = logging_user['password']

    user = User.query.filter_by(email=email.lower()).first()
    if not user:
        return jsonify({"message": "Account not created!"}), 401

    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({"message": "Invalid credentials!"}), 401

    access_token = create_access_token(
        identity={"email": user.email, "id": user.id, "first_name": user.first_name, "last_name": user.last_name, })

    refresh_token_exp = datetime.utcnow() + timedelta(days=30)
    refresh_token_duration = refresh_token_exp - datetime.utcnow()
    refresh_token = create_refresh_token(identity={"user_id": user.id}, expires_delta=refresh_token_duration)
    new_refresh_token = RefreshToken(token=refresh_token, user_id=user.id, expires_at=refresh_token_exp)
    db.session.add(new_refresh_token)
    db.session.commit()

    return jsonify(
        {"access_token": access_token, 'refresh_token': refresh_token, 'message': 'Logged in successfully'}), 200


def refresh_token_is_valid(refresh_token):
    now = datetime.utcnow()
    refresh_token_record = RefreshToken.query.filter_by(token=refresh_token).first()
    if refresh_token_record and refresh_token_record.expires_at > now:
        user = User.query.filter_by(id=refresh_token_record.user_id).first()
        return refresh_token_record, user
    return None, None


# Refresh Token (Client Side)
@auth.route('/client/refresh-token', methods=['POST'])
def refresh_token():
    refresh_token = request.json.get('refresh_token')
    refresh_token_record, user = refresh_token_is_valid(refresh_token)
    if refresh_token_record:
        new_access_token = create_access_token(identity={
            "email": user.email,
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
        })
        refresh_token_exp = datetime.utcnow() + timedelta(days=30)
        refresh_token_duration = refresh_token_exp - datetime.utcnow()
        add_refresh_token = create_refresh_token(identity={"user_id": user.id}, expires_delta=refresh_token_duration)
        new_refresh_token = RefreshToken(token=add_refresh_token, user_id=user.id, expires_at=refresh_token_exp)
        db.session.add(new_refresh_token)
        db.session.commit()
        return {'access_token': new_access_token, 'refresh_token': add_refresh_token}, 200
    else:
        return {'message': 'Invalid refresh token'}, 401


# Forgot Password
def generate_reset_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))


@auth.route('/forgot_password', methods=['POST'])
def forgot_password():
    email = request.json.get('email')

    # Check if the email exists in the user database (Replace with actual database query)
    user = User.query.filter_by(email=email).first()

    if user:
        reset_token = generate_reset_token()
        user.reset_token = reset_token
        user.reset_token_timestamp = datetime.utcnow()
        db.session.commit()

        # Here, you would construct a password reset link with the reset_token
        reset_link = f"{current_app.config['FRONTEND_URL']}/auth/reset-password?token={reset_token}&email={user.email}"

        thread = threading.Thread(target=send_reset_password_link,
                                  args=(reset_link, user.email, current_app._get_current_object()))
        thread.start()

        return jsonify({'message': 'Password reset link sent to your email.'}), 200
    else:
        return jsonify({'error': 'User not found.'}), 404


def send_reset_password_link(reset_link, user_email, app):
    with app.app_context():
        msg = Message(f'Password Reset', recipients=[f'{user_email}'])
        msg.html = f"""
                <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                    </head>
                    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px;">
                        <div style="max-width: 600px; margin: 0 auto; background-color: #fff; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <div style="text-align: center; margin-bottom: 20px;">
                                <h2>Password Reset</h2>
                            </div>
                            <div style="padding: 20px; background-color: #f9f9f9; border-radius: 5px;">
                                <p style="margin-bottom: 20px;">You've requested to reset your password. Click the button below to reset:</p>
                                <p style="text-align: center; margin: 0;">
                                    <a href="{reset_link}" style="text-decoration: none; background-color: #007bff; color: #fff; padding: 10px 20px; border-radius: 5px; display: inline-block;">Reset Password</a>
                                </p>
                                <p style="margin-top: 20px;">If you didn't request a password reset, you can ignore this email.</p>
                            </div>
                        </div>
                    </body>
                </html>
        """
        msg.mimetype = 'text/html'
        mail.send(msg)


@auth.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.json
    email = request.args.get('email')
    reset_token = request.args.get('token')
    new_password = data.get('new_password')

    # Find the user by email (Replace this with actual database query)
    user = User.query.filter_by(email=email, reset_token=reset_token).first()

    if user:
        token_timestamp = user.reset_token_timestamp
        # Check if the reset token is within a valid timeframe (e.g., 1 hour)
        if token_timestamp and (datetime.utcnow() - token_timestamp) < timedelta(hours=1):
            password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
            user.password = password_hash
            user.reset_token = None
            user.reset_token_timestamp = None
            db.session.commit()
            return jsonify({'message': 'Password reset successful.'})
        else:
            return jsonify({'error': 'Reset token has expired.'}), 400
    else:
        return jsonify({'error': 'Invalid reset token.'}), 400
