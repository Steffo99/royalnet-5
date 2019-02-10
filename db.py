import datetime
import logging
import os
import coloredlogs
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.hybrid import hybrid_property
# noinspection PyUnresolvedReferences
from sqlalchemy import Column, BigInteger, Integer, String, DateTime, ForeignKey, Float, Enum, create_engine, \
                       UniqueConstraint, PrimaryKeyConstraint, Boolean, LargeBinary, Text, Date, func
from sqlalchemy.inspection import inspect
import requests
import errors
from errors import NotFoundError, AlreadyExistingError, PrivateError
import re
import enum
import loldata
from utils.dirty import Dirty, DirtyDelta
import sql_queries
from flask import escape
import configparser
import typing
from utils import MatchmakingStatus
import strings
if typing.TYPE_CHECKING:
    # noinspection PyPackageRequirements
    from discord import User as DiscordUser
    # noinspection PyPackageRequirements
    from telegram import User as TelegramUser

# Init the config reader
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


def relationship_name_search(_class, keyword) -> typing.Optional[tuple]:
    """Recursively find a relationship with a given name."""
    inspected = set()

    def search(_mapper, chain):
        inspected.add(_mapper)
        relationships = _mapper.relationships
        try:
            return chain + (relationships[keyword],)
        except KeyError:
            for _relationship in set(relationships):
                if _relationship.mapper in inspected:
                    continue
                result = search(_relationship.mapper, chain + (_relationship,))
                if result is not None:
                    return result
            return None

    return search(inspect(_class), tuple())


def relationship_link_chain(starting_class, ending_class) -> typing.Optional[tuple]:
    """Find the path to follow to get from the starting table to the ending table."""
    inspected = set()

    def search(_mapper, chain):
        inspected.add(_mapper)
        if _mapper.class_ == ending_class:
            return chain
        relationships = _mapper.relationships
        for _relationship in set(relationships):
            if _relationship.mapper in inspected:
                continue
            try:
                return search(_relationship.mapper, chain + (_relationship,))
            except errors.NotFoundError:
                continue
        raise errors.NotFoundError()

    return search(inspect(starting_class), tuple())


class Mini(object):
    """Mixin for every table that has an associated mini."""
    _mini_full_name = NotImplemented
    _mini_name = NotImplemented
    _mini_order = NotImplemented

    @classmethod
    def mini_get_all(cls, session: Session) -> list:
        return session.query(cls).order_by(*cls._mini_order).all()

    @classmethod
    def mini_get_single(cls, session: Session, **kwargs):
        return session.query(cls).filter_by(**kwargs).one_or_none()

    @classmethod
    def mini_get_single_from_royal(cls, session: Session, royal: "Royal"):
        chain = relationship_link_chain(cls, Royal)
        if chain is None:
            chain = tuple()
        start = session.query(cls)
        for connection in chain:
            start = start.join(connection.mapper.class_)
        start = start.filter(Royal.id == royal.id)
        mini = start.one()
        return mini


class Royal(Base, Mini):
    __tablename__ = "royals"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(LargeBinary)
    role = Column(String)
    fiorygi = Column(Integer, default=0)
    member_since = Column(Date)

    _mini_full_name = "Royalnet"
    _mini_name = "ryg"
    _mini_order = [fiorygi.desc()]

    @staticmethod
    def create(session: Session, username: str):
        r = session.query(Royal).filter_by(username=username).first()
        if r is not None:
            raise AlreadyExistingError(repr(r))
        return Royal(username=username)

    def __repr__(self):
        return f"<db.Royal {self.username}>"

    @classmethod
    def mini_get_single_from_royal(cls, session: Session, royal: "Royal"):
        return royal


class Telegram(Base, Mini):
    __tablename__ = "telegram"

    royal_id = Column(Integer, ForeignKey("royals.id"))
    royal = relationship("Royal", backref="telegram", lazy="joined")

    telegram_id = Column(BigInteger, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String)

    _mini_full_name = "Telegram"
    _mini_name = "tg"
    _mini_order = [telegram_id]

    @staticmethod
    def create(session: Session, royal_username, telegram_user: "TelegramUser"):
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

    @classmethod
    def mini_get_single_from_royal(cls, session: Session, royal: "Royal"):
        return royal.telegram


