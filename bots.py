import multiprocessing
import telegrambot
import discordbot
import redditbot
import statsupdate
import time
import logging
import coloredlogs
import os

os.environ["COLOREDLOGS_LOG_FORMAT"] = "%(asctime)s %(levelname)s %(name)s %(message)s"

logging.getLogger().disabled = True
logger = logging.getLogger(__name__)
coloredlogs.install(level="DEBUG", logger=logger)

discord_telegram_pipe = multiprocessing.Pipe()
discord = multiprocessing.Process(target=discordbot.process, args=(discord_telegram_pipe[0],), daemon=True)
telegram = multiprocessing.Process(target=telegrambot.process, args=(discord_telegram_pipe[1],), daemon=True)
reddit = multiprocessing.Process(target=redditbot.process, daemon=True)
stats = multiprocessing.Process(target=statsupdate.process, daemon=True)

if __name__ == "__main__":
    logger.info("Starting Discord Bot process...")
    discord.start()
    logger.info("Starting Telegram Bot process...")
    telegram.start()
    logger.info("Starting Reddit Bot process...")
    reddit.start()
    logger.info("Starting StatsUpdate process...")
    stats.start()
    try:
        while True:
            if discord.exitcode is not None:
                logger.warning(f"Discord Bot exited with {discord.exitcode}")
                del discord
                logger.info("Restarting Discord Bot process...")
                discord = multiprocessing.Process(target=discordbot.process, args=(discord_telegram_pipe[0],), daemon=True)
                discord.start()
            if telegram.exitcode is not None:
                logger.warning(f"Telegram Bot exited with {telegram.exitcode}")
                del telegram
                telegram = multiprocessing.Process(target=telegrambot.process, args=(discord_telegram_pipe[1],), daemon=True)
                logger.info("Restarting Telegram Bot process...")
                telegram.start()
            if reddit.exitcode is not None:
                logger.warning(f"Reddit Bot exited with {reddit.exitcode}")
                del reddit
                reddit = multiprocessing.Process(target=redditbot.process, daemon=True)
                logger.info("Restarting Reddit Bot process...")
                reddit.start()
            if stats.exitcode is not None:
                logger.warning(f"StatsUpdater exited with {stats.exitcode}")
                del stats
                stats = multiprocessing.Process(target=statsupdate.process, daemon=True)
                logger.info("Restarting StatsUpdate process...")
                stats.start()
            time.sleep(10)
    except KeyboardInterrupt:
        logger.info("Now stopping...")
        logger.info("Asking Discord process to stop...")
        discord_telegram_pipe[0].send("stop")
        logger.info("Waiting for Discord Bot process to stop...")
        discord.join()
        logger.info("Waiting for Telegram Bot process to stop...")
        telegram.join()
        logger.info("Waiting for Reddit Bot process to stop...")
        reddit.join()
        logger.info("Waiting for StatsUpdate process to stop...")
        stats.join()
