import typing
import riotwatcher
from royalnet.commands import *
from royalnet.utils import *
from ..tables import LeagueOfLegends
from ..utils import LeagueLeague


class LeagueoflegendsCommand(Command):
    name: str = "leagueoflegends"

    aliases = ["lol", "league"]

    description: str = "Connetti un account di League of Legends a un account Royalnet, e visualizzane le statistiche."

    syntax = "[regione] [nomeevocatore] OPPURE [nomeevocatore]"

    tables = {LeagueOfLegends}

    def __init__(self, interface: CommandInterface):
        super().__init__(interface)
        self._riotwatcher = riotwatcher.RiotWatcher(self.interface.bot.get_secret("riotgames"))

    async def run(self, args: CommandArgs, data: CommandData) -> None:
        author = await data.get_author(error_if_none=True)
        name = args.optional(1)

        if not name:
            # Update and display the League of Legends stats for the current account
            if len(author.leagueoflegends) == 0:
                raise CommandError("Nessun account di League of Legends trovato.")
            elif len(author.leagueoflegends) > 1:
                name = args.optional(0)
                if name is None:
                    raise CommandError("Più account di League of Legends sono registrati a questo account.\n"
                                       "Specifica di quale account vuoi vedere le statistiche.\n"
                                       f"Sintassi: [c]{self.interface.prefix}{self.name} [nomeevocatore][/c]")
                for account in author.leagueoflegends:
                    if account.summoner_name == name:
                        leagueoflegends = account
                else:
                    raise CommandError("Nessun account con il nome specificato trovato.")
            else:
                leagueoflegends = author.leagueoflegends[0]
        else:
            region = args[0]
            # Connect a new League of Legends account to Royalnet
            summoner = self._riotwatcher.summoner.by_name(region=region, summoner_name=name)
            # Ensure the account isn't already connected to something else
            leagueoflegends = await asyncify(data.session.query(self.alchemy.LeagueOfLegends).filter_by(summoner_id=summoner["id"]).one_or_none())
            if leagueoflegends:
                raise CommandError(f"L'account {leagueoflegends} è già registrato su Royalnet.")
            # Get rank information
            leagues = self._riotwatcher.league.by_summoner(region=region, encrypted_summoner_id=summoner["id"])
            soloq = None
            flexq = None
            twtrq = None
            tftq = None
            for league in leagues:
                if league["queueType"] == "RANKED_SOLO_5x5":
                    soloq = league
                if league["queueType"] == "RANKED_FLEX_SR":
                    flexq = league
                if league["queueType"] == "RANKED_FLEX_TT":
                    twtrq = league
                if league["queueType"] == "RANKED_TFT":
                    tftq = league
            # Get mastery score
            mastery = self._riotwatcher.champion_mastery.by_summoner(region=region, encrypted_summoner_id=summoner["id"])
            # Create database row
            leagueoflegends = self.alchemy.LeagueOfLegends(
                region=region,
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
            data.session.add(leagueoflegends)
            await data.session_commit()
            await data.reply(f"↔️ Account {leagueoflegends} connesso a {author}!")
