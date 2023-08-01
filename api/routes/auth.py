import uuid
import os
from dotenv import load_dotenv, find_dotenv
from flask_restx import Namespace, Resource, fields
from ..model.db import connect_to_db
from http import HTTPStatus
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from bson.objectid import ObjectId
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from ..redisview import cache
from functools import wraps
import jwt


load_dotenv(find_dotenv())

auth_ns = Namespace('auth', description='Namesake for Authentication')

#   User model
user_model = auth_ns.model('User', {
    'username': fields.String(required=True, description='User first name'),
    'email': fields.String(required=True, description='User email address'),
    'password': fields.String(required=True, description='User password'),
    'confirm_password': fields.String(required=True, description='Confirm user password')
})

#   Login model
login_model = auth_ns.model('Login', {
    'email': fields.String(required=True, description='User email address'),
    'password': fields.String(required=True, description='User password')
})

reset_password_model = auth_ns.model('ResetPassword', {
    'email': fields.String(required=True, description='User email address'),
    'new_password': fields.String(required=True, description='New password'),
    'confirm_password': fields.String(required=True, description='Confirm new password')
})


#   Database connection
database = connect_to_db()


@auth_ns.route('/auth/register')
class SignUp(Resource):
    @auth_ns.expect(user_model)
    @auth_ns.doc(description='Register a new user')
    @cache.cached(timeout=60)
    def post(self):
        """
            Register a new user
        """

        data = request.get_json()

        #   Check if user already exists
        user = database.users.find_one({'email': data['email']})


        if user:
            return {'message': 'User already exists'}, HTTPStatus.BAD_REQUEST
        
        api_key = str(uuid.uuid4())

        username = data['username']
        email = data['email']
        password = data['password']
        confirm_password = data['confirm_password']

        #   Check if password and confirm password match
        if password != confirm_password:
            return {'message': 'Password and confirm password do not match'}, HTTPStatus.BAD_REQUEST

        user = {
            'username': username,
            'email': email,
            'password_hash': generate_password_hash(password),
            'confirm_password_hash': generate_password_hash(confirm_password),
            'api_key': api_key,
            'created_at': datetime.utcnow()
        }

        #   Insert user into database
        database.users.insert_one(user)

        return {'message': 'User created successfully'}, HTTPStatus.CREATED
    
@auth_ns.route('/auth/login')
class Login(Resource):
    @auth_ns.expect(login_model)
    @auth_ns.doc(description='Login a user', 
                 params={'email': 'User email address', 
                        'password': 'User password'})
    def post(self):
        """
            Login a user
        """

        data = request.get_json()

        email = data.get('email')
        password = data.get('password')

        #   Check if email and password are provided
        if not email or not password:
            return {'message': 'Email and password required'}, HTTPStatus.BAD_REQUEST
        
        #   Check if user exists
        user = database.users.find_one({'email': email})

        #   Check if user exists and password is correct
        if user and check_password_hash(user['password_hash'], password):

            api_key = user.get('api_key')

            if not api_key:
                return {'message': 'Invalid API key'}, HTTPStatus.NOT_FOUND

            #   Generate access and refresh tokens
            access_token = create_access_token(identity=str(ObjectId(user['_id'])))
            refresh_token = create_refresh_token(identity=str(ObjectId(user['_id'])))

            token_data = {
                'sub': str(ObjectId(user['_id'])),
                'identity': str(ObjectId(user['_id'])),
                'api_key': api_key
            }

            # Encode token data
            jwt_token = jwt.encode(token_data, 
                                   os.getenv('JWT_SECRET_KEY'),
                                    algorithm='HS256')

            response = {
                'message': 'User logged in',
                'api_key': api_key,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'jwt_token': jwt_token
            }

            return response, HTTPStatus.OK
        
        return {'message': 'Invalid credentials'}, HTTPStatus.UNAUTHORIZED

    
@auth_ns.route('/auth/refresh')
class Refresh(Resource):
    @auth_ns.doc(description='Refresh a user\'s token')
    @cache.cached(timeout=60)
    @jwt_required(refresh=True)
    def post(self):
        """
            Refresh a user's token
        """

        current_user = get_jwt_identity()

        #   Generate new access token
        access_token = create_access_token(identity=current_user)

        return {'access_token': access_token}, HTTPStatus.OK

    
@auth_ns.route('/auth/logout')
class Logout(Resource):
    @auth_ns.doc(description='Logout a user')
    @jwt_required()
    def post(self):
        """
            Logout a user
        """

        return {'message': 'User logged out'}
    
@auth_ns.route('/auth/reset-password')
class ResetPassword(Resource):
    @auth_ns.expect(reset_password_model)
    @auth_ns.doc(description='Reset a user\'s password')
    @jwt_required()
    def post(self):
        """
            Reset a user's password
        """

        data = request.get_json()
        email = data.get('email')
        new_password = data.get('new_password')
        confirm_new_password = data.get('confirm_new_password')

        #   Check if email, new password and confirm new password are provided
        if not email or not new_password or not confirm_new_password:
            return {'message': 'Email, new password and confirm new password required'}, HTTPStatus.BAD_REQUEST
        
        #   Check if new password and confirm new password match
        if new_password != confirm_new_password:
            return {'message': 'New password and confirm new password must match'}, HTTPStatus.BAD_REQUEST

        user = database.users.find_one({'email': email})

        if user:
            new_password_hash = generate_password_hash(new_password)
            database.users.update_one({'email': email}, {'$set': {'password_hash': new_password_hash}})

            return {'message': 'Password reset successfuly'}, HTTPStatus.OK
        
        return {'message': 'User not found'}, HTTPStatus.NOT_FOUND

    
@auth_ns.route('/auth/forgot-password')
class ForgotPassword(Resource):
    def post(self):
        """
            Forgot a user's password
        """

        return {'message': 'Password reset'}
    
@auth_ns.route('/auth/confirm-email')
class ConfirmEmail(Resource):
    def post(self):
        """
            Confirm a user's email
        """

        return {'message': 'Email confirmed'}
    
@auth_ns.route('/resend-confirmation-email')
class ResendConfirmationEmail(Resource):
    def post(self):
        """
            Resend a user's confirmation email
        """

        return {'message': 'Email resent'}