class Steam(Base, Mini):
    __tablename__ = "steam"

    royal_id = Column(Integer, ForeignKey("royals.id"))
    royal = relationship("Royal", backref="steam", lazy="joined")

    steam_id = Column(String, primary_key=True)
    persona_name = Column(String)
    avatar_hex = Column(String)
    trade_token = Column(String)
    most_played_game_id = Column(BigInteger)

    _mini_full_name = "Steam"
    _mini_name = "steam"
    _mini_order = [steam_id]

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
        return f"https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/{self.avatar_hex[0:2]}/"\
               f"{self.avatar_hex}.jpg"

    @staticmethod
    def create(session: Session, royal_id: int, steam_id: str):
        s = session.query(Steam).get(steam_id)
        if s is not None:
            raise AlreadyExistingError(repr(s))
        r = requests.get(f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
                         f"?key={config['Steam']['api_key']}&steamids={steam_id}")
        r.raise_for_status()
        j = r.json()
        if len(j) == 0:
            raise NotFoundError(f"The steam_id doesn't match any steam account")
        s = Steam(royal_id=royal_id,
                  steam_id=steam_id,
                  persona_name=j["response"]["players"][0]["personaname"],
                  avatar_hex=re.search(r"https://steamcdn-a\.akamaihd\.net/steamcommunity/public/images/avatars/../"
                                       r"(.+).jpg", j["response"]["players"][0]["avatar"]).group(1))
        return s

    @staticmethod
    def find_trade_token(trade_url):
        return re.search(r"https://steamcommunity\.com/tradeoffer/new/\?partner=[0-9]+&token=(.{8})", trade_url)\
                 .group(1)

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

    # noinspection PyUnusedLocal
    def update(self, session=None, raise_if_private: bool=False):
        r = requests.get(f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
                         f"?key={config['Steam']['api_key']}&steamids={self.steam_id}")
        r.raise_for_status()
        j = r.json()
        self.persona_name = j["response"]["players"][0]["personaname"]
        self.avatar_hex = re.search(r"https://steamcdn-a\.akamaihd\.net/steamcommunity/public/images/avatars/../"
                                    r"(.+).jpg", j["response"]["players"][0]["avatar"]).group(1)
        r = requests.get(f"http://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/"
                         f"?key={config['Steam']['api_key']}&steamid={self.steam_id}&format=json")
        r.raise_for_status()
        j = r.json()
        if "response" not in j or "games" not in j["response"] or len(j["response"]["games"]) < 1:
            if raise_if_private:
                raise PrivateError(f"Game data is private")
            return
        self.most_played_game_id = j["response"]["games"][0]["appid"]

    @classmethod
    def mini_get_single_from_royal(cls, session: Session, royal: "Royal"):
        return royal.steam


class RocketLeague(Base, Mini):
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

    _mini_full_name = "Rocket League"
    _mini_name = "rl"
    _mini_order = [solo_std_mmr.desc().nullslast(),
                   doubles_mmr.desc().nullslast(),
                   standard_mmr.desc().nullslast(),
                   single_mmr.desc().nullslast()]

    def __repr__(self):
        return f"<db.RocketLeague {self.steam_id}>"

    def update(self, session=None, data=None):
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


