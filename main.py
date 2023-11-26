import smtplib
from email.mime.text import MIMEText
from flask_bootstrap import Bootstrap

import api
from models import *
from flask_caching import Cache, CachedResponse
from flask import Flask, render_template, request, session, redirect, make_response, flash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql://{os.environ.get('POSTGRES_USER')}"
    f":{os.environ.get('POSTGRES_PASSWORD')}"
    f"@{os.environ.get('POSTGRES_HOST')}"
    f":{os.environ.get('POSTGRES_PORT')}"
    f"/{os.environ.get('POSTGRES_DB')}"
)
cache = Cache(
    app,
    config={
        "CACHE_TYPE": redis_config["CACHE_TYPE"],
        "CACHE_KEY_PREFIX": redis_config["CACHE_KEY_PREFIX"],
        "CACHE_REDIS_HOST": redis_config["CACHE_REDIS_HOST"],
        "CACHE_REDIS_PORT": redis_config["CACHE_REDIS_PORT"],
        "CACHE_REDIS_URL": redis_config["CACHE_REDIS_URL"]
    }
)
db.init_app(app)
Bootstrap(app)


@app.route('/clear_cache')
def clear_cache():
    cache.clear()
    return 'Cache cleared'


@app.route('/')
def hello():
    session.clear()
    page = int(request.args.get('page') if request.args.get('page') else 1)
    search = request.args.get('search_string', '')
    if search != '':
        pokemons = search_result_names(search)
        max_pages = len(pokemons) // multiplier if len(pokemons) // multiplier > 0 else 1
        pages = count_pages(page, max_pages)
        pokemons = search_result(page, pokemons)
    else:
        pages = count_pages(page, len(pokemon_names) // multiplier)
        pokemons = cache.get(str(page))
        if pokemons:
            return CachedResponse(
                response=make_response(
                    render_template(
                        'index.html',
                        pokemons=pokemons,
                        pages=pages,
                        max_pages=len(pokemon_names) // multiplier,
                        current_page=page,
                        search_string=search)
                ),
                timeout=50,
            )
        cache.set(str(page), standart_result(page))
        pokemons = standart_result(page)
        max_pages = len(pokemon_names) // multiplier
    return render_template(
        'index.html',
        pokemons=pokemons,
        pages=pages,
        max_pages=max_pages,
        current_page=page,
        search_string=search)


@app.route('/<pokemon_name>_page')
@cache.cached()
def pokemon_page(pokemon_name):
    pokemon = cache.get(pokemon_name)
    if pokemon:
        return CachedResponse(
            response=make_response(render_template('pokemon_page.html', pokemon=pokemon),
                                   timeout=50,
                                   )
        )
    cache.set(pokemon_name, get_pokemon_data(pokemon_name))
    return render_template('pokemon_page.html', pokemon=get_pokemon_data(pokemon_name))


@app.route('/<pokemon_name>_page/save', methods=['POST'])
def pokemon_page_save(pokemon_name):
    save_response = requests.post(f'{request.host_url}api/{pokemon_name}/save')
    if save_response.status_code == 201:
        flash('Файл успешно создан', 'info')
    else:
        flash('Не удалось создать файл', 'info')
    return redirect(f'/{pokemon_name}_page')


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
    sender = email_config['sender']
    password = email_config['sender']
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


@app.route("/api/<pokemon_name>/save", methods=['POST'])
def api_pokemon_save(pokemon_name):
    return api.api_pokemon_save(pokemon_name)


@app.route("/api/pokemon/list")
def api_list():
    return api.api_list()


@app.route("/api/pokemon/<pokemon_id>")
def api_pokemon(pokemon_id):
    return api.api_pokemon(pokemon_id)


@app.route("/api/pokemon/random")
def api_random_pokemon():
    return api.api_random_pokemon()


@app.route("/api/fight")
def api_fight():
    return api.api_fight()


@app.route("/api/fight/<number>", methods=['POST'])
def api_fight_number(number):
    return api.api_fight_number(number)


@app.route("/api/fight/fast")
def api_fast_fight():
    return api.api_fast_fight()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host=os.environ.get('APP_HOST'), port=os.environ.get('APP_PORT'))
