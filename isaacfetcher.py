import steamleaderboards
import datetime
import db
import time
import telegram
import configparser


def dates_generator(last_date: datetime.date):
    date = datetime.date.today()
    while True:
        if date < last_date:
            return
        yield date
        date -= datetime.timedelta(days=1)


session = db.Session()
players = session.query(db.BindingOfIsaac).all()

config = configparser.ConfigParser()
config.read("config.ini")

print("Fetching leaderboardgroup...")
isaac = steamleaderboards.LeaderboardGroup(250900)

telegram_bot = telegram.Bot(config["Telegram"]["bot_token"])

for date in dates_generator(datetime.date(year=2017, month=1, day=3)):
    lb_name = "{year:04d}{month:02d}{day:02d}_scores+".format(year=date.year, month=date.month, day=date.day)
    print(f"Fetching {lb_name}...")
    leaderboard = isaac.get(name=lb_name)
    print(f"Finding players...")
    runs = []
    for player in players:
        entry = leaderboard.find_entry(player.steam_id)
        if entry is None:
            continue
        print(f"Found new entry: {entry}")
        run = db.BindingOfIsaacRun(player=player, score=entry.score, date=date)
        runs.append(run)
        session.add(run)
    if len(runs) > 1:
        runs.sort(key=lambda x: x.score)
        best = runs[-1]
        best.player.daily_victories += 1
        try:
            telegram_bot.send_message(config["Telegram"]["main_group"],
                                      f"🏆 **{best.player.steam.persona_name}** ha vinto la Daily Run di Isaac del {date.isoformat()}!",
                                      parse_mode="HTML", disable_web_page_preview=True, disable_notification=True)
        except Exception:
            pass
    session.commit()
    print("Sleeping 5s...")
    time.sleep(5)
