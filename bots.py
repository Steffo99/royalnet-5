import multiprocessing
import telegrambot
import discordbot
import redditbot
import statsupdater
import time
import logging
import coloredlogs

logging.getLogger().setLevel(level=logging.ERROR)
logger = logging.getLogger(__name__)
coloredlogs.install(level="DEBUG", logger=logger)

discord_telegram_pipe = multiprocessing.Pipe()
discord = multiprocessing.Process(target=discordbot.process, args=(discord_telegram_pipe[0],), daemon=True)
telegram = multiprocessing.Process(target=telegrambot.process, args=(discord_telegram_pipe[1],), daemon=True)
reddit = multiprocessing.Process(target=redditbot.process, daemon=True)
stats = multiprocessing.Process(target=statsupdater.process, daemon=True)

if __name__ == "__main__":
    logging.info("Starting Discord Bot process...")
    discord.start()
    logging.info("Starting Telegram Bot process...")
    telegram.start()
    logging.info("Starting Reddit Bot process...")
    reddit.start()
    logging.info("Starting StatsUpdater process...")
    stats.start()
    try:
        while True:
            if discord.exitcode is not None:
                logging.warning(f"Discord Bot exited with {discord.exitcode}")
                del discord
                logging.info("Restarting Discord Bot process...")
                discord = multiprocessing.Process(target=discordbot.process, args=(discord_telegram_pipe[0],), daemon=True)
                discord.start()
            if telegram.exitcode is not None:
                logging.warning(f"Telegram Bot exited with {telegram.exitcode}")
                del telegram
                telegram = multiprocessing.Process(target=telegrambot.process, args=(discord_telegram_pipe[1],), daemon=True)
                logging.info("Restarting Telegram Bot process...")
                telegram.start()
            if reddit.exitcode is not None:
                logging.warning(f"Reddit Bot exited with {reddit.exitcode}")
                del reddit
                reddit = multiprocessing.Process(target=redditbot.process, daemon=True)
                logging.info("Restarting Reddit Bot process...")
                reddit.start()
            if stats.exitcode is not None:
                logging.warning(f"StatsUpdater exited with {stats.exitcode}")
                del stats
                stats = multiprocessing.Process(target=statsupdater.process, daemon=True)
                logging.info("Restarting StatsUpdater process...")
                stats.start()
            time.sleep(10)
    except KeyboardInterrupt:
        logging.info("Now stopping...")
        logging.info("Asking Discord process to stop...")
        discord_telegram_pipe[0].send("stop")
        logging.info("Waiting for Discord Bot process to stop...")
        discord.join()
        logging.info("Waiting for Telegram Bot process to stop...")
        telegram.join()
        logging.info("Waiting for Reddit Bot process to stop...")
        reddit.join()
        logging.info("Waiting for StatsUpdater process to stop...")
        stats.join()
