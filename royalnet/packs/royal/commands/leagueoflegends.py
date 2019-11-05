import typing
import riotwatcher
import logging
import asyncio
import sentry_sdk
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

    _telegram_group_id = -1001153723135

    def __init__(self, interface: CommandInterface):
        super().__init__(interface)
        self._riotwatcher = riotwatcher.RiotWatcher(api_key=self.interface.bot.get_secret("leagueoflegends"))
        if self.interface.name == "telegram":
            self.loop.create_task(self._updater(900))

    async def _send(self, message):
        client = self.interface.bot.client
        await self.interface.bot.safe_api_call(client.send_message,
                                               chat_id=self._telegram_group_id,
                                               text=telegram_escape(message),
                                               parse_mode="HTML",
                                               disable_webpage_preview=True)

    async def _notify(self,
                      obj: LeagueOfLegends,
                      attribute_name: str,
                      old_value: typing.Any,
                      new_value: typing.Any):
        if self.interface.name == "telegram":
            if isinstance(old_value, LeagueLeague):
                # This is a rank change!
                # Don't send messages for every rank change, send messages just if the TIER or RANK changes!
                if old_value.tier == new_value.tier and old_value.rank == new_value.rank:
                    return
                # Find the queue
                queue_names = {
                    "rank_soloq": "Solo/Duo",
                    "rank_flexq": "Flex",
                    "rank_twtrq": "3v3",
                    "rank_tftq": "TFT"
                }
                # Prepare the message
                if new_value > old_value:
                    message = f"📈 [b]{obj.user}[/b] è salito a {new_value} su League of Legends " \
                              f"({queue_names[attribute_name]})! Congratulazioni!"
                else:
                    message = f"📉 [b]{obj.user}[/b] è sceso a {new_value} su League of Legends " \
                              f"({queue_names[attribute_name]})."
                # Send the message
                await self._send(message)
            # Level up!
            elif attribute_name == "summoner_level":
                if new_value == 30 or (new_value >= 50 and (new_value % 25 == 0)):
                    await self._send(f"🆙 [b]{obj.user}[/b] è salito al livello [b]{new_value}[/b] su League of Legends!")

    @staticmethod
    async def _change(obj: LeagueOfLegends,
                      attribute_name: str,
                      new_value: typing.Any,
                      callback: typing.Callable[
                          [LeagueOfLegends, str, typing.Any, typing.Any], typing.Awaitable[None]]):
        old_value = obj.__getattribute__(attribute_name)
        if old_value != new_value:
            await callback(obj, attribute_name, old_value, new_value)
        obj.__setattr__(attribute_name, new_value)

    async def _update(self, lol: LeagueOfLegends):
        log.info(f"Updating: {lol}")
        log.debug(f"Getting summoner data: {lol}")
        summoner = await asyncify(self._riotwatcher.summoner.by_id, region=self._region,
                                  encrypted_summoner_id=lol.summoner_id)
        await self._change(lol, "profile_icon_id", summoner["profileIconId"], self._notify)
        await self._change(lol, "summoner_name", summoner["name"], self._notify)
        await self._change(lol, "puuid", summoner["puuid"], self._notify)
        await self._change(lol, "summoner_level", summoner["summonerLevel"], self._notify)
        await self._change(lol, "summoner_id", summoner["id"], self._notify)
        await self._change(lol, "account_id", summoner["accountId"], self._notify)
        log.debug(f"Getting leagues data: {lol}")
        leagues = await asyncify(self._riotwatcher.league.by_summoner, region=self._region,
                                 encrypted_summoner_id=lol.summoner_id)
        soloq = LeagueLeague()
        flexq = LeagueLeague()
        twtrq = LeagueLeague()
        tftq = LeagueLeague()
        for league in leagues:
            if league["queueType"] == "RANKED_SOLO_5x5":
                soloq = LeagueLeague.from_dict(league)
            if league["queueType"] == "RANKED_FLEX_SR":
                flexq = LeagueLeague.from_dict(league)
            if league["queueType"] == "RANKED_FLEX_TT":
                twtrq = LeagueLeague.from_dict(league)
            if league["queueType"] == "RANKED_TFT":
                tftq = LeagueLeague.from_dict(league)
        await self._change(lol, "rank_soloq", soloq, self._notify)
        await self._change(lol, "rank_flexq", flexq, self._notify)
        await self._change(lol, "rank_twtrq", twtrq, self._notify)
        await self._change(lol, "rank_tftq", tftq, self._notify)
        log.debug(f"Getting mastery data: {lol}")
        mastery = await asyncify(self._riotwatcher.champion_mastery.scores_by_summoner, region=self._region,
                                 encrypted_summoner_id=lol.summoner_id)
        await self._change(lol, "mastery_score", mastery, self._notify)

    async def _updater(self, period: int):
        log.info(f"Started updater with {period}s period")
        while True:
            log.info(f"Updating...")
            session = self.alchemy.Session()
            log.info("")
            lols = session.query(self.alchemy.LeagueOfLegends).all()
            for lol in lols:
                try:
                    await self._update(lol)
                except Exception as e:
                    sentry_sdk.capture_exception(e)
                    log.error(f"Error while updating {lol.user.username}: {e}")
                await asyncio.sleep(1)
            await asyncify(session.commit)
            session.close()
            log.info(f"Sleeping for {period}s")
            await asyncio.sleep(period)

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
            soloq = LeagueLeague()
            flexq = LeagueLeague()
            twtrq = LeagueLeague()
            tftq = LeagueLeague()
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
            message = ""
            for account in author.leagueoflegends:
                try:
                    await self._update(account)
                    message += self._display(account)
                except riotwatcher.ApiError as e:
                    message += f"⚠️ [b]{account.summoner_name}[/b]\n" \
                               f"{e}"
                message += "\n"
            await data.session_commit()
            await data.reply(message)
