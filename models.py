import os
import random
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

import requests
from flask import session

dotenv_path = os.path.join(os.path.dirname(__file__), '.env.local')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

db = SQLAlchemy()


class Battles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    main_pokemon = db.Column(db.String(150), nullable=False)
    opponent_pokemon = db.Column(db.String(150), nullable=False)
    win = db.Column(db.String(150), nullable=False)


response = requests.get('https://pokeapi.co/api/v2/pokemon/?limit=1')
data = response.json()
response = requests.get(f'https://pokeapi.co/api/v2/pokemon/?limit={data["count"]}')
data = response.json()
pokemon_names = []
multiplier = 5

for i in data['results']:
    pokemon_names.append(i['name'])

ftp_config = {
    'username': os.environ.get('FTP_USERNAME'),
    'password': os.environ.get('FTP_PASSWORD'),
    'hostname': os.environ.get('FTP_HOSTNAME')
}
email_config = {
    'sender': os.environ.get('EMAIL_SENDER'),
    'password': os.environ.get('EMAIL_PASSWORD')
}
redis_config = {
    'CACHE_TYPE': os.environ.get('CACHE_TYPE'),
    'CACHE_KEY_PREFIX': os.environ.get('CACHE_KEY_PREFIX'),
    'CACHE_REDIS_HOST': os.environ.get('CACHE_REDIS_HOST'),
    'CACHE_REDIS_PORT': os.environ.get('CACHE_REDIS_PORT'),
    'CACHE_REDIS_URL': f"{os.environ.get('CACHE_TYPE')}://{os.environ.get('CACHE_REDIS_HOST')}"
                       f":{os.environ.get('CACHE_REDIS_PORT')}"
}


def count_pages(current_page: int, finale_page: int):
    left = current_page - 3 if current_page >= 4 else 1
    right = current_page + 3 if finale_page - current_page >= 3 else finale_page
    return list(range(left, right + 1))


def get_pokemon_data(pokemon_name):
    url = f'https://pokeapi.co/api/v2/pokemon/{pokemon_name}/'
    temp_response = requests.get(url)
    temp_data = temp_response.json()
    pokemon = {'name': temp_data['name'], 'image': temp_data['sprites']['front_default']}

    for stat in temp_data['stats']:
        pokemon[stat['stat']['name'].replace('-', '_')] = stat['base_stat']
    return pokemon


def standart_result(current_page):
    global multiplier
    pokemons = [
        get_pokemon_data(pokemon_names[index])
        for index in range((current_page - 1) * multiplier, (current_page - 1) * multiplier + multiplier)
    ]
    return pokemons


def search_result(current_page, search_pokemons):
    global multiplier
    if len(search_pokemons) >= multiplier:
        pokemons = \
            [
                get_pokemon_data(search_pokemons[index])
                for index in range((current_page - 1) * multiplier, (current_page - 1) * multiplier + multiplier)
            ]
    else:
        pokemons = \
            [
                get_pokemon_data(pokemon)
                for pokemon in search_pokemons
            ]
    return pokemons


def search_result_names(search_prompt):
    global multiplier
    pokemons = []
    for name in pokemon_names:
        if search_prompt in name:
            pokemons.append(name)
    return pokemons


def decrease_hp(players_number, opponent_pokemon_number):
    if players_number % 2 == opponent_pokemon_number % 2:
        session['opponent_pokemon']['hp'] -= session['main_pokemon']['attack']
        return True
    else:
        session['main_pokemon']['hp'] -= session['opponent_pokemon']['attack']
        return False


def define_global_win():
    return session['opponent_pokemon']['hp'] <= 0 or session['main_pokemon']['hp'] <= 0


def winner():
    result = None
    if session['opponent_pokemon']['hp'] <= 0:
        result = session['main_pokemon']
    elif session['main_pokemon']['hp'] <= 0:
        result = session['opponent_pokemon']
    return result


def auto_fight_history():
    history = []
    while not define_global_win():
        session.pop('players_number', None)
        session.pop('opponent_pokemon_number', None)
        session['players_number'] = random.randint(1, 11)
        session['opponent_pokemon_number'] = random.randint(1, 11)
        decrease_hp(session['players_number'], session['opponent_pokemon_number'])
        history.append(
            {'players_number': session['players_number'],
             'opponent_pokemon_number': session['opponent_pokemon_number'],
             'main_hp': session['main_pokemon']['hp'],
             'opponent_hp': session['opponent_pokemon']['hp']})
    return history
