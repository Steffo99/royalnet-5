"""A User Games Diario viewer :py:class:`royalnet.web.Royalprint`."""

import flask as f
import os
from ...royalprint import Royalprint
from ...shortcuts import error
from royalnet.packs.common.tables import User
from royalnet.packs.royal.tables import Diario


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
rp = Royalprint("diarioview", __name__, url_prefix="/diario", template_folder=tmpl_dir,
                required_tables={User, Diario})


@rp.route("/", defaults={"page": 1})
@rp.route("/<int:page>")
def diarioview_page(page):
    alchemy, alchemy_session = f.current_app.config["ALCHEMY"], f.current_app.config["ALCHEMY_SESSION"]
    if page < 1:
        return error(404, "Il numero di pagina deve essere maggiore di 0.")
    entries = alchemy_session.query(alchemy.Diario).order_by(alchemy.Diario.diario_id.desc()).offset((page - 1) * 1000).limit(1000).all()
    if len(entries) == 0:
        return error(404, "Non ci sono righe di diario in questa pagina (e in tutte le successive).")
    return f.render_template("diarioview_page.html", page=page, entries=entries)
