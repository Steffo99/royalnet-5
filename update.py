import db
import errors
import time

# Create a new database session
session = db.Session()

# Stop updating if Ctrl-C is pressed
try:
    # Update Steam
    print("STEAM")
    for user in session.query(db.Steam).all():
        print(f"Updating {user.royal.username}", end="\t\t", flush=True)
        try:
            user.update()
        except errors.RequestError:
            print("Request Error")
        except errors.NotFoundError:
            print("Not Found Error (?)")
        else:
            print("OK")
        finally:
            time.sleep(1)
    # Update Rocket League
    print("ROCKET LEAGUE")
    for user in session.query(db.RocketLeague).all():
        print(f"Updating {user.steam.royal.username}", end="\t\t", flush=True)
        try:
            user.update()
        except errors.RequestError:
            print("Request Error")
        except errors.NotFoundError:
            print("Not Found Error (?)")
        else:
            print("OK")
        finally:
            time.sleep(1)
    # Update Dota 2
    print("DOTA 2")
    for user in session.query(db.Dota).all():
        print(f"Updating {user.steam.royal.username}", end="\t\t", flush=True)
        try:
            user.update()
        except errors.RequestError:
            print("Request Error")
        except errors.NotFoundError:
            print("Not Found Error (?)")
        else:
            print("OK")
        finally:
            time.sleep(1)
    # Update League of Legends
    print("LEAGUE OF LEGENDS")
    for user in session.query(db.LeagueOfLegends).all():
        print(f"Updating {user.royal.username}", end="\t\t", flush=True)
        try:
            user.update()
        except errors.RequestError:
            print("Request Error")
        except errors.NotFoundError:
            print("Not Found Error (?)")
        else:
            print("OK")
        finally:
            time.sleep(1)
    # Update Osu!
    print("OSU!")
    for user in session.query(db.Osu).all():
        print(f"Updating {user.royal.username}", end="\t\t", flush=True)
        try:
            user.update()
        except errors.RequestError:
            print("Request Error")
        except errors.NotFoundError:
            print("Not Found Error (?)")
        else:
            print("OK")
        finally:
            time.sleep(1)

except KeyboardInterrupt:
    pass
finally:
    print("Committing...\t\t")
    session.commit()
    print("OK")