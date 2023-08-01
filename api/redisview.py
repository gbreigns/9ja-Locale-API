import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv, find_dotenv
from flask_caching import Cache
from flask import Flask



app = Flask(__name__)



load_dotenv(find_dotenv())


limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.environ.get('REDIS_URL'),
    default_limits=["3 per minute"]
)

cache = Cache(app, config={
    "CACHE_TYPE": "redis",
    "CACHE_REDIS_URL": os.environ.get('REDIS_URL')
})


