import click
import multiprocessing
import toml
import logging
import royalnet.constellation as rc
import royalnet.serf.telegram as rst
import royalnet.serf.discord as rsd
import royalnet.serf.matrix as rsm
import royalnet.utils as ru
import royalnet.herald as rh

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
    if config["Herald"]["Local"]["enabled"]:
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
    elif config["Herald"]["Remote"]["enabled"]:
        log.info("Herald: Enabled (Remote)")
        herald_cfg = config["Herald"]["Remote"]
    else:
        log.info("Herald: Disabled")

    # Serfs
    telegram_process = None
    if "Telegram" in config["Serfs"] and config["Serfs"]["Telegram"]["enabled"]:
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
    if "Discord" in config["Serfs"] and config["Serfs"]["Discord"]["enabled"]:
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
    if "Matrix" in config["Serfs"] and config["Serfs"]["Matrix"]["enabled"]:
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
        log.info("Serf.Discord: Started")
    else:
        log.info("Serf.Discord: Disabled")

    # Constellation
    constellation_process = None
    if config["Constellation"]["enabled"]:
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
        constellation_process.join()
    if telegram_process is not None:
        telegram_process.join()
    if discord_process is not None:
        discord_process.join()
    if herald_process is not None:
        herald_process.join()


if __name__ == "__main__":
    run()
