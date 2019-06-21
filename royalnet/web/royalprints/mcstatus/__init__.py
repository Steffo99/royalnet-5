"""Minecraft server status :py:class:`royalnet.web.Royalprint`."""
import flask as f
from ... import Royalprint
from mcstatus import MinecraftServer


rp = Royalprint("mcstatus", __name__, url_prefix="/mcstatus")


@rp.route("/<server_str>")
def mcstatus_index(server_str: str):
    server = MinecraftServer(server_str)
    # TODO
    ...
