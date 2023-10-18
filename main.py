import os
import random
import requests
from models import connect_string, db, Battles
from flask import Flask, render_template, request, session
from flask_bootstrap import Bootstrap


def count_pages(current_page, finale_page):
    left = current_page - 3 if current_page >= 4 else 1
    right = current_page + 3 if finale_page - current_page >= 3 else finale_page
    return list(range(left, right + 1))


def get_pokemon_data(pokemon_name):
    url = f'https://pokeapi.co/api/v2/pokemon/{pokemon_name}/'
    temp_response = requests.get(url)
    temp_data = temp_response.json()
    pokemon = {'name': pokemon_name, 'image': temp_data['sprites']['front_default']}

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


def search_result(current_page, search_prompt):
    global multiplier
    counter = 0
    pokemons = []
    for name in pokemon_names:
        if search_prompt in name:
            if counter < current_page * multiplier + multiplier:
                if current_page * multiplier <= counter:
                    pokemons.append(get_pokemon_data(name))
            else:
                break
            counter += 1

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


response = requests.get('https://pokeapi.co/api/v2/pokemon/?limit=1')
data = response.json()
response = requests.get(f'https://pokeapi.co/api/v2/pokemon/?limit={data["count"]}')
data = response.json()
pokemon_names = []
multiplier = 5

for i in data['results']:
    pokemon_names.append(i['name'])


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = connect_string
db.init_app(app)
Bootstrap(app)


@app.route('/')
def hello():
    page = int(request.args.get('page') if request.args.get('page') else 1)
    search = request.args.get('search_string', '')
    pages = count_pages(page, len(pokemon_names) // multiplier)
    if search != '':
        pokemons = search_result(page, search)
    else:
        pokemons = standart_result(page)

    return render_template(
        'index.html',
        pokemons=pokemons,
        pages=pages,
        max_pages=len(pokemon_names) // multiplier,
        current_page=page,
        search_string=search)


@app.route('/<pokemon_name>')
def pokemon_page(pokemon_name):
    return render_template('pokemon_page.html', pokemon=get_pokemon_data(pokemon_name))


@app.route('/<main_pokemon_name>_battle', methods=['GET', 'POST'])
def battle(main_pokemon_name):
    if request.method == 'GET':
        session.clear()
        session['main_pokemon'] = get_pokemon_data(main_pokemon_name)

        if 'opponent_pokemon' not in session:
            opponent_pokemon_name = \
                random.choice([pokemon for pokemon in pokemon_names if pokemon != session['main_pokemon']['name']])

            session['opponent_pokemon'] = get_pokemon_data(opponent_pokemon_name)

        return render_template('battle.html',
                               main_pokemon=get_pokemon_data(session['main_pokemon']['name']),
                               opponent_pokemon=get_pokemon_data(session['opponent_pokemon']['name']))
    else:
        try:
            players_number = request.form["players_number"]
        except KeyError:
            players_number = None

        if define_global_win():
            fight_row = Battles(main_pokemon=session['main_pokemon']['name'],
                                opponent_pokemon=session['opponent_pokemon']['name'],
                                win=winner()['name'])
            db.session.add(fight_row)
            db.session.commit()
            return render_template('battle.html',
                                   main_pokemon=get_pokemon_data(session['main_pokemon']['name']),
                                   opponent_pokemon=get_pokemon_data(session['opponent_pokemon']['name']),
                                   global_win=define_global_win(),
                                   winner=winner())

        ok = 'ok' in request.form  # True только если кнопка 'ok' после каждого раунда

        if ok and 'players_number' in session:
            session.pop('players_number', None)
            session.pop('opponent_pokemon_number', None)
            return render_template('battle.html',
                                   main_pokemon=get_pokemon_data(session['main_pokemon']['name']),
                                   opponent_pokemon=get_pokemon_data(session['opponent_pokemon']['name']))

        if players_number:
            if players_number.isdigit() and int(players_number) in list(range(1, 11)):
                session['players_number'] = int(players_number)
                if 'opponent_pokemon_number' not in session:
                    opponent_pokemon_number = random.randint(1, 10)
                    session['opponent_pokemon_number'] = opponent_pokemon_number

                round_win = decrease_hp(session['players_number'], session['opponent_pokemon_number'])
                return render_template('battle.html',
                                       main_pokemon=get_pokemon_data(session['main_pokemon']['name']),
                                       opponent_pokemon=get_pokemon_data(session['opponent_pokemon']['name']),
                                       round_win=round_win)


@app.route("/battle-history")
def archive():
    battles = Battles.query.all()
    return render_template('battle_history.html',
                           battles=battles,
                           some_list=['№', 'Покемон', 'Противник', 'Победитель'])


if __name__ == '__main__':
    app.secret_key = os.urandom(24)
    app.run()
