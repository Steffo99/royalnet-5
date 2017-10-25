import db

user = db.Royal.get_or_create(input("Nome account: "))
db.session.add(user)
db.session.commit()
try:
    steam = db.Steam.get_or_create(user.id, input("Steam ID 1: "))
except KeyboardInterrupt:
    pass
else:
    db.session.add(steam)
try:
    dota = db.Dota.get_or_create(steam.steam_id)
except:
    pass
else:
    db.session.add(dota)
try:
    rl = db.RocketLeague.get_or_create(steam.steam_id)
except:
    pass
else:
    db.session.add(rl)
try:
    osu = db.Osu.get_or_create(user.id, input("Osu! username: "))
except KeyboardInterrupt:
    pass
else:
    db.session.add(osu)
try:
    overwatch = db.Overwatch.get_or_create(user.id, input("Battle.net battletag: "))
except KeyboardInterrupt:
    pass
else:
    db.session.add(overwatch)
try:
    lol = db.LeagueOfLegends.get_or_create(user.id, input("League summoner name: "))
except KeyboardInterrupt:
    pass
else:
    db.session.add(lol)
db.session.commit()
db.session.close()