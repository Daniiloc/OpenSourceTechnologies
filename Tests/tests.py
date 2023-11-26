import os
import sys
import unittest, ftplib
from datetime import date
from io import StringIO

import flask_unittest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.webdriver import WebDriver

import load_env
from main import app
from models import search_result_names, multiplier


class TestApiMethods(unittest.TestCase):

    def setUp(self):
        self.test_client = app.test_client()
        self.ftp = ftplib.FTP(host=os.environ.get('FTP_HOSTNAME'))
        self.ftp.login(user=os.environ.get('FTP_USERNAME'), passwd=os.environ.get('FTP_PASSWORD'))

    # Тест получения информации о N-ом количестве покемонов
    def test_api_pokemon_list(self):
        for limit in range(1, 16, 7):
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

    def test_api_ftp(self):
        poke_id = 1
        response = self.test_client.post(f'/api/{poke_id}/save')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')
        data = response.json
        poke_name = 'bulbasaur'

        folder_name = str(date.today()).replace('-', '').strip()
        self.assertTrue(folder_name in self.ftp.nlst())
        self.ftp.cwd(folder_name)
        self.assertTrue(f'{poke_name}.md' in self.ftp.nlst())

        tmp = sys.stdout
        res = StringIO()
        sys.stdout = res
        self.ftp.retrlines(f'RETR {poke_name}.md')
        sys.stdout = tmp
        text = res.getvalue()
        self.assertTrue(f'# {poke_name}' in text)


class TestBySelenium(flask_unittest.LiveTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = WebDriver()
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        self.test_client = app.test_client()

    def test_index_page(self):
        self.selenium.get(f'http://{os.environ.get("APP_HOST")}:{os.environ.get("APP_PORT")}/')
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, "body")
        )
        response = self.test_client.get(f'/api/pokemon/list?limit={multiplier}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = response.json
        cards = self.selenium.find_elements(By.CLASS_NAME, "card")
        self.assertTrue(len(cards) == len(data))
        pagions_elements = self.selenium.find_elements(By.CLASS_NAME, "page-item")
        self.assertTrue(pagions_elements[0].text == str(1))
        self.assertTrue(pagions_elements[1].text == str(2))
        self.assertTrue(pagions_elements[-1].text == 'Следующая')
        self.selenium.get(f'http://{os.environ.get("APP_HOST")}:{os.environ.get("APP_PORT")}/?page=2')
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, "body")
        )
        pagions_elements = self.selenium.find_elements(By.CLASS_NAME, "page-item")
        self.assertTrue(pagions_elements[0].text == 'Предыдущая')
        self.assertTrue(pagions_elements[1].text == str(1))
        self.assertTrue(pagions_elements[-1].text == 'Следующая')

    def test_poke_page(self):
        pokemon_name = 'bulbasaur'
        self.selenium.get(f'http://{os.environ.get("APP_HOST")}:{os.environ.get("APP_PORT")}/{pokemon_name}_page')
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, "body")
        )
        response = self.test_client.get(f'/api/pokemon/{pokemon_name}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = response.json

        cards_body = self.selenium.find_elements(By.CLASS_NAME, "card-body")
        poke_name = cards_body[0].find_element(By.TAG_NAME, "h5").text
        poke_info_spans = cards_body[0].find_elements(By.TAG_NAME, "span")
        poke_info = [poke_ch.text for poke_ch in poke_info_spans]
        self.assertEqual(poke_name, pokemon_name)
        self.assertEqual(poke_info, [
            f"HP: {data['hp']}", f"Attack: {data['attack']}", f"Defense: {data['defense']}",
            f"Special-attack: {data['special_attack']}", f"Special-defense: {data['special_defense']}",
            f"Speed: {data['speed']}"
        ])

    def test_poke_search(self):
        search_promt = 'ark'
        self.selenium.get(f'http://{os.environ.get("APP_HOST")}:{os.environ.get("APP_PORT")}/')
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, "body")
        )
        search_input = self.selenium.find_element(By.NAME, "search_string")
        search_input.send_keys(search_promt)
        self.selenium.find_element(By.XPATH, '//button[text()="Поиск"]').click()
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, "body")
        )

        response = search_result_names(search_promt)
        data = response

        cards = self.selenium.find_elements(By.CLASS_NAME, "card")
        self.assertTrue(len(cards) == (len(data) if len(data) <= 5 else 5))
        pagions_elements = self.selenium.find_elements(By.CLASS_NAME, "page-item")
        self.assertTrue(len(pagions_elements) == 1)

    def test_move_player_in_fight(self):
        number = 2
        self.selenium.get(f'http://{os.environ.get("APP_HOST")}:{os.environ.get("APP_PORT")}/')
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, 'body')
        )
        self.selenium.find_element(By.XPATH, '//button[text()="Битва"]').click()
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, 'body')
        )
        select_number_input = self.selenium.find_element(By.NAME, 'players_number')
        select_number_input.send_keys(number)
        self.selenium.find_element(By.ID, 'confirm_button').click()
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, 'body')
        )
        player_span = self.selenium.find_element(By.ID, 'player_span')
        self.assertTrue(player_span.text == str(number))

    def test_history(self):
        self.selenium.get(f'http://{os.environ.get("APP_HOST")}:{os.environ.get("APP_PORT")}/')
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, 'body')
        )
        self.selenium.find_element(By.ID, 'history').click()
        WebDriverWait(self.selenium, 10).until(
            lambda driver: driver.find_element(By.TAG_NAME, 'body')
        )
        self.assertTrue(self.selenium.find_element(By.TAG_NAME, 'table'))
        self.assertTrue(self.selenium.find_element(By.ID, 'return'))


if __name__ == '__main__':
    load_env.load_environment()
    suite = flask_unittest.LiveTestSuite(app)
    suite.addTest(unittest.makeSuite(TestBySelenium))
    suite.addTest(unittest.makeSuite(TestApiMethods))
    unittest.TextTestRunner(verbosity=2).run(suite)
