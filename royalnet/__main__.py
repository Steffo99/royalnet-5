import logging
import multiprocessing
import time
from typing import *

import click
import toml

import royalnet.serf as rs
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
@click.option("-c", "--config-file", default="./config.toml", type=click.File(encoding="utf8"),
              help="The filename of the Royalnet configuration file.")
def run(config_file: str):
    # Read the configuration file
    config: dict = toml.load(config_file)

    ru.init_logging(config["Logging"])

    if config["Sentry"] is None or not config["Sentry"]["enabled"]:
        log.info("Sentry: disabled")
    else:
        try:
            ru.init_sentry(config["Sentry"])
        except ImportError:
            log.info("Sentry: not installed")
        else:
            log.info("Sentry: enabled")

    processes: Dict[str, ru.RoyalnetProcess] = {}
    """A list of all processes that the launcher should start and monitor."""

    herald_cfg = config.get("Herald")
    if rh is None:
        log.info("Herald: Not installed")
    elif herald_cfg is None:
        log.warning("Herald: Not configured")
    elif not herald_cfg["enabled"]:
        log.info("Herald: Disabled")
    elif herald_cfg["mode"] == "local":
        log.info("Herald: Enabled (local server)")

        def herald_constructor() -> multiprocessing.Process:
            # Create a Herald server
            herald_server = rh.Server(rh.Config.from_config(name="<server>", **herald_cfg))
            # Run the Herald server on a new process
            return multiprocessing.Process(
                name="Herald.Local",
                target=herald_server.run_blocking,
                daemon=True,
                kwargs={
                    "logging_cfg": config["Logging"]
                }
            )

        processes["Herald"] = ru.RoyalnetProcess(herald_constructor, None)
    elif herald_cfg["mode"] == "remote":
        log.info("Herald: Enabled (remote server)")
    else:
        log.error(f"Invalid Herald mode: {herald_cfg['mode']}")

    # Serfs
    serfs_cfg = config.get("Serfs")
    if serfs_cfg is None:
        log.warning("__serfs__: Not configured")
    else:
        log.debug("__serfs__: Configured")

        def configure_serf(n: str, module, class_: Type[rs.Serf]):
            serf_cfg = serfs_cfg.get(n)
            if module is None:
                log.info(f"Serf.{n}: Not installed")
            elif serf_cfg is None:
                log.warning(f"Serf.{n}: Not configured")
            elif not serf_cfg["enabled"]:
                log.info(f"Serf.{n}: Disabled")
            else:
                def serf_constructor() -> multiprocessing.Process:
                    return multiprocessing.Process(
                        name=f"Serf.{n}",
                        target=class_.run_process,
                        daemon=True,
                        kwargs={
                            "alchemy_cfg": config["Alchemy"],
                            "herald_cfg": herald_cfg,
                            "packs_cfg": config["Packs"],
                            "sentry_cfg": config["Sentry"],
                            "logging_cfg": config["Logging"],
                            "serf_cfg": serf_cfg,
                        }
                    )

                processes[f"Serf.{n}"] = ru.RoyalnetProcess(serf_constructor, None)
                log.info(f"Serf.{n}: Enabled")

        configure_serf("Telegram", rst, rst.TelegramSerf)
        configure_serf("Discord", rsd, rsd.DiscordSerf)

    # Constellation
    constellation_cfg = config.get("Constellation")
    if rc is None:
        log.info(f"Constellation: Not installed")
    elif constellation_cfg is None:
        log.warning(f"Constellation: Not configured")
    elif not constellation_cfg["enabled"]:
        log.info(f"Constellation: Disabled")
    else:
        def constellation_constructor() -> multiprocessing.Process:
            return multiprocessing.Process(
                name="Constellation",
                target=rc.Constellation.run_process,
                daemon=True,
                kwargs={
                    "alchemy_cfg": config["Alchemy"],
                    "herald_cfg": herald_cfg,
                    "packs_cfg": config["Packs"],
                    "sentry_cfg": config["Sentry"],
                    "logging_cfg": config["Logging"],
                    "constellation_cfg": config["Constellation"],
                }
            )

        processes["Constellation"] = ru.RoyalnetProcess(constellation_constructor, None)

        log.info("Constellation: Enabled")

    try:
        # Monitor processes
        while True:
            log.debug("Checking process status...")
            for name, process in processes.items():
                if process.current_process is None:
                    log.info(f"{name}: Starting...")
                    process.current_process = process.constructor()
                    process.current_process.start()
                elif not process.current_process.is_alive():
                    log.error(f"{name}: Process is dead, restarting...")
                    process.current_process = process.constructor()
                    process.current_process.start()
            log.debug("Done, checking again in 60 seconds.")
            time.sleep(60)
    except KeyboardInterrupt:
        log.info("Received SIGTERM, stopping everything!")
        for name, process in processes.items():
            log.info(f"{name}: Killing...")
            process.current_process.kill()
        log.info("Goodbye!")


if __name__ == "__main__":
    run()
