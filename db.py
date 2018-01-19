import time
import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import Column, BigInteger, Integer, String, Numeric, DateTime, ForeignKey, Float, Enum, create_engine, UniqueConstraint
import requests
from errors import RequestError, NotFoundError, AlreadyExistingError
import re
import enum
from discord import User as DiscordUser
from telegram import User as TelegramUser

# Init the config reader
import configparser
config = configparser.ConfigParser()
config.read("config.ini")

# Init the sqlalchemy engine
engine = create_engine(config["Database"]["database_uri"])
Base = declarative_base(bind=engine)
Session = sessionmaker(bind=engine)

class Royal(Base):
    __tablename__ = "royals"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)

    @staticmethod
    def create(session: Session, username: str):
        r = session.query(Royal).filter_by(username=username).first()
        if r is not None:
            raise AlreadyExistingError(repr(r))
        return Royal(username=username)

    def __repr__(self):
        return f"<Royal {self.username}>"


class Telegram(Base):
    __tablename__ = "telegram"

    royal_id = Column(Integer, ForeignKey("royals.id"), nullable=False)
    royal = relationship("Royal")

    telegram_id = Column(BigInteger, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String)
    username = Column(String)

    @staticmethod
    def create(session: Session, royal_username, telegram_user: TelegramUser):
        t = session.query(Telegram).filter_by(telegram_id=telegram_user.id).first()
        if t is not None:
            raise AlreadyExistingError(repr(t))
        r = session.query(Royal).filter(Royal.username == royal_username).first()
        if r is None:
            raise NotFoundError("No Royal exists with that username")
        t = session.query(Telegram).filter(Telegram.royal_id == r.id).first()
        if t is not None:
            raise AlreadyExistingError(repr(t))
        return Telegram(royal=r,
                        telegram_id=telegram_user.id,
                        first_name=telegram_user.first_name,
                        last_name=telegram_user.last_name,
                        username=telegram_user.username)


    def __repr__(self):
        return f"<Telegram {self.id}>"

    def __str__(self):
        if self.username is not None:
            return f"@{self.username}"
        elif self.last_name is not None:
            return f"{self.first_name} {self.last_name}"
        else:
            return self.first_name


