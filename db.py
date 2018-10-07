import datetime
import logging
import os
import typing
import coloredlogs
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Column, BigInteger, Integer, String, DateTime, ForeignKey, Float, Enum, create_engine, UniqueConstraint, PrimaryKeyConstraint, Boolean, or_, LargeBinary, Text, Date, func, desc
import requests
from errors import RequestError, NotFoundError, AlreadyExistingError
import re
import enum
from discord import User as DiscordUser
from telegram import User as TelegramUser
import loldata

# Init the config reader
import configparser
config = configparser.ConfigParser()
config.read("config.ini")

# Init the sqlalchemy engine
engine = create_engine(config["Database"]["database_uri"])
Base = declarative_base(bind=engine)
Session = sessionmaker(bind=engine)

logging.getLogger().disabled = True
logger = logging.getLogger(__name__)
os.environ["COLOREDLOGS_LOG_FORMAT"] = "%(asctime)s %(levelname)s %(name)s %(message)s"
coloredlogs.install(level="DEBUG", logger=logger)


class Royal(Base):
    __tablename__ = "royals"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(LargeBinary)
    role = Column(String)
    fiorygi = Column(Integer, default=0)
    member_since = Column(Date)

    @staticmethod
    def create(session: Session, username: str):
        r = session.query(Royal).filter_by(username=username).first()
        if r is not None:
            raise AlreadyExistingError(repr(r))
        return Royal(username=username)

    def __repr__(self):
        return f"<db.Royal {self.username}>"


class Telegram(Base):
    __tablename__ = "telegram"

    royal_id = Column(Integer, ForeignKey("royals.id"))
    royal = relationship("Royal", backref="telegram", lazy="joined")

    telegram_id = Column(BigInteger, primary_key=True)
    first_name = Column(String)
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
        return f"<db.Telegram {self.telegram_id}>"

    def mention(self):
        if self.username is not None:
            return f"@{self.username}"
        else:
            return self.first_name

    def __str__(self):
        if self.username is not None:
            return self.username
        elif self.last_name is not None:
            return f"{self.first_name} {self.last_name}"
        else:
            return self.first_name


