import flask as f
import os
from ... import Royalprint


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
bp = Royalprint("home", __name__, template_folder="templates")


@bp.route("/")
def home_index():
    return f.render_template("home.html")
