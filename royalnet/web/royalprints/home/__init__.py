"""Homepage :py:class:`royalnet.web.Royalprint` of the Royal Games website."""
import flask as f
import os
from ... import Royalprint


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
rp = Royalprint("home", __name__, template_folder="templates")


@rp.route("/")
def home_index():
    return f.render_template("home.html")