class Steam(Base):
    __tablename__ = "steam"

    royal_id = Column(Integer, ForeignKey("royals.id"), nullable=False)
    royal = relationship("Royal")

    steam_id = Column(String, primary_key=True)
    persona_name = Column(String, nullable=False)
    avatar_hex = Column(String, nullable=False)
    trade_token = Column(String)

    def __repr__(self):
        return f"<Steam {self.steam_id}>"

    def __str__(self):
        if self.persona_name is not None:
            return self.persona_name
        else:
            return self.steam_id

    def avatar_url(self):
        return f"https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/{self.avatar_hex[0:2]}/{self.avatar_hex}.jpg"

    @staticmethod
    def create(session: Session, royal_id: int, steam_id: str):
        s = session.query(Steam).get(steam_id)
        if s is not None:
            raise AlreadyExistingError(repr(s))
        r = requests.get(f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={config['Steam']['api_key']}&steamids={steam_id}")
        if r.status_code != 200:
            raise RequestError(f"Steam returned {r.status_code}")
        j = r.json()
        if len(j) == 0:
            raise NotFoundError(f"The steam_id doesn't match any steam account")
        s = Steam(royal_id=royal_id,
                  steam_id=steam_id,
                  persona_name=j["response"]["players"][0]["personaname"],
                  avatar_hex=re.search(r"https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/../(.+).jpg", j["response"]["players"][0]["avatar"]).group(1))
        return s

    @staticmethod
    def find_trade_token(trade_url):
        return re.search(r"https://steamcommunity\.com/tradeoffer/new/\?partner=[0-9]+&token=(.{8})", trade_url).group(1)

    @staticmethod
    def to_steam_id_2(steam_id):
        # Got this code from a random github gist. It could be completely wrong.
        z = (int(steam_id) - 76561197960265728) // 2
        y = int(steam_id) % 2
        return f"STEAM_0:{y}:{z}"

    @staticmethod
    def to_steam_id_3(steam_id, full=False):
        # Got this code from a random github gist. It could be completely wrong.
        if full:
            return f"[U:1:{int(steam_id) - 76561197960265728}]"
        else:
            return f"{int(steam_id) - 76561197960265728}"

    def update(self):
        r = requests.get(f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={config['Steam']['api_key']}&steamids={self.steam_id}")
        if r.status_code != 200:
            raise RequestError(f"Steam returned {r.status_code}")
        j = r.json()
        self.persona_name = j["response"]["players"][0]["personaname"]
        self.avatar_hex = re.search(r"https://steamcdn-a\.akamaihd\.net/steamcommunity/public/images/avatars/../(.+).jpg", j["response"]["players"][0]["avatar"]).group(1)


class RocketLeague(Base):
    __tablename__ = "rocketleague"

    steam_id = Column(String, ForeignKey("steam.steam_id"), primary_key=True)
    steam = relationship("Steam")

    season = Column(Integer)

    single_rank = Column(Integer)
    single_div = Column(Integer)
    single_mmr = Column(Integer)

    doubles_rank = Column(Integer)
    doubles_div = Column(Integer)
    doubles_mmr = Column(Integer)

    standard_rank = Column(Integer)
    standard_div = Column(Integer)
    standard_mmr = Column(Integer)

    solo_std_rank = Column(Integer)
    solo_std_div = Column(Integer)
    solo_std_mmr = Column(Integer)

    wins = Column(Integer)

    def __repr__(self):
        return f"<RocketLeague {self.steam_id}>"

    @staticmethod
    def create(session: Session, steam_id: str):
        rl = session.query(RocketLeague).get(steam_id)
        if rl is not None:
            raise AlreadyExistingError(repr(rl))
        r = requests.get(f"https://api.rocketleaguestats.com/v1/player?apikey={config['Rocket League']['rlstats_api_key']}&unique_id={str(steam_id)}&platform_id=1")
        if r.status_code == 404:
            raise NotFoundError("The specified user has never played Rocket League")
        elif r.status_code != 200:
            raise RequestError("Rocket League Stats returned {r.status_code}")
        new_record = RocketLeague(steam_id=steam_id)
        new_record.update(data=r.json())
        return new_record

    def update(self, data=None):
        if data is None:
            r = requests.get(f"https://api.rocketleaguestats.com/v1/player?apikey={config['Rocket League']['rlstats_api_key']}&unique_id={self.steam_id}&platform_id=1")
            if r.status_code != 200:
                raise RequestError(f"Rocket League Stats returned {r.status_code}")
            data = r.json()
        # Get current season
        current_season = 0
        for season in data["rankedSeasons"]:
            if int(season) > current_season:
                current_season = int(season)
        if current_season == 0:
            return
        self.season = current_season
        current_season = str(current_season)
        # Get wins
        self.wins = data["stats"]["wins"]
        # Get ranked data
        # Single 1v1
        if "10" in data["rankedSeasons"][current_season]:
            self.single_mmr = data["rankedSeasons"][current_season]["10"]["rankPoints"]
            if data["rankedSeasons"][current_season]["10"]["matchesPlayed"] >= 10:
                self.single_rank = data["rankedSeasons"][current_season]["10"]["tier"]
                self.single_div = data["rankedSeasons"][current_season]["10"]["division"]
            else:
                self.single_rank = None
                self.single_div = None
        # Doubles 2v2
        if "11" in data["rankedSeasons"][current_season]:
            self.doubles_mmr = data["rankedSeasons"][current_season]["11"]["rankPoints"]
            if data["rankedSeasons"][current_season]["11"]["matchesPlayed"] >= 10:
                self.doubles_rank = data["rankedSeasons"][current_season]["11"]["tier"]
                self.doubles_div = data["rankedSeasons"][current_season]["11"]["division"]
            else:
                self.doubles_rank = None
                self.doubles_div = None
        # Standard 3v3
        if "13" in data["rankedSeasons"][current_season]:
            self.standard_mmr = data["rankedSeasons"][current_season]["13"]["rankPoints"]
            if data["rankedSeasons"][current_season]["13"]["matchesPlayed"] >= 10:
                self.standard_rank = data["rankedSeasons"][current_season]["13"]["tier"]
                self.standard_div = data["rankedSeasons"][current_season]["13"]["division"]
            else:
                self.standard_rank = None
                self.standard_div = None
        # Solo Standard 3v3
        if "12" in data["rankedSeasons"][current_season]:
            self.solo_std_mmr = data["rankedSeasons"][current_season]["12"]["rankPoints"]
            if data["rankedSeasons"][current_season]["12"]["matchesPlayed"] >= 10:
                self.solo_std_rank = data["rankedSeasons"][current_season]["12"]["tier"]
                self.solo_std_div = data["rankedSeasons"][current_season]["12"]["division"]
            else:
                self.solo_std_rank = None
                self.solo_std_div = None


class Dota(Base):
    __tablename__ = "dota"

    steam_id = Column(String, ForeignKey("steam.steam_id"), primary_key=True)
    steam = relationship("Steam")

    rank_tier = Column(Integer)

    wins = Column(Integer, nullable=False)
    losses = Column(Integer, nullable=False)

    def get_rank_icon_url(self):
        # Rank icon is determined by the first digit of the rank tier
        return f"https://www.opendota.com/assets/images/dota2/rank_icons/rank_icon_{str(self.rank_tier)[0] if self.rank_tier is not None else '0'}.png"

    def get_rank_stars_url(self):
        # Rank stars are determined by the second digit of the rank tier
        if self.rank_tier is None or str(self.rank_tier)[1] == "0":
            return ""
        return f"https://www.opendota.com/assets/images/dota2/rank_icons/rank_star_{str(self.rank_tier)[1]}.png"

    def get_rank_name(self):
        # This should probably be an enum, but who cares
        if self.rank_tier is None or self.rank_tier < 10:
            return "Unranked"
        number = str(self.rank_tier)[0]
        if number == "1":
            return "Harald"
        elif number == "2":
            return "Guardian"
        elif number == "3":
            return "Crusader"
        elif number == "4":
            return "Archon"
        elif number == "5":
            return "Legend"
        elif number == "6":
            return "Ancient"
        elif number == "7":
            return "Divine"

    def get_rank_number(self):
        if self.rank_tier is None or self.rank_tier < 10:
            return ""
        return str(self.rank_tier)[1]

    @staticmethod
    def create(session: Session, steam_id: int):
        d = session.query(Dota).get(steam_id)
        if d is not None:
            raise AlreadyExistingError(repr(d))
        r = requests.get(f"https://api.opendota.com/api/players/{Steam.to_steam_id_3(steam_id)}")
        if r.status_code != 200:
            raise RequestError("OpenDota returned {r.status_code}")
        data = r.json()
        if "profile" not in data:
            raise NotFoundError("The specified user has never played Dota or has a private match history")
        r = requests.get(f"https://api.opendota.com/api/players/{Steam.to_steam_id_3(steam_id)}/wl")
        if r.status_code != 200:
            raise RequestError("OpenDota returned {r.status_code}")
        wl = r.json()
        new_record = Dota(steam_id=steam_id,
                          rank_tier=data["rank_tier"],
                          wins=wl["win"],
                          losses=wl["lose"])
        return new_record

    def update(self):
        r = requests.get(f"https://api.opendota.com/api/players/{Steam.to_steam_id_3(self.steam_id)}")
        if r.status_code != 200:
            raise RequestError("OpenDota returned {r.status_code}")
        data = r.json()
        r = requests.get(f"https://api.opendota.com/api/players/{Steam.to_steam_id_3(self.steam_id)}/wl")
        if r.status_code != 200:
            raise RequestError("OpenDota returned {r.status_code}")
        wl = r.json()
        self.rank_tier = data["rank_tier"]
        self.wins = wl["win"]
        self.losses = wl["lose"]


class LeagueOfLegendsRanks(enum.Enum):
    BRONZE = 0
    SILVER = 1
    GOLD = 2
    PLATINUM = 3
    DIAMOND = 4
    MASTER = 5
    CHALLENGER = 6


class RomanNumerals(enum.Enum):
    I = 1
    II = 2
    III = 3
    IV = 4
    V = 5


class LeagueOfLegends(Base):
    __tablename__ = "leagueoflegends"

    royal_id = Column(Integer, ForeignKey("royals.id"), nullable=False)
    royal = relationship("Royal")

    summoner_id = Column(BigInteger, primary_key=True)
    summoner_name = Column(String, nullable=False)

    level = Column(Integer, nullable=False)
    solo_division = Column(Enum(LeagueOfLegendsRanks))
    solo_rank = Column(Enum(RomanNumerals))
    flex_division = Column(Enum(LeagueOfLegendsRanks))
    flex_rank = Column(Enum(RomanNumerals))
    twtr_division = Column(Enum(LeagueOfLegendsRanks))
    twtr_rank = Column(Enum(RomanNumerals))

    @staticmethod
    def create(session: Session, royal_id, summoner_name=None, summoner_id=None):
        if summoner_name:
            lol = session.query(LeagueOfLegends).filter(LeagueOfLegends.summoner_name == summoner_name).first()
        elif summoner_id:
            lol = session.query(LeagueOfLegends).get(summoner_id)
        else:
            raise SyntaxError("Neither summoner_name or summoner_id are specified")
        if lol is not None:
            raise AlreadyExistingError(repr(lol))
        # Get the summoner_id
        if summoner_name:
            r = requests.get(f"https://euw1.api.riotgames.com/lol/summoner/v3/summoners/by-name/{summoner_name}?api_key={config['League of Legends']['riot_api_key']}")
        else:
            r = requests.get(f"https://euw1.api.riotgames.com/lol/summoner/v3/summoners/{summoner_id}?api_key={config['League of Legends']['riot_api_key']}")
        if r.status_code != 200:
            return RequestError(f"League of Legends API returned {r.status_code}")
        data = r.json()
        lol = LeagueOfLegends(royal_id=royal_id,
                              summoner_id=data["id"],
                              summoner_name=data["name"],
                              level=data["summonerLevel"])
        lol.update()
        return lol

    def update(self):
        r = requests.get(f"https://euw1.api.riotgames.com/lol/summoner/v3/summoners/{self.summoner_id}?api_key={config['League of Legends']['riot_api_key']}")
        if r.status_code != 200:
            return RequestError(f"League of Legends API returned {r.status_code}")
        data = r.json()
        r = requests.get(f"https://euw1.api.riotgames.com/lol/league/v3/positions/by-summoner/{self.summoner_id}?api_key={config['League of Legends']['riot_api_key']}")
        if r.status_code != 200:
            return RequestError(f"League of Legends API returned {r.status_code}")
        rank = r.json()
        solo_rank = None
        flex_rank = None
        twtr_rank = None
        for league in rank:
            if league["queueType"] == "RANKED_SOLO_5x5":
                solo_rank = league
            elif league["queueType"] == "RANKED_FLEX_SR":
                flex_rank = league
            elif league["queueType"] == "RANKED_FLEX_TT":
                twtr_rank = league
        self.summoner_id = data["id"]
        self.summoner_name = data["name"]
        self.level = data["summonerLevel"]
        if solo_rank is not None:
            self.solo_division = LeagueOfLegendsRanks[solo_rank["tier"]]
            self.solo_rank = RomanNumerals[solo_rank["rank"]]
        else:
            self.solo_division = None
            self.solo_rank = None
        if flex_rank is not None:
            self.flex_division = LeagueOfLegendsRanks[flex_rank["tier"]]
            self.flex_rank = RomanNumerals[flex_rank["rank"]]
        else:
            self.flex_division = None
            self.flex_rank = None
        if twtr_rank is not None:
            self.twtr_division = LeagueOfLegendsRanks[twtr_rank["tier"]]
            self.twtr_rank = RomanNumerals[twtr_rank["rank"]]
        else:
            self.twtr_division = None
            self.twtr_rank = None


class Osu(Base):
    __tablename__ = "osu"

    royal_id = Column(Integer, ForeignKey("royals.id"), nullable=False)
    royal = relationship("Royal")

    osu_id = Column(Integer, primary_key=True)
    osu_name = Column(String, nullable=False)

    std_pp = Column(Float)
    taiko_pp = Column(Float)
    catch_pp = Column(Float)
    mania_pp = Column(Float)

    @staticmethod
    def create(session: Session, royal_id, osu_name):
        o = session.query(Osu).filter(Osu.osu_name == osu_name).first()
        if o is not None:
            raise AlreadyExistingError(repr(o))
        r0 = requests.get(f"https://osu.ppy.sh/api/get_user?k={config['Osu!']['ppy_api_key']}&u={osu_name}&m=0")
        r1 = requests.get(f"https://osu.ppy.sh/api/get_user?k={config['Osu!']['ppy_api_key']}&u={osu_name}&m=1")
        r2 = requests.get(f"https://osu.ppy.sh/api/get_user?k={config['Osu!']['ppy_api_key']}&u={osu_name}&m=2")
        r3 = requests.get(f"https://osu.ppy.sh/api/get_user?k={config['Osu!']['ppy_api_key']}&u={osu_name}&m=3")
        if r0.status_code != 200 or r1.status_code != 200 or r2.status_code != 200 or r3.status_code != 200:
            raise RequestError(f"Osu! API returned an error ({r0.status_code} {r1.status_code} {r2.status_code} {r3.status_code})")
        j0 = r0.json()[0]
        j1 = r1.json()[0]
        j2 = r2.json()[0]
        j3 = r3.json()[0]
        new_record = Osu(royal_id=royal_id,
                         osu_id=j0["user_id"],
                         osu_name=j0["username"],
                         std_pp=j0["pp_raw"],
                         taiko_pp=j1["pp_raw"],
                         catch_pp=j2["pp_raw"],
                         mania_pp=j3["pp_raw"])
        return new_record

    def update(self):
        r0 = requests.get(f"https://osu.ppy.sh/api/get_user?k={config['Osu!']['ppy_api_key']}&u={self.osu_name}&m=0")
        r1 = requests.get(f"https://osu.ppy.sh/api/get_user?k={config['Osu!']['ppy_api_key']}&u={self.osu_name}&m=1")
        r2 = requests.get(f"https://osu.ppy.sh/api/get_user?k={config['Osu!']['ppy_api_key']}&u={self.osu_name}&m=2")
        r3 = requests.get(f"https://osu.ppy.sh/api/get_user?k={config['Osu!']['ppy_api_key']}&u={self.osu_name}&m=3")
        if r0.status_code != 200 or r1.status_code != 200 or r2.status_code != 200 or r3.status_code != 200:
            raise RequestError(
                f"Osu! API returned an error ({r0.status_code} {r1.status_code} {r2.status_code} {r3.status_code})")
        j0 = r0.json()[0]
        j1 = r1.json()[0]
        j2 = r2.json()[0]
        j3 = r3.json()[0]
        self.osu_name = j0["username"]
        self.std_pp = j0["pp_raw"]
        self.taiko_pp = j1["pp_raw"]
        self.catch_pp = j2["pp_raw"]
        self.mania_pp = j3["pp_raw"]


class Discord(Base):
    __tablename__ = "discord"
    __table_args__ = tuple(UniqueConstraint("name", "discriminator"))

    royal_id = Column(Integer, ForeignKey("royals.id"), nullable=False)
    royal = relationship("Royal")

    discord_id = Column(BigInteger, primary_key=True)
    name = Column(String, nullable=False)
    discriminator = Column(Integer, nullable=False)
    avatar_hex = Column(String)

    def __str__(self):
        return f"{self.username}#{self.discriminator}"

    def __repr__(self):
        return f"<Discord user {self.discord_id}>"

    @staticmethod
    def create(session: Session, royal_username, discord_user: DiscordUser):
        d = session.query(Discord).filter(Discord.discord_id == discord_user.id).first()
        if d is not None:
            raise AlreadyExistingError(repr(d))
        r = session.query(Royal).filter(Royal.username == royal_username).first()
        if r is None:
            raise NotFoundError("No Royal exists with that username")
        d = session.query(Discord).filter(Discord.royal_id == r.id).first()
        if d is not None:
            raise AlreadyExistingError(repr(d))
        d = Discord(royal=r,
                    discord_id=discord_user.id,
                    name=discord_user.name,
                    discriminator=discord_user.discriminator,
                    avatar_hex=discord_user.avatar)
        return d

    def mention(self):
        return f"<@{self.id}>"

    def avatar_url(self, size=256):
        if self.avatar_hex is None:
            return "https://discordapp.com/assets/6debd47ed13483642cf09e832ed0bc1b.png"
        return f"https://cdn.discordapp.com/avatars/{self.id}/{self.avatar}.png?size={size}"


class Overwatch(Base):
    __tablename__ = "overwatch"

    royal_id = Column(Integer, ForeignKey("royals.id"), nullable=False)
    royal = relationship("Royal")

    battletag = Column(String, primary_key=True)
    discriminator = Column(Integer, primary_key=True)
    icon = Column(String, nullable=False)

    level = Column(Integer, nullable=False)
    rank = Column(Integer)

    def __str__(self, separator="#"):
        return f"{self.battletag}{separator}{self.discriminator}"

    def __repr__(self):
        return f"<Overwatch {self}>"

    @staticmethod
    def create(session: Session, royal_id, battletag, discriminator=None):
        if discriminator is None:
            battletag, discriminator = battletag.split("#", 1)
        o = session.query(Overwatch).filter_by(battletag=battletag, discriminator=discriminator).first()
        if o is not None:
            raise AlreadyExistingError(repr(o))
        r = requests.get(f"https://owapi.net/api/v3/u/{battletag}-{discriminator}/stats", headers={
            "User-Agent": "Royal-Bot/4.0",
            "From": "ste.pigozzi@gmail.com"
        })
        if r.status_code != 200:
            raise RequestError(f"OWAPI.net returned {r.status_code}")
        try:
            j = r.json()["eu"]["stats"]["quickplay"]["overall_stats"]
        except TypeError:
            raise RequestError("Something went wrong when retrieving the stats.")
        o = Overwatch(royal_id=royal_id,
                      battletag=battletag,
                      discriminator=discriminator,
                      icon=re.search(r"https://.+\.cloudfront\.net/game/unlocks/(0x[0-9A-F]+)\.png", j["avatar"]).group(1),
                      level=j["prestige"] * 100 + j["level"],
                      rank=j["comprank"])
        return o

    def icon_url(self):
        return f"https://d1u1mce87gyfbn.cloudfront.net/game/unlocks/{self.icon}.png"

    def update(self):
        r = requests.get(f"https://owapi.net/api/v3/u/{self.battletag}-{self.discriminator}/stats", headers={
            "User-Agent": "Royal-Bot/4.0",
            "From": "ste.pigozzi@gmail.com"
        })
        if r.status_code != 200:
            raise RequestError(f"OWAPI.net returned {r.status_code}")
        try:
            j = r.json()["eu"]["stats"]["quickplay"]["overall_stats"]
        except TypeError:
            raise RequestError("Something went wrong when retrieving the stats.")
        self.icon = re.search(r"https://.+\.cloudfront\.net/game/unlocks/(0x[0-9A-F]+)\.png", j["avatar"]).group(1)
        self.level = j["prestige"] * 100 + j["level"]
        self.rank = j["comprank"]


class Diario(Base):
    __tablename__ = "diario"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    saver_id = Column(Integer, ForeignKey("telegram.telegram_id"))
    saver = relationship("Telegram", foreign_keys=saver_id)
    author_id = Column(Integer, ForeignKey("telegram.telegram_id"))
    author = relationship("Telegram", foreign_keys=author_id)
    text = Column(String)

    def __repr__(self):
        return f"<Diario {self.id}>"

    def __str__(self):
        return f"{self.id} - {self.timestamp} - {self.author}: {self.text}"

    @staticmethod
    def import_from_json(file):
        import json
        session = Session()
        file = open(file, "r")
        j = json.load(file)
        for entry in j:
            if "sender" in entry:
                author = session.query(Telegram).filter_by(username=entry["sender"].lstrip("@")).first()
            else:
                author = None
            d = Diario(timestamp=datetime.datetime.fromtimestamp(float(entry["timestamp"])),
                       author=author,
                       text=entry["text"])
            print(d)
            session.add(d)
        session.commit()
        session.close()


# If run as script, create all the tables in the db
if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)