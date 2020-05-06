import click
import multiprocessing
import toml
import logging
import royalnet.utils as ru

try:
    import royalnet.serf.telegram as rst
except ImportError:
    rst = None

try:
    import royalnet.serf.discord as rsd
except ImportError:
    rsd = None

try:
    import royalnet.serf.matrix as rsm
except ImportError:
    rsm = None

try:
    import royalnet.constellation as rc
except ImportError:
    rc = None

try:
    import royalnet.herald as rh
except ImportError:
    rh = None

try:
    import coloredlogs
except ImportError:
    coloredlogs = None


log = logging.getLogger(__name__)


@click.command()
@click.option("-c", "--config-filename", default="./config.toml", type=click.Path(exists=True),
              help="The filename of the Royalnet configuration file.")
def run(config_filename: str):
    # Read the configuration file
    with open(config_filename, "r") as t:
        config: dict = toml.load(t)

    ru.init_logging(config["Logging"])

    if config["Sentry"] is None or not config["Sentry"]["enabled"]:
        log.info("Sentry: disabled")
    else:
        try:
            ru.init_sentry(config["Sentry"])
        except ImportError:
            log.info("Sentry: not installed")

    # Herald Server
    herald_cfg = None
    herald_process = None
    if rh is not None and "Herald" in config:
        if "Local" in config["Herald"] and config["Herald"]["Local"]["enabled"]:
            # Create a Herald server
            herald_server = rh.Server(rh.Config.from_config(name="<server>", **config["Herald"]["Local"]))
            # Run the Herald server on a new process
            herald_process = multiprocessing.Process(name="Herald.Local",
                                                     target=herald_server.run_blocking,
                                                     daemon=True,
                                                     kwargs={
                                                         "logging_cfg": config["Logging"]
                                                     })
            herald_process.start()
            herald_cfg = config["Herald"]["Local"]
            log.info("Herald: Enabled (Local)")
        elif "Remote" in config["Herald"] and config["Herald"]["Remote"]["enabled"]:
            log.info("Herald: Enabled (Remote)")
            herald_cfg = config["Herald"]["Remote"]
        else:
            log.info("Herald: Disabled")
    else:
        log.info("Herald: Disabled")

    # Serfs
    telegram_process = None
    if rst is not None and "Telegram" in config["Serfs"] and config["Serfs"]["Telegram"]["enabled"]:
        telegram_process = multiprocessing.Process(name="Serf.Telegram",
                                                   target=rst.TelegramSerf.run_process,
                                                   daemon=True,
                                                   kwargs={
                                                       "alchemy_cfg": config["Alchemy"],
                                                       "herald_cfg": herald_cfg,
                                                       "packs_cfg": config["Packs"],
                                                       "sentry_cfg": config["Sentry"],
                                                       "logging_cfg": config["Logging"],
                                                       "serf_cfg": config["Serfs"]["Telegram"],
                                                   })
        telegram_process.start()
        log.info("Serf.Telegram: Started")
    else:
        log.info("Serf.Telegram: Disabled")

    discord_process = None
    if rsd is not None and "Discord" in config["Serfs"] and config["Serfs"]["Discord"]["enabled"]:
        discord_process = multiprocessing.Process(name="Serf.Discord",
                                                  target=rsd.DiscordSerf.run_process,
                                                  daemon=True,
                                                  kwargs={
                                                      "alchemy_cfg": config["Alchemy"],
                                                      "herald_cfg": herald_cfg,
                                                      "packs_cfg": config["Packs"],
                                                      "sentry_cfg": config["Sentry"],
                                                      "logging_cfg": config["Logging"],
                                                      "serf_cfg": config["Serfs"]["Discord"],
                                                  })
        discord_process.start()
        log.info("Serf.Discord: Started")
    else:
        log.info("Serf.Discord: Disabled")

    matrix_process = None
    if rsm is not None and "Matrix" in config["Serfs"] and config["Serfs"]["Matrix"]["enabled"]:
        matrix_process = multiprocessing.Process(name="Serf.Matrix",
                                                 target=rsm.MatrixSerf.run_process,
                                                 daemon=True,
                                                 kwargs={
                                                     "alchemy_cfg": config["Alchemy"],
                                                     "herald_cfg": herald_cfg,
                                                     "packs_cfg": config["Packs"],
                                                     "sentry_cfg": config["Sentry"],
                                                     "logging_cfg": config["Logging"],
                                                     "serf_cfg": config["Serfs"]["Matrix"],
                                                 })
        matrix_process.start()
        log.info("Serf.Matrix: Started")
    else:
        log.info("Serf.Matrix: Disabled")

    # Constellation
    constellation_process = None
    if rc is not None and "Constellation" in config and config["Constellation"]["enabled"]:
        constellation_process = multiprocessing.Process(name="Constellation",
                                                        target=rc.Constellation.run_process,
                                                        daemon=True,
                                                        kwargs={
                                                            "alchemy_cfg": config["Alchemy"],
                                                            "herald_cfg": herald_cfg,
                                                            "packs_cfg": config["Packs"],
                                                            "sentry_cfg": config["Sentry"],
                                                            "logging_cfg": config["Logging"],
                                                            "constellation_cfg": config["Constellation"],
                                                        })
        constellation_process.start()
        log.info("Constellation: Started")
    else:
        log.info("Constellation: Disabled")

    log.info("All processes started!")
    if constellation_process is not None:
        log.info("Waiting for Constellation to stop...")
        constellation_process.join()
    if telegram_process is not None:
        log.info("Waiting for Serf.Telegram to stop...")
        telegram_process.join()
    if discord_process is not None:
        log.info("Waiting for Serf.Discord to stop...")
        discord_process.join()
    if matrix_process is not None:
        log.info("Waiting for Serf.Matrix to stop...")
        matrix_process.join()
    if herald_process is not None:
        log.info("Waiting for Herald to stop...")
        herald_process.join()


if __name__ == "__main__":
    run()
