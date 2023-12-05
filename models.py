import random
from settings import *
from flask import session
from flask_login import UserMixin, current_user
from sqlalchemy import ForeignKey


class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)

    def __init__(self, name: str, email: str, password: str):
        super().__init__()
        self.name = name
        self.email = email
        self.password = self.get_password_hash(password)

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    def get_password_hash(self, password):
        return bcrypt.generate_password_hash(password).decode('utf-8')


class Battles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    main_pokemon = db.Column(db.String(150), nullable=False)
    opponent_pokemon = db.Column(db.String(150), nullable=False)
    win = db.Column(db.String(150), nullable=False)
    user_id = db.Column(db.Integer, ForeignKey('users.id'))


def count_pages(current_page: int, finale_page: int):
    left = current_page - 3 if current_page >= 4 else 1
    right = current_page + 3 if finale_page - current_page >= 3 else finale_page
    return list(range(left, right + 1))


def get_pokemon_data(pokemon_name: str or int):
    url = f'https://pokeapi.co/api/v2/pokemon/{pokemon_name}/'
    temp_response = requests.get(url)
    temp_data = temp_response.json()
    pokemon = {'name': temp_data['name'], 'image': temp_data['sprites']['front_default']}

    for stat in temp_data['stats']:
        pokemon[stat['stat']['name'].replace('-', '_')] = stat['base_stat']
    return pokemon


def standart_result(current_page: int):
    global multiplier
    pokemons = [
        get_pokemon_data(pokemon_names[index])
        for index in range((current_page - 1) * multiplier, (current_page - 1) * multiplier + multiplier)
    ]
    return pokemons


def search_result(current_page: int, search_pokemons: list):
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


def search_result_names(search_prompt: str):
    global multiplier
    pokemons = []
    for name in pokemon_names:
        if search_prompt in name:
            pokemons.append(name)
    return pokemons


def decrease_hp(players_number: int, opponent_pokemon_number: int):
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


def add_row_to_battles():
    print(current_user.id)
    fight_row = Battles(main_pokemon=session['main_pokemon']['name'],
                        opponent_pokemon=session['opponent_pokemon']['name'],
                        win=winner()['name'],
                        user_id=current_user.id if current_user.is_authenticated else None)
    db.session.add(fight_row)
    db.session.commit()


def clear_session():
    if 'players_number' in session:
        session.pop('players_number')
    if 'opponent_pokemon_number' in session:
        session.pop('opponent_pokemon_number')
    if 'main_pokemon' in session:
        session.pop('main_pokemon')
    if 'opponent_pokemon' in session:
        session.pop('opponent_pokemon')