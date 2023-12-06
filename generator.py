import random as rd
from faker import Faker
from models import *


def generate_data(quantity: int):
    fake = Faker()

    for _ in range(quantity):
        main = rd.choice(pokemon_names)
        opponent_pokemon = rd.choice(pokemon_names)
        a = fake.date_time_between(start_date='-2w', end_date='now')
        battle = Battles(main_pokemon=main,
                         opponent_pokemon=opponent_pokemon,
                         win=rd.choice([main, opponent_pokemon]),
                         date=a,
                         rounds=rd.randint(1, 5))
        db.session.add(battle)

    db.session.commit()
    return 0