class Dota(Base, Mini):
    __tablename__ = "dota"

    steam_id = Column(String, ForeignKey("steam.steam_id"), primary_key=True)
    steam = relationship("Steam", backref="dota", lazy="joined")

    rank_tier = Column(Integer)
    wins = Column(Integer)
    losses = Column(Integer)
    most_played_hero = Column(Integer)

    _mini_full_name = "DOTA 2"
    _mini_name = "dota"
    _mini_order = [rank_tier.desc().nullslast(), wins.desc().nullslast()]

    def __repr__(self):
        return f"<db.Dota {self.steam_id}>"

    def get_rank_icon_url(self):
        # Rank icon is determined by the first digit of the rank tier
        if self.rank_tier is None:
            return f"https://www.opendota.com/assets/images/dota2/rank_icons/rank_icon_0.png"
        return f"https://www.opendota.com/assets/images/dota2/rank_icons/rank_icon_{str(self.rank_tier)[0]}.png"

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
        r.raise_for_status()
        data = r.json()
        if "profile" not in data:
            raise NotFoundError("The specified user has never played Dota or has a private match history")
        new_record = Dota(steam_id=str(steam_id))
        new_record.update()
        return new_record

    # noinspection PyUnusedLocal
    def update(self, session=None) -> bool:
        r = requests.get(f"https://api.opendota.com/api/players/{Steam.to_steam_id_3(self.steam_id)}")
        r.raise_for_status()
        data = r.json()
        r = requests.get(f"https://api.opendota.com/api/players/{Steam.to_steam_id_3(self.steam_id)}/wl")
        r.raise_for_status()
        wl = r.json()
        r = requests.get(f"https://api.opendota.com/api/players/{Steam.to_steam_id_3(self.steam_id)}/heroes")
        r.raise_for_status()
        heroes = r.json()
        changed = self.rank_tier != data["rank_tier"]
        self.rank_tier = data["rank_tier"]
        self.wins = wl["win"]
        self.losses = wl["lose"]
        self.most_played_hero = heroes[0]["hero_id"]
        return changed


class LeagueOfLegendsRanks(enum.Enum):
    IRON = 0
    BRONZE = 1
    SILVER = 2
    GOLD = 3
    PLATINUM = 4
    DIAMOND = 5
    MASTER = 6
    GRANDMASTER = 7
    CHALLENGER = 8

    def __str__(self):
        return self.name.capitalize()


class RomanNumerals(enum.Enum):
    I = 1
    II = 2
    III = 3
    IV = 4

    def __str__(self):
        return self.name


