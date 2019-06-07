import flask as f
import hashlib
import hmac
from ... import Royalprint
from ....database.tables import Royal, Telegram


bp = Royalprint("tglogin", __name__, url_prefix="/login/telegram", required_tables={Royal, Telegram},
                template_folder="templates")


@bp.route("/")
def tglogin_index():
    return f.render_template("tglogin_index.html")


@bp.route("/done")
def tglogin_done():
    from ...alchemyhandler import alchemy, alchemy_session
    data_check_string = ""
    for field in f.request.args:
        if field == "hash":
            continue
        data_check_string += f"{field}={f.request.args['field']}\n"
    data_check_string.rstrip("\n")
    secret_key = hashlib.sha256(f.current_app.config["TG_AK"])
    hex_data = hmac.new(key=secret_key, msg=data_check_string, digestmod="sha256").hexdigest()
    if hex_data != f.request.args["hash"]:
        return "Invalid authentication", 403
    tg_user = alchemy_session.query(alchemy.Telegram).filter(alchemy.Telegram.tg_id == f.request.args["id"]).one_or_none()
    if tg_user is None:
        return "No such telegram", 404
    royal_user = tg_user.royal
    f.session["royal_id"] = royal_user.id
    return f.redirect(f.url_for("/"))
