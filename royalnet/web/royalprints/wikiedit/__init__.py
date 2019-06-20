"""A Royal Games Wiki viewer :py:class:`royalnet.web.Royalprint`. Doesn't support any kind of edit."""
import flask as f
import uuid
import os
from ... import Royalprint
from ....database.tables import Royal, WikiPage, WikiRevision


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
rp = Royalprint("wikiedit", __name__, url_prefix="/wikiedit", template_folder=tmpl_dir,
                required_tables={Royal, WikiPage, WikiRevision})


@rp.route("/<uuid:page_id>", defaults={"title": ""}, methods=["GET", "POST"])
@rp.route("/<uuid:page_id>/<title>")
def wikiedit_by_id(page_id: uuid.UUID, title: str):
    alchemy, alchemy_session = f.current_app.config["ALCHEMY"], f.current_app.config["ALCHEMY_SESSION"]
    page = alchemy_session.query(alchemy.WikiPage).filter(alchemy.WikiPage.page_id == page_id).one_or_none()
    if page is None:
        return "No such page", 404

    if f.request.method == "GET":
        return f.render_template("wikiedit_page.html", page=page)

    elif f.request.method == "POST":
        return "Haha doesn't work yet"
