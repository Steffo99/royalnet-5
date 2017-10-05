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

    def __repr__(self):
        return f"<Steam {self.steam_id}>"

    def __str__(self):
        if self.steam_name is not None:
            return self.steam_name
        else:
            return self.steam_id

    def update(self):
        r = requests.get(f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={config['Steam']['api_key']}&steamids={self.steam_id}")
        if r.status_code != 200:
            raise RequestError(f"Steam returned {r.status_code}")
        j = r.json()
        self.persona_name = j["response"]["players"][0]["personaname"]
        self.avatar_hex = re.search("https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/../(.+).jpg", j["response"]["players"][0]["avatar"]).group(1)

# If run as script, create all the tables in the db
if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)