import multiprocessing
import os
import telegrambot
import discordbot
import time
import platform
import logging

logging.getLogger().setLevel(level=logging.ERROR)
logging.getLogger(__name__).setLevel(level=logging.DEBUG)

discord_telegram_pipe = multiprocessing.Pipe()
discord = multiprocessing.Process(target=discordbot.process, args=(discord_telegram_pipe[0],), daemon=True)
telegram = multiprocessing.Process(target=telegrambot.process, args=(discord_telegram_pipe[1],), daemon=True)

if __name__ == "__main__":
    logging.info("Starting Discord process...")
    discord.start()
    logging.info("Starting Telegram process...")
    telegram.start()
    try:
        while True:
            if discord.exitcode is not None:
                logging.warning(f"Discord Bot exited with {discord.exitcode}")
                del discord
                logging.info("Starting Discord process...")
                discord = multiprocessing.Process(target=discordbot.process, args=(discord_telegram_pipe[0],), daemon=True)
                discord.start()
            if telegram.exitcode is not None:
                logging.warning(f"Telegram Bot exited with {discord.exitcode}")
                del telegram
                telegram = multiprocessing.Process(target=telegrambot.process, args=(discord_telegram_pipe[1],), daemon=True)
                logging.info("Starting Telegram process...")
                telegram.start()
            time.sleep(10)
    except KeyboardInterrupt:
        logging.info("Now stopping...")
        if platform.system() == "Linux":
            os.system("reset")
        logging.info("Asking Discord process to stop...")
        discord_telegram_pipe[0].send("stop")
        logging.info("Waiting for Discord process to stop...")
        time.sleep(30)
