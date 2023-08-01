import os
from flask import Flask
from .config.config import config_dict
from .model.db import connect_to_db
from flask_restx import Api
from .routes.views import state_ns
from .routes.auth import auth_ns
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import redis
from http import HTTPStatus
from dotenv import load_dotenv, find_dotenv
from flask_swagger_ui import get_swaggerui_blueprint
from .redisview import cache



load_dotenv(find_dotenv())


def create_app(config=config_dict['development']):
  app = Flask(__name__)
  app.config.from_object(config)
  
  CORS(app)

  jwt = JWTManager(app)
  
  db = connect_to_db()

  r = redis.Redis(
    host=os.environ.get('REDIS_HOST'),
    port=12668,
    password=os.environ.get('REDIS_PASSWORD'))
  
  # cache = Cache(app)

  cache.init_app(app)

  authorizations = {
    'Bearer Auth': {
      'type': 'apiKey',
      'in': 'header',
      'name': 'Authorization',
      # 'description': 'Add a JWT token to the header with ** Bearer &lt;JWT token&gt; to authorize **'
    }
  }

  
  api = Api(app, 
            title='Locale API',  
            description='''
              A simple API for getting states and local governments in Nigeria
            ''',
            authorizations=authorizations,
            security='Bearer Auth',
            # prefix='/api/v1'
          )

  SWAGGER_URL = '/swagger'
  API_URL = '/static/swagger.json'
  SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
      'app_name': 'Locale API'
    }
  )

  app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)
  
  api.add_namespace(state_ns, path='/api/v1')
  api.add_namespace(auth_ns, path='/api/v1')

  @app.errorhandler(429)
  def handle_rate_limit_exception(e):
      return {'message': 'Rate limit exceeded. Too many requests'}, HTTPStatus.TOO_MANY_REQUESTS

  return app
