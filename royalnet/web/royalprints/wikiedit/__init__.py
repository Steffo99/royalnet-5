"""A User Games Wiki viewer :py:class:`royalnet.web.Royalprint`. Doesn't support any kind of edit."""
import flask as f
import uuid
import os
import datetime
import difflib
from ...royalprint import Royalprint
from ...shortcuts import error, from_urluuid
from royalnet.packs.common.tables import User
from royalnet.packs.royal.tables import WikiPage, WikiRevision


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
rp = Royalprint("wikiedit", __name__, url_prefix="/wiki/edit", template_folder=tmpl_dir,
                required_tables={User, WikiPage, WikiRevision})


@rp.route("/newpage", methods=["GET", "POST"])
def wikiedit_newpage():
    if "royal" not in f.session:
        return error(403, "Devi aver effettuato il login per creare pagine wiki.")

    if f.request.method == "GET":
        return f.render_template("wikiedit_page.html", page=None)

    elif f.request.method == "POST":
        fd = f.request.form
        if not ("title" in fd and "contents" in fd and "css" in fd):
            return error(400, "Uno dei campi obbligatori non è stato compilato. Controlla e riprova!")
        alchemy, alchemy_session = f.current_app.config["ALCHEMY"], f.current_app.config["ALCHEMY_SESSION"]
        page = alchemy.WikiPage(page_id=uuid.uuid4(),
                                title=fd["title"],
                                contents=fd["contents"],
                                format="markdown",
                                css=fd["css"] if fd["css"] != "None" else None)
        revision = alchemy.WikiRevision(revision_id=uuid.uuid4(),
                                        page=page,
                                        author_id=f.session["royal"]["uid"],
                                        timestamp=datetime.datetime.now(),
                                        reason=fd.get("reason"),
                                        diff="\n".join(difflib.unified_diff([], page.contents.split("\n"))))
        alchemy_session.add(page)
        alchemy_session.add(revision)
        alchemy_session.commit()
        return f.redirect(f.url_for("wikiview.wikiview_by_id", page_id=page.page_short_id, title=page.title))


@rp.route("/<page_id>", defaults={"title": ""}, methods=["GET", "POST"])
@rp.route("/<page_id>/<title>", methods=["GET", "POST"])
def wikiedit_by_id(page_id: str, title: str):
    page_uuid = from_urluuid(page_id)
    if "royal" not in f.session:
        return error(403, "Devi aver effettuato il login per modificare pagine wiki.")

    alchemy, alchemy_session = f.current_app.config["ALCHEMY"], f.current_app.config["ALCHEMY_SESSION"]
    page = alchemy_session.query(alchemy.WikiPage).filter(alchemy.WikiPage.page_id == page_uuid).one_or_none()
    if page is None:
        return error(404, "La pagina che stai cercando di modificare non esiste.")

    if f.request.method == "GET":
        return f.render_template("wikiedit_page.html", page=page)

    elif f.request.method == "POST":
        fd = f.request.form
        if not ("title" in fd and "contents" in fd and "css" in fd):
            return error(400, "Uno dei campi obbligatori non è stato compilato. Controlla e riprova!")
        # Create new revision
        revision = alchemy.WikiRevision(revision_id=uuid.uuid4(),
                                        page=page,
                                        author_id=f.session["royal"]["uid"],
                                        timestamp=datetime.datetime.now(),
                                        reason=fd.get("reason"),
                                        diff="\n".join(difflib.unified_diff(page.contents.split("\n"), fd["contents"].split("\n"))))
        alchemy_session.add(revision)
        # Apply changes
        page.contents = fd["contents"]
        page.title = fd["title"]
        page.css = fd["css"] if fd["css"] != "None" else None
        alchemy_session.commit()
        return f.redirect(f.url_for("wikiview.wikiview_by_id", page_id=page.page_short_id, title=page.title))
