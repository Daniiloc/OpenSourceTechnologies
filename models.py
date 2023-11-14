import os
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

dotenv_path = os.path.join(os.path.dirname(__file__), '.env.local')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

db = SQLAlchemy()


class Battles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    main_pokemon = db.Column(db.String(150), nullable=False)
    opponent_pokemon = db.Column(db.String(150), nullable=False)
    win = db.Column(db.String(150), nullable=False)
