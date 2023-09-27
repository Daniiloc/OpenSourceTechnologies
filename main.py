import requests
from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap

response = requests.get("https://pokeapi.co/api/v2/pokemon/?limit=1")
data = response.json()
response = requests.get(f"https://pokeapi.co/api/v2/pokemon/?limit={data['count']}")
data = response.json()
pokemonNames = []

for i in data['results']:
    pokemonNames.append(i['name'])

app = Flask(__name__)
Bootstrap(app)


@app.route("/")
def hello_world():
    return render_template("index.html", pokemonList=pokemonNames)


@app.route("/search-result", methods=["POST"])
def search_result():
    result = []
    stroka = request.form['searchLabel']
    for i in pokemonNames:
        if stroka in i:
            result.append(i)
    return render_template("index.html", pokemonList=result)


if __name__ == "__main__":
    app.run()

