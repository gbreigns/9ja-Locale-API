from email_validator import validate_email, EmailNotValidError
from api.model.db import connect_to_db



# Create database
database = connect_to_db()

users = database.users

def is_valid_email(email):
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False
    
user_validation = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["username", "email", "password_hash", "confirm_password"],
        "properties": {
            "username": {
                "bsonType": "string",
                "description": "First name is required and must be a string"
            },
            "email": {
                "bsonType": "string",
                "description": "Email is required and must be in a valid email format",
                "pattern": "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
                "uniqueItems": True
            },
            "password_hash": {
                "bsonType": "string",
                "description": "Password is required and must be a string",
                "minLength": 6,
                "maxLength": 1024
            },
            "confirm_password": {
                "bsonType": "string",
                "description": "Confirm password is required and must be a string",
                "minLength": 6,
                "maxLength": 1024
            },
            "api_key": {
                "bsonType": "string",
                "description": "API key is required and must be a string"
            },
            "created_at": {
                "bsonType": "date",
                "description": "Date the user was created"
            },
        }
    }
}

try:
    database.command({
        "collMod": "users",
        "validator": user_validation,
        "validationLevel": "strict"
    })
except Exception as e:
    print(e)


# users.create_index("email", unique=True)
# def insert_test_doc():
#     test_document = {
#         "name": "test3",
#         "email": "ggtt3@gmail.com",
#         "password_hash": "test12345"
#     }
#     try:
#         users.insert_one(test_document)
#     except Exception as e:
#         print(e)

# insert_test_doc()