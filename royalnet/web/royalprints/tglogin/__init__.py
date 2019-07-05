"""A Royalnet Telegram login :py:class:`royalnet.web.Royalprint`."""
import flask as f
import hashlib
import hmac
import datetime
import os
from ... import Royalprint
from ....database.tables import Royal, Telegram


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
rp = Royalprint("tglogin", __name__, url_prefix="/login/telegram", required_tables={Royal, Telegram},
                template_folder=tmpl_dir)


@rp.route("/")
def tglogin_index():
    f.session.pop("royal", None)
    return f.render_template("tglogin_index.html")


@rp.route("/done")
def tglogin_done():
    alchemy, alchemy_session = f.current_app.config["ALCHEMY"], f.current_app.config["ALCHEMY_SESSION"]
    data_check_string = ""
    for field in sorted(list(f.request.args)):
        if field == "hash":
            continue
        data_check_string += f"{field}={f.request.args[field]}\n"
    data_check_string = data_check_string.rstrip("\n")
    data_check = bytes(data_check_string, encoding="ascii")
    secret_key = hashlib.sha256(bytes(f.current_app.config["TG_AK"], encoding="ascii")).digest()
    hex_data = hmac.new(key=secret_key, msg=data_check, digestmod="sha256").hexdigest()
    if hex_data != f.request.args["hash"]:
        return "Invalid authentication", 403
    tg_user = alchemy_session.query(alchemy.Telegram).filter(alchemy.Telegram.tg_id == f.request.args["id"]).one_or_none()
    if tg_user is None:
        return "No such telegram", 404
    royal_user = tg_user.royal
    f.session["royal"] = {
        "uid": royal_user.uid,
        "username": royal_user.username,
        "avatar": royal_user.avatar,
        "role": royal_user.role
    }
    f.session["login_date"] = datetime.datetime.now()
    return f.render_template("tglogin_success.html")