class Steam(Base):
    __tablename__ = "steam"

    royal_id = Column(Integer, ForeignKey("royals.id"))
    royal = relationship("Royal", backref="steam", lazy="joined")

    steam_id = Column(String, primary_key=True)
    persona_name = Column(String)
    avatar_hex = Column(String)
    trade_token = Column(String)
    most_played_game_id = Column(BigInteger)

    def __repr__(self):
        if not self.persona_name:
            return f"<db.Steam {self.steam_id}>"
        return f"<db.Steam {self.persona_name}>"

    def __str__(self):
        if self.persona_name is not None:
            return self.persona_name
        else:
            return self.steam_id

    def most_played_game_url(self):
        return f"https://steamcdn-a.akamaihd.net/steam/apps/{self.most_played_game_id}/header.jpg"

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

    def update(self, raise_if_private: bool=False):
        r = requests.get(f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={config['Steam']['api_key']}&steamids={self.steam_id}")
        if r.status_code != 200:
            raise RequestError(f"Steam returned {r.status_code}")
        j = r.json()
        self.persona_name = j["response"]["players"][0]["personaname"]
        self.avatar_hex = re.search(r"https://steamcdn-a\.akamaihd\.net/steamcommunity/public/images/avatars/../(.+).jpg", j["response"]["players"][0]["avatar"]).group(1)
        r = requests.get(f"http://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/?key={config['Steam']['api_key']}&steamid={self.steam_id}&format=json")
        if r.status_code != 200:
            raise RequestError(f"Steam returned {r.status_code}")
        j = r.json()
        if "response" not in j \
            or "games" not in j["response"] \
            or len(j["response"]["games"]) < 1:
            if raise_if_private:
                raise RequestError(f"Game data is private")
            return
        self.most_played_game_id = j["response"]["games"][0]["appid"]


class RocketLeague(Base):
    __tablename__ = "rocketleague"

    steam_id = Column(String, ForeignKey("steam.steam_id"), primary_key=True)
    steam = relationship("Steam", backref="rl", lazy="joined")

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
        return f"<db.RocketLeague {self.steam_id}>"

    def update(self, data=None):
        raise NotImplementedError("rlstats API is no longer available.")

    def solo_rank_image(self):
        if self.single_rank is None:
            rank = 0
        else:
            rank = self.single_rank
        return f"https://rocketleaguestats.com/assets/img/rocket_league/ranked/season_four/{rank}.png"

    def doubles_rank_image(self):
        if self.doubles_rank is None:
            rank = 0
        else:
            rank = self.doubles_rank
        return f"https://rocketleaguestats.com/assets/img/rocket_league/ranked/season_four/{rank}.png"

    def standard_rank_image(self):
        if self.standard_rank is None:
            rank = 0
        else:
            rank = self.standard_rank
        return f"https://rocketleaguestats.com/assets/img/rocket_league/ranked/season_four/{rank}.png"

    def solo_std_rank_image(self):
        if self.solo_std_rank is None:
            rank = 0
        else:
            rank = self.solo_std_rank
        return f"https://rocketleaguestats.com/assets/img/rocket_league/ranked/season_four/{rank}.png"


class Dota(Base):
    __tablename__ = "dota"

    steam_id = Column(String, ForeignKey("steam.steam_id"), primary_key=True)
    steam = relationship("Steam", backref="dota", lazy="joined")

    rank_tier = Column(Integer)

    wins = Column(Integer)
    losses = Column(Integer)

    most_played_hero = Column(Integer)

    def __repr__(self):
        return f"<db.Dota {self.steam_id}>"

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
    def create(session: Session, steam_id: int) -> "Dota":
        d = session.query(Dota).get(steam_id)
        if d is not None:
            raise AlreadyExistingError(repr(d))
        r = requests.get(f"https://api.opendota.com/api/players/{Steam.to_steam_id_3(steam_id)}")
        if r.status_code != 200:
            raise RequestError("OpenDota returned {r.status_code}")
        data = r.json()
        if "profile" not in data:
            raise NotFoundError("The specified user has never played Dota or has a private match history")
        new_record = Dota(steam_id=str(steam_id))
        new_record.update()
        return new_record

    def update(self) -> bool:
        r = requests.get(f"https://api.opendota.com/api/players/{Steam.to_steam_id_3(self.steam_id)}")
        if r.status_code != 200:
            raise RequestError("OpenDota / returned {r.status_code}")
        data = r.json()
        r = requests.get(f"https://api.opendota.com/api/players/{Steam.to_steam_id_3(self.steam_id)}/wl")
        if r.status_code != 200:
            raise RequestError("OpenDota /wl returned {r.status_code}")
        wl = r.json()
        r = requests.get(f"https://api.opendota.com/api/players/{Steam.to_steam_id_3(self.steam_id)}/heroes")
        if r.status_code != 200:
            raise RequestError("OpenDota /heroes returned {r.status_code}")
        heroes = r.json()
        changed = self.rank_tier != data["rank_tier"]
        self.rank_tier = data["rank_tier"]
        self.wins = wl["win"]
        self.losses = wl["lose"]
        self.most_played_hero = heroes[0]["hero_id"]
        return changed


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

    royal_id = Column(Integer, ForeignKey("royals.id"))
    royal = relationship("Royal", backref="lol", lazy="joined")

    summoner_id = Column(BigInteger, primary_key=True)
    account_id = Column(BigInteger)
    summoner_name = Column(String)

    level = Column(Integer)
    solo_division = Column(Enum(LeagueOfLegendsRanks))
    solo_rank = Column(Enum(RomanNumerals))
    flex_division = Column(Enum(LeagueOfLegendsRanks))
    flex_rank = Column(Enum(RomanNumerals))
    twtr_division = Column(Enum(LeagueOfLegendsRanks))
    twtr_rank = Column(Enum(RomanNumerals))

    highest_mastery_champ = Column(Integer)

    def __repr__(self):
        if not self.summoner_name:
            return f"<LeagueOfLegends {self.summoner_id}>"
        return f"<LeagueOfLegends {(''.join([x if x.isalnum else '' for x in self.summoner_name]))}>"

    def update(self) -> bool:
        r = requests.get(f"https://euw1.api.riotgames.com/lol/summoner/v3/summoners/{self.summoner_id}?api_key={config['League of Legends']['riot_api_key']}")
        if r.status_code != 200:
            raise RequestError(f"League of Legends API /summoner returned {r.status_code}")
        data = r.json()
        r = requests.get(f"https://euw1.api.riotgames.com/lol/league/v3/positions/by-summoner/{self.summoner_id}?api_key={config['League of Legends']['riot_api_key']}")
        if r.status_code != 200:
            raise RequestError(f"League of Legends API /league returned {r.status_code}")
        rank = r.json()
        r = requests.get(f"https://euw1.api.riotgames.com/lol/champion-mastery/v3/champion-masteries/by-summoner/{self.summoner_id}?api_key={config['League of Legends']['riot_api_key']}")
        if r.status_code != 200:
            raise RequestError(f"League of Legends API /champion-mastery returned {r.status_code}")
        mastery = r.json()
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
        self.account_id = data["accountId"]
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
        self.highest_mastery_champ = mastery[0]["championId"]

    def highest_mastery_champ_name(self):
        champ = loldata.get_champ_by_key(self.highest_mastery_champ)
        return champ["name"]

    def highest_mastery_champ_image(self):
        champ = loldata.get_champ_by_key(self.highest_mastery_champ)
        return loldata.get_champ_icon(champ["name"])


class Osu(Base):
    __tablename__ = "osu"

    royal_id = Column(Integer, ForeignKey("royals.id"), nullable=False)
    royal = relationship("Royal", backref="osu", lazy="joined")

    osu_id = Column(Integer, primary_key=True)
    osu_name = Column(String)

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

    def __repr__(self):
        if not self.osu_name:
            return f"<db.Osu {self.osu_id}>"
        return f"<db.Osu {self.osu_name}>"


class Discord(Base):
    __tablename__ = "discord"
    __table_args__ = tuple(UniqueConstraint("name", "discriminator"))

    royal_id = Column(Integer, ForeignKey("royals.id"))
    royal = relationship("Royal", backref="discord", lazy="joined")

    discord_id = Column(BigInteger, primary_key=True)
    name = Column(String)
    discriminator = Column(Integer)
    avatar_hex = Column(String)

    def __str__(self):
        return f"{self.name}#{self.discriminator}"

    def __repr__(self):
        return f"<db.Discord {self.discord_id}>"

    @staticmethod
    def create(session: Session, royal_username, discord_user: DiscordUser):
        # TODO: remove this
        print("Discord.create is deprecated and should be removed soon.")
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
        return f"https://cdn.discordapp.com/avatars/{self.discord_id}/{self.avatar_hex}.png?size={size}"


class Overwatch(Base):
    __tablename__ = "overwatch"

    royal_id = Column(Integer, ForeignKey("royals.id"), nullable=False)
    royal = relationship("Royal", backref="overwatch", lazy="joined")

    battletag = Column(String, primary_key=True)
    discriminator = Column(Integer, primary_key=True)
    icon = Column(String)

    level = Column(Integer)
    rank = Column(Integer)

    def __str__(self, separator="#"):
        return f"{self.battletag}{separator}{self.discriminator}"

    def __repr__(self):
        return f"<db.Overwatch {self}>"

    @staticmethod
    def create(session: Session, royal_id, battletag, discriminator=None):
        if discriminator is None:
            battletag, discriminator = battletag.split("#", 1)
        o = session.query(Overwatch).filter_by(battletag=battletag, discriminator=discriminator).first()
        if o is not None:
            raise AlreadyExistingError(repr(o))
        o = Overwatch(royal_id=royal_id,
                      battletag=battletag,
                      discriminator=discriminator)
        o.update()
        return o

    def icon_url(self):
        return f"https://d1u1mce87gyfbn.cloudfront.net/game/unlocks/{self.icon}.png"

    def update(self):
        r = requests.get(f"https://owapi.net/api/v3/u/{self.battletag}-{self.discriminator}/stats", headers={
            "User-Agent": "Royal-Bot/4.1",
            "From": "ste.pigozzi@gmail.com"
        })
        if r.status_code != 200:
            raise RequestError(f"OWAPI.net returned {r.status_code}")
        try:
            j = r.json()["eu"]["stats"].get("competitive")
            if j is None:
                logging.debug(f"No stats for {repr(self)}, skipping...")
                return
            if not j["game_stats"]:
                logging.debug(f"No stats for {repr(self)}, skipping...")
                return
            j = j["overall_stats"]
        except TypeError:
            logging.debug(f"No stats for {repr(self)}, skipping...")
            return
        try:
            self.icon = re.search(r"https://.+\.cloudfront\.net/game/unlocks/(0x[0-9A-F]+)\.png", j["avatar"]).group(1)
        except AttributeError:
            logging.debug(f"No icon available for {repr(self)}.")
        self.level = j["prestige"] * 100 + j["level"]
        self.rank = j["comprank"]

    def rank_url(self):
        if self.rank < 1500:
            n = 1
        elif self.rank < 2000:
            n = 2
        elif self.rank < 2500:
            n = 3
        elif self.rank < 3000:
            n = 4
        elif self.rank < 3500:
            n = 5
        elif self.rank < 4000:
            n = 6
        else:
            n = 7
        return f"https://d1u1mce87gyfbn.cloudfront.net/game/rank-icons/season-2/rank-{n}.png"


class Diario(Base):
    __tablename__ = "diario"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    saver_id = Column(Integer, ForeignKey("telegram.telegram_id"))
    saver = relationship("Telegram", foreign_keys=saver_id, backref="diario_saves", lazy="joined")
    author_id = Column(Integer, ForeignKey("telegram.telegram_id"))
    author = relationship("Telegram", foreign_keys=author_id, backref="diario_authored", lazy="joined")
    spoiler = Column(Boolean, default=False)
    text = Column(String)

    def __repr__(self):
        return f"<db.Diario {self.id}>"

    def __str__(self):
        return f"{self.id} - {self.timestamp} - {self.author}: {self.text}"

    @staticmethod
    def import_from_json(file):
        import json
        session = Session()
        file = open(file, "r")
        j = json.load(file)
        author_ids = {
            "@Steffo": 25167391,
            "@GoodBalu": 19611986,
            "@gattopandacorno": 200821462,
            "@Albertino04": 131057096,
            "@Francesco_Cuoghi": 48371848,
            "@VenomousDoc": 48371848,
            "@MaxSensei": 1258401,
            "@Protoh": 125711787,
            "@McspKap": 304117728,
            "@FrankRekt": 31436195,
            "@EvilBalu": 26842090,
            "@Dailir": 135816455,
            "@Paltri": 186843362,
            "@Doom_darth_vader": 165792255,
            "@httpIma": 292086686,
            "@DavidoMessori": 509208316,
            "@DavidoNiichan": 509208316,
            "@Peraemela99": 63804599,
            "@infopz": 20403805,
            "@Baithoven": 121537369,
            "@Tauei": 102833717
        }
        for n, entry in enumerate(j):
            author = author_ids[entry["sender"]] if "sender" in entry and entry["sender"] in author_ids else None
            d = Diario(timestamp=datetime.datetime.fromtimestamp(float(entry["timestamp"])),
                       author_id=author,
                       text=entry["text"])
            print(f"{n} - {d}")
            session.add(d)
        session.commit()
        session.close()


class BaluRage(Base):
    __tablename__ = "balurage"

    id = Column(Integer, primary_key=True)
    royal_id = Column(Integer, ForeignKey("royals.id"))
    royal = relationship("Royal", backref="times_raged", lazy="joined")
    reason = Column(String)

    def __repr__(self):
        return f"<db.BaluRage {self.id}>"


class PlayedMusic(Base):
    __tablename__ = "playedmusic"

    id = Column(Integer, primary_key=True)
    enqueuer_id = Column(BigInteger, ForeignKey("discord.discord_id"))
    enqueuer = relationship("Discord", backref="music_played", lazy="joined")
    filename = Column(String)
    timestamp = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<db.PlayedMusic {self.filename}>"


class VoteQuestion(Base):
    __tablename__ = "votequestion"

    id = Column(Integer, primary_key=True)
    message_id = Column(BigInteger)
    question = Column(String, nullable=False)
    anonymous = Column(Boolean, nullable=False)
    open = Column(Boolean, default=True)

    def __repr__(self):
        return f"<db.Vote {self.id}>"

    def generate_text(self, session: Session):
        text = f"<b>{self.question}</b>\n\n"
        none, yes, no, abstain = 0, 0, 0, 0
        if self.message_id is not None:
            query = session.execute("SELECT * FROM telegram LEFT JOIN (SELECT voteanswer.question_id, voteanswer.user_id, voteanswer.choice FROM votequestion JOIN voteanswer ON votequestion.id = voteanswer.question_id WHERE votequestion.message_id = " + str(self.message_id) + ") answer ON telegram.telegram_id = answer.user_id ORDER BY answer.choice;")
            for record in query:
                if record["username"] == "royalgamesbot":
                    continue
                elif record["question_id"] is None:
                    text += "⚪️"
                    none += 1
                elif record["choice"] == "YES":
                    text += "🔵"
                    yes += 1
                elif record["choice"] == "NO":
                    text += "🔴"
                    no += 1
                elif record["choice"] == "ABSTAIN":
                    text += "⚫️"
                    abstain += 1
                if not self.anonymous:
                    text += f" {str(record['username'])}\n"
            if self.anonymous:
                text += "\n"
            text += f"\n" \
                    f"⚪ {none}\n" \
                    f"🔵 {yes}\n" \
                    f"🔴 {no}\n" \
                    f"⚫️ {abstain}"
        return text


class VoteChoices(enum.Enum):
    ABSTAIN = 1
    YES = 2
    NO = 3


class VoteAnswer(Base):
    __tablename__ = "voteanswer"

    question_id = Column(Integer, ForeignKey("votequestion.id"))
    question = relationship("VoteQuestion", backref="answers", lazy="joined")
    user_id = Column(BigInteger, ForeignKey("telegram.telegram_id"))
    user = relationship("Telegram", backref="votes_cast", lazy="joined")
    choice = Column(Enum(VoteChoices), nullable=False)

    __table_args__ = (PrimaryKeyConstraint("question_id", "user_id"),)

    def __repr__(self):
        return f"<db.VoteAnswer {self.question_id} {self.user} {self.choice}>"


class ProfileData(Base):
    __tablename__ = "profiledata"

    royal_id = Column(Integer, ForeignKey("royals.id"), primary_key=True)
    royal = relationship("Royal", backref="profile_data", uselist=False, lazy="joined")

    css = Column(Text)
    bio = Column(Text)

    def __repr__(self):
        return f"<ProfileData for {self.royal.username}>"


class WikiEntry(Base):
    __tablename__ = "wikientries"

    key = Column(String, primary_key=True)
    content = Column(Text, nullable=False)

    def __repr__(self):
        return f"<WikiEntry {self.key}>"


class WikiLog(Base):
    __tablename__ = "wikilog"

    edit_id = Column(Integer, primary_key=True)
    editor_id = Column(Integer, ForeignKey("royals.id"), nullable=False)
    editor = relationship("Royal", backref="wiki_edits", lazy="joined")
    edited_key = Column(String, ForeignKey("wikientries.key"), nullable=False)
    edited = relationship("WikiEntry", backref="edit_logs", lazy="joined")
    timestamp = Column(DateTime, nullable=False)
    reason = Column(Text)

    def __repr__(self):
        return f"<WikiLog {self.edit_id}>"


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey("royals.id"), nullable=False)
    author = relationship("Royal", lazy="joined")
    name = Column(String, nullable=False)
    description = Column(Text)
    time = Column(DateTime, nullable=False)

    @hybrid_property
    def time_left(self) -> datetime.timedelta:
        return self.time - datetime.datetime.now()

    @time_left.setter
    def time_left(self, value):
        if not isinstance(value, datetime.timedelta):
            raise TypeError("time_left should be a datetime.timedelta")
        self.time = datetime.datetime.now() + value

    def __repr__(self):
        return f"<Event {self.name}>"


