import flask as f
from ... import Royalprint


bp = Royalprint("home", __name__, template_folder="templates")


@bp.route("/")
def home_index():
    return f.render_template("home.html")
