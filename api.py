import io
import ftplib
from datetime import date
from flask import make_response, request

from models import *


def api_pokemon_save(pokemon_name):
    pokemon = get_pokemon_data(pokemon_name)
    folder_name = str(date.today()).replace('-', '').strip()
    text_markdown = (f"# {pokemon['name']}\n\n### Характерисики:\n"
                     f"- HP: {pokemon['hp']}\n- Attack: {pokemon['attack']}\n- Defense: {pokemon['defense']}\n"
                     f"- Special_attack: {pokemon['special_attack']}\n- Special_defense: {pokemon['special_defense']}\n"
                     f"- Speed: {pokemon['speed']}")

    ftp = ftplib.FTP(host=ftp_config['hostname'])
    ftp.login(user=ftp_config['username'], passwd=ftp_config['password'])

    files = ftp.nlst()
    if folder_name not in files:
        ftp.mkd(folder_name)
    ftp.cwd(folder_name)
    ftp.storbinary(f"STOR {pokemon['name']}.md", io.BytesIO(text_markdown.encode('utf-8')))
    ftp.quit()
    return make_response({'result': 'success'}, 201)


def api_list():
    params = ['name']
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


def api_pokemon(pokemon_id):
    return get_pokemon_data(pokemon_id)


def api_fight():
    session.clear()
    if 'main_pokemon' in request.args:
        session['main_pokemon'] = get_pokemon_data(request.args.get('main_pokemon'))
    else:
        session['main_pokemon'] = get_pokemon_data(api_random_pokemon()['id'])
    if 'opponent_pokemon' in request.args:
        session['opponent_pokemon'] = get_pokemon_data(request.args.get('opponent_pokemon'))
    else:
        session['opponent_pokemon'] = get_pokemon_data(api_random_pokemon()['id'])
    return [session['main_pokemon'], session['opponent_pokemon']]


def api_fight_number(number):
    if 'main_pokemon' not in session:
        return make_response({'error': 'No selected pokemon'}, 400)
    if 'opponent_pokemon' not in session:
        return make_response({'error': 'No selected pokemon'}, 400)
    opponent_pokemon_number = random.randint(1, 11)
    decrease_hp(int(number), opponent_pokemon_number)
    return [session['main_pokemon'], session['opponent_pokemon']]


def api_fast_fight():
    if 'main_pokemon' not in session:
        session['main_pokemon'] = get_pokemon_data(random.choice(pokemon_names))
    if 'opponent_pokemon' not in session:
        session['opponent_pokemon'] = get_pokemon_data(random.choice(pokemon_names))
    auto_fight_history()
    return {'main_pokemon': session['main_pokemon'], 'opponent_pokemon': session['opponent_pokemon'],
            'result': winner()['name']}


def api_random_pokemon():
    pokemon_name = pokemon_names[random.randrange(len(pokemon_names))]
    url = f'https://pokeapi.co/api/v2/pokemon/{pokemon_name}/'
    temp_response = requests.get(url)
    temp_data = temp_response.json()
    return {'id': temp_data['id']}
