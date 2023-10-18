import json
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

with open('db.json', encoding='utf-8') as file:
    connect_string = json.load(file)['connection_string']

db = SQLAlchemy()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = connect_string
db.init_app(app)


class Battles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    main_pokemon = db.Column(db.String(150), nullable=False)
    opponent_pokemon = db.Column(db.String(150), nullable=False)
    win = db.Column(db.String(150), nullable=False)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
