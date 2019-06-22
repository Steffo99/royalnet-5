"""Minecraft server status :py:class:`royalnet.web.Royalprint`."""
import os
import flask as f
import socket
from ... import Royalprint
from mcstatus import MinecraftServer


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
rp = Royalprint("mcstatus", __name__, url_prefix="/mcstatus", template_folder=tmpl_dir)


@rp.route("/<server_str>")
def mcstatus_index(server_str: str):
    try:
        if ":" not in server_str:
            server_str += ":25565"
        server = MinecraftServer.lookup(server_str)
        status = server.status()
        try:
            query = server.query()
        except (socket.timeout, ConnectionRefusedError, OSError):
            query = None
    except socket.gaierror:
        return "No such address", 404
    except (socket.timeout, ConnectionRefusedError, OSError):
        status = None
        query = None
    return f.render_template("mcstatus.html", server_str=server_str, status=status, query=query)