class LeagueOfLegends(Base, Mini):
    __tablename__ = "leagueoflegends"

    royal_id = Column(Integer, ForeignKey("royals.id"))
    royal = relationship("Royal", backref="lol", lazy="joined")

    icon_id = Column(Integer)
    summoner_id = Column(String, primary_key=True)
    account_id = Column(String)
    summoner_name = Column(String)
    level = Column(Integer)
    solo_division = Column(Enum(LeagueOfLegendsRanks))
    solo_rank = Column(Enum(RomanNumerals))
    flex_division = Column(Enum(LeagueOfLegendsRanks))
    flex_rank = Column(Enum(RomanNumerals))
    twtr_division = Column(Enum(LeagueOfLegendsRanks))
    twtr_rank = Column(Enum(RomanNumerals))
    highest_mastery_champ = Column(Integer)

    _mini_full_name = "League of Legends"
    _mini_name = "lol"
    _mini_order = [solo_division.desc().nullslast(),
                   solo_rank.desc().nullslast(),
                   flex_division.desc().nullslast(),
                   flex_rank.desc().nullslast(),
                   twtr_division.desc().nullslast(),
                   twtr_rank.desc().nullslast()]

    def __repr__(self):
        if not self.summoner_name:
            return f"<LeagueOfLegends {self.summoner_id}>"
        return f"<LeagueOfLegends {(''.join([x if x.isalnum else '' for x in self.summoner_name]))}>"

    @staticmethod
    def create(royal_id, summoner_name) -> "LeagueOfLegends":
        r = requests.get(f"https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}"
                         f"?api_key={config['League of Legends']['riot_api_key']}")
        r.raise_for_status()
        data = r.json()
        lol = LeagueOfLegends()
        lol.royal_id = royal_id
        lol.summoner_name = summoner_name
        lol.summoner_id = data["id"]
        lol.account_id = data["accountId"]
        lol.icon_id = data["profileIconId"]
        lol.level = data["summonerLevel"]
        lol.update()
        return lol

    # noinspection PyUnusedLocal
    def update(self, session=None):
        r = requests.get(f"https://euw1.api.riotgames.com/lol/summoner/v4/summoners/"
                         f"{self.summoner_id}?api_key={config['League of Legends']['riot_api_key']}")
        r.raise_for_status()
        data = r.json()
        r = requests.get(f"https://euw1.api.riotgames.com/lol/league/v4/positions/by-summoner/"
                         f"{self.summoner_id}?api_key={config['League of Legends']['riot_api_key']}")
        r.raise_for_status()
        rank = r.json()
        r = requests.get(f"https://euw1.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-summoner/"
                         f"{self.summoner_id}?api_key={config['League of Legends']['riot_api_key']}")
        r.raise_for_status()
        mastery = r.json()
        solo_q = None
        flex_q = None
        twtr_q = None
        for league in rank:
            if league["queueType"] == "RANKED_SOLO_5x5":
                solo_q = league
            elif league["queueType"] == "RANKED_FLEX_SR":
                flex_q = league
            elif league["queueType"] == "RANKED_FLEX_TT":
                twtr_q = league
        self.summoner_id = data["id"]
        self.summoner_name = data["name"]
        self.account_id = data["accountId"]
        self.level = data["summonerLevel"]
        solo = Dirty((self.solo_division, self.solo_rank))
        flex = Dirty((self.flex_division, self.flex_rank))
        twtr = Dirty((self.twtr_division, self.twtr_rank))
        solo.value = (None, None) if solo_q is None else (LeagueOfLegendsRanks[solo_q["tier"]],
                                                          RomanNumerals[solo_q["rank"]])
        flex.value = (None, None) if flex_q is None else (LeagueOfLegendsRanks[flex_q["tier"]],
                                                          RomanNumerals[flex_q["rank"]])
        twtr.value = (None, None) if twtr_q is None else (LeagueOfLegendsRanks[twtr_q["tier"]],
                                                          RomanNumerals[twtr_q["rank"]])
        self.highest_mastery_champ = mastery[0]["championId"]
        self.solo_division = solo.value[0]
        self.solo_rank = solo.value[1]
        self.flex_division = flex.value[0]
        self.flex_rank = flex.value[1]
        self.twtr_division = twtr.value[0]
        self.twtr_rank = twtr.value[1]
        return solo, flex, twtr

    def highest_mastery_champ_name(self):
        champ = loldata.get_champ_by_key(self.highest_mastery_champ)
        return champ["name"]

    def highest_mastery_champ_image(self):
        champ = loldata.get_champ_by_key(self.highest_mastery_champ)
        return loldata.get_champ_icon(champ["name"])


