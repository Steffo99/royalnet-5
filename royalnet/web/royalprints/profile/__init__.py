"""The profile page :py:class:`royalnet.web.Royalprint` for Royalnet members."""

import flask as f
import os
from ...royalprint import Royalprint
from ...shortcuts import error
from ....utils.wikirender import prepare_page_markdown, RenderError
from royalnet.packs.royal.tables import *


# Maybe some of these tables are optional...
tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
rp = Royalprint("profile", __name__, url_prefix="/profile", template_folder=tmpl_dir,
                required_tables={User, ActiveKvGroup, Alias, Diario, Discord, Keygroup, Keyvalue, Telegram, WikiPage,
                                 WikiRevision, Bio, TriviaScore})


@rp.route("/")
def profile_index():
    alchemy, alchemy_session = f.current_app.config["ALCHEMY"], f.current_app.config["ALCHEMY_SESSION"]
    royals = alchemy_session.query(alchemy.User).order_by(alchemy.User.username).all()
    return f.render_template("profile_index.html", royals=royals)


@rp.route("/<username>")
def profile_page(username):
    alchemy, alchemy_session = f.current_app.config["ALCHEMY"], f.current_app.config["ALCHEMY_SESSION"]
    royal = alchemy_session.query(alchemy.User).filter_by(username=username).one_or_none()
    if royal is None:
        return error(404, "Non esiste nessun utente con l'username richiesto.")
    if royal.bio is not None and royal.bio.contents != "":
        try:
            parsed_bio = f.Markup(prepare_page_markdown(royal.bio.contents))
        except RenderError as e:
            return error(500, f"Il profilo non può essere visualizzato a causa di un errore nella bio: {str(e)}")
    else:
        parsed_bio = None
    return f.render_template("profile_page.html", royal=royal, parsed_bio=parsed_bio)


@rp.route("/<username>/editbio", methods=["GET", "POST"])
def profile_editbio(username):
    if "royal" not in f.session:
        return error(403, "Devi aver effettuato il login per modificare una bio.")
    alchemy, alchemy_session = f.current_app.config["ALCHEMY"], f.current_app.config["ALCHEMY_SESSION"]
    royal = alchemy_session.query(alchemy.User).filter_by(username=username).one_or_none()
    if not (f.session["royal"]["uid"] == royal.uid or f.session["royal"]["role"] == "Admin"):
        return error(403, "Non sei autorizzato a modificare questa pagina bio.")

    if f.request.method == "GET":
        return f.render_template("profile_editbio.html", royal=royal)

    elif f.request.method == "POST":
        fd = f.request.form
        if royal.bio is None:
            bio = alchemy.Bio(royal=royal, contents=fd.get("contents", ""))
            alchemy_session.add(bio)
        else:
            royal.bio.contents = fd.get("contents", "")
        alchemy_session.commit()
        return f.redirect(f.url_for(".profile_page", username=username))
