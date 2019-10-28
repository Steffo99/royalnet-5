import typing
import riotwatcher
import logging
from royalnet.commands import *
from royalnet.utils import *
from ..tables import LeagueOfLegends
from ..utils import LeagueLeague


log = logging.getLogger(__name__)


class LeagueoflegendsCommand(Command):
    name: str = "leagueoflegends"

    aliases = ["lol", "league"]

    description: str = "Connetti un account di League of Legends a un account Royalnet, e visualizzane le statistiche."

    syntax = "[nomeevocatore]"
    
    tables = {LeagueOfLegends}
    
    _region = "euw1"

    def __init__(self, interface: CommandInterface):
        super().__init__(interface)
        self._riotwatcher = riotwatcher.RiotWatcher(api_key=self.interface.bot.get_secret("leagueoflegends"))
        ...

    async def _update(self, lol: LeagueOfLegends):
        log.info(f"Updating: {lol}")
        log.debug(f"Getting summoner data: {lol}")
        summoner = self._riotwatcher.summoner.by_id(region=self._region, encrypted_summoner_id=lol.summoner_id)
        lol.profile_icon_id = summoner["profileIconId"]
        lol.summoner_name = summoner["name"]
        lol.puuid = summoner["puuid"]
        lol.summoner_level = summoner["summonerLevel"]
        lol.summoner_id = summoner["id"]
        lol.account_id = summoner["accountId"]
        log.debug(f"Getting leagues data: {lol}")
        leagues = self._riotwatcher.league.by_summoner(region=self._region, encrypted_summoner_id=lol.summoner_id)
        soloq = None
        flexq = None
        twtrq = None
        tftq = None
        for league in leagues:
            if league["queueType"] == "RANKED_SOLO_5x5":
                soloq = LeagueLeague.from_dict(league)
            if league["queueType"] == "RANKED_FLEX_SR":
                flexq = LeagueLeague.from_dict(league)
            if league["queueType"] == "RANKED_FLEX_TT":
                twtrq = LeagueLeague.from_dict(league)
            if league["queueType"] == "RANKED_TFT":
                tftq = LeagueLeague.from_dict(league)
        lol.rank_soloq = soloq
        lol.rank_flexq = flexq
        lol.rank_twtrq = twtrq
        lol.rank_tftq = tftq
        log.debug(f"Getting mastery data: {lol}")
        mastery = self._riotwatcher.champion_mastery.scores_by_summoner(region=self._region, encrypted_summoner_id=lol.summoner_id)
        lol.mastery_score = mastery

    def _display(self, lol: LeagueOfLegends):
        string = f"ℹ️ [b]{lol.summoner_name}[/b]\n" \
                 f"Lv. {lol.summoner_level}\n" \
                 f"Mastery score: {lol.mastery_score}\n" \
                 f"\n"
        if lol.rank_soloq:
            string += f"Solo: {lol.rank_soloq}\n"
        if lol.rank_flexq:
            string += f"Flex: {lol.rank_flexq}\n"
        if lol.rank_twtrq:
            string += f"3v3: {lol.rank_twtrq}\n"
        if lol.rank_tftq:
            string += f"TFT: {lol.rank_tftq}\n"
        return string

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        author = await data.get_author(error_if_none=True)

        name = args.joined()

        if name:
            # Create new LeagueOfLegends
            name = args.joined(require_at_least=2).split(" ", 1)[1]
            # Connect a new League of Legends account to Royalnet
            log.debug(f"Searching for: {name}")
            summoner = self._riotwatcher.summoner.by_name(region=self._region, summoner_name=name)
            # Ensure the account isn't already connected to something else
            leagueoflegends = await asyncify(
                data.session.query(self.alchemy.LeagueOfLegends).filter_by(summoner_id=summoner["id"]).one_or_none)
            if leagueoflegends:
                raise CommandError(f"L'account {leagueoflegends} è già registrato su Royalnet.")
            # Get rank information
            log.debug(f"Getting leagues data: {name}")
            leagues = self._riotwatcher.league.by_summoner(region=self._region, encrypted_summoner_id=summoner["id"])
            soloq = None
            flexq = None
            twtrq = None
            tftq = None
            for league in leagues:
                if league["queueType"] == "RANKED_SOLO_5x5":
                    soloq = LeagueLeague.from_dict(league)
                if league["queueType"] == "RANKED_FLEX_SR":
                    flexq = LeagueLeague.from_dict(league)
                if league["queueType"] == "RANKED_FLEX_TT":
                    twtrq = LeagueLeague.from_dict(league)
                if league["queueType"] == "RANKED_TFT":
                    tftq = LeagueLeague.from_dict(league)
            # Get mastery score
            log.debug(f"Getting mastery data: {name}")
            mastery = self._riotwatcher.champion_mastery.scores_by_summoner(region=self._region,
                                                                            encrypted_summoner_id=summoner["id"])
            # Create database row
            leagueoflegends = self.alchemy.LeagueOfLegends(
                region=self._region,
                user=author,
                profile_icon_id=summoner["profileIconId"],
                summoner_name=summoner["name"],
                puuid=summoner["puuid"],
                summoner_level=summoner["summonerLevel"],
                summoner_id=summoner["id"],
                account_id=summoner["accountId"],
                rank_soloq=soloq,
                rank_flexq=flexq,
                rank_twtrq=twtrq,
                rank_tftq=tftq,
                mastery_score=mastery
            )
            log.debug(f"Saving to the DB: {name}")
            data.session.add(leagueoflegends)
            await data.session_commit()
            await data.reply(f"↔️ Account {leagueoflegends} connesso a {author}!")
        else:
            # Update and display the League of Legends stats for the current account
            if len(author.leagueoflegends) == 0:
                raise CommandError("Nessun account di League of Legends trovato.")
            for account in author.leagueoflegends:
                await self._update(account)
            await data.session_commit()
            message = ""
            for account in author.leagueoflegends:
                message += self._display(account)
            await data.reply(message)
