from sqlalchemy import *
from sqlalchemy.orm import relationship, composite
from sqlalchemy.ext.declarative import declared_attr
from ..utils import LeagueRank, LeagueTier, LeagueLeague


class LeagueOfLegends:
    __tablename__ = "leagueoflegends"

    @declared_attr
    def region(self):
        return Column(String, nullable=False)

    @declared_attr
    def user_id(self):
        return Column(Integer, ForeignKey("users.uid"))

    @declared_attr
    def user(self):
        return relationship("User", backref="leagueoflegends")

    @declared_attr
    def profile_icon_id(self):
        # 3777
        return Column(Integer, nullable=False)

    @declared_attr
    def summoner_name(self):
        # SteffoRYG
        return Column(String, nullable=False)

    @declared_attr
    def puuid(self):
        # iNW0i7w_cC2kxgNB13UhyGPeyxZChmRqKylZ--bzbZAhFM6EXAImUqeRWmGtK6iKiYbz3bkCV8fMQQ
        return Column(String, nullable=False)

    @declared_attr
    def summoner_level(self):
        # 68
        return Column(Integer, nullable=False)

    @declared_attr
    def summoner_id(self):
        # aEsHyfXA2q8bK-g7GlT4kFK_0uLL3w-jBPyfMAy8kOXTJXo
        return Column(String, nullable=False, primary_key=True)

    @declared_attr
    def account_id(self):
        # -2Ex-VpkkNBN4ceQev8oJsamxY5iGb2liRUqkES5TU_7vtI
        return Column(String, nullable=False)

    @declared_attr
    def rank_soloq_tier(self):
        return Column(Enum(LeagueTier))

    @declared_attr
    def rank_soloq_rank(self):
        return Column(Enum(LeagueRank))

    @declared_attr
    def rank_soloq_points(self):
        return Column(Integer)

    @declared_attr
    def rank_soloq_wins(self):
        return Column(Integer)

    @declared_attr
    def rank_soloq_losses(self):
        return Column(Integer)

    @declared_attr
    def rank_soloq_inactive(self):
        return Column(Boolean)

    @declared_attr
    def rank_soloq_hot_streak(self):
        return Column(Boolean)

    @declared_attr
    def rank_soloq_fresh_blood(self):
        return Column(Boolean)

    @declared_attr
    def rank_soloq_veteran(self):
        return Column(Boolean)

    @declared_attr
    def rank_soloq(self):
        return composite(LeagueLeague,
                         self.rank_soloq_tier,
                         self.rank_soloq_rank,
                         self.rank_soloq_points,
                         self.rank_soloq_wins,
                         self.rank_soloq_losses,
                         self.rank_soloq_inactive,
                         self.rank_soloq_hot_streak,
                         self.rank_soloq_fresh_blood,
                         self.rank_soloq_veteran)

    @declared_attr
    def rank_flexq_tier(self):
        return Column(Enum(LeagueTier))

    @declared_attr
    def rank_flexq_rank(self):
        return Column(Enum(LeagueRank))

    @declared_attr
    def rank_flexq_points(self):
        return Column(Integer)

    @declared_attr
    def rank_flexq_wins(self):
        return Column(Integer)

    @declared_attr
    def rank_flexq_losses(self):
        return Column(Integer)

    @declared_attr
    def rank_flexq_inactive(self):
        return Column(Boolean)

    @declared_attr
    def rank_flexq_hot_streak(self):
        return Column(Boolean)

    @declared_attr
    def rank_flexq_fresh_blood(self):
        return Column(Boolean)

    @declared_attr
    def rank_flexq_veteran(self):
        return Column(Boolean)

    @declared_attr
    def rank_flexq(self):
        return composite(LeagueLeague,
                         self.rank_flexq_tier,
                         self.rank_flexq_rank,
                         self.rank_flexq_points,
                         self.rank_flexq_wins,
                         self.rank_flexq_losses,
                         self.rank_flexq_inactive,
                         self.rank_flexq_hot_streak,
                         self.rank_flexq_fresh_blood,
                         self.rank_flexq_veteran)

    @declared_attr
    def rank_twtrq_tier(self):
        return Column(Enum(LeagueTier))

    @declared_attr
    def rank_twtrq_rank(self):
        return Column(Enum(LeagueRank))

    @declared_attr
    def rank_twtrq_points(self):
        return Column(Integer)

    @declared_attr
    def rank_twtrq_wins(self):
        return Column(Integer)

    @declared_attr
    def rank_twtrq_losses(self):
        return Column(Integer)

    @declared_attr
    def rank_twtrq_inactive(self):
        return Column(Boolean)

    @declared_attr
    def rank_twtrq_hot_streak(self):
        return Column(Boolean)

    @declared_attr
    def rank_twtrq_fresh_blood(self):
        return Column(Boolean)

    @declared_attr
    def rank_twtrq_veteran(self):
        return Column(Boolean)

    @declared_attr
    def rank_twtrq(self):
        return composite(LeagueLeague,
                         self.rank_twtrq_tier,
                         self.rank_twtrq_rank,
                         self.rank_twtrq_points,
                         self.rank_twtrq_wins,
                         self.rank_twtrq_losses,
                         self.rank_twtrq_inactive,
                         self.rank_twtrq_hot_streak,
                         self.rank_twtrq_fresh_blood,
                         self.rank_twtrq_veteran)

    @declared_attr
    def rank_tftq_tier(self):
        return Column(Enum(LeagueTier))

    @declared_attr
    def rank_tftq_rank(self):
        return Column(Enum(LeagueRank))

    @declared_attr
    def rank_tftq_points(self):
        return Column(Integer)

    @declared_attr
    def rank_tftq_wins(self):
        return Column(Integer)

    @declared_attr
    def rank_tftq_losses(self):
        return Column(Integer)

    @declared_attr
    def rank_tftq_inactive(self):
        return Column(Boolean)

    @declared_attr
    def rank_tftq_hot_streak(self):
        return Column(Boolean)

    @declared_attr
    def rank_tftq_fresh_blood(self):
        return Column(Boolean)

    @declared_attr
    def rank_tftq_veteran(self):
        return Column(Boolean)

    @declared_attr
    def rank_tftq(self):
        return composite(LeagueLeague,
                         self.rank_tftq_tier,
                         self.rank_tftq_rank,
                         self.rank_tftq_points,
                         self.rank_tftq_wins,
                         self.rank_tftq_losses,
                         self.rank_tftq_inactive,
                         self.rank_tftq_hot_streak,
                         self.rank_tftq_fresh_blood,
                         self.rank_tftq_veteran)

    @declared_attr
    def mastery_score(self):
        return Column(Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<{self.__class__.__qualname__} {str(self)}>"

    def __str__(self):
        return f"[c]{self.__tablename__}:{self.summoner_name}[/c]"