class Osu(Base, Mini):
    __tablename__ = "osu"

    royal_id = Column(Integer, ForeignKey("royals.id"), nullable=False)
    royal = relationship("Royal", backref="osu", lazy="joined")

    osu_id = Column(Integer, primary_key=True)
    osu_name = Column(String)
    std_pp = Column(Float, default=0)
    std_best_song = Column(BigInteger)
    taiko_pp = Column(Float, default=0)
    taiko_best_song = Column(BigInteger)
    catch_pp = Column(Float, default=0)
    catch_best_song = Column(BigInteger)
    mania_pp = Column(Float, default=0)
    mania_best_song = Column(BigInteger)

    _mini_full_name = "osu!"
    _mini_name = "osu"
    _mini_order = [mania_pp.desc().nullslast(),
                   std_pp.desc().nullslast(),
                   taiko_pp.desc().nullslast(),
                   catch_pp.desc().nullslast()]

    @staticmethod
    def create(session: Session, royal_id, osu_name):
        o = session.query(Osu).filter(Osu.osu_name == osu_name).first()
        if o is not None:
            raise AlreadyExistingError(repr(o))
        r0 = requests.get(f"https://osu.ppy.sh/api/get_user?k={config['Osu!']['ppy_api_key']}&u={osu_name}&m=0")
        r0.raise_for_status()
        r1 = requests.get(f"https://osu.ppy.sh/api/get_user?k={config['Osu!']['ppy_api_key']}&u={osu_name}&m=1")
        r1.raise_for_status()
        r2 = requests.get(f"https://osu.ppy.sh/api/get_user?k={config['Osu!']['ppy_api_key']}&u={osu_name}&m=2")
        r2.raise_for_status()
        r3 = requests.get(f"https://osu.ppy.sh/api/get_user?k={config['Osu!']['ppy_api_key']}&u={osu_name}&m=3")
        r3.raise_for_status()
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

    # noinspection PyUnusedLocal
    def update(self, session=None):
        std = DirtyDelta(self.std_pp)
        taiko = DirtyDelta(self.taiko_pp)
        catch = DirtyDelta(self.catch_pp)
        mania = DirtyDelta(self.mania_pp)
        r0 = requests.get(f"https://osu.ppy.sh/api/get_user?k={config['Osu!']['ppy_api_key']}&u={self.osu_name}&m=0")
        r0.raise_for_status()
        j0 = r0.json()[0]
        r1 = requests.get(f"https://osu.ppy.sh/api/get_user?k={config['Osu!']['ppy_api_key']}&u={self.osu_name}&m=1")
        r1.raise_for_status()
        j1 = r1.json()[0]
        r2 = requests.get(f"https://osu.ppy.sh/api/get_user?k={config['Osu!']['ppy_api_key']}&u={self.osu_name}&m=2")
        r2.raise_for_status()
        j2 = r2.json()[0]
        r3 = requests.get(f"https://osu.ppy.sh/api/get_user?k={config['Osu!']['ppy_api_key']}&u={self.osu_name}&m=3")
        r3.raise_for_status()
        j3 = r3.json()[0]
        self.osu_name = j0["username"]
        std.value = float(j0["pp_raw"] or 0)
        taiko.value = float(j1["pp_raw"] or 0)
        catch.value = float(j2["pp_raw"] or 0)
        mania.value = float(j3["pp_raw"] or 0)
        self.std_pp = std.value
        self.taiko_pp = taiko.value
        self.catch_pp = catch.value
        self.mania_pp = mania.value
        return std, taiko, catch, mania

    def __repr__(self):
        if not self.osu_name:
            return f"<db.Osu {self.osu_id}>"
        return f"<db.Osu {self.osu_name}>"


class Discord(Base, Mini):
    __tablename__ = "discord"
    __table_args__ = tuple(UniqueConstraint("name", "discriminator"))

    royal_id = Column(Integer, ForeignKey("royals.id"))
    royal = relationship("Royal", backref="discord", lazy="joined")

    discord_id = Column(BigInteger, primary_key=True)
    name = Column(String)
    discriminator = Column(Integer)
    avatar_hex = Column(String)

    _mini_full_name = "Discord"
    _mini_name = "discord"
    _mini_order = [discord_id]

    def __str__(self):
        return f"{self.name}#{self.discriminator}"

    def __repr__(self):
        return f"<db.Discord {self.discord_id}>"

    @staticmethod
    def create(session: Session, royal_username, discord_user: "DiscordUser"):
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
        return f"<@{self.discord_id}>"

    def avatar_url(self, size=256):
        if self.avatar_hex is None:
            return "https://discordapp.com/assets/6debd47ed13483642cf09e832ed0bc1b.png"
        return f"https://cdn.discordapp.com/avatars/{self.discord_id}/{self.avatar_hex}.png?size={size}"

    @classmethod
    def mini_get_all(cls, session: Session):
        return [dict(row) for row in session.execute(sql_queries.all_music_query)]

    @classmethod
    def mini_get_single(cls, session: Session, **kwargs):
        return session.execute(sql_queries.one_music_query, {"royal": kwargs["royal"].id}).fetchone()

    @classmethod
    def mini_get_single_from_royal(cls, session: Session, royal: "Royal"):
        return cls.mini_get_single(session, royal=royal)


