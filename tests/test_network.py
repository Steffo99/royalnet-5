import pytest
import uuid
import asyncio
from royalnet.network import Package, RoyalnetLink, RoyalnetServer, ConnectionClosedError


@pytest.fixture
def async_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.mark.skip("Not a test")
def echo_request_handler(message):
    return message


def test_package_serialization():
    pkg = Package({"ciao": "ciao"},
                  source=str(uuid.uuid4()),
                  destination=str(uuid.uuid4()),
                  source_conv_id=str(uuid.uuid4()),
                  destination_conv_id=str(uuid.uuid4()))
    assert pkg == Package.from_dict(pkg.to_dict())
    assert pkg == Package.from_json_string(pkg.to_json_string())
    assert pkg == Package.from_json_bytes(pkg.to_json_bytes())


def test_links(async_loop: asyncio.AbstractEventLoop):
    address, port = "127.0.0.1", 1234
    master = RoyalnetServer(address, port, "test")
    async_loop.run_until_complete(master.start())
    # Test invalid secret
    wrong_secret_link = RoyalnetLink("ws://127.0.0.1:1234", "invalid", "test", echo_request_handler, loop=async_loop)
    with pytest.raises(ConnectionClosedError):
        async_loop.run_until_complete(wrong_secret_link.run())
    # Test regular connection
    link1 = RoyalnetLink("ws://127.0.0.1:1234", "test", "one", echo_request_handler, loop=async_loop)
    link1_run_task = async_loop.create_task(link1.run())
    link2 = RoyalnetLink("ws://127.0.0.1:1234", "test", "two", echo_request_handler, loop=async_loop)
    link2_run_task = async_loop.create_task(link2.run())
    message = {"ciao": "ciao"}
    response = async_loop.run_until_complete(link1.request(message, "two"))
    assert message == response
