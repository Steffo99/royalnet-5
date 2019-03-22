import pytest
import asyncio
from royalnet.network import RoyalnetLink, RoyalnetServer
from royalnet.network import Message


async def echo(message: Message):
    return message


def test_connection():
    loop = asyncio.SelectorEventLoop()
    server = RoyalnetServer("localhost", 1234, "testing")
    link = RoyalnetLink("ws://localhost:1234", "testing", "testing", echo)
    loop.create_task(server.run())
    loop.run_until_complete(link.run())
    assert link.websocket is not None
    assert link.identify_event.is_set()
    assert len(server.identified_clients) == 1
    assert server.identified_clients[0].link_type == "testing"


def test_request():
    loop = asyncio.SelectorEventLoop()
    server = RoyalnetServer("localhost", 1234, "testing")
    link1 = RoyalnetLink("ws://localhost:1234", "testing", "testing1", echo)
    link2 = RoyalnetLink("ws://localhost:1234", "testing", "testing2", echo)
    loop.create_task(server.run())
    loop.create_task(link1.run())
    loop.create_task(link2.run())
    message = Message()
    response = loop.run_until_complete(link1.request(message, "testing2"))
    assert message is response
