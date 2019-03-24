import db

session = db.Session()
username = input("Nome account: ")
user = session.query(db.Royal).filter_by(username=username).one_or_none()
if user is None:
    user = db.Royal.create(session, username)
session.add(user)
session.flush()
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
    lol = db.LeagueOfLegends.create(user.id, input("League summoner name: "))
except Exception as e:
    print(e)
else:
    session.add(lol)
session.commit()
session.close()