class Reddit(Base):
    __tablename__ = "reddit"

    royal_id = Column(Integer, ForeignKey("royals.id"))
    royal = relationship("Royal", backref="reddit", lazy="joined")

    username = Column(String, primary_key=True)
    karma = Column(BigInteger)

    def __repr__(self):
        return f"<Reddit u/{self.username}>"


class GameLog(Base):
    __tablename__ = "gamelog"

    royal_id = Column(Integer, ForeignKey("royals.id"))
    royal = relationship("Royal", backref="gamelog", lazy="joined")

    username = Column(String, primary_key=True)
    owned_games = Column(Integer)
    unfinished_games = Column(Integer)
    beaten_games = Column(Integer)
    completed_games = Column(Integer)
    mastered_games = Column(Integer)

    def __repr__(self):
        return f"<GameLog {self.username}>"


class ParsedRedditPost(Base):
    __tablename__ = "parsedredditposts"

    id = Column(String, primary_key=True)

    author_username = Column(String)

    def __repr__(self):
        return f"<ParsedRedditPost {self.id}>"


class LoginToken(Base):
    __tablename__ = "logintoken"

    royal_id = Column(Integer, ForeignKey("royals.id"))
    royal = relationship("Royal", backref="tokens", lazy="joined")

    token = Column(String, primary_key=True)
    expiration = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<LoginToken for {self.royal.username}>"


