import asyncio
from royalnet.bots.telegram import TelegramBot

bot = TelegramBot("375232708:AAExsD_prmxJOXzmJwYZyNUt5zc_EbXxR38")

asyncio.get_event_loop().run_until_complete(bot.run())
