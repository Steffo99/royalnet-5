"""A :py:class:`royalnet.web.Royalprint` to create new Royals."""
import flask as f
import os
import bcrypt
from ...royalprint import Royalprint
from ...shortcuts import error
from royalnet.packs.common.tables import User
from royalnet.packs.royal.tables import Alias


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
rp = Royalprint("newaccount", __name__, url_prefix="/newaccount", required_tables={User, Alias},
                template_folder=tmpl_dir)


@rp.route("/", methods=["GET", "POST"])
def login_index():
    if f.request.method == "GET":
        return f.render_template("newaccount_index.html")
    elif f.request.method == "POST":
        alchemy, alchemy_session = f.current_app.config["ALCHEMY"], f.current_app.config["ALCHEMY_SESSION"]
        fd = f.request.form
        if "username" not in fd:
            return error(400, "Non è stato inserito nessun username.")
        if "password" not in fd:
            return error(400, "Non è stata inserita nessuna password.")
        royal = alchemy_session.query(alchemy.User).filter_by(username=fd["username"]).one_or_none()
        if royal is not None:
            return error(403, "Esiste già un utente con quell'username.")
        alias = alchemy_session.query(alchemy.Alias).filter_by(alias=fd["username"]).one_or_none()
        if alias is not None:
            return error(403, "Esiste già un utente con quell'alias.")
        royal = alchemy.Royal(username=fd["username"],
                              password=bcrypt.hashpw(bytes(fd["password"], encoding="utf8"), bcrypt.gensalt()),
                              role="Guest")
        alchemy_session.add(royal)
        alias = alchemy.Alias(royal=royal, alias=royal.username.lower())
        alchemy_session.add(alias)
        alchemy_session.commit()
        return f.redirect(f.url_for("login.login_index"))
