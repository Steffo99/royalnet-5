from db import session, Steam, RocketLeague
from time import sleep

def check_for_new_players():
    steam_users = session.query(Steam).all()
    for user in steam_users:
        print(user)
        rl = RocketLeague.check_and_create(user.steam_id)
        if rl is not None:
            session.add(rl)
            sleep(1)
    session.commit()

def update_existing_players():
    rocket_league_players = session.query(RocketLeague).all()
    for player in rocket_league_players:
        player.update()
    session.commit()

if __name__ == "__main__":
    check_for_new_players()
