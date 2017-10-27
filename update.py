import db
import errors
import time

# Stop updating if Ctrl-C is pressed
try:
    # Update Steam
    print("STEAM")
    for user in db.session.query(db.Steam).all():
        t = time.clock()
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
            sleep_time = 1 - time.clock() + t
            time.sleep(sleep_time if sleep_time > 0 else 0)
    # Update Rocket League
    print("ROCKET LEAGUE")
    for user in db.session.query(db.RocketLeague).all():
        t = time.clock()
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
            sleep_time = 1 - time.clock() + t
            time.sleep(sleep_time if sleep_time > 0 else 0)
    # Update Dota 2
    print("DOTA 2")
    for user in db.session.query(db.Dota).all():
        t = time.clock()
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
            sleep_time = 1 - time.clock() + t
            time.sleep(sleep_time if sleep_time > 0 else 0)
    # Update League of Legends
    print("LEAGUE OF LEGENDS")
    for user in db.session.query(db.LeagueOfLegends).all():
        t = time.clock()
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
            sleep_time = 1 - time.clock() + t
            time.sleep(sleep_time if sleep_time > 0 else 0)
    # Update Osu!
    print("OSU!")
    for user in db.session.query(db.Osu).all():
        t = time.clock()
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
            sleep_time = 1 - time.clock() + t
            time.sleep(sleep_time if sleep_time > 0 else 0)
    # Update Overwatch
    print("OVERWATCH")
    for user in db.session.query(db.Overwatch).all():
        t = time.clock()
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
            sleep_time = 1 - time.clock() + t
            time.sleep(sleep_time if sleep_time > 0 else 0)
except KeyboardInterrupt:
    pass
finally:
    print("Committing...\t\t")
    db.session.commit()
    print("OK")
    db.session.close()