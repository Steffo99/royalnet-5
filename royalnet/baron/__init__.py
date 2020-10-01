from typing import *
import redis
import redis.client
import threading

__all__ = [
    "Baron"
]


class Baron:
    def __init__(self, baron_cfg):
        self.publisher: redis.Redis = redis.Redis(
            host=baron_cfg["host"],
            port=baron_cfg["port"],
            db=baron_cfg["db"],
            password=baron_cfg["password"]
        )
        self.listener: redis.client.PubSub = self.publisher.pubsub()

    def publish(self, channel: str, message):
        self.publisher.publish(channel=channel, message=message)

    def subscribe(self, channel: str, callback: Callable):
        self.listener.subscribe({
            channel: callback
        })

    def listen(self):
        self.listener.listen()
