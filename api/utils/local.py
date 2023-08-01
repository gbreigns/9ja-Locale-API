from functools import wraps
import jwt
import os
from flask import request
from http import HTTPStatus
from api.model.db import connect_to_db


database = connect_to_db()



def verify_api_key(api_key):
    # Retrieve the user from the database or any other data source
    user = get_user_by_api_key(api_key)
    
    if user:
        return True
    
    return False

def get_user_by_api_key(api_key):
    user = database.users.find_one({'api_key': api_key})

    if user:
        return user
    
    return {"message": "User not found"}, HTTPStatus.NOT_FOUND

def authenticate_with_jwt_and_api_key():
    def wrapper(fn):
        @wraps(fn)
        def decorated_function(*args, **kwargs):
            # Extract JWT from request header
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                jwt_token = auth_header.split(' ')[1]
            else:
                # Handle missing or invalid JWT
                return {'message': 'Invalid token'}, HTTPStatus.UNAUTHORIZED
            
            # Decode and verify JWT
            try:
                decoded_token = jwt.decode(jwt_token, os.getenv('JWT_SECRET_KEY'), algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                # Handle expired token
                return {'message': 'Token expired'}, HTTPStatus.UNAUTHORIZED
            except jwt.InvalidTokenError:
                # Handle invalid token
                return {'message': 'Invalid token'}, HTTPStatus.UNAUTHORIZED

            # Access API key from decoded token
            api_key = decoded_token.get('api_key')

            # Authenticate the user based on the API key
            if api_key:
                user = get_user_by_api_key(api_key)
                if user:
                    # User authenticated, proceed with the operation
                    return fn(*args, **kwargs)
                
            # Handle missing or invalid API key
            return {'message': 'Invalid API key'}, HTTPStatus.UNAUTHORIZED

        return decorated_function
    
    return wrapper