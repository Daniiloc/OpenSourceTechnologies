import json
import os
import smtplib
import random
from email.mime.text import MIMEText
import requests
from models import connect_string, db, Battles
from flask import Flask, render_template, request, session, redirect, make_response
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


response = requests.get('https://pokeapi.co/api/v2/pokemon/?limit=1')
data = response.json()
response = requests.get(f'https://pokeapi.co/api/v2/pokemon/?limit={data["count"]}')
data = response.json()
pokemon_names = []
multiplier = 5
sleep_seconds = 1

for i in data['results']:
    pokemon_names.append(i['name'])

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = connect_string
db.init_app(app)
Bootstrap(app)


@app.route('/')
def hello():
    session.clear()
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


@app.route('/<pokemon_name>_page')
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
                               opponent_pokemon=get_pokemon_data(session['opponent_pokemon']['name']),
                               auto_fight=False)
    else:
        if 'auto_fight' in request.form:
            history = auto_fight_history()
            fight_row = Battles(main_pokemon=session['main_pokemon']['name'],
                                opponent_pokemon=session['opponent_pokemon']['name'],
                                win=winner()['name'])
            db.session.add(fight_row)
            db.session.commit()
            return render_template('battle.html',
                                   main_pokemon=get_pokemon_data(session['main_pokemon']['name']),
                                   opponent_pokemon=get_pokemon_data(session['opponent_pokemon']['name']),
                                   global_win=define_global_win(),
                                   winner=winner(),
                                   history=history,
                                   auto_fight=True)
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
                                       winner=winner(),
                                       auto_fight=False)

            ok = 'ok' in request.form  # True только если кнопка 'ok' после каждого раунда

            if ok and 'players_number' in session:
                session.pop('players_number', None)
                session.pop('opponent_pokemon_number', None)
                return render_template('battle.html',
                                       main_pokemon=get_pokemon_data(session['main_pokemon']['name']),
                                       opponent_pokemon=get_pokemon_data(session['opponent_pokemon']['name']),
                                       auto_fight=False)

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
                                           round_win=round_win,
                                           auto_fight=False)


@app.route("/battle-history")
def archive():
    battles = Battles.query.all()
    return render_template('battle_history.html',
                           battles=battles,
                           some_list=['№', 'Покемон', 'Противник', 'Победитель'])


@app.route("/email", methods=["POST"])
def email():
    sender = 'danil.n.ermakov@gmail.com'
    password = 'ieuzomkllhlxrspn'
    to_email = request.form.get('email_string')
    message = f'Ваш покемон: {session["main_pokemon"]["name"]}\n' \
              f'Противник: {session["opponent_pokemon"]["name"]}\n' \
              f'Победил: {winner()["name"]}'

    msg = MIMEText(message)
    msg['Subject'] = 'Результат боя'
    msg['From'] = sender
    msg['To'] = to_email

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender, password)
    server.sendmail(sender, to_email, msg.as_string())

    server.quit()
    return redirect('/')


@app.route("/pokemon/list")
def api_list():
    params = []
    result = []
    limit = len(pokemon_names)
    for param in request.args:
        if param == 'limit':
            limit = int(request.args.get(param))
        else:
            params.append(request.args.get(param))

    for name in range(limit):
        pokemon = get_pokemon_data(pokemon_names[name])
        result.append({})
        for key in pokemon:
            if key in params:
                result[-1][key] = pokemon[key]
    return result


@app.route("/pokemon/<id>")
def api_pokemon(id):
    return get_pokemon_data(id)


@app.route("/pokemon/random")
def api_random_pokemon():
    pokemon_name = pokemon_names[random.randrange(len(pokemon_names))]
    url = f'https://pokeapi.co/api/v2/pokemon/{pokemon_name}/'
    temp_response = requests.get(url)
    temp_data = temp_response.json()
    return [temp_data['id']]


@app.route("/fight")
def api_fight():
    session.clear()
    session['main_pokemon'] = request.args.get('main_pokemon')
    session['opponent_pokemon'] = request.args.get('opponent_pokemon')
    return [get_pokemon_data(session['main_pokemon']), get_pokemon_data(session['opponent_pokemon'])]


@app.route("/fight/<number>", methods=['POST'])
def api_fight_number(number):
    if 'main_pokemon' not in session:
        return make_response({'error': 'No selected pokemon'}, 400)
    if 'opponent_pokemon' not in session:
        return make_response({'error': 'No selected pokemon'}, 400)
    opponent_pokemon_number = random.randint(1, 11)
    decrease_hp(number, opponent_pokemon_number)
    return [session['main_pokemon'], session['opponent_pokemon']]


@app.route("/fight/fast")
def api_fast_fight():
    if 'main_pokemon' not in session:
        session['main_pokemon'] = get_pokemon_data(random.choice(pokemon_names))
    if 'opponent_pokemon' not in session:
        session['opponent_pokemon'] = get_pokemon_data(random.choice(pokemon_names))
    auto_fight_history()
    return {'main_pokemon': session['main_pokemon'], 'opponent_pokemon': session['opponent_pokemon'],
            'result': winner()['name']}


if __name__ == '__main__':
    app.secret_key = os.urandom(24)
    app.run()
