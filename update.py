import db
import errors
import time

session = None
# Stop updating if Ctrl-C is pressed
try:
    while True:
        session = db.Session()
        # Update Steam
        print("STEAM")
        for user in session.query(db.Steam).all():
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
        for user in session.query(db.RocketLeague).all():
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
        for user in session.query(db.Dota).all():
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
        for user in session.query(db.LeagueOfLegends).all():
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
        for user in session.query(db.Osu).all():
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
        for user in session.query(db.Overwatch).all():
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
        print("Committing...\t\t")
        session.commit()
        print("OK")
        print("Closing...\n\n")
        session.close()
        print("OK")
        print("Waiting 1800s...\t\t")
        for i in range(0, 20):
            time.sleep(90)
            print("█")
except KeyboardInterrupt:
    pass
finally:
    print("Closing...")
    try:
        session.close()
    except Exception:
        print("Maybe")
