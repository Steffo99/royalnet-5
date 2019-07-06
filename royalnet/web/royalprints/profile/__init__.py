"""The profile page :py:class:`royalnet.web.Royalprint` for Royalnet members."""

import flask as f
import os
from ... import Royalprint
from ....database.tables import *


# Maybe some of these tables are optional...
tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
rp = Royalprint("profile", __name__, url_prefix="/profile", template_folder=tmpl_dir,
                required_tables={Royal, ActiveKvGroup, Alias, Diario, Discord, Keygroup, Keyvalue, Telegram, WikiPage,
                                 WikiRevision})


@rp.route("/")
def profile_index():
    alchemy, alchemy_session = f.current_app.config["ALCHEMY"], f.current_app.config["ALCHEMY_SESSION"]
    royals = alchemy_session.query(alchemy.Royal).order_by(alchemy.Royal.username).all()
    return f.render_template("profile_index.html", royals=royals)


@rp.route("/<username>")
def profile_by_username(username):
    alchemy, alchemy_session = f.current_app.config["ALCHEMY"], f.current_app.config["ALCHEMY_SESSION"]
    royal = alchemy_session.query(alchemy.Royal).filter_by(username=username).one_or_none()
    if royal is None:
        return "No such user", 404
    return f.render_template("profile_page.html", royal=royal)
