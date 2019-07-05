"""A Royal Games Diario viewer :py:class:`royalnet.web.Royalprint`."""

import flask as f
import os
from ... import Royalprint
from ....database.tables import Royal, WikiPage, WikiRevision


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
rp = Royalprint("diarioview", __name__, url_prefix="/diarioview", template_folder=tmpl_dir,
                required_tables={Royal, WikiPage, WikiRevision})


@rp.route("/", defaults={"page": 0})
@rp.route("/<int:page>")
def diarioview_index(page):
    alchemy, alchemy_session = f.current_app.config["ALCHEMY"], f.current_app.config["ALCHEMY_SESSION"]
    return "TODO"
