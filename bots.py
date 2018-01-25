import multiprocessing
import telegrambot
import discordbot
import time

discord_telegram_pipe = multiprocessing.Pipe()
discord = multiprocessing.Process(target=discordbot.process, args=(discord_telegram_pipe[0],), daemon=True)
telegram = multiprocessing.Process(target=telegrambot.process, args=(discord_telegram_pipe[1],), daemon=True)

if __name__ == "__main__":
    discord.start()
    telegram.start()
    while True:
        if discord.exitcode is not None:
            print("Restarting Discord Bot...")
            del discord
            discord = multiprocessing.Process(target=discordbot.process, args=(discord_telegram_pipe[0],), daemon=True)
            discord.start()
        if telegram.exitcode is not None:
            print("Restarting Telegram Bot...")
            del telegram
            telegram = multiprocessing.Process(target=telegrambot.process, args=(discord_telegram_pipe[1],), daemon=True)
            telegram.start()
        time.sleep(60)