class Overwatch(Base, Mini):
    __tablename__ = "overwatch"

    royal_id = Column(Integer, ForeignKey("royals.id"), nullable=False)
    royal = relationship("Royal", backref="overwatch", lazy="joined")

    battletag = Column(String, primary_key=True)
    discriminator = Column(Integer, primary_key=True)
    icon = Column(String)
    level = Column(Integer)
    rank = Column(Integer)

    _mini_full_name = "Overwatch"
    _mini_name = "ow"
    _mini_order = [rank.desc().nullslast(), level.desc()]

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

    # noinspection PyUnusedLocal
    def update(self, session=None):
        r = requests.get(f"https://owapi.net/api/v3/u/{self.battletag}-{self.discriminator}/stats", headers={
            "User-Agent": "Royal-Bot/4.1",
            "From": "ste.pigozzi@gmail.com"
        })
        r.raise_for_status()
        try:
            j = r.json()["eu"]["stats"].get("competitive")
            if j is None:
                logger.debug(f"No stats for {repr(self)}, skipping...")
                return
            if not j["game_stats"]:
                logger.debug(f"No stats for {repr(self)}, skipping...")
                return
            j = j["overall_stats"]
        except TypeError:
            logger.debug(f"No stats for {repr(self)}, skipping...")
            return
        try:
            self.icon = re.search(r"https://.+\.cloudfront\.net/game/unlocks/(0x[0-9A-F]+)\.png", j["avatar"]).group(1)
        except AttributeError:
            logger.debug(f"No icon available for {repr(self)}.")
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

    def rank_name(self):
        if self.rank < 1500:
            return "Bronze"
        elif self.rank < 2000:
            return "Silver"
        elif self.rank < 2500:
            return "Gold"
        elif self.rank < 3000:
            return "Platinum"
        elif self.rank < 3500:
            return "Diamond"
        elif self.rank < 4000:
            return "Master"
        else:
            return "Grandmaster"


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

    def to_telegram(self):
        return '<a href="https://ryg.steffo.eu/diario#entry-{id}">#{id}</a> di <b>{author}</b>\n{text}'.format(
            id=self.id,
            author=self.author,
            text=escape(self.text))

    def to_html(self):
        return str(escape(self.text)).replace("\n", "<br>")

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
            query = session.execute(sql_queries.vote_answers, {"message_id": self.message_id})
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
    locked = Column(Boolean, default=False)

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


class Halloween(Base, Mini):
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

    _mini_full_name = "Halloween 2018"
    _mini_name = "halloween2018"
    _mini_order = [first_trigger]

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
            if h.royal.role == "Affiliato":
                continue
            if h.royal.username == "Steffo":
                continue
            for i in range(7):
                if h.first_trigger is not None:
                    started = True
                if h[i+1]:
                    completed[i] = True
        return started, completed


class ActivityReport(Base):
    __tablename__ = "activityreports"

    timestamp = Column(DateTime, primary_key=True)

    discord_members_online = Column(Integer)
    discord_members_ingame = Column(Integer)
    discord_cv = Column(Integer)
    discord_members_cv = Column(Integer)
    discord_channels_used = Column(Integer)

    def __repr__(self):
        return f"<ActivityReport at {self.timestamp.isoformat()}>"


class Quest(Base):
    __tablename__ = "quests"

    id = Column(Integer, primary_key=True)

    title = Column(String)
    description = Column(Text)
    reward = Column(Integer)
    expiration_date = Column(DateTime)

    def __repr__(self):
        return f"<Quest {self.id}: {self.title}>"


class Terraria13(Base, Mini):
    __tablename__ = "terraria13"

    game_name = "Terraria 13"

    royal_id = Column(Integer, ForeignKey("royals.id"), primary_key=True)
    royal = relationship("Royal", backref="terraria13", lazy="joined")

    character_name = Column(String)
    contribution = Column(Integer)

    _mini_full_name = "Terraria 13"
    _mini_name = "terraria13"
    _mini_order = [contribution.desc()]

    def __repr__(self):
        return f"<Terraria13 {self.character_name} {self.contribution}>"


