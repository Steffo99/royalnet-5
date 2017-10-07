from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import Column, BigInteger, Integer, String, Numeric, DateTime, ForeignKey, Float, create_engine
import requests
from errors import RequestError
import re

# Init the config reader
import configparser
config = configparser.ConfigParser()
config.read("config.ini")

# Init the sqlalchemy engine
engine = create_engine(config["Database"]["database_uri"])
Base = declarative_base(bind=engine)
Session = sessionmaker(bind=engine)

# Create a new default session
session = Session()


class Royal(Base):
    __tablename__ = "royals"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)

    def __repr__(self):
        return f"<Royal {self.username}>"


class Telegram(Base):
    __tablename__ = "telegram"

    royal_id = Column(Integer, ForeignKey("royals.id"))
    royal = relationship("Royal")

    telegram_id = Column(BigInteger, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String)
    username = Column(String)

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

    royal_id = Column(Integer, ForeignKey("royals.id"))
    royal = relationship("Royal")

    steam_id = Column(String, primary_key=True)
    persona_name = Column(String)
    avatar_hex = Column(String)
    trade_token = Column(String)

    def __repr__(self):
        return f"<Steam {self.steam_id}>"

    def __str__(self):
        if self.persona_name is not None:
            return self.persona_name
        else:
            return self.steam_id

    def steam_id_1(self):
        return self.steam_id

    def steam_id_2(self):
        # Got this code from a random github gist. It could be completely wrong.
        z = (int(self.steam_id) - 76561197960265728) // 2
        y = int(self.steam_id) % 2
        return f"STEAM_0:{y}:{z}"

    def steam_id_3(self, full=False):
        # Got this code from a random github gist. It could be completely wrong.
        if full:
            return f"[U:1:{int(self.steam_id) - 76561197960265728}]"
        else:
            return f"{int(self.steam_id) - 76561197960265728}"

    def update(self):
        r = requests.get(f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={config['Steam']['api_key']}&steamids={self.steam_id}")
        if r.status_code != 200:
            raise RequestError(f"Steam returned {r.status_code}")
        j = r.json()
        self.persona_name = j["response"]["players"][0]["personaname"]
        self.avatar_hex = re.search("https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/../(.+).jpg", j["response"]["players"][0]["avatar"]).group(1)


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
    def check_and_create(steam_id):
        rl = session.query(RocketLeague).filter(RocketLeague.steam_id == steam_id).first()
        if rl is not None:
            return None
        r = requests.get(f"https://api.rocketleaguestats.com/v1/player?apikey={config['Rocket League']['rlstats_api_key']}&unique_id={str(steam_id)}&platform_id=1")
        if r.status_code == 404:
            return None
        elif r.status_code == 500:
            raise RequestError("Rocket League Stats returned {r.status_code}")
        new_record = RocketLeague(steam_id=steam_id)
        new_record.update()
        return new_record

    def update(self):
        r = requests.get(f"https://api.rocketleaguestats.com/v1/player?apikey={config['Rocket League']['rlstats_api_key']}&unique_id={self.steam_id}&platform_id=1")
        if r.status_code != 200:
            raise RequestError(f"Rocket League Stats returned {r.status_code}")
        j = r.json()
        # Get current season
        current_season = 0
        for season in j["rankedSeasons"]:
            if int(season) > current_season:
                current_season = int(season)
        self.season = current_season
        if current_season == 0:
            return
        current_season = str(current_season)
        # Get ranked data
        # Single 1v1
        if "10" in j["rankedSeasons"][current_season]:
            self.single_mmr = j["rankedSeasons"][current_season]["10"]["rankPoints"]
            if j["rankedSeasons"][current_season]["10"]["matchesPlayed"] >= 10:
                self.single_rank = j["rankedSeasons"][current_season]["10"]["tier"]
                self.single_div = j["rankedSeasons"][current_season]["10"]["division"]
            else:
                self.single_rank = None
                self.single_div = None
        # Doubles 2v2
        if "11" in j["rankedSeasons"][current_season]:
            self.doubles_mmr = j["rankedSeasons"][current_season]["11"]["rankPoints"]
            if j["rankedSeasons"][current_season]["11"]["matchesPlayed"] >= 10:
                self.doubles_rank = j["rankedSeasons"][current_season]["11"]["tier"]
                self.doubles_div = j["rankedSeasons"][current_season]["11"]["division"]
            else:
                self.doubles_rank = None
                self.doubles_div = None
        # Standard 3v3
        if "13" in j["rankedSeasons"][current_season]:
            self.standard_mmr = j["rankedSeasons"][current_season]["13"]["rankPoints"]
            if j["rankedSeasons"][current_season]["13"]["matchesPlayed"] >= 10:
                self.standard_rank = j["rankedSeasons"][current_season]["13"]["tier"]
                self.standard_div = j["rankedSeasons"][current_season]["13"]["division"]
            else:
                self.standard_rank = None
                self.standard_div = None
        # Solo Standard 3v3
        if "12" in j["rankedSeasons"][current_season]:
            self.solo_std_mmr = j["rankedSeasons"][current_season]["12"]["rankPoints"]
            if j["rankedSeasons"][current_season]["12"]["matchesPlayed"] >= 10:
                self.solo_std_rank = j["rankedSeasons"][current_season]["12"]["tier"]
                self.solo_std_div = j["rankedSeasons"][current_season]["12"]["division"]
            else:
                self.solo_std_rank = None
                self.solo_std_div = None


# If run as script, create all the tables in the db
if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)