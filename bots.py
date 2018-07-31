import multiprocessing
import os
import telegrambot
import discordbot
import time
import platform

discord_telegram_pipe = multiprocessing.Pipe()
discord = multiprocessing.Process(target=discordbot.process, args=(discord_telegram_pipe[0],), daemon=True)
telegram = multiprocessing.Process(target=telegrambot.process, args=(discord_telegram_pipe[1],), daemon=True)

if __name__ == "__main__":
    discord.start()
    telegram.start()
    try:
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
    except KeyboardInterrupt:
        if platform.system() == "Linux":
            os.system("reset")
        print("Stopping...")
        discord_telegram_pipe[0].send("stop")
        time.sleep(30)