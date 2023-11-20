import os
import unittest

from dotenv import load_dotenv

from main import app
from models import search_result_names


class TestApiMethods(unittest.TestCase):

    def setUp(self):
        self.test_client = app.test_client()

    # Тест получения информации о N-ом количестве покемонов
    def test_api_pokemon_list(self):
        for limit in range(1, 52, 7):
            result = self.test_client.get(f'/api/pokemon/list?limit={limit}').json
            self.assertEquals(len(result), limit)
        for param in ['hp', 'attack', 'defense', 'special_attack', 'special_defense', 'speed']:
            result = self.test_client.get(f'/api/pokemon/list?limit=1&param1={param}').json
            self.assertTrue(param in result[0].keys())

    # Тест получения информации о покемоне
    def test_api_pokemon(self):
        id_name = {1: 'bulbasaur', 2: 'ivysaur', 3: 'venusaur', 4: 'charmander', 5: 'charmeleon', 6: 'charizard'}
        for pokemon_id, pokemon_name in id_name.items():
            result = self.test_client.get(f'/api/pokemon/{pokemon_id}').json
            self.assertEquals(result['name'], pokemon_name)
        # Тест получения id рандомного покемона
        self.assertTrue(isinstance(self.test_client.get('/api/pokemon/random').json['id'], int))

    # Тест создания сессии битвы
    def test_api_fight(self):
        result = self.test_client.get('/api/fight').json
        self.assertTrue(len(result) == 2)
        self.assertTrue(result[0]['name'] != result[1]['name'])
        for param in ['hp', 'attack', 'defense', 'special_attack', 'special_defense', 'speed']:
            self.assertTrue(param in result[0].keys())
            self.assertTrue(param in result[1].keys())
        result = self.test_client.get('/api/fight?main_pokemon=bulbasaur&opponent_pokemon=charmander').json
        self.assertTrue(result[0]['name'] == 'bulbasaur')
        self.assertTrue(result[1]['name'] == 'charmander')

    # Тест автоматической битвы
    def test_api_fight_fast(self):
        result = self.test_client.get('/api/fight/fast').json
        self.assertTrue(result['main_pokemon']['hp'] <= 0 or result['opponent_pokemon']['hp'] <= 0)
        if result['main_pokemon']['hp'] > 0:
            self.assertTrue(result['main_pokemon']['name'] == result['result'])
        else:
            self.assertTrue(result['opponent_pokemon']['name'] == result['result'])

    # Тест проверки раунда
    def test_api_fight_round(self):
        result = self.test_client.get('/api/fight').json
        result_2 = self.test_client.post('/api/fight/5').json
        self.assertTrue(result[0]['hp'] > result_2[0]['hp'] or result[1]['hp'] > result_2[1]['hp'])

    def test_search(self):
        result = search_result_names('aaaaaaaaaaaa')
        self.assertTrue(len(result) == 0)
        result = search_result_names('ardo')
        self.assertTrue(len(result) == 1)
        self.assertTrue('rampardos' in result)
        result = search_result_names('bulb')
        self.assertTrue(len(result) == 2)
        self.assertTrue('bulbasaur' in result)
        self.assertTrue('tadbulb' in result)
        result = search_result_names('ark')
        self.assertTrue(len(result) == 4)
        self.assertTrue('darkrai' in result)
        self.assertTrue('zoroark' in result)
        self.assertTrue('carkol' in result)
        self.assertTrue('zoroark-hisui' in result)


dotenv_path = os.path.join(os.path.dirname(__file__), '../.env.local')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
