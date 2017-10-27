import db

user = db.Royal.create(input("Nome account: "))
db.session.add(user)
db.session.commit()
try:
    steam = db.Steam.create(user.id, input("Steam ID 1: "))
except Exception as e:
    print(e)
else:
    db.session.add(steam)
try:
    dota = db.Dota.create(steam.steam_id)
except Exception as e:
    print(e)
else:
    db.session.add(dota)
try:
    rl = db.RocketLeague.create(steam.steam_id)
except Exception as e:
    print(e)
else:
    db.session.add(rl)
try:
    osu = db.Osu.create(user.id, input("Osu! username: "))
except Exception as e:
    print(e)
else:
    db.session.add(osu)
try:
    overwatch = db.Overwatch.create(user.id, input("Battle.net battletag: "))
except Exception as e:
    print(e)
else:
    db.session.add(overwatch)
try:
    lol = db.LeagueOfLegends.create(user.id, input("League summoner name: "))
except Exception as e:
    print(e)
else:
    db.session.add(lol)
db.session.commit()
db.session.close()