class Halloween(Base):
    """This is some nice spaghetti, don't you think?"""
    __tablename__ = "halloween"

    royal_id = Column(Integer, ForeignKey("royals.id"), primary_key=True)
    royal = relationship("Royal", backref="halloween", lazy="joined")

    first_trigger = Column(DateTime)

    puzzle_piece_a = Column(DateTime)
    puzzle_piece_b = Column(DateTime)
    puzzle_piece_c = Column(DateTime)
    puzzle_piece_d = Column(DateTime)
    puzzle_piece_e = Column(DateTime)
    puzzle_piece_f = Column(DateTime)
    puzzle_piece_g = Column(DateTime)

    boss_battle = Column(DateTime)

    def __getitem__(self, item):
        if not isinstance(item, int):
            raise TypeError("The index should be an int")
        if item == 1:
            return self.puzzle_piece_a
        elif item == 2:
            return self.puzzle_piece_b
        elif item == 3:
            return self.puzzle_piece_c
        elif item == 4:
            return self.puzzle_piece_d
        elif item == 5:
            return self.puzzle_piece_e
        elif item == 6:
            return self.puzzle_piece_f
        elif item == 7:
            return self.puzzle_piece_g
        else:
            raise ValueError("No such puzzle piece")

    def __setitem__(self, key, value):
        if not isinstance(key, int):
            raise TypeError("The index should be an int")
        if key == 1:
            self.puzzle_piece_a = value
        elif key == 2:
            self.puzzle_piece_b = value
        elif key == 3:
            self.puzzle_piece_c = value
        elif key == 4:
            self.puzzle_piece_d = value
        elif key == 5:
            self.puzzle_piece_e = value
        elif key == 6:
            self.puzzle_piece_f = value
        elif key == 7:
            self.puzzle_piece_g = value
        else:
            raise ValueError("No such puzzle piece")

    def pieces_completed(self) -> int:
        count = 0
        for i in range(1, 8):
            if self[i]:
                count += 1
        return count

    @staticmethod
    def puzzle_status() -> typing.Tuple[bool, typing.List[bool]]:
        session = Session()
        halloweens = session.query(Halloween).all()
        session.close()
        completed = [False for _ in range(7)]
        started = False
        for h in halloweens:
            for i in range(7):
                if h.first_trigger is not None:
                    started = True
                if h[i+1]:
                    completed[i] = True
        return started, completed

# If run as script, create all the tables in the db
if __name__ == "__main__":
    print("Creating new tables...")
    Base.metadata.create_all(bind=engine)
    print("Done!")
