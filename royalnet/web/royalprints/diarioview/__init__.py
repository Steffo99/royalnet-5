"""A Royal Games Diario viewer :py:class:`royalnet.web.Royalprint`."""

import flask as f
import os
from ... import Royalprint
from ....database.tables import Royal, Diario


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
rp = Royalprint("diarioview", __name__, url_prefix="/diario", template_folder=tmpl_dir,
                required_tables={Royal, Diario})


@rp.route("/", defaults={"page": 1})
@rp.route("/<int:page>")
def diarioview_page(page):
    alchemy, alchemy_session = f.current_app.config["ALCHEMY"], f.current_app.config["ALCHEMY_SESSION"]
    if page < 1:
        return "Page should be >1", 404
    entries = alchemy_session.query(alchemy.Diario).order_by(alchemy.Diario.diario_id.desc()).offset((page - 1) * 1000).limit(1000).all()
    return f.render_template("diarioview_page.html", page=page, entries=entries)
