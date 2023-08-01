from flask_restx import Namespace, Resource
from ..model.db import connect_to_db
from flask import jsonify, Response
from bson.objectid import ObjectId
from http import HTTPStatus
from bson import json_util
from ..redisview import limiter, cache
from flask import Flask
# from flask_caching import Cache
import os
from dotenv import load_dotenv, find_dotenv
from flask_jwt_extended import jwt_required
from ..utils.local import authenticate_with_jwt_and_api_key
from flask_caching import Cache



load_dotenv(find_dotenv())


app = Flask(__name__)

limiter.init_app(app)

cache.init_app(app)

# cache = Cache(app, config={
#     "CACHE_TYPE": "redis",
#     "CACHE_REDIS_URL": os.environ.get('REDIS_URL')
# })

# cache.init_app(app, config={
#                     "CACHE_TYPE": "redis",
#                     "CACHE_REDIS_URL": os.environ.get('REDIS_URL')
# })


state_ns = Namespace('state', description='Namespace for State')

#   Serialize region data
def get_regions():
    database = connect_to_db()
    regions = database.regions

    data = list(regions.find())

    for item in data:
        item['_id'] = str(ObjectId(item['_id']))
    # database.close()
    return data

#   Serialize state data
def get_states(): 
    database = connect_to_db()
    states = database.data

    data = list(states.find().sort('state', 1))

    for item in data:
        item['_id'] = str(ObjectId(item['_id']))

    return data

#   Serialize lga data
def get_lgas():
    database = connect_to_db()
    lgas = database.local_governments

    data = list(lgas.find())

    # for item in data:
    #     item['_id'] = str(ObjectId(item['_id']))
    #     item['state_id'] = str(ObjectId(item['state_id']))

    return data


@state_ns.route('/regions')
class Regions(Resource):
    @authenticate_with_jwt_and_api_key()
    @limiter.limit('5/minute')
    @cache.cached(timeout=60)
    # @jwt_required()
    def get(self):
        """
            Get all regions
        """
        try:
            data = get_regions()

            response = jsonify(data)
            
            return Response(response.get_data(), status=HTTPStatus.OK, mimetype='application/json')
        
        except Exception as e:
            print(e)

            return {'message': 'An error occurred'}, HTTPStatus.INTERNAL_SERVER_ERROR

@state_ns.route('/lgas')
class Lgas(Resource):
    @limiter.limit('3/minute')
    @cache.cached(timeout=60)
    @jwt_required()
    def get(self):
        """
            Get all lgas
        """
        try:
            data = get_lgas()
            json_data = json_util.dumps(data)
            lgas = json_util.loads(json_data)

            for item in lgas:
                item['_id'] = str(ObjectId(item['_id']))
                item['state_id'] = str(ObjectId(item['state_id']))

            response = jsonify(lgas)

            return Response(response.get_data(), status=HTTPStatus.OK, mimetype='application/json')
        
        except Exception as e:
            print(e)

            return {'message': 'An error occurred'}, HTTPStatus.INTERNAL_SERVER_ERROR

@state_ns.route('/states')
class States(Resource):
    @limiter.limit('3/minute')
    @cache.cached(timeout=60)
    @jwt_required()
    def get(self):
        """
            Get all states
        """
        try:
            data = get_states()

            response = jsonify(data)

            return Response(response.get_data(), status=HTTPStatus.OK, mimetype='application/json')
        
        except Exception as e:
            print(e)

            return {'message': 'An error occurred'}, HTTPStatus.INTERNAL_SERVER_ERROR

@state_ns.route('/states/<string:state_id>')
class State(Resource):
    @limiter.limit('3/minute')
    @cache.cached(timeout=60)
    @jwt_required()
    def get(self, state_id):
        """
            Get a single state
        """
        try:
            database = connect_to_db()
            states = database.data

            state = states.find_one({'_id': ObjectId(state_id)})

            state['_id'] = str(ObjectId(state['_id']))

            response = jsonify(state)

            return Response(response.get_data(), status=HTTPStatus.OK, mimetype='application/json')
        
        except Exception as e:
            print(e)

            return {'message': 'An error occurred'}, HTTPStatus.INTERNAL_SERVER_ERROR
        
@state_ns.route('/lgas/<string:state_id>')
class Lga(Resource):
    @limiter.limit('3/minute')
    @cache.cached(timeout=60)
    @jwt_required()
    def get(self, state_id):
        """
            Get all lgas in a state
        """
        try:
            database = connect_to_db()
            lgas = database.local_governments

            data = list(lgas.find({'state_id': ObjectId(state_id)}))

            for item in data:
                item['_id'] = str(ObjectId(item['_id']))
                item['state_id'] = str(ObjectId(item['state_id']))

            response = jsonify(data)

            return Response(response.get_data(), status=HTTPStatus.OK, mimetype='application/json')
        
        except Exception as e:
            print(e)

            return {'message': 'An error occurred'}, HTTPStatus.INTERNAL_SERVER_ERROR
        
@state_ns.route('/regions/<string:region_id>')
class Region(Resource):
    @limiter.limit('3/minute')
    @cache.cached(timeout=60)
    @jwt_required()
    def get(self, region_id):
        """
            Get a single region
        """
        try:
            database = connect_to_db()
            regions = database.regions

            geo_political_zone = regions.find_one({'_id': ObjectId(region_id)})

            geo_political_zone['_id'] = str(ObjectId(geo_political_zone['_id']))

            response = jsonify(geo_political_zone)

            return Response(response.get_data(), status=HTTPStatus.OK, mimetype='application/json')
        
        except Exception as e:
            print(e)

            return {'message': 'An error occurred'}, HTTPStatus.INTERNAL_SERVER_ERROR
    
@state_ns.route('/search/<string:query>')
class Search(Resource):
    @limiter.limit('3/minute')
    @cache.cached(timeout=60)
    @jwt_required()
    def get(self, query):
        """
            Search for a state or lga
        """
        try:
            database = connect_to_db()
            states = database.data
            lgas = database.local_governments
            regions = database.regions

            state = states.find_one({'state': query})
            lga = lgas.find_one({'lga': query})
            region = regions.find_one({'name': query})

            if state:
                state['_id'] = str(ObjectId(state['_id']))

                response = jsonify(state)

                return Response(response.get_data(), status=HTTPStatus.OK, mimetype='application/json')
            
            elif lga:
                lga['_id'] = str(ObjectId(lga['_id']))
                lga['state_id'] = str(ObjectId(lga['state_id']))

                response = jsonify(lga)

                return Response(response.get_data(), status=HTTPStatus.OK, mimetype='application/json')

            elif region:
                region['_id'] = str(ObjectId(region['_id']))

                response = jsonify(region)

                return Response(response.get_data(), status=HTTPStatus.OK, mimetype='application/json')
                        
            else:
                return {'message': 'No results found'}, HTTPStatus.NOT_FOUND
        
        except Exception as e:
            print(e)

            return {'message': 'An error occurred'}, HTTPStatus.INTERNAL_SERVER_ERROR

