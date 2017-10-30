import db

session = db.Session()
user = db.Royal.create(session, input("Nome account: "))
session.add(user)
session.commit()
try:
    steam = db.Steam.create(session, user.id, input("Steam ID 1: "))
except Exception as e:
    print(e)
else:
    session.add(steam)
try:
    dota = db.Dota.create(session, steam.steam_id)
except Exception as e:
    print(e)
else:
    session.add(dota)
try:
    rl = db.RocketLeague.create(session, steam.steam_id)
except Exception as e:
    print(e)
else:
    session.add(rl)
try:
    osu = db.Osu.create(session, user.id, input("Osu! username: "))
except Exception as e:
    print(e)
else:
    session.add(osu)
try:
    overwatch = db.Overwatch.create(session, user.id, input("Battle.net battletag: "))
except Exception as e:
    print(e)
else:
    session.add(overwatch)
try:
    lol = db.LeagueOfLegends.create(session, user.id, input("League summoner name: "))
except Exception as e:
    print(e)
else:
    session.add(lol)
session.commit()
session.close()