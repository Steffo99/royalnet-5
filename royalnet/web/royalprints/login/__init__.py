"""A Royalnet password-based login :py:class:`royalnet.web.Royalprint`."""
import flask as f
import os
import datetime
import bcrypt
from ...royalprint import Royalprint
from ...shortcuts import error
from ....database.tables import Royal


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
rp = Royalprint("login", __name__, url_prefix="/login/password", required_tables={Royal},
                template_folder=tmpl_dir)


@rp.route("/")
def login_index():
    f.session.pop("royal", None)
    return f.render_template("login_index.html")


@rp.route("/done", methods=["POST"])
def login_done():
    alchemy, alchemy_session = f.current_app.config["ALCHEMY"], f.current_app.config["ALCHEMY_SESSION"]
    data = f.request.form
    if "username" not in data:
        return error(400, "Nessun username inserito.")
    royal_user = alchemy_session.query(alchemy.Royal).filter_by(username=data["username"]).one_or_none()
    if royal_user is None:
        return error(404, "L'username inserito non corrisponde a nessun account registrato.")
    if "password" not in data:
        return error(400, "Nessuna password inserita.")
    if not bcrypt.checkpw(bytes(data["password"], encoding="utf8"), royal_user.password):
        return error(400, "La password inserita non è valida.")
    f.session["royal"] = {
        "uid": royal_user.uid,
        "username": royal_user.username,
        "avatar": royal_user.avatar,
        "role": royal_user.role
    }
    f.session["login_date"] = datetime.datetime.now()
    return f.render_template("login_success.html")