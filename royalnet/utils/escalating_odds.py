import random
import datetime
import logging

log = logging.getLogger(__name__)


def escalating_odds(target_day: datetime.datetime) -> bool:
    time_left: datetime.timedelta = target_day - datetime.datetime.now()
    log.debug(f"Time left is {time_left}")

    if time_left.total_seconds() <= 0:
        log.debug("Target has passed, autorolling a success")
        return True

    odds = 1 / (time_left.days + 1)
    result = random.uniform(0, 1) <= odds
    log.debug(f"Odds are {odds}, rolled a {result}")
    return result