mini_list = [Royal, Telegram, Steam, Dota, LeagueOfLegends, Osu, Discord, Overwatch, Halloween,
             Terraria13]


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    creator_id = Column(BigInteger, ForeignKey("telegram.telegram_id"))
    creator = relationship("Telegram", backref="matches_created", lazy="joined")

    match_title = Column(String)
    match_desc = Column(Text)
    min_players = Column(Integer)
    max_players = Column(Integer)
    closed = Column(Boolean, default=False)

    message_id = Column(BigInteger)

    def active_players_count(self):
        count = 0
        for player in self.players:
            if player.status == MatchmakingStatus.READY \
                    or player.status == MatchmakingStatus.WAIT_FOR_ME \
                    or player.status == MatchmakingStatus.SOMEONE_ELSE:
                count += 1
        return count

    def generate_text(self, session):
        player_list = session.query(MatchPartecipation).filter_by(match=self).all()
        title = f"<b>{self.match_title}</b>"
        description = f"{self.match_desc}\n" if self.match_desc else ""
        if self.min_players:
            minimum = f" <i>(minimo {self.min_players})</i>"
        else:
            minimum = ""
        plist = f"Giocatori{minimum}:\n"
        ignore_count = 0
        for player in player_list:
            icon = strings.MATCHMAKING.ENUM_TO_EMOJIS[player.status]
            if player.status == MatchmakingStatus.IGNORED:
                ignore_count += 1
                continue
            plist += f"{icon} {player.user.royal.username}\n"
        if ignore_count:
            ignored = f"❌ <i>{ignore_count} persone non sono interessate.</i>\n"
        else:
            ignored = ""
        if self.max_players:
            players = f"[{self.active_players_count()}/{self.max_players}]"
        else:
            players = f"[{self.active_players_count()}]"
        close = f"[matchmaking terminato]\n" if self.closed else ""
        message = f"{title} {players}\n" \
                  f"{description}\n" \
                  f"{plist}\n" \
                  f"{ignored}" \
                  f"{close}"
        return message

    def __repr__(self):
        return f"<Match {self.match_title}>"

    def format_dict(self) -> typing.Dict[str, str]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "creator_id": self.creator_id,
            "creator_name": self.creator.mention(),
            "match_title": self.match_title,
            "match_desc": self.match_desc,
            "min_players": self.min_players,
            "max_players": self.max_players,
            "active_players": self.active_players_count(),
            "players": len(self.players)
        }


class MatchPartecipation(Base):
    __tablename__ = "matchpartecipations"
    __table_args__ = (PrimaryKeyConstraint("user_id", "match_id"),)

    user_id = Column(BigInteger, ForeignKey("telegram.telegram_id"))
    user = relationship("Telegram", backref="match_partecipations", lazy="joined")

    match_id = Column(Integer, ForeignKey("matches.id"))
    match = relationship("Match", backref="players", lazy="joined")

    status = Column(Integer)

    def __repr__(self):
        return f"<MatchPartecipation {self.user.username} in {self.match.match_title}>"


class BindingOfIsaac(Base, Mini):
    __tablename__ = "bindingofisaac"

    steam_id = Column(String, ForeignKey("steam.steam_id"), primary_key=True)
    steam = relationship("Steam", backref="binding_of_isaac", lazy="joined")

    daily_victories = Column(Integer, default=0)

    def __repr__(self):
        return f"<db.BindingOfIsaac {self.steam_id}>"

    def recalc_victories(self):
        raise NotImplementedError()  # TODO


class BindingOfIsaacRun(Base):
    __tablename__ = "bindingofisaacruns"
    __table_args__ = (PrimaryKeyConstraint("date", "player_id"),)

    date = Column(Date)

    player_id = Column(String, ForeignKey("bindingofisaac.steam_id"))
    player = relationship("BindingOfIsaac", backref="runs", lazy="joined")

    score = Column(BigInteger)
    # time = Column(???)

    def __repr__(self):
        return f"<db.BindingOfIsaacRun {self.player_id}: {self.score}>"


# If run as script, create all the tables in the db
if __name__ == "__main__":
    print("Creating new tables...")
    Base.metadata.create_all(bind=engine)
    print("Done!")
