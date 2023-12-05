import os
import load_env
import requests

from flask_bcrypt import Bcrypt
from flask_caching import Cache
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

load_env.load_environment()

SECRET_KEY = os.getenv('SECRET_KEY')
YANDEX_ID_URL = os.getenv('YANDEX_ID_URL')
YANDEX_ID_CLIENT_ID = os.getenv('YANDEX_ID_CLIENT_ID')
YANDEX_ID_CALLBACK_URI = os.getenv('YANDEX_ID_CALLBACK_URI')
YANDEX_ID_CLIENT_SECRET = os.getenv('YANDEX_ID_CLIENT_SECRET')
YANDEX_ID_TOKEN_URL = os.getenv('YANDEX_ID_TOKEN_URL')

ftp_config = {
    'username': os.getenv('FTP_USERNAME'),
    'password': os.getenv('FTP_PASSWORD'),
    'hostname': os.getenv('FTP_HOSTNAME')
}
email_config = {
    'sender': os.getenv('EMAIL_SENDER'),
    'password': os.getenv('EMAIL_PASSWORD')
}
redis_config = {
    'CACHE_TYPE': os.getenv('CACHE_TYPE'),
    'CACHE_KEY_PREFIX': os.getenv('CACHE_KEY_PREFIX'),
    'CACHE_REDIS_HOST': os.getenv('CACHE_REDIS_HOST'),
    'CACHE_REDIS_PORT': os.getenv('CACHE_REDIS_PORT'),
    'CACHE_REDIS_URL': f"{os.getenv('CACHE_TYPE')}://{os.getenv('CACHE_REDIS_HOST')}"
                       f":{os.getenv('CACHE_REDIS_PORT')}"
}
postgres_config = {
    'POSTGRES_USER': os.getenv('POSTGRES_USER'),
    'POSTGRES_PASSWORD': os.getenv('POSTGRES_PASSWORD'),
    'POSTGRES_HOST': os.getenv('POSTGRES_HOST'),
    'POSTGRES_PORT': os.getenv('POSTGRES_PORT'),
    'POSTGRES_DB': os.getenv('POSTGRES_DB')
}

cache = Cache(
    config={
        "CACHE_TYPE": redis_config["CACHE_TYPE"],
        "CACHE_KEY_PREFIX": redis_config["CACHE_KEY_PREFIX"],
        "CACHE_REDIS_HOST": redis_config["CACHE_REDIS_HOST"],
        "CACHE_REDIS_PORT": redis_config["CACHE_REDIS_PORT"],
        "CACHE_REDIS_URL": redis_config["CACHE_REDIS_URL"]
    }
)

db = SQLAlchemy()
csrf = CSRFProtect()
bcrypt = Bcrypt()
login_manager = LoginManager()

response = requests.get('https://pokeapi.co/api/v2/pokemon/?limit=1')
data = response.json()
response = requests.get(f'https://pokeapi.co/api/v2/pokemon/?limit={data["count"]}')
data = response.json()

pokemon_names = []
multiplier = 5

for i in data['results']:
    pokemon_names.append(i['name